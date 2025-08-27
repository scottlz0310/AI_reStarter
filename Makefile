# AI reStarter プロジェクト用 Makefile
# Windows環境での開発作業を効率化するためのコマンド集

# 仮想環境のパス
VENV = venv\Scripts
PYTHON = $(VENV)\python.exe
PIP = $(VENV)\pip.exe

# プロジェクト設定
SRC_DIR = src
TESTS_DIR = tests
COVERAGE_DIR = htmlcov

.PHONY: help install install-dev test test-unit test-integration test-gui test-fast test-coverage clean format lint type-check quality-check all-checks setup-dev

# デフォルトターゲット
help:
	@echo AI reStarter プロジェクト用 Makefile
	@echo.
	@echo 利用可能なコマンド:
	@echo   help              このヘルプメッセージを表示
	@echo   setup-dev         開発環境をセットアップ
	@echo   install           本番用依存関係をインストール
	@echo   install-dev       開発用依存関係をインストール
	@echo   test              全てのテストを実行
	@echo   test-unit         単体テストのみ実行
	@echo   test-integration  統合テストのみ実行
	@echo   test-gui          GUIテストのみ実行
	@echo   test-fast         高速テスト（slowマーカー以外）を実行
	@echo   test-coverage     カバレッジ付きテスト実行
	@echo   format            コードフォーマット実行
	@echo   lint              リント実行
	@echo   type-check        型チェック実行
	@echo   quality-check     コード品質チェック実行
	@echo   all-checks        全ての品質チェックを実行
	@echo   clean             一時ファイルを削除
	@echo.

# 開発環境セットアップ
setup-dev:
	@echo 開発環境をセットアップしています...
	$(VENV)\activate && $(PIP) install -e ".[dev]"
	$(VENV)\activate && pre-commit install
	@echo 開発環境のセットアップが完了しました

# 依存関係インストール
install:
	@echo 本番用依存関係をインストールしています...
	$(VENV)\activate && $(PIP) install -e .

install-dev:
	@echo 開発用依存関係をインストールしています...
	$(VENV)\activate && $(PIP) install -e ".[dev]"

# テスト実行
test:
	@echo 全てのテストを実行しています...
	$(VENV)\activate && $(PYTHON) -m pytest $(TESTS_DIR) -v --cov=$(SRC_DIR) --cov-report=term-missing --cov-report=html

test-unit:
	@echo 単体テストを実行しています...
	$(VENV)\activate && $(PYTHON) -m pytest $(TESTS_DIR)\unit -v --cov=$(SRC_DIR) --cov-report=term-missing

test-integration:
	@echo 統合テストを実行しています...
	$(VENV)\activate && $(PYTHON) -m pytest $(TESTS_DIR)\integration -v --cov=$(SRC_DIR) --cov-report=term-missing

test-gui:
	@echo GUIテストを実行しています...
	$(VENV)\activate && $(PYTHON) -m pytest $(TESTS_DIR)\gui -v --cov=$(SRC_DIR) --cov-report=term-missing

test-fast:
	@echo 高速テストを実行しています...
	$(VENV)\activate && $(PYTHON) -m pytest $(TESTS_DIR) -m "not slow" -v --cov=$(SRC_DIR) --cov-report=term-missing

test-coverage:
	@echo カバレッジ付きテストを実行しています...
	$(VENV)\activate && $(PYTHON) -m pytest $(TESTS_DIR) --cov=$(SRC_DIR) --cov-report=html --cov-report=xml --cov-report=term-missing
	@echo カバレッジレポートが $(COVERAGE_DIR) に生成されました

# コード品質チェック
format:
	@echo コードをフォーマットしています...
	$(VENV)\activate && $(PYTHON) -m black $(SRC_DIR) $(TESTS_DIR)
	$(VENV)\activate && $(PYTHON) -m isort $(SRC_DIR) $(TESTS_DIR)

lint:
	@echo リントを実行しています...
	$(VENV)\activate && $(PYTHON) -m flake8 $(SRC_DIR) $(TESTS_DIR)
	$(VENV)\activate && $(PYTHON) -m pylint $(SRC_DIR)
	$(VENV)\activate && $(PYTHON) -m ruff check $(SRC_DIR) $(TESTS_DIR)

type-check:
	@echo 型チェックを実行しています...
	$(VENV)\activate && $(PYTHON) -m mypy $(SRC_DIR)

quality-check:
	@echo コード品質チェックを実行しています...
	$(VENV)\activate && $(PYTHON) -m flake8 $(SRC_DIR) $(TESTS_DIR)
	$(VENV)\activate && $(PYTHON) -m ruff check $(SRC_DIR) $(TESTS_DIR)

all-checks: format lint type-check test-fast
	@echo 全ての品質チェックが完了しました

# クリーンアップ
clean:
	@echo 一時ファイルを削除しています...
	@if exist __pycache__ rmdir /s /q __pycache__
	@if exist .pytest_cache rmdir /s /q .pytest_cache
	@if exist $(COVERAGE_DIR) rmdir /s /q $(COVERAGE_DIR)
	@if exist .coverage del .coverage
	@if exist coverage.xml del coverage.xml
	@for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
	@for /d /r . %%d in (*.egg-info) do @if exist "%%d" rmdir /s /q "%%d"
	@echo クリーンアップが完了しました

# CI/CD用コマンド
ci-test:
	@echo CI環境でテストを実行しています...
	$(VENV)\activate && $(PYTHON) -m pytest $(TESTS_DIR) --cov=$(SRC_DIR) --cov-report=xml --cov-report=term-missing --junitxml=test-results.xml

ci-quality:
	@echo CI環境でコード品質チェックを実行しています...
	$(VENV)\activate && $(PYTHON) -m flake8 $(SRC_DIR) $(TESTS_DIR) --format=junit-xml --output-file=flake8-results.xml
	$(VENV)\activate && $(PYTHON) -m mypy $(SRC_DIR) --junit-xml=mypy-results.xml

# 開発用ユーティリティ
run-main:
	@echo メインアプリケーションを実行しています...
	$(VENV)\activate && $(PYTHON) main.py

run-tests-watch:
	@echo テストの監視モードを開始しています...
	$(VENV)\activate && $(PYTHON) -m pytest-watch $(TESTS_DIR)

install-pre-commit:
	@echo pre-commitフックをインストールしています...
	$(VENV)\activate && pre-commit install

update-deps:
	@echo 依存関係を更新しています...
	$(VENV)\activate && $(PIP) install --upgrade pip
	$(VENV)\activate && $(PIP) install --upgrade -e ".[dev]"

# ドキュメント生成
docs:
	@echo ドキュメントを生成しています...
	$(VENV)\activate && $(PIP) install -e ".[docs]"
	$(VENV)\activate && sphinx-build -b html docs docs/_build/html

# パフォーマンステスト
test-performance:
	@echo パフォーマンステストを実行しています...
	$(VENV)\activate && $(PYTHON) -m pytest $(TESTS_DIR) -m "slow" -v

# メモリプロファイリング
profile-memory:
	@echo メモリプロファイリングを実行しています...
	$(VENV)\activate && $(PYTHON) -m memory_profiler main.py

# セキュリティチェック
security-check:
	@echo セキュリティチェックを実行しています...
	$(VENV)\activate && $(PIP) install bandit safety
	$(VENV)\activate && bandit -r $(SRC_DIR)
	$(VENV)\activate && safety check