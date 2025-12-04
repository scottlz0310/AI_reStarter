# AI reStarter モダン化実装計画

## プロジェクト概要
Windows画面監視による汎用IDE自動復旧システム。特定パターン検出時の自動アクション実行を目的とする常駐型アプリケーション。

## 技術スタック

### パッケージ管理
- **パッケージマネージャー**: uv（高速な依存関係解決とインストール）
- **依存関係更新**: Renovate（自動バージョン管理）
- **ロックファイル**: uv.lock（再現可能なビルド）

### コア依存関係
```toml
[project]
name = "ai-restarter"
requires-python = ">=3.13"
dependencies = [
    "opencv-python-headless>=4.8.0",  # 画像処理（GUI不要版）
    "pillow>=10.0.0",                  # 画像操作
    "numpy>=1.26.0",                   # 数値計算
    "pyautogui>=0.9.54",              # 自動操作
    "keyboard>=0.13.5",                # ホットキー
    "pystray>=0.19.0",                 # システムトレイ
    "pywin32>=306; sys_platform == 'win32'",  # Windows API
]

# モジュール実行エントリーポイント
[project.scripts]
ai-restarter = "ai_restarter.__main__:main"

[dependency-groups]
dev = [
    "ruff>=0.8.0",           # リンター・フォーマッター統合
    "basedpyright>=1.21.0",  # 型チェック
    "pre-commit>=4.0.0",     # Git フック
]
test = [
    "pytest>=8.0.0",         # テストフレームワーク
    "pytest-cov>=6.0.0",     # カバレッジ測定
]
gui = ["tkinter"]              # 標準ライブラリ

# pyproject.toml統合設定例
[tool.ruff]
target-version = "py313"
line-length = 120  # モダンな画面幅に対応
select = ["ALL"]
ignore = ["D", "ANN", "COM812", "ISC001"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"

[tool.basedpyright]
pythonVersion = "3.13"
typeCheckingMode = "all"  # 最も厳格な型チェック（AI実装の一貫性確保）
reportMissingTypeStubs = false

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = ["--cov=src/ai_restarter", "-v"]

[tool.coverage.run]
source = ["src/ai_restarter"]
omit = ["tests/*", "src/ai_restarter/__main__.py"]
```

### 開発ツール統一
- **パッケージ管理**: uv + Renovate
- **リンター**: ruff のみ（black, isort, flake8, pylint を統合）
- **型チェック**: basedpyright（最も厳格な "all" モード）
- **テスト**: pytest
- **フォーマット**: ruff format
- **設定ファイル**: pyproject.toml 一元化（ruff, basedpyright, pytest, coverage）
- **アプリ設定**: profiles.toml（コメント対応、階層構造）

### 削除対象ファイル・ディレクトリ
```
削除対象:
├── src/                    # 既存ソースコード
├── playground/             # 開発・テスト用ファイル
├── scripts/               # 開発・運用スクリプト
├── tests/                 # 既存テストコード
├── .flake8               # flake8設定（ruffに統合）
├── .pylintrc             # pylint設定（ruffに統合）
├── Makefile              # 開発コマンド（ruffに統合）
└── .pre-commit-config.yaml # pre-commit設定（pyproject.tomlに統合）

保持対象:
├── pyproject.toml         # 全設定統合
├── README.md             # プロジェクト説明
└── MODERNIZATION_PLAN.md # この計画書
```

## アーキテクチャ設計

### 3層構造
```
ScreenWatcher/
├── Core/                    # 監視エンジン
│   ├── ExecutionModeManager # 実行モード管理（click/chat/keyboard）
│   ├── MonitorEngine       # 画面監視・マッチング
│   ├── ActionEngine        # 自動アクション実行
│   └── DisplayManager      # マルチモニター・DPI対応
├── UI/                     # ユーザーインターフェース
│   ├── SystemTray          # 常駐トレイアイコン
│   ├── SetupWizard         # 3ステップ設定
│   ├── ConfigViewer        # 設定確認・デバッグ
│   └── OverlaySelector     # 視覚的領域選択
└── Config/                 # 設定管理
    ├── TemplateConfig      # テンプレート設定（汎用的）
    ├── TemplateManager     # テンプレート画像管理
    └── LogManager          # ログレベル分離
```

## 実装フェーズ

### Phase 1: コア機能（最優先）
**目標**: 基本的な監視・アクション実行機能

#### 1.1 ExecutionModeManager
- 実行モード切り替え（click/chat/keyboard）
- モード別テンプレート・アクション管理
- アクティブモードの状態管理
- テンプレートベースの汎用的な設定

#### 1.2 MonitorEngine
- 効率的な画面キャプチャ（3秒間隔、適応的調整）
- OpenCVテンプレートマッチング
- マルチテンプレート対応
- メモリキャッシュによる高速化

