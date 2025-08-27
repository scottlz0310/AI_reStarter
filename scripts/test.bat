@echo off
REM AI reStarter テスト実行用バッチファイル
REM 使用方法: test.bat [unit|integration|gui|all|fast|coverage]

setlocal enabledelayedexpansion

REM 仮想環境のパス
set VENV=venv\Scripts
set PYTHON=%VENV%\python.exe
set SRC_DIR=src
set TESTS_DIR=tests

REM 引数チェック
if "%1"=="" (
    echo 使用方法: test.bat [unit^|integration^|gui^|all^|fast^|coverage^|help]
    echo.
    echo   unit         単体テストのみ実行
    echo   integration  統合テストのみ実行
    echo   gui          GUIテストのみ実行
    echo   all          全てのテストを実行
    echo   fast         高速テスト（slowマーカー以外）を実行
    echo   coverage     カバレッジ付きテスト実行
    echo   help         このヘルプを表示
    goto :end
)

REM 仮想環境の存在確認
if not exist "%VENV%\activate.bat" (
    echo エラー: 仮想環境が見つかりません。
    echo 先に仮想環境を作成してください: python -m venv venv
    exit /b 1
)

REM テストタイプに応じて実行
if "%1"=="unit" (
    echo 単体テストを実行しています...
    %VENV%\activate && %PYTHON% -m pytest %TESTS_DIR%\unit -v --cov=%SRC_DIR% --cov-report=term-missing
) else if "%1"=="integration" (
    echo 統合テストを実行しています...
    %VENV%\activate && %PYTHON% -m pytest %TESTS_DIR%\integration -v --cov=%SRC_DIR% --cov-report=term-missing
) else if "%1"=="gui" (
    echo GUIテストを実行しています...
    %VENV%\activate && %PYTHON% -m pytest %TESTS_DIR%\gui -v --cov=%SRC_DIR% --cov-report=term-missing
) else if "%1"=="all" (
    echo 全てのテストを実行しています...
    %VENV%\activate && %PYTHON% -m pytest %TESTS_DIR% -v --cov=%SRC_DIR% --cov-report=term-missing --cov-report=html
) else if "%1"=="fast" (
    echo 高速テストを実行しています...
    %VENV%\activate && %PYTHON% -m pytest %TESTS_DIR% -m "not slow" -v --cov=%SRC_DIR% --cov-report=term-missing
) else if "%1"=="coverage" (
    echo カバレッジ付きテストを実行しています...
    %VENV%\activate && %PYTHON% -m pytest %TESTS_DIR% --cov=%SRC_DIR% --cov-report=html --cov-report=xml --cov-report=term-missing
    echo カバレッジレポートが htmlcov に生成されました
) else if "%1"=="help" (
    echo AI reStarter テスト実行用バッチファイル
    echo.
    echo 使用方法: test.bat [unit^|integration^|gui^|all^|fast^|coverage^|help]
    echo.
    echo   unit         単体テストのみ実行
    echo   integration  統合テストのみ実行
    echo   gui          GUIテストのみ実行
    echo   all          全てのテストを実行
    echo   fast         高速テスト（slowマーカー以外）を実行
    echo   coverage     カバレッジ付きテスト実行
    echo   help         このヘルプを表示
) else (
    echo エラー: 無効なオプション "%1"
    echo 使用方法: test.bat [unit^|integration^|gui^|all^|fast^|coverage^|help]
    exit /b 1
)

:end
endlocal
