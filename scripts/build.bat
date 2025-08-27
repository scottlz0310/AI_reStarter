@echo off
REM AI reStarter ビルドスクリプト

echo AI reStarter ビルドを開始します...

REM 仮想環境をアクティベート
call venv\Scripts\activate

REM 依存関係をインストール
echo 依存関係をインストール中...
pip install pyinstaller

REM テストを実行
echo テストを実行中...
pytest tests/ --cov=src --cov-report=term-missing
if %ERRORLEVEL% neq 0 (
    echo テストが失敗しました
    exit /b 1
)

REM 実行ファイルをビルド
echo 実行ファイルをビルド中...
pyinstaller --onefile --windowed --name AI_reStarter main.py

REM リリースパッケージを作成
echo リリースパッケージを作成中...
if exist release rmdir /s /q release
mkdir release
copy dist\AI_reStarter.exe release\
copy README.md release\
copy kiro_config.json release\
xcopy error_templates release\error_templates\ /E /I /Q
xcopy amazonq_templates release\amazonq_templates\ /E /I /Q

echo ビルド完了: release\AI_reStarter.exe