#### 1.3 ActionEngine
- クリック、キー送信、コマンド実行
- アクション実行ログ
- 失敗時のリトライ機能

#### 1.4 DisplayManager
- マルチモニター座標統一
- DPI変更対応
- 相対座標による設定保存

### Phase 2: UI・設定機能（中優先）
**目標**: 直感的な設定とデバッグ機能

#### 2.1 SetupWizard
- Step1: 監視領域のドラッグ選択
- Step2: テンプレート画像の取得
- Step3: アクション設定とテスト
- Step4: 設定確認と保存

#### 2.2 ConfigViewer
- 現在の設定状態を視覚表示
- マッチング精度のリアルタイム表示
- 設定妥当性チェック
- 環境変化検出と再設定提案

#### 2.3 SystemTray
- 監視状態の表示
- プロファイル切り替え
- 設定画面へのアクセス
- ログ表示

### Phase 3: 高度機能（低優先）
**目標**: カスタマイズ性と保守性向上

#### 3.1 AdvancedTemplateManager
- 複数テンプレートの組み合わせ
- テンプレートの自動更新
- 精度向上のための機械学習適用

#### 3.2 CustomizableOverlay
- デバッグ情報の選択表示
- 監視領域の視覚的確認
- パフォーマンス情報表示

## 設定ファイル構造

### profiles.toml
```toml
# AI reStarter 設定

[global]
# グローバル設定
check_interval = 3.0        # 監視間隔（秒）
adaptive_interval = true    # 適応的間隔調整
log_level = "INFO"         # ログレベル
active_mode = "click"      # アクティブ実行モード（click/chat/keyboard）

[[templates]]
name = "run_button"
description = "実行ボタン検出用テンプレート"
execution_mode = "click"  # このテンプレートの実行モード

# 監視領域（相対座標 0.0-1.0）
[templates.monitor_region]
x = 0.1      # 左端からの相対位置
y = 0.2      # 上端からの相対位置
width = 0.8  # 幅の相対サイズ
height = 0.6 # 高さの相対サイズ

# 画像マッチング設定
[templates.matching]
file = "run_button.png"  # テンプレート画像ファイル
threshold = 0.8          # マッチング閾値

# アクション設定（実行モード: click）
[templates.action]
type = "click"        # アクション種別（click/chat/keyboard）
offset = [0, 0]      # クリック位置オフセット
retry_count = 3      # リトライ回数

# チャットコマンド例（実行モード: chat）
# [templates.action]
# type = "chat"
# command = "/fix"
# target_element = "chat_input"  # チャット入力欄のテンプレート名

# キーボード操作例（実行モード: keyboard）
# [templates.action]
# type = "keyboard"
# keys = ["ctrl", "shift", "p"]  # 送信するキー
```

## ログ戦略

### レベル分離
- **INFO**: 一般ユーザー向け（監視開始、ボタン検出、アクション実行）
- **DEBUG**: 開発・トラブルシューティング用（座標詳細、マッチング数値、システム情報）

### 出力先
- コンソール: INFO以上
- ファイル: DEBUG以上
- GUI: INFO以上（フィルタリング可能）

## パフォーマンス最適化

### 監視効率化
- 適応的監視間隔（通常3秒、検出後0.5秒、高負荷時5秒）
- テンプレート画像のメモリキャッシュ
- 不要な画像処理の削減

### メモリ管理
- 画面キャプチャの即座解放
- テンプレート画像の圧縮保存
- ログローテーション

## マルチモニター・DPI対応

### 座標系統一
- 仮想スクリーン座標系の採用
- 相対座標による設定保存
- DPI変更の自動検出

### 環境変化対応
- 解像度・DPI変更の検出
- 設定の妥当性チェック
- 再設定の提案（自動修正は行わない）

## エラーハンドリング

### 設定エラー
- 監視領域の範囲外チェック
- テンプレートファイルの存在確認
- アクション設定の妥当性検証

### 実行時エラー
- 画面キャプチャ失敗時の処理
- テンプレートマッチング失敗時の対応
- アクション実行失敗時のリトライ

## テスト戦略

### 単体テスト
- 各エンジンの独立テスト
- モック使用による外部依存排除
- 設定ファイルの読み込みテスト

### 統合テスト
- エンドツーエンドの動作確認
- 実際の画面を使用したテスト
- パフォーマンステスト

## 実装戦略

### ゼロベース実装（完全作り直し）
1. **作業ブランチ作成**: `feature/v2-complete-rewrite`
2. **既存コード全削除**: クリーンな状態から開始
3. **pyproject.toml統合**: 全設定を一元化
4. **モダンなベストプラクティス適用**: Python 3.13, uv, basedpyright
5. **AI実装による一貫性確保**: 厳格な型チェックで品質保証

### Git ワークフロー戦略

