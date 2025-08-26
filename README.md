# AI reStarter - AI実装用自動復旧システム

Kiro-IDEでエラーが発生した際に、画面キャプチャでエラーを自動検知し、チャットに復旧コマンドを自動送信するシステムです。

## 機能

- **画面監視**: 定期的に画面をキャプチャしてエラーを検出
- **テンプレートマッチング**: 事前に保存したエラー画像と比較
- **自動復旧**: エラー検出時にチャットに復旧コマンドを自動送信
- **ホットキー操作**: キーボードショートカットで手動操作が可能
- **設定管理**: JSONファイルで動作をカスタマイズ可能

## インストール

### 前提条件

- Python 3.8以上
- 仮想環境（推奨）
- Windows環境（win32guiライブラリを使用）

### セットアップ

1. リポジトリをクローン
```bash
git clone <repository-url>
cd AI_reStarter
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

### 1. 初期設定

#### 設定ファイル作成
```bash
python kiro_auto_recovery.py --create-config
```

#### 画面座標設定（重要）
**⚠️ 重要: マルチモニター環境では、Kiro-IDEをメインディスプレイに配置してください**

設定GUIを使用して監視エリアとチャット入力位置を設定：
```bash
python kiro_setup.py
```

このスクリプトは以下の手順で設定を行います：
1. Kiro-IDEウィンドウを前面に移動
2. 監視エリアの左上と右下をクリックして設定
3. チャット入力欄をクリックして位置を設定
4. 設定を`kiro_config.json`に保存

**注意事項:**
- マルチモニター環境では、Kiro-IDEをメインディスプレイ（座標0,0が左上のディスプレイ）に配置してください
- 負の座標が設定されると、画面キャプチャが正常に動作しない場合があります
- **Windowsのディスプレイ設定で、メインディスプレイを左側に配置することを推奨します**

### 2. エラーテンプレート保存

#### 手動保存
```bash
python kiro_auto_recovery.py --template "compilation_error"
```

#### ホットキー保存
アプリケーション実行中に`Ctrl+Alt+S`を押すと、現在の画面からエラーテンプレートを保存できます。

### 3. 監視開始
```bash
python kiro_auto_recovery.py
```

## ホットキー操作

アプリケーション実行中に以下のホットキーが使用できます：

- **`Ctrl+Alt+S`**: 現在の画面からエラーテンプレートを保存
- **`Ctrl+Alt+R`**: 手動で復旧コマンドを送信
- **`Ctrl+Alt+P`**: 監視の一時停止/再開
- **`Ctrl+Alt+Q`**: 監視停止

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
  ],
  "custom_commands": {
    "compilation_error": "コンパイルエラーを修正して続行してください",
    "runtime_error": "ランタイムエラーを解決して再実行してください",
    "timeout_error": "タイムアウトエラー、再度実行してください"
  },
  "chat_input_position": [1457, 932],
  "monitor_region": [1431, 777, 480, 217]
}
```

### 設定項目の説明

- `monitor_interval`: 監視間隔（秒）
- `action_delay`: アクション間の遅延時間（秒）
- `max_recovery_attempts`: 最大復旧試行回数
- `recovery_cooldown`: 復旧試行間のクールダウン時間（秒）
- `template_threshold`: テンプレートマッチングの信頼度閾値（0.0-1.0）
- `recovery_commands`: デフォルトの復旧コマンドリスト
- `custom_commands`: エラータイプ別のカスタムコマンド
- `chat_input_position`: チャット入力欄の座標 [x, y]
- `monitor_region`: 監視エリアの座標 [x, y, width, height]

## プロジェクト構造

```
AI_reStarter/
├── kiro_auto_recovery.py    # メインスクリプト
├── kiro_setup.py           # 設定GUIアプリケーション
├── kiro_config.json        # 設定ファイル
├── error_templates/        # エラー画像テンプレート
├── test_scripts/          # 試行スクリプト（Gitから除外）
├── pyproject.toml         # プロジェクト設定
├── .pre-commit-config.yaml # pre-commit設定
├── .flake8                # flake8設定
├── .pylintrc             # pylint設定
├── Makefile              # 開発用コマンド
└── README.md             # このファイル
```

## トラブルシューティング

### よくある問題

1. **画面キャプチャが真っ黒になる**
   - Kiro-IDEをメインディスプレイに移動してください
   - Windowsのディスプレイ設定で、メインディスプレイを左側に配置してください
   - 設定GUIで座標を再設定してください

2. **復旧コマンドが入力されない**
   - チャット入力位置が正しく設定されているか確認してください
   - Kiro-IDEウィンドウが前面にあるか確認してください

3. **ホットキーが動作しない**
   - 管理者権限で実行している場合、ホットキー機能が無効になる場合があります
   - 通常の権限で実行してください

## ライセンス

MIT License

## 貢献

1. フォークを作成
2. 機能ブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成
