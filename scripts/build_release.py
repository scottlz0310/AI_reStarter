#!/usr/bin/env python3
"""
AI reStarter リリースビルドスクリプト
"""
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


def run_command(command, description):
    """コマンドを実行し、結果を表示"""
    print(f"\n{description}...")
    try:
        subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        print(f"{description}完了")
        return True
    except subprocess.CalledProcessError as e:
        print(f"{description}失敗: {e}")
        if e.stdout:
            print(f"stdout: {e.stdout}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        return False


def clean_build_directories():
    """ビルドディレクトリをクリーンアップ"""
    print("\nビルドディレクトリをクリーンアップ中...")
    dirs_to_clean = ["build", "dist", "release"]
    for dir_name in dirs_to_clean:
        dir_path = Path(dir_name)
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"{dir_name}/ を削除")

    # 古いZIPファイルを削除
    for zip_file in Path(".").glob("AI_reStarter-*.zip"):
        zip_file.unlink()
        print(f"{zip_file} を削除")


def create_release_package():
    """リリースパッケージを作成"""
    print("\nリリースパッケージを作成中...")

    # releaseディレクトリを作成
    release_dir = Path("release")
    release_dir.mkdir(exist_ok=True)

    # 必要なファイルをコピー
    files_to_copy = [
        ("dist/AI_reStarter.exe", "AI_reStarter.exe"),
        ("README.md", "README.md"),
        ("kiro_config.json", "kiro_config.json"),
    ]

    for src, dst in files_to_copy:
        src_path = Path(src)
        dst_path = release_dir / dst
        if src_path.exists():
            shutil.copy2(src_path, dst_path)
            print(f"{src} -> {dst}")
        else:
            print(f"{src} が見つかりません")
            return False

    # テンプレートディレクトリをコピー
    template_dirs = ["amazonq_templates", "error_templates"]
    for template_dir in template_dirs:
        src_dir = Path(template_dir)
        dst_dir = release_dir / template_dir
        if src_dir.exists():
            shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)
            print(f"{template_dir}/ をコピー")

    return True


def create_zip_package():
    """ZIPパッケージを作成"""
    print("\nZIPパッケージを作成中...")

    # バージョン情報を取得
    version = "v0.1.0"  # pyproject.tomlから取得することも可能
    zip_path = Path(f"AI_reStarter-{version}.zip")
    release_dir = Path("release")

    if zip_path.exists():
        zip_path.unlink()

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _dirs, files in os.walk(release_dir):
            for file in files:
                file_path = Path(root) / file
                arc_path = file_path.relative_to(release_dir)
                zipf.write(file_path, arc_path)

    print(f"{zip_path} を作成 ({zip_path.stat().st_size / 1024 / 1024:.1f} MB)")
    return True


def main():
    """メインビルドプロセス"""
    print("AI reStarter リリースビルド開始")
    print("=" * 50)

    # 仮想環境の確認
    if not Path("venv").exists():
        print("仮想環境が見つかりません。先に仮想環境を作成してください。")
        return 1

    # ビルドディレクトリのクリーンアップ
    clean_build_directories()

    # テストの実行
    if not run_command("venv\\Scripts\\activate && pytest tests/ -v", "テスト実行"):
        print("テストが失敗しました。ビルドを中止します。")
        return 1

    # PyInstallerでビルド
    if not run_command(
        "venv\\Scripts\\activate && pyinstaller --onefile --windowed --name AI_reStarter main.py",
        "PyInstallerビルド",
    ):
        print("ビルドが失敗しました。")
        return 1

    # リリースパッケージの作成
    if not create_release_package():
        print("リリースパッケージの作成が失敗しました。")
        return 1

    # ZIPパッケージの作成
    if not create_zip_package():
        print("ZIPパッケージの作成が失敗しました。")
        return 1

    # 最終テスト
    if not run_command(
        "venv\\Scripts\\activate && python test_executable.py", "最終テスト"
    ):
        print("最終テストが失敗しました。")
        return 1

    print("\n" + "=" * 50)
    print("リリースビルドが完了しました！")
    print("\n作成されたファイル:")
    print("  - dist/AI_reStarter.exe (実行ファイル)")
    print("  - AI_reStarter-v0.1.0.zip (リリースパッケージ)")
    print("  - release/ (リリースディレクトリ)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