#### Phase 1: 作業ブランチでの開発
```bash
# 1. 作業ブランチ作成
git checkout -b feature/v2-complete-rewrite

# 2. 既存ファイル全削除（git管理下）
git rm -rf src/ tests/ playground/ scripts/
git rm .flake8 .pylintrc Makefile .pre-commit-config.yaml 2>/dev/null || true

# 3. 新構造で実装開始
# （この段階で完全にクリーンな状態）
```

#### Phase 2: 完成後のmainマージ（安全な置き換え）
```bash
# 1. main ブランチに切り替え
git checkout main

# 2. main の既存ファイルを全削除（git除外ファイルの影響を排除）
git rm -rf .
git clean -fdx  # git除外ファイルも完全削除

# 3. 作業ブランチの内容をマージ
git checkout feature/v2-complete-rewrite -- .

# 4. コミット
git add .
git commit -m "feat: complete rewrite with modern architecture (v2.0.0)"

# 5. タグ付け
git tag -a v2.0.0 -m "Version 2.0.0 - Complete modernization"
```

> [!CAUTION]
> **main ブランチの全削除について**
>
> この戦略は、git除外ファイル（`__pycache__/`, `.venv/`, ビルド成果物など）が残留して新実装に悪影響を与えるのを防ぐためです。
>
> - **実行前**: 必ず作業ブランチが完全に動作することを確認
> - **バックアップ**: 念のため main ブランチのタグを作成（`git tag backup-before-v2`）
> - **レビュー**: 完全な置き換えであることをチーム全体で合意

### 移行サポート
- 既存設定ファイル（JSON）の自動変換ツール
- 設定移行ガイドとドキュメント整備
- v1 → v2 移行チェックリスト

## 品質保証

### 静的解析
- ruff による包括的チェック
- basedpyright による型安全性確保
- pre-commit による自動品質チェック

### 継続的インテグレーション
- 自動テスト実行
- カバレッジ測定
- パフォーマンス回帰テスト

## デプロイメント

### パッケージング
- PyInstaller による単一実行ファイル化
- 依存関係の最小化
- Windows環境での動作確認

### 配布
- GitHub Releases による配布
- 自動ビルドパイプライン
- バージョン管理の自動化

## 今後の拡張性

### プラグインシステム
- カスタムアクションの追加
- 新しいIDEへの対応
- サードパーティ統合

### AI機能
- ボタンの自動検出
- 最適なアクションの提案
- 使用パターンの学習

## 実装開始手順

### ゼロベース開発フロー
```bash
# 1. 新ブランチ作成
git checkout -b feature/v2-rewrite

# 2. 既存ディレクトリ・ファイル削除
git rm -r src/ playground/ scripts/ tests/
git rm .flake8 .pylintrc Makefile .pre-commit-config.yaml

# 3. 新構造作成（src/レイアウト）
mkdir -p src/ai_restarter/{core,ui,config}
mkdir -p tests/{test_core,test_ui,test_config}
mkdir -p templates

# 4. pyproject.toml統合設定
# 全ての開発設定をpyproject.tomlに統合
# ruff, basedpyright, pytest設定を一元化
```

### 実装順序
1. **環境整備**:
   - 既存ファイル削除
   - pyproject.toml統合設定
   - src/レイアウトプロジェクト構造作成
2. **コア実装**: ExecutionModeManager → MonitorEngine → ActionEngine
3. **UI実装**: SystemTray → SetupWizard → ConfigViewer
4. **テスト**: 単体テスト → 統合テスト → パフォーマンステスト
5. **移行ツール**: JSON→TOML変換、設定移行
6. **リリース**: パッケージング → 配布 → ドキュメント更新

### 新プロジェクト構造（モダンsrc/レイアウト）
```
AI_reStarter/
├── src/
│   └── ai_restarter/          # メインパッケージ
│       ├── __init__.py
│       ├── __main__.py        # python -m ai_restarter エントリー
│       ├── core/              # コア機能
│       │   ├── __init__.py
│       │   ├── execution_mode_manager.py  # 実行モード管理
│       │   ├── monitor_engine.py
│       │   ├── action_engine.py
│       │   └── display_manager.py
│       ├── ui/                # UIコンポーネント
│       │   ├── __init__.py
│       │   ├── system_tray.py
│       │   ├── setup_wizard.py
│       │   └── config_viewer.py
│       └── config/            # 設定管理
│           ├── __init__.py
│           ├── toml_loader.py
│           └── template_manager.py
├── tests/                     # テストコード
│   ├── test_core/
│   ├── test_ui/
│   └── test_config/
├── templates/                 # テンプレート画像
├── profiles.toml              # アプリケーション設定
├── pyproject.toml             # プロジェクト・開発設定統合
└── README.md                 # プロジェクト説明
```

この計画により、保守性・拡張性・パフォーマンスを兼ね備えた現代的なアプリケーションへの進化を実現する。
