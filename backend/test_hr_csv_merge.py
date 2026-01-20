import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from models import Activity, Record, Session
from hr_csv_merge import merge_offline_hr_csv_into_activity, sanitize_device_name


class TestSanitizeDeviceName(unittest.TestCase):
    """Test device name sanitization for field naming."""
    
    def test_sanitize_none(self):
        self.assertEqual(sanitize_device_name(None), "default")
    
    def test_sanitize_empty(self):
        self.assertEqual(sanitize_device_name(""), "default")
    
    def test_sanitize_with_spaces(self):
        self.assertEqual(sanitize_device_name("Polar H10"), "polar_h10")
    
    def test_sanitize_with_special_chars(self):
        self.assertEqual(sanitize_device_name("Garmin HRM-Dual"), "garmin_hrm_dual")
    
    def test_sanitize_multiple_underscores(self):
        self.assertEqual(sanitize_device_name("Device  Name!!"), "device_name")
    
    def test_sanitize_leading_trailing(self):
        self.assertEqual(sanitize_device_name("  Device123  "), "device123")


class TestHrCsvMerge(unittest.TestCase):
    def _make_activity(self, start: datetime, seconds: int) -> Activity:
        session = Session(start_time=start, total_elapsed_time=float(seconds), avg_speed=3.0)
        records = []
        for i in range(seconds + 1):
            records.append(Record(timestamp=start + timedelta(seconds=i), elapsed_time=float(i)))
        return Activity(
            id="a1",
            name="test",
            file_name="test.fit",
            created_at=start,
            session=session,
            records=records,
            laps=[],
            available_fields=["heart_rate"],
            available_iq_fields=[],
        )

    def test_parse_and_merge_prefers_metadata_align_when_perfect_match(self):
        start = datetime(2025, 12, 15, 20, 18, 18)
        activity = self._make_activity(start, seconds=10)

        # CSV with exact matching timestamps and seconds.
        csv_text = """Name,Sport,Date,Start time,Duration\n""" \
            "ttu,Running,2025-12-15,20:18:18,00:00:10\n" \
            "Time,Second,HR (bpm)\n" \
            "20:18:18,0,120\n" \
            "20:18:19,1,121\n" \
            "20:18:20,2,122\n" \
            "20:18:21,3,123\n" \
            "20:18:22,4,124\n" \
            "20:18:23,5,125\n" \
            "20:18:24,6,126\n" \
            "20:18:25,7,127\n" \
            "20:18:26,8,128\n" \
            "20:18:27,9,129\n" \
            "20:18:28,10,130\n"

        merge_offline_hr_csv_into_activity(activity, csv_text.encode("utf-8"), source_file_name="hr.csv")

        self.assertIsNotNone(activity.merge_provenance)
        assert activity.merge_provenance is not None
        self.assertEqual(activity.merge_provenance.method, "metadata_align")
        # With no device name, should use "default"
        self.assertIn("imported_default_hr", activity.available_iq_fields)
        # Check a few points
        self.assertEqual(activity.records[0].iq_fields.get("imported_default_hr"), 120)
        self.assertEqual(activity.records[10].iq_fields.get("imported_default_hr"), 130)

    def test_merge_uses_interpolation_when_sampling_mismatch(self):
        start = datetime(2025, 12, 15, 20, 18, 18)
        activity = self._make_activity(start, seconds=4)

        # CSV samples every 2 seconds; FIT every 1 second.
        csv_text = """Name,Sport,Date,Start time,Duration\n""" \
            "ttu,Running,2025-12-15,20:18:18,00:00:04\n" \
            "Time,Second,HR (bpm)\n" \
            "20:18:18,0,100\n" \
            "20:18:20,2,110\n" \
            "20:18:22,4,120\n"

        merge_offline_hr_csv_into_activity(activity, csv_text.encode("utf-8"), source_file_name="hr.csv")

        self.assertIsNotNone(activity.merge_provenance)
        assert activity.merge_provenance is not None
        # With only 3 samples, exact matches won't hit match_ratio threshold; should interpolate.
        self.assertEqual(activity.merge_provenance.method, "linear_interpolate")
        self.assertEqual(activity.records[0].iq_fields.get("imported_default_hr"), 100)
        # t=1 should be ~105
        self.assertEqual(activity.records[1].iq_fields.get("imported_default_hr"), 105)
        self.assertEqual(activity.records[2].iq_fields.get("imported_default_hr"), 110)

    def test_merge_handles_naive_csv_with_aware_activity_timestamps(self):
        # Activity timestamps are timezone-aware (e.g., loaded from ISO with Z),
        # while CSV timestamps are timezone-naive. Merge should not crash.
        start = datetime(2025, 12, 15, 20, 18, 18, tzinfo=timezone.utc)
        activity = self._make_activity(start, seconds=2)

        csv_text = """Name,Sport,Date,Start time,Duration\n""" \
            "ttu,Running,2025-12-15,20:18:18,00:00:02\n" \
            "Time,Second,HR (bpm)\n" \
            "20:18:18,0,140\n" \
            "20:18:19,1,141\n" \
            "20:18:20,2,142\n"

        merge_offline_hr_csv_into_activity(activity, csv_text.encode("utf-8"), source_file_name="hr.csv")

        self.assertIsNotNone(activity.merge_provenance)
        self.assertIn("imported_default_hr", activity.available_iq_fields)
        self.assertEqual(activity.records[0].iq_fields.get("imported_default_hr"), 140)

    def test_merge_adjusts_local_csv_time_against_utc_activity(self):
        """Naive CSV times recorded in local timezone should align with UTC FIT timestamps."""
        start = datetime(2025, 12, 15, 12, 18, 18, tzinfo=timezone.utc)
        activity = self._make_activity(start, seconds=2)

        # CSV shows local time 20:18:18 (UTC+8) while FIT start_time is 12:18:18Z.
        csv_text = """Name,Sport,Date,Start time,Duration\n""" \
            "ttu,Running,2025-12-15,20:18:18,00:00:02\n" \
            "Time,Second,HR (bpm)\n" \
            "20:18:18,0,140\n" \
            "20:18:19,1,141\n" \
            "20:18:20,2,142\n"

        class _FixedDatetime(datetime):
            @classmethod
            def now(cls, tz=None):  # type: ignore[override]
                # Simulate a UTC+8 local timezone to trigger the drift correction path.
                return datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone(timedelta(hours=8)))

        with patch("hr_csv_merge.datetime", _FixedDatetime):
            merge_offline_hr_csv_into_activity(activity, csv_text.encode("utf-8"), source_file_name="hr.csv")

        self.assertIn("imported_default_hr", activity.available_iq_fields)
        self.assertEqual(activity.records[0].iq_fields.get("imported_default_hr"), 140)
        assert activity.merge_provenance is not None
        dropped_ratio = activity.merge_provenance.stats.dropped_ratio
        self.assertIsNotNone(dropped_ratio)
        self.assertLess(dropped_ratio, 1.0)

    def test_merge_with_device_name_sanitizes_field_key(self):
        """Test that device name is sanitized for field naming."""
        start = datetime(2025, 12, 15, 20, 18, 18)
        activity = self._make_activity(start, seconds=2)

        # CSV with device name containing spaces
        csv_text = """Name,Sport,Date,Start time,Duration,Device Name\n""" \
            "ttu,Running,2025-12-15,20:18:18,00:00:02,Polar H10\n" \
            "Time,Second,HR (bpm)\n" \
            "20:18:18,0,140\n" \
            "20:18:19,1,141\n" \
            "20:18:20,2,142\n"

        merge_offline_hr_csv_into_activity(activity, csv_text.encode("utf-8"), source_file_name="hr.csv")

        # Should create field "imported_polar_h10_hr"
        self.assertIn("imported_polar_h10_hr", activity.available_iq_fields)
        self.assertEqual(activity.records[0].iq_fields.get("imported_polar_h10_hr"), 140)

    def test_csv_missing_header_raises_error(self):
        """Test that missing header row raises ValueError."""
        start = datetime(2025, 12, 15, 20, 18, 18)
        activity = self._make_activity(start, seconds=2)

        # CSV without proper header
        csv_text = """Name,Sport,Date,Start time,Duration\n""" \
            "ttu,Running,2025-12-15,20:18:18,00:00:02\n" \
            "20:18:18,0,140\n"

        with self.assertRaises(ValueError) as cm:
            merge_offline_hr_csv_into_activity(activity, csv_text.encode("utf-8"), source_file_name="hr.csv")
        
        self.assertIn("未找到数据区表头", str(cm.exception))

    def test_csv_no_valid_data_raises_error(self):
        """Test that CSV with no valid data raises ValueError."""
        start = datetime(2025, 12, 15, 20, 18, 18)
        activity = self._make_activity(start, seconds=2)

        # CSV with header but no valid data rows
        csv_text = """Name,Sport,Date,Start time,Duration\n""" \
            "ttu,Running,2025-12-15,20:18:18,00:00:02\n" \
            "Time,Second,HR (bpm)\n"

        with self.assertRaises(ValueError) as cm:
            merge_offline_hr_csv_into_activity(activity, csv_text.encode("utf-8"), source_file_name="hr.csv")
        
        self.assertIn("无有效心率样本", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
