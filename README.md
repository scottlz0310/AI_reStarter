# Kiro-IDE自動復旧システム

Kiro-IDEでエラーが発生した際に、画面キャプチャでエラーを自動検知し、チャットに復旧コマンドを自動送信するシステムです。

## 機能

- **画面監視**: 定期的に画面をキャプチャしてエラーを検出
- **テンプレートマッチング**: 事前に保存したエラー画像と比較
- **自動復旧**: エラー検出時にチャットに復旧コマンドを自動送信
- **設定管理**: JSONファイルで動作をカスタマイズ可能

## インストール

### 前提条件

- Python 3.8以上
- 仮想環境（推奨）

### セットアップ

1. リポジトリをクローン
```bash
git clone <repository-url>
cd Kiro-Auto_Recovery
```

2. 仮想環境を作成・有効化
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# または
venv\Scripts\activate     # Windows
```

3. 開発環境をセットアップ
```bash
# 開発用依存関係を含めてインストール
pip install -e ".[dev]"

# pre-commitフックをインストール
pre-commit install
```

### 依存関係

#### 本番用
```bash
pip install -e .
```

#### 開発用
```bash
pip install -e ".[dev]"
```

#### テスト用
```bash
pip install -e ".[test]"
```

#### ドキュメント生成用
```bash
pip install -e ".[docs]"
```

## 使用方法

### 1. 設定ファイル作成
```bash
python kiro_auto_recovery.py --create-config
```

### 2. エラーテンプレート保存
```bash
python kiro_auto_recovery.py --template "compilation_error"
```

### 3. 監視開始
```bash
python kiro_auto_recovery.py
```

## 開発

### コード品質チェック

```bash
# フォーマット
make format

# リント
make lint

# テスト
make test

# 全てのチェック
make check
```

### 利用可能なコマンド

```bash
make help
```

### pre-commitフック

コミット前に自動でコード品質チェックが実行されます：

- コードフォーマット（black）
- インポート整理（isort）
- リント（flake8, pylint）
- 型チェック（mypy）

## 設定

`kiro_config.json`で以下の設定が可能です：

```json
{
  "monitor_interval": 2.0,
  "action_delay": 0.5,
  "max_recovery_attempts": 3,
  "recovery_cooldown": 30,
  "template_threshold": 0.8,
  "recovery_commands": [
    "続行してください",
    "エラーを修正して続行",
    "タスクを再開してください"
  ]
}
```

## プロジェクト構造

```
Kiro-Auto_Recovery/
├── kiro_auto_recovery.py    # メインスクリプト
├── kiro_config.json         # 設定ファイル
├── error_templates/         # エラー画像テンプレート
├── pyproject.toml          # プロジェクト設定
├── .pre-commit-config.yaml # pre-commit設定
├── .flake8                 # flake8設定
├── .pylintrc              # pylint設定
├── Makefile               # 開発用コマンド
└── README.md              # このファイル
```

## ライセンス

MIT License

## 貢献

1. フォークを作成
2. 機能ブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成
