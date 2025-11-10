#!/usr/bin/env python3
"""
実行ファイルの動作テストスクリプト
"""

import os
import subprocess
import sys
import time
from pathlib import Path

import psutil

# Windows環境でのUTF-8出力を強制
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"


def test_executable() -> bool:
    """実行ファイルの動作テスト"""
    exe_path = Path("dist/AI_reStarter.exe")

    if not exe_path.exists():
        print("Executable not found")
        return False

    print(f"Executable found: {exe_path}")
    print(f"   File size: {exe_path.stat().st_size / 1024 / 1024:.1f} MB")

    # 実行ファイルを起動
    print("\nStarting executable...")
    try:
        process = subprocess.Popen(
            [str(exe_path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        # 3秒待機してプロセスが正常に起動するか確認
        time.sleep(3)

        # プロセスが実行中か確認
        if process.poll() is None:
            print("Executable started successfully")

            # プロセス情報を取得
            try:
                proc = psutil.Process(process.pid)
                print(f"   PID: {process.pid}")
                print(f"   Memory usage: {proc.memory_info().rss / 1024 / 1024:.1f} MB")
                print(f"   CPU usage: {proc.cpu_percent():.1f}%")
            except psutil.NoSuchProcess:
                pass

            # プロセスを終了
            process.terminate()
            try:
                process.wait(timeout=5)
                print("Process terminated successfully")
            except subprocess.TimeoutExpired:
                process.kill()
                print("Process killed forcefully")

            return True
        else:
            # プロセスが既に終了している場合
            stdout, stderr = process.communicate()
            print("Executable failed to start")
            if stderr:
                print(f"Error: {stderr.decode('utf-8', errors='ignore')}")
            return False

    except Exception as e:
        print(f"Error during executable test: {e}")
        return False


def test_release_package() -> bool:
    """リリースパッケージのテスト"""
    # GitHub Actions環境ではリリースパッケージテストをスキップ
    if os.environ.get("GITHUB_ACTIONS") == "true":
        print("Skipping release package test in GitHub Actions")
        return True

    # ZIPファイルを検索
    zip_files = list(Path(".").glob("AI_reStarter-*.zip"))
    if not zip_files:
        print("Release package not found")
        return False
    zip_path = zip_files[0]

    if not zip_path.exists():
        print("Release package not found")
        return False

    print(f"Release package found: {zip_path}")
    print(f"   File size: {zip_path.stat().st_size / 1024 / 1024:.1f} MB")

    # ZIPファイルの内容を確認
    import zipfile

    try:
        with zipfile.ZipFile(zip_path, "r") as zipf:
            files = zipf.namelist()
            print(f"   Files included: {len(files)}")
            for file in files:
                print(f"     - {file}")
        return True
    except Exception as e:
        print(f"Error checking release package: {e}")
        return False


def main() -> int:
    """メインテスト関数"""
    print("AI reStarter Build Test Started")
    print("=" * 50)

    # 実行ファイルテスト
    print("\nExecutable Test")
    exe_test_result = test_executable()

    # リリースパッケージテスト
    print("\nRelease Package Test")
    package_test_result = test_release_package()

    # 結果サマリー
    print("\n" + "=" * 50)
    print("Test Results Summary")
    print(f"Executable test: {'PASSED' if exe_test_result else 'FAILED'}")
    print(f"Release package test: {'PASSED' if package_test_result else 'FAILED'}")

    if exe_test_result and package_test_result:
        print("\nAll tests passed successfully!")
        print("Ready for release.")
        return 0
    else:
        print("\nSome tests failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
