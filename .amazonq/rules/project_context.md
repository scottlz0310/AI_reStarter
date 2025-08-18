# Kiro Auto Recovery プロジェクトルール

## プロジェクト概要
- **プロジェクト名**: Kiro-IDE自動復旧システム
- **目的**: Kiro-IDEでエラーが発生した際に、画面キャプチャでエラーを自動検知し、チャットに復旧コマンドを自動送信
- **言語**: Python 3.8+
- **環境**: Windows（win32guiライブラリ使用）

## 重要な制約
- **最小限のコード**: 要件を満たす最小限のコードのみを実装
- **既存コードの保持**: ユーザーのコードやテストケースは削除しない
- **日本語対応**: コメントやメッセージは日本語で記述

## プロジェクト構造
```
Kiro-Auto_Recovery/
├── kiro_auto_recovery.py    # メインスクリプト
├── kiro_setup.py           # 設定GUIアプリケーション
├── kiro_config.json        # 設定ファイル
├── error_templates/        # エラー画像テンプレート
├── test_scripts/          # 試行スクリプト
├── tests/                 # テストファイル
└── pyproject.toml         # プロジェクト設定
```

## 開発方針
- コード品質: black, flake8, pylint, mypy使用
- テスト: pytest使用
- 依存関係管理: pyproject.toml使用
- pre-commitフック有効

## 主要機能
1. 画面監視とエラー検出
2. テンプレートマッチング
3. 自動復旧コマンド送信
4. ホットキー操作
5. 設定管理（JSON）

## 技術スタック
- 画面キャプチャ: PIL, pyautogui
- GUI: tkinter
- ホットキー: keyboard
- 画像処理: OpenCV
- Windows API: win32gui, win32con