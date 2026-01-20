"""
FIT Running Data Analyzer - Build Script
Package application using PyInstaller for Windows and macOS
"""
import os
import sys
import shutil
import subprocess
import platform
import zipfile
from pathlib import Path

def main():
    # Import version from config
    sys.path.insert(0, str(Path(__file__).parent))
    from config import VERSION
    
    # Detect platform
    system = platform.system()
    is_windows = system == 'Windows'
    is_macos = system == 'Darwin'
    
    print("=" * 60)
    print("FIT Running Data Analyzer - Build Tool")
    print(f"Version: {VERSION}")
    print(f"Platform: {system}")
    print("=" * 60)
    print()
    
    # Ensure in correct directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Check virtual environment
    if is_windows:
        venv_python = script_dir / ".venv" / "Scripts" / "python.exe"
    else:
        venv_python = script_dir / ".venv" / "bin" / "python"
    
    if not venv_python.exists():
        print(f"[ERROR] Virtual environment not found at {venv_python}")
        print(f"Please run {'run.bat' if is_windows else 'run.sh'} to initialize environment")
        return 1
    
    # Install PyInstaller
    print("[1/3] Installing PyInstaller...")
    result = subprocess.run(
        [str(venv_python), "-m", "pip", "install", "pyinstaller"],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"[ERROR] Failed to install PyInstaller: {result.stderr}")
        return 1
    print("      ✓ PyInstaller installed successfully")
    print()
    
    # Clean old build files
    print("[2/3] Cleaning old build files...")
    for dir_name in ["build", "dist"]:
        dir_path = script_dir / dir_name
        if dir_path.exists():
            try:
                # On Windows, use rmtree with error handler for locked files
                def handle_remove_readonly(func, path, exc):
                    """Error handler for Windows readonly/locked files"""
                    import stat
                    import time
                    # Try to change permissions and retry
                    try:
                        os.chmod(path, stat.S_IWRITE)
                        func(path)
                    except Exception:
                        # If still fails, wait and retry once
                        time.sleep(0.5)
                        try:
                            func(path)
                        except Exception:
                            print(f"      ⚠ Warning: Could not delete {path}")
                
                shutil.rmtree(dir_path, onerror=handle_remove_readonly)
                print(f"      ✓ Deleted {dir_name}/")
            except Exception as e:
                print(f"      ⚠ Warning: Could not fully delete {dir_name}/: {e}")
                print(f"      → Continuing build anyway...")
    print()
    
    # Execute packaging
    print("[3/3] Building application (this may take a few minutes)...")
    result = subprocess.run(
        [str(venv_python), "-m", "PyInstaller", "fitanalysis.spec"],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"[ERROR] Build failed:")
        print(result.stderr)
        return 1
    
    print("      ✓ Build successful!")
    print()
    
    # Check output
    dist_dir = script_dir / "dist"
    
    if is_macos:
        # macOS generates .app bundle
        app_bundle = dist_dir / "fitanalysis.app"
        if app_bundle.exists():
            print("=" * 60)
            print("✓ Build Complete!")
            print("=" * 60)
            print()
            print(f"Application location: {app_bundle}")
            print()
            print("Usage:")
            print("1. Double-click fitanalysis.app to launch")
            print("2. Browser will automatically open at http://127.0.0.1:8082")
            print("3. Press Ctrl+C in the terminal window to stop server")
            print()
            
            # Copy documentation
            print("Copying documentation...")
            for doc in ["README.md", f"RELEASE_v{VERSION}.md"]:
                src = script_dir / doc
                dst = dist_dir / doc
                if src.exists():
                    shutil.copy2(src, dst)
                    print(f"  ✓ Copied {doc}")
            print()
            
            # Create ZIP package
            zip_name = f"fitanalysis-{VERSION}-macos.zip"
            zip_path = dist_dir / zip_name
            print(f"Creating ZIP package: {zip_name}")
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add .app bundle recursively
                for root, dirs, files in os.walk(app_bundle):
                    for file in files:
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(dist_dir)
                        zipf.write(file_path, arcname)
                # Add documentation
                for doc in ["README.md", f"RELEASE_v{VERSION}.md"]:
                    doc_path = dist_dir / doc
                    if doc_path.exists():
                        zipf.write(doc_path, doc)
            print(f"  ✓ Created {zip_path}")
            print()
            return 0
    else:
        # Windows generates exe in folder
        exe_dir = dist_dir / "fitanalysis"
        exe_file = exe_dir / "fitanalysis.exe"
        
        if exe_file.exists():
            print("=" * 60)
            print("✓ Build Complete!")
            print("=" * 60)
            print()
            print(f"Executable location: {exe_dir}")
            print(f"Main program: {exe_file.name}")
            print()
            print("Usage:")
            print("1. Copy entire dist/fitanalysis folder to target machine")
            print("2. Double-click start_server.bat or fitanalysis.exe")
            print("3. Browser will automatically open at http://127.0.0.1:8082")
            print()
            
            # Create startup script (English)
            start_script = exe_dir / "start_server.bat"
            with open(start_script, "w", encoding="utf-8") as f:
                f.write("@echo off\n")
                f.write("chcp 65001 >nul\n")
                f.write("echo ==========================================\n")
                f.write("echo FIT Running Data Analyzer\n")
                f.write(f"echo Version: {VERSION}\n")
                f.write("echo ==========================================\n")
                f.write("echo.\n")
                f.write("echo Starting server...\n")
                f.write("echo Access at: http://127.0.0.1:8082\n")
                f.write("echo Press Ctrl+C to stop server\n")
                f.write("echo.\n")
                f.write("fitanalysis.exe\n")
                f.write("pause\n")
            print(f"Created startup script: {start_script.name}")
            print()
            
            # Copy documentation
            print("Copying documentation...")
            for doc in ["README.md", f"RELEASE_v{VERSION}.md"]:
                src = script_dir / doc
                dst = exe_dir / doc
                if src.exists():
                    shutil.copy2(src, dst)
                    print(f"  ✓ Copied {doc}")
            print()
            
            # Create ZIP package
            zip_name = f"fitanalysis-{VERSION}-windows.zip"
            zip_path = dist_dir / zip_name
            print(f"Creating ZIP package: {zip_name}")
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add entire fitanalysis directory recursively
                for root, dirs, files in os.walk(exe_dir):
                    for file in files:
                        file_path = Path(root) / file
                        arcname = Path("fitanalysis") / file_path.relative_to(exe_dir)
                        zipf.write(file_path, arcname)
            print(f"  ✓ Created {zip_path}")
            print()
            return 0
    
    print("[ERROR] Executable not found")
    return 1

if __name__ == "__main__":
    sys.exit(main())
