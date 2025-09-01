#!/usr/bin/env python3
"""
実行ファイルの動作テストスクリプト
"""
import subprocess
import sys
import time
from pathlib import Path

import psutil


def test_executable():
    """実行ファイルの動作テスト"""
    exe_path = Path("dist/AI_reStarter.exe")

    if not exe_path.exists():
        print("実行ファイルが見つかりません")
        return False

    print(f"実行ファイルを確認: {exe_path}")
    print(f"   ファイルサイズ: {exe_path.stat().st_size / 1024 / 1024:.1f} MB")

    # 実行ファイルを起動
    print("\n実行ファイルを起動中...")
    try:
        process = subprocess.Popen(
            [str(exe_path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )

        # 3秒待機してプロセスが正常に起動するか確認
        time.sleep(3)

        # プロセスが実行中か確認
        if process.poll() is None:
            print("実行ファイルが正常に起動しました")

            # プロセス情報を取得
            try:
                proc = psutil.Process(process.pid)
                print(f"   PID: {process.pid}")
                print(f"   メモリ使用量: {proc.memory_info().rss / 1024 / 1024:.1f} MB")
                print(f"   CPU使用率: {proc.cpu_percent():.1f}%")
            except psutil.NoSuchProcess:
                pass

            # プロセスを終了
            process.terminate()
            try:
                process.wait(timeout=5)
                print("プロセスを正常に終了しました")
            except subprocess.TimeoutExpired:
                process.kill()
                print("プロセスを強制終了しました")

            return True
        else:
            # プロセスが既に終了している場合
            stdout, stderr = process.communicate()
            print("実行ファイルが起動に失敗しました")
            if stderr:
                print(f"エラー: {stderr.decode('utf-8', errors='ignore')}")
            return False

    except Exception as e:
        print(f"実行ファイルのテストでエラーが発生: {e}")
        return False


def test_release_package():
    """リリースパッケージのテスト"""
    # ZIPファイルを検索
    zip_files = list(Path(".").glob("AI_reStarter-*.zip"))
    if not zip_files:
        print("リリースパッケージが見つかりません")
        return False
    zip_path = zip_files[0]

    if not zip_path.exists():
        print("リリースパッケージが見つかりません")
        return False

    print(f"リリースパッケージを確認: {zip_path}")
    print(f"   ファイルサイズ: {zip_path.stat().st_size / 1024 / 1024:.1f} MB")

    # ZIPファイルの内容を確認
    import zipfile

    try:
        with zipfile.ZipFile(zip_path, "r") as zipf:
            files = zipf.namelist()
            print(f"   含まれるファイル数: {len(files)}")
            for file in files:
                print(f"     - {file}")
        return True
    except Exception as e:
        print(f"リリースパッケージの確認でエラー: {e}")
        return False


def main():
    """メインテスト関数"""
    print("AI reStarter ビルドテスト開始")
    print("=" * 50)

    # 実行ファイルテスト
    print("\n実行ファイルテスト")
    exe_test_result = test_executable()

    # リリースパッケージテスト
    print("\nリリースパッケージテスト")
    package_test_result = test_release_package()

    # 結果サマリー
    print("\n" + "=" * 50)
    print("テスト結果サマリー")
    print(f"実行ファイルテスト: {'成功' if exe_test_result else '失敗'}")
    print(f"リリースパッケージテスト: {'成功' if package_test_result else '失敗'}")

    if exe_test_result and package_test_result:
        print("\nすべてのテストが成功しました！")
        print("リリース準備完了です。")
        return 0
    else:
        print("\n一部のテストが失敗しました。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
