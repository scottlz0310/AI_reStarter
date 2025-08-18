.PHONY: help install install-dev test lint format clean docs

help: ## このヘルプを表示
	@echo "利用可能なコマンド:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## 本番用依存関係をインストール
	pip install -e .

install-dev: ## 開発用依存関係をインストール
	pip install -e ".[dev]"
	pre-commit install

test: ## テストを実行
	pytest

test-cov: ## カバレッジ付きでテストを実行
	pytest --cov=kiro_auto_recovery --cov-report=html --cov-report=term-missing

lint: ## コード品質チェックを実行
	ruff check .
	flake8 kiro_auto_recovery.py
	pylint kiro_auto_recovery.py
	mypy kiro_auto_recovery.py

format: ## コードフォーマットを実行
	ruff format .
	black kiro_auto_recovery.py
	isort kiro_auto_recovery.py

format-check: ## フォーマットチェックを実行
	ruff check --diff .
	black --check kiro_auto_recovery.py
	isort --check-only kiro_auto_recovery.py

clean: ## 一時ファイルを削除
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf htmlcov/

docs: ## ドキュメントを生成
	sphinx-build -b html docs/ docs/_build/html

setup: install-dev ## 開発環境をセットアップ
	@echo "開発環境のセットアップが完了しました！"

check: format-check lint test ## 全てのチェックを実行
	@echo "全てのチェックが完了しました！"
