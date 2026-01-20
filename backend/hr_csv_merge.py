"""Offline HR CSV merge utilities.

This module supports merging a specific HR CSV format (as provided by the user) into an
existing Activity by aligning timestamps to the Activity record timeline.

Key behavior:
- Only reads the first 3 columns in data rows: Time, Second, HR (bpm)
- Uses Second column to correct/derive the time axis
- Uses Activity record timestamps as the target timeline (does not resample FIT)
- Auto-decides between metadata alignment vs linear interpolation
"""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from datetime import date as date_cls
from datetime import datetime, timedelta, timezone
from typing import Iterable, List, Optional, Sequence, Tuple

from models import Activity, HrMergeOptions, MergeCriteria, MergeProvenance, MergeSource, MergeStats
import re

try:
    import config as app_config
except Exception:  # pragma: no cover
    app_config = None


def sanitize_device_name(device_name: Optional[str]) -> str:
    """Clean device name to be a valid field identifier.
    
    Examples:
        "Polar H10" -> "polar_h10"
        "Garmin HRM-Dual" -> "garmin_hrm_dual"
        None -> "default"
    """
    if not device_name:
        return "default"
    # Convert to lowercase, replace spaces and special chars with underscore
    cleaned = re.sub(r'[^a-z0-9]+', '_', device_name.lower())
    # Remove leading/trailing underscores
    cleaned = cleaned.strip('_')
    return cleaned if cleaned else "default"


@dataclass(frozen=True)
class HrSample:
    t: datetime
    bpm: int


@dataclass(frozen=True)
class ParsedHrCsv:
    source_file_name: Optional[str]
    device_name: Optional[str]
    samples: List[HrSample]


def _decode_text(file_bytes: bytes) -> str:
    """Best-effort decode; CSV may come from Excel/Windows tooling."""
    for encoding in ("utf-8-sig", "utf-8", "gbk"):
        try:
            return file_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue
    # Last resort: replace errors
    return file_bytes.decode("utf-8", errors="replace")


def _parse_date_from_summary(rows: Sequence[Sequence[str]]) -> Optional[date_cls]:
    """Try to read Date from the summary section near the top of the CSV."""
    # The sample has:
    #   Name,Sport,Date,Start time,...
    #   ttu,Running,2025-12-15,20:18:18,...
    for i in range(min(len(rows) - 1, 50)):
        header = [c.strip().lower() for c in rows[i]]
        if len(header) >= 4 and header[:4] == ["name", "sport", "date", "start time"]:
            values = rows[i + 1]
            if len(values) >= 3:
                raw_date = values[2].strip()
                try:
                    return datetime.strptime(raw_date, "%Y-%m-%d").date()
                except ValueError:
                    return None
    return None


def _extract_device_name(rows: Sequence[Sequence[str]]) -> Optional[str]:
    """Extract device name from CSV metadata block if present.
    
    Supports two formats:
    1. Standalone label format:
        Device Name
        Polar H10
    2. Header column format:
        Name,Sport,Date,Start time,Duration,Device Name
        ttu,Running,2025-12-15,20:18:18,00:00:02,Polar H10
    """
    # Try header column format first
    for i in range(min(len(rows) - 1, 50)):
        header = [c.strip().lower() for c in rows[i]]
        try:
            device_idx = header.index("device name")
            # Check next row for value
            if i + 1 < len(rows) and len(rows[i + 1]) > device_idx:
                device_value = rows[i + 1][device_idx].strip()
                if device_value:
                    return device_value
        except ValueError:
            pass
    
    # Try standalone label format
    for i in range(min(len(rows) - 1, 200)):
        if not rows[i]:
            continue
        first = rows[i][0].strip().lower()
        if first == "device name":
            # The next row typically contains the actual device name in col1.
            for j in range(i + 1, min(i + 6, len(rows))):
                if rows[j] and rows[j][0].strip() and rows[j][0].strip().lower() != "device name":
                    return rows[j][0].strip()
            return None
    return None


def _parse_time_cell(time_cell: str, base_date: Optional[date_cls]) -> Optional[datetime]:
    v = (time_cell or "").strip()
    if not v:
        return None

    # Common formats:
    # - "2025-12-15 20:18:18"
    # - "2025/12/15 20:18:18"
    # - "20:18:18" (needs base_date)
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(v, fmt)
        except ValueError:
            pass

    # Time only
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            t = datetime.strptime(v, fmt).time()
            if base_date is None:
                return None
            return datetime.combine(base_date, t)
        except ValueError:
            pass

    return None


def parse_offline_hr_csv(file_bytes: bytes, source_file_name: Optional[str] = None) -> ParsedHrCsv:
    """Parse the provided offline HR CSV format into corrected (timestamp, bpm) samples."""
    text = _decode_text(file_bytes)

    reader = csv.reader(io.StringIO(text))
    rows = [row for row in reader if row is not None]

    base_date = _parse_date_from_summary(rows)
    device_name = _extract_device_name(rows)

    # Find the data header row: starts with "Time,Second,HR"
    data_header_idx = None
    for i in range(len(rows)):
        if len(rows[i]) < 3:
            continue
        c0 = rows[i][0].strip().lower()
        c1 = rows[i][1].strip().lower()
        c2 = rows[i][2].strip().lower()
        if c0 == "time" and c1 == "second" and (c2.startswith("hr") or "bpm" in c2):
            data_header_idx = i
            break

    if data_header_idx is None:
        raise ValueError("CSV格式错误：未找到数据区表头(Time,Second,HR (bpm))")

    raw_samples: List[Tuple[datetime, float, int]] = []

    for row in rows[data_header_idx + 1 :]:
        if len(row) < 3:
            continue
        time_cell, sec_cell, hr_cell = row[0], row[1], row[2]

        t_raw = _parse_time_cell(time_cell, base_date)
        if t_raw is None:
            continue

        try:
            sec = float(sec_cell.strip())
        except ValueError:
            continue

        try:
            bpm = int(float(hr_cell.strip()))
        except ValueError:
            continue

        raw_samples.append((t_raw, sec, bpm))

    if not raw_samples:
        raise ValueError("CSV格式错误：数据区无有效心率样本，请检查Time/Second/HR列是否正确")

    # Correct timeline using Second column.
    t0, s0, _ = raw_samples[0]
    samples: List[HrSample] = []
    for t_raw, s, bpm in raw_samples:
        t_corr = t0 + timedelta(seconds=(s - s0))
        samples.append(HrSample(t=t_corr, bpm=bpm))

    # Ensure sorted by corrected time (Second can have duplicates; keep stable order)
    samples.sort(key=lambda x: x.t)

    return ParsedHrCsv(source_file_name=source_file_name, device_name=device_name, samples=samples)


def _effective_options(options: Optional[HrMergeOptions]) -> MergeCriteria:
    def _cfg(name: str, fallback):
        if app_config is None:
            return fallback
        return getattr(app_config, name, fallback)

    return MergeCriteria(
        auto_align_max_shift_sec=(
            options.auto_align_max_shift_sec
            if options and options.auto_align_max_shift_sec is not None
            else _cfg("HR_MERGE_AUTO_ALIGN_MAX_SHIFT_SEC", 8)
        ),
        auto_align_match_tolerance_sec=(
            options.auto_align_match_tolerance_sec
            if options and options.auto_align_match_tolerance_sec is not None
            else _cfg("HR_MERGE_AUTO_ALIGN_MATCH_TOLERANCE_SEC", 1)
        ),
        auto_align_min_match_ratio=(
            options.auto_align_min_match_ratio
            if options and options.auto_align_min_match_ratio is not None
            else _cfg("HR_MERGE_AUTO_ALIGN_MIN_MATCH_RATIO", 0.85)
        ),
        interpolate_max_gap_sec=(
            options.interpolate_max_gap_sec
            if options and options.interpolate_max_gap_sec is not None
            else _cfg("HR_MERGE_INTERPOLATE_MAX_GAP_SEC", 5)
        ),
        allow_extrapolation=(
            options.allow_extrapolation
            if options and options.allow_extrapolation is not None
            else bool(_cfg("HR_MERGE_ALLOW_EXTRAPOLATION", False))
        ),
    )


def _get_activity_base_timestamp(activity: Activity) -> Optional[datetime]:
    if activity.session and activity.session.start_time is not None:
        return activity.session.start_time
    for r in activity.records:
        if r.timestamp is not None:
            return r.timestamp
    return None


def _record_datetime(activity: Activity, base_ts: datetime, record_index: int) -> Optional[datetime]:
    r = activity.records[record_index]
    if r.timestamp is not None:
        return r.timestamp
    if r.elapsed_time is not None:
        return base_ts + timedelta(seconds=float(r.elapsed_time))
    return None


