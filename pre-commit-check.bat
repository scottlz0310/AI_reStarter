@echo off
echo コミット前チェックを実行中...

echo.
echo [1/4] ruff check実行中...
venv\Scripts\activate.bat
python -m ruff check src/ tests/
if %errorlevel% neq 0 (
    echo ruffチェックに失敗しました
    exit /b 1
)

echo.
echo [2/4] ruff format実行中...
python -m ruff format .
if %errorlevel% neq 0 (
    echo ruff formatに失敗しました
    exit /b 1
)

echo.
echo [3/4] black format実行中...
python -m black .
if %errorlevel% neq 0 (
    echo blackフォーマットに失敗しました
    exit /b 1
)

echo.
echo [4/4] isort実行中...
python -m isort .
if %errorlevel% neq 0 (
    echo isortに失敗しました
    exit /b 1
)

echo.
echo すべてのチェックが完了しました！
echo 変更をステージングしてコミットできます。