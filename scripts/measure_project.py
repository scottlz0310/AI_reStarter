#!/usr/bin/env python3
"""
プロジェクト規模測定スクリプト
"""
import os
from pathlib import Path


def count_lines_in_file(file_path):
    """ファイルの行数をカウント"""
    try:
        with open(file_path, encoding="utf-8", errors="ignore") as f:
            return len(f.readlines())
    except Exception:
        return 0


def measure_directory(directory, extensions=None):
    """ディレクトリ内のファイル行数を測定"""
    if extensions is None:
        extensions = [".py"]

    total_lines = 0
    file_count = 0

    for root, _dirs, files in os.walk(directory):
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                file_path = Path(root) / file
                lines = count_lines_in_file(file_path)
                total_lines += lines
                file_count += 1
                print(f"  {file_path.relative_to(directory)}: {lines:,} lines")

    return total_lines, file_count


def main():
    """プロジェクト規模測定"""
    print("AI reStarter プロジェクト規模測定")
    print("=" * 50)

    # ソースコード
    print("\nソースコード (src/)")
    src_lines, src_files = measure_directory("src")
    print(f"合計: {src_files} files, {src_lines:,} lines")

    # テストコード
    print("\nテストコード (tests/)")
    test_lines, test_files = measure_directory("tests")
    print(f"合計: {test_files} files, {test_lines:,} lines")

    # スクリプト
    print("\nスクリプト (scripts/)")
    script_lines, script_files = measure_directory("scripts")
    print(f"合計: {script_files} files, {script_lines:,} lines")

    # メインファイル
    print("\nメインファイル")
    main_lines = count_lines_in_file("main.py")
    print(f"  main.py: {main_lines:,} lines")

    # 設定ファイル
    print("\n設定ファイル")
    config_files = [
        "pyproject.toml",
        ".pre-commit-config.yaml",
        ".flake8",
        ".pylintrc",
        "ruff.toml",
    ]
    config_lines = 0
    config_count = 0
    for config_file in config_files:
        if Path(config_file).exists():
            lines = count_lines_in_file(config_file)
            config_lines += lines
            config_count += 1
            print(f"  {config_file}: {lines:,} lines")

    # ドキュメント
    print("\nドキュメント")
    doc_files = ["README.md", "FEATURES.md", "RELEASE_NOTES.md"]
    doc_lines = 0
    doc_count = 0
    for doc_file in doc_files:
        if Path(doc_file).exists():
            lines = count_lines_in_file(doc_file)
            doc_lines += lines
            doc_count += 1
            print(f"  {doc_file}: {lines:,} lines")

    # docs/フォルダ
    if Path("docs").exists():
        docs_lines, docs_files = measure_directory("docs", [".md"])
        doc_lines += docs_lines
        doc_count += docs_files
        print(f"  docs/: {docs_files} files, {docs_lines:,} lines")

    # 総計
    total_code_lines = src_lines + test_lines + script_lines + main_lines
    total_lines = total_code_lines + config_lines + doc_lines
    total_files = src_files + test_files + script_files + 1 + config_count + doc_count

    print("\n" + "=" * 50)
    print("プロジェクト規模サマリー")
    print(f"実装コード: {src_lines + main_lines:,} lines ({src_files + 1} files)")
    print(f"テストコード: {test_lines:,} lines ({test_files} files)")
    print(f"スクリプト: {script_lines:,} lines ({script_files} files)")
    print(f"設定ファイル: {config_lines:,} lines ({config_count} files)")
    print(f"ドキュメント: {doc_lines:,} lines ({doc_count} files)")
    print("-" * 30)
    print(f"総コード行数: {total_code_lines:,} lines")
    print(f"総ファイル数: {total_files} files")
    print(f"総行数: {total_lines:,} lines")

    # テストカバレッジ比率
    if src_lines > 0:
        test_ratio = (test_lines / src_lines) * 100
        print(f"テスト/ソース比率: {test_ratio:.1f}%")


if __name__ == "__main__":
    main()