def _coerce_to_base_timezone(dt: datetime, base_ts: datetime) -> datetime:
    """Coerce dt to be compatible with base_ts for arithmetic.

    Python forbids subtracting offset-aware and offset-naive datetimes.
    We normalize datetimes so relative-second calculations are safe.

    Policy:
    - If base_ts is timezone-aware:
      - naive dt is assumed to be in base_ts's timezone (attach tzinfo)
      - aware dt is converted to base_ts's timezone
    - If base_ts is timezone-naive:
      - aware dt is converted to UTC then made naive
      - naive dt is kept as-is
    """

    if base_ts.tzinfo is None:
        if dt.tzinfo is None:
            return dt
        # Make arithmetic possible; keep a deterministic mapping.
        try:
            return dt.astimezone(timezone.utc).replace(tzinfo=None)
        except Exception:
            return dt.replace(tzinfo=None)

    base_tz = base_ts.tzinfo
    if dt.tzinfo is None:
        # First assume CSV time is recorded in the same timezone as base_ts.
        candidate = dt.replace(tzinfo=base_tz)
        # Normalize to builtin datetime to avoid subclass arithmetic issues.
        try:
            candidate = datetime.fromtimestamp(candidate.timestamp(), tz=base_tz)
        except Exception:
            pass

        # If the assumed alignment is off by many hours (typical UTC/local drift),
        # fallback to treating the CSV timestamp as local time and convert to base_tz.
        try:
            drift = abs((candidate - base_ts).total_seconds())
        except Exception:
            drift = None

        if drift is not None and drift > 6 * 3600:
            try:
                local_tz = datetime.now().astimezone().tzinfo
                if local_tz is not None:
                    localized = dt.replace(tzinfo=local_tz).astimezone(base_tz)
                    return datetime.fromtimestamp(localized.timestamp(), tz=base_tz)
            except Exception:
                pass

        return candidate
    coerced = dt.astimezone(base_tz)
    try:
        return datetime.fromtimestamp(coerced.timestamp(), tz=base_tz)
    except Exception:
        return coerced


def _nearest_index(sorted_times: Sequence[float], t: float) -> int:
    # Equivalent to bisect_left but avoids importing bisect in tight loops.
    lo = 0
    hi = len(sorted_times)
    while lo < hi:
        mid = (lo + hi) // 2
        if sorted_times[mid] < t:
            lo = mid + 1
        else:
            hi = mid
    return lo


def _find_nearest_time(sorted_times: Sequence[float], t: float) -> Optional[float]:
    if not sorted_times:
        return None
    i = _nearest_index(sorted_times, t)
    candidates = []
    if 0 <= i < len(sorted_times):
        candidates.append(sorted_times[i])
    if 0 <= i - 1 < len(sorted_times):
        candidates.append(sorted_times[i - 1])
    if not candidates:
        return None
    return min(candidates, key=lambda x: abs(x - t))


def _has_match_within(sorted_times: Sequence[float], t: float, tol: float) -> bool:
    if not sorted_times:
        return False
    i = _nearest_index(sorted_times, t)
    if i < len(sorted_times) and abs(sorted_times[i] - t) <= tol:
        return True
    if i > 0 and abs(sorted_times[i - 1] - t) <= tol:
        return True
    return False


def _interpolate_value(
    sample_times: Sequence[float],
    sample_values: Sequence[int],
    t: float,
    max_gap: float,
    allow_extrapolation: bool,
) -> Optional[int]:
    if not sample_times:
        return None

    i = _nearest_index(sample_times, t)

    # Exact or right-neighbor
    if i < len(sample_times) and sample_times[i] == t:
        return int(sample_values[i])

    # Left and right bracketing
    left_i = i - 1
    right_i = i

    if left_i < 0:
        if not allow_extrapolation:
            return None
        # Extrapolate using first point
        return int(sample_values[0])

    if right_i >= len(sample_times):
        if not allow_extrapolation:
            return None
        # Extrapolate using last point
        return int(sample_values[-1])

    t0 = sample_times[left_i]
    t1 = sample_times[right_i]
    if t1 <= t0:
        return int(sample_values[left_i])

    if (t1 - t0) > max_gap:
        return None

    v0 = float(sample_values[left_i])
    v1 = float(sample_values[right_i])
    alpha = (t - t0) / (t1 - t0)
    v = (1.0 - alpha) * v0 + alpha * v1
    return int(round(v))


