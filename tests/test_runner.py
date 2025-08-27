"""
テスト実行用スクリプト

このスクリプトは様々なテストシナリオを実行するためのユーティリティを提供します。
"""

import logging
import subprocess
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class TestRunner:
    """テスト実行管理クラス"""

    def __init__(self, project_root: Path | None = None):
        """
        テストランナーを初期化

        Args:
            project_root: プロジェクトのルートディレクトリ
        """
        self.project_root = project_root or Path(__file__).parent.parent
        self.tests_dir = self.project_root / "tests"

    def run_unit_tests(self, verbose: bool = True) -> int:
        """
        単体テストを実行

        Args:
            verbose: 詳細出力を行うかどうか

        Returns:
            int: 終了コード
        """
        logger.info("単体テストを実行します")

        cmd = [
            sys.executable,
            "-m",
            "pytest",
            str(self.tests_dir / "unit"),
            "-m",
            "unit or not integration and not gui",
            "--cov=src",
            "--cov-report=term-missing",
        ]

        if verbose:
            cmd.append("-v")

        return subprocess.run(cmd, cwd=self.project_root).returncode

    def run_integration_tests(self, verbose: bool = True) -> int:
        """
        統合テストを実行

        Args:
            verbose: 詳細出力を行うかどうか

        Returns:
            int: 終了コード
        """
        logger.info("統合テストを実行します")

        cmd = [
            sys.executable,
            "-m",
            "pytest",
            str(self.tests_dir / "integration"),
            "-m",
            "integration",
            "--cov=src",
            "--cov-report=term-missing",
        ]

        if verbose:
            cmd.append("-v")

        return subprocess.run(cmd, cwd=self.project_root).returncode

    def run_gui_tests(self, verbose: bool = True) -> int:
        """
        GUIテストを実行

        Args:
            verbose: 詳細出力を行うかどうか

        Returns:
            int: 終了コード
        """
        logger.info("GUIテストを実行します")

        cmd = [
            sys.executable,
            "-m",
            "pytest",
            str(self.tests_dir / "gui"),
            "-m",
            "gui",
            "--cov=src",
            "--cov-report=term-missing",
        ]

        if verbose:
            cmd.append("-v")

        return subprocess.run(cmd, cwd=self.project_root).returncode

    def run_all_tests(self, verbose: bool = True, coverage_html: bool = False) -> int:
        """
        全てのテストを実行

        Args:
            verbose: 詳細出力を行うかどうか
            coverage_html: HTMLカバレッジレポートを生成するかどうか

        Returns:
            int: 終了コード
        """
        logger.info("全てのテストを実行します")

        cmd = [
            sys.executable,
            "-m",
            "pytest",
            str(self.tests_dir),
            "--cov=src",
            "--cov-report=term-missing",
        ]

        if coverage_html:
            cmd.append("--cov-report=html")

        if verbose:
            cmd.append("-v")

        return subprocess.run(cmd, cwd=self.project_root).returncode

    def run_specific_test(self, test_path: str, verbose: bool = True) -> int:
        """
        特定のテストファイルまたはテストメソッドを実行

        Args:
            test_path: テストファイルパスまたはテストメソッドパス
            verbose: 詳細出力を行うかどうか

        Returns:
            int: 終了コード
        """
        logger.info(f"特定のテストを実行します: {test_path}")

        cmd = [
            sys.executable,
            "-m",
            "pytest",
            test_path,
            "--cov=src",
            "--cov-report=term-missing",
        ]

        if verbose:
            cmd.append("-v")

        return subprocess.run(cmd, cwd=self.project_root).returncode

    def run_tests_with_markers(self, markers: list[str], verbose: bool = True) -> int:
        """
        指定されたマーカーのテストを実行

        Args:
            markers: テストマーカーのリスト
            verbose: 詳細出力を行うかどうか

        Returns:
            int: 終了コード
        """
        marker_expr = " or ".join(markers)
        logger.info(f"マーカー指定でテストを実行します: {marker_expr}")

        cmd = [
            sys.executable,
            "-m",
            "pytest",
            str(self.tests_dir),
            "-m",
            marker_expr,
            "--cov=src",
            "--cov-report=term-missing",
        ]

        if verbose:
            cmd.append("-v")

        return subprocess.run(cmd, cwd=self.project_root).returncode

    def run_fast_tests(self, verbose: bool = True) -> int:
        """
        高速テスト（slowマーカー以外）を実行

        Args:
            verbose: 詳細出力を行うかどうか

        Returns:
            int: 終了コード
        """
        logger.info("高速テストを実行します")

        cmd = [
            sys.executable,
            "-m",
            "pytest",
            str(self.tests_dir),
            "-m",
            "not slow",
            "--cov=src",
            "--cov-report=term-missing",
        ]

        if verbose:
            cmd.append("-v")

        return subprocess.run(cmd, cwd=self.project_root).returncode

    def generate_coverage_report(self, format_type: str = "html") -> int:
        """
        カバレッジレポートを生成

        Args:
            format_type: レポート形式 ("html", "xml", "term")

        Returns:
            int: 終了コード
        """
        logger.info(f"カバレッジレポートを生成します: {format_type}")

        cmd = [sys.executable, "-m", "coverage", "report"]

        if format_type == "html":
            cmd = [sys.executable, "-m", "coverage", "html"]
        elif format_type == "xml":
            cmd = [sys.executable, "-m", "coverage", "xml"]

        return subprocess.run(cmd, cwd=self.project_root).returncode


def main():
    """メイン関数"""
    import argparse

    parser = argparse.ArgumentParser(description="AI reStarter テスト実行ツール")
    parser.add_argument(
        "test_type",
        choices=["unit", "integration", "gui", "all", "fast", "specific"],
        help="実行するテストの種類",
    )
    parser.add_argument("--path", help="特定のテストパス（test_type=specificの場合）")
    parser.add_argument("--markers", nargs="+", help="テストマーカー（複数指定可能）")
    parser.add_argument("--verbose", "-v", action="store_true", help="詳細出力")
    parser.add_argument(
        "--coverage-html", action="store_true", help="HTMLカバレッジレポートを生成"
    )

    args = parser.parse_args()

    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    runner = TestRunner()

    try:
        if args.test_type == "unit":
            exit_code = runner.run_unit_tests(verbose=args.verbose)
        elif args.test_type == "integration":
            exit_code = runner.run_integration_tests(verbose=args.verbose)
        elif args.test_type == "gui":
            exit_code = runner.run_gui_tests(verbose=args.verbose)
        elif args.test_type == "all":
            exit_code = runner.run_all_tests(
                verbose=args.verbose, coverage_html=args.coverage_html
            )
        elif args.test_type == "fast":
            exit_code = runner.run_fast_tests(verbose=args.verbose)
        elif args.test_type == "specific":
            if not args.path:
                logger.error("--pathオプションが必要です")
                sys.exit(1)
            exit_code = runner.run_specific_test(args.path, verbose=args.verbose)
        elif args.markers:
            exit_code = runner.run_tests_with_markers(
                args.markers, verbose=args.verbose
            )
        else:
            logger.error("無効なテストタイプです")
            sys.exit(1)

        if exit_code == 0:
            logger.info("全てのテストが成功しました")
        else:
            logger.error(f"テストが失敗しました（終了コード: {exit_code}）")

        sys.exit(exit_code)

    except KeyboardInterrupt:
        logger.info("テスト実行が中断されました")
        sys.exit(1)
    except Exception as e:
        logger.error(f"テスト実行中にエラーが発生しました: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