def merge_offline_hr_csv_into_activity(
    activity: Activity,
    file_bytes: bytes,
    source_file_name: Optional[str] = None,
    options: Optional[HrMergeOptions] = None,
) -> Activity:
    """Merge offline HR CSV into an existing activity (mutates and returns activity)."""
    parsed = parse_offline_hr_csv(file_bytes, source_file_name=source_file_name)

    criteria = _effective_options(options)

    base_ts = _get_activity_base_timestamp(activity)
    if base_ts is None:
        raise ValueError("目标活动缺少可用于对齐的起始时间戳")

    # Build CSV time/value arrays in seconds relative to base timestamp.
    csv_times: List[float] = []
    csv_values: List[int] = []
    for s in parsed.samples:
        t_corr = _coerce_to_base_timezone(s.t, base_ts)
        csv_times.append((t_corr - base_ts).total_seconds())
        csv_values.append(int(s.bpm))

    if not csv_times:
        raise ValueError("CSV心率样本为空")

    # FIT record timeline in seconds relative to base_ts
    fit_times: List[Optional[float]] = []
    for i in range(len(activity.records)):
        dt = _record_datetime(activity, base_ts, i)
        if dt is not None:
            dt = _coerce_to_base_timezone(dt, base_ts)
        fit_times.append((dt - base_ts).total_seconds() if dt is not None else None)

    # Auto choose offset by simple histogram on nearest-neighbor deltas.
    max_shift = float(criteria.auto_align_max_shift_sec or 0)
    tol = float(criteria.auto_align_match_tolerance_sec or 0)

    # Sample a subset to keep runtime bounded.
    # Use float deltas and bin them to 0.1s resolution for sub-second precision.
    deltas: List[float] = []
    for t in (t for t in fit_times[: min(800, len(fit_times))] if t is not None):
        nearest = _find_nearest_time(csv_times, float(t))
        if nearest is None:
            continue
        delta = nearest - float(t)
        if abs(delta) <= (max_shift + tol):
            deltas.append(delta)

    best_offset = 0.0
    if deltas:
        # Bin deltas to 0.1s resolution for histogram
        counts = {}
        for d in deltas:
            if abs(d) <= max_shift:
                binned = round(d * 10) / 10.0  # Round to nearest 0.1s
                counts[binned] = counts.get(binned, 0) + 1
        if counts:
            best_offset = max(counts.items(), key=lambda kv: kv[1])[0]

    # Evaluate match ratio
    matched_near = 0
    matched_exact = 0
    total = 0
    exact_tol = min(0.2, tol / 5.0) if tol > 0 else 0.0
    for t in fit_times:
        if t is None:
            continue
        total += 1
        target = float(t) + float(best_offset)
        if _has_match_within(csv_times, target, tol):
            matched_near += 1
        if exact_tol > 0 and _has_match_within(csv_times, target, exact_tol):
            matched_exact += 1

    match_ratio = (matched_exact / total) if total else 0.0

    method = "linear_interpolate"
    if total and match_ratio >= float(criteria.auto_align_min_match_ratio or 0):
        method = "metadata_align"

    # Decide IQ key with sanitized device name
    sanitized_device = sanitize_device_name(parsed.device_name)
    iq_key = f"imported_{sanitized_device}_hr"

    # Merge values into records
    dropped = 0
    interpolated = 0

    for i, t in enumerate(fit_times):
        if t is None:
            dropped += 1
            continue
        target_t = float(t) + float(best_offset)

        value: Optional[int]
        if method == "metadata_align":
            # Take nearest raw CSV value within tolerance.
            nearest_idx = _nearest_index(csv_times, target_t)
            candidates: List[Tuple[float, int]] = []
            if 0 <= nearest_idx < len(csv_times):
                candidates.append((abs(csv_times[nearest_idx] - target_t), nearest_idx))
            if 0 <= nearest_idx - 1 < len(csv_times):
                candidates.append((abs(csv_times[nearest_idx - 1] - target_t), nearest_idx - 1))
            if not candidates:
                value = None
            else:
                _, idx = min(candidates, key=lambda x: x[0])
                if abs(csv_times[idx] - target_t) <= exact_tol:
                    value = int(csv_values[idx])
                else:
                    value = None
                    dropped += 1
        else:
            value = _interpolate_value(
                csv_times,
                csv_values,
                target_t,
                max_gap=float(criteria.interpolate_max_gap_sec or 0),
                allow_extrapolation=bool(criteria.allow_extrapolation),
            )
            if value is None:
                dropped += 1
            else:
                interpolated += 1

        if value is not None:
            activity.records[i].iq_fields[iq_key] = value

    # Update available IQ fields
    if iq_key not in activity.available_iq_fields:
        activity.available_iq_fields.append(iq_key)
        activity.available_iq_fields.sort()

    total_records = sum(1 for t in fit_times if t is not None)
    dropped_ratio = (dropped / total_records) if total_records else None
    interp_ratio = (interpolated / total_records) if total_records else None

    activity.merge_provenance = MergeProvenance(
        method=method,
        decision="auto",
        sources=[
            MergeSource(file_name=parsed.source_file_name, device_name=parsed.device_name)
        ],
        criteria=criteria,
        stats=MergeStats(
            offset_sec=float(best_offset),
            match_ratio=match_ratio,
            interp_ratio=interp_ratio,
            dropped_ratio=dropped_ratio,
        ),
    )

    return activity
