# AI reStarter モダン化実装計画 (Rust版)

## プロジェクト概要
Windows画面監視による汎用IDE自動復旧システム。特定パターン検出時の自動アクション実行を目的とする常駐型アプリケーション。

## 言語選択: Rust

### 選択理由
- ✅ **単一バイナリ配布**: 依存関係なし、5-10MB程度
- ✅ **高速起動**: ネイティブコード、起動時間 <100ms
- ✅ **メモリ効率**: 常駐型アプリに最適、低リソース消費
- ✅ **型安全性**: コンパイル時の厳格な型チェック、実行時エラー最小化
- ✅ **メモリ安全性**: 所有権システムによるメモリリーク・競合状態の防止
- ✅ **パフォーマンス**: C/C++並みの実行速度
- ✅ **将来性**: モダンなエコシステム、急成長中のコミュニティ

### 懸念点と対策
- ⚠️ **学習曲線**: 所有権システムの理解が必要
  - **対策**: 段階的実装、小さいモジュールから検証
- ⚠️ **AI実装難易度**: Pythonより修正ループのリスク
  - **対策**: Claude 3.5 Sonnet, GPT-4等のRust対応LLM使用
- ⚠️ **ライブラリ成熟度**: Pythonより選択肢が少ない
  - **対策**: 実績あるクレートを厳選、プロトタイプで検証

## 技術スタック

### パッケージ管理
- **ビルドツール**: Cargo（Rust標準）
- **依存関係更新**: Renovate（自動バージョン管理）
- **ロックファイル**: Cargo.lock（再現可能なビルド）

### コア依存関係
```toml
[package]
name = "ai-restarter"
version = "2.0.0"
edition = "2021"
rust-version = "1.75"  # 最新安定版

[dependencies]
# 画像処理
image = "0.25"           # 画像読み込み・操作
imageproc = "0.25"       # テンプレートマッチング

# Windows API
windows = { version = "0.58", features = [
    "Win32_UI_WindowsAndMessaging",
    "Win32_Graphics_Gdi",
    "Win32_Foundation",
    "Win32_System_Threading",
] }

# 自動操作
enigo = "0.2"            # クロスプラットフォーム入力シミュレーション

# システムトレイ
tray-item = "0.9"        # システムトレイアイコン

# GUI（設定ツール）
egui = "0.29"            # 即時モードGUI
eframe = "0.29"          # eGuiアプリケーションフレームワーク

# 設定ファイル
toml = "0.8"             # TOML パーサー
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"       # JSON サポート（移行用）

# ログ
tracing = "0.1"          # 構造化ログ
tracing-subscriber = { version = "0.3", features = ["env-filter"] }

# 非同期ランタイム
tokio = { version = "1.0", features = ["full"] }

# エラーハンドリング
anyhow = "1.0"           # エラー処理簡略化
thiserror = "1.0"        # カスタムエラー型

[dev-dependencies]
# テストフレームワーク
criterion = "0.5"        # ベンチマーク
mockall = "0.12"         # モック

[profile.release]
opt-level = 3            # 最大最適化
lto = true               # Link Time Optimization
codegen-units = 1        # 単一コード生成ユニット（最適化優先）
strip = true             # デバッグシンボル削除（サイズ削減）
```

### 開発ツール統一
- **パッケージ管理**: Cargo + Renovate
- **リンター**: clippy（Rust標準、厳格モード）
- **フォーマッター**: rustfmt（Rust標準）
- **型チェック**: Rustコンパイラ（最も厳格）
- **テスト**: cargo test（標準テストフレームワーク）
- **ベンチマーク**: criterion

### 削除対象ファイル・ディレクトリ
```
削除対象:
├── src/                    # 既存Pythonソースコード
├── playground/             # 開発・テスト用ファイル
├── scripts/               # 開発・運用スクリプト
├── tests/                 # 既存テストコード
├── pyproject.toml         # Python設定
├── .flake8               # Python設定
├── .pylintrc             # Python設定
├── Makefile              # Python設定
└── .pre-commit-config.yaml # Python設定

保持対象:
├── Cargo.toml             # Rust設定
├── README.md             # プロジェクト説明
├── MODERNIZATION_PLAN_RUST.md # この計画書
└── profiles.toml         # アプリケーション設定
```

## アーキテクチャ設計

### モジュール構造
```
src/
├── main.rs                      # エントリーポイント
├── lib.rs                       # ライブラリルート
├── core/                        # コア機能
│   ├── mod.rs
│   ├── execution_mode.rs        # 実行モード管理（click/chat/keyboard）
│   ├── monitor.rs               # 画面監視・マッチング
│   ├── action.rs                # 自動アクション実行
│   └── display.rs               # マルチモニター・DPI対応
├── ui/                          # ユーザーインターフェース
│   ├── mod.rs
│   ├── tray.rs                  # システムトレイ
│   ├── setup_wizard.rs          # 設定ウィザード
│   └── config_viewer.rs         # 設定確認・デバッグ
├── config/                      # 設定管理
│   ├── mod.rs
│   ├── template.rs              # テンプレート設定
│   └── loader.rs                # TOML読み込み
└── error.rs                     # エラー型定義
```

### 型設計（重要）

```rust
// 実行モード
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ExecutionMode {
    Click,
    Chat,
    Keyboard,
}

// テンプレート設定
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Template {
    pub name: String,
    pub description: String,
    pub execution_mode: ExecutionMode,
    pub monitor_region: MonitorRegion,
    pub matching: MatchingConfig,
    pub action: Action,
}

// 監視領域（相対座標）
#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub struct MonitorRegion {
    pub x: f32,      // 0.0 - 1.0
    pub y: f32,      // 0.0 - 1.0
    pub width: f32,  // 0.0 - 1.0
    pub height: f32, // 0.0 - 1.0
}

// マッチング設定
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MatchingConfig {
    pub file: PathBuf,
    pub threshold: f32,  // 0.0 - 1.0
}

// アクション
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "lowercase")]
pub enum Action {
    Click {
        offset: (i32, i32),
        retry_count: u32,
    },
    Chat {
        command: String,
        target_element: String,
    },
    Keyboard {
        keys: Vec<String>,
    },
}

// グローバル設定
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GlobalConfig {
    pub check_interval: f32,
    pub adaptive_interval: bool,
    pub log_level: String,
    pub active_mode: ExecutionMode,
}

// アプリケーション設定
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AppConfig {
    pub global: GlobalConfig,
    pub templates: Vec<Template>,
}
```

## 実装フェーズ

### Phase 0: プロトタイプ検証（1-2日）
**目標**: Rustでの実装可能性を検証

#### 検証項目
1. **画面キャプチャ**: `windows-rs`でスクリーンショット取得
2. **画像処理**: `image` + `imageproc`でテンプレートマッチング
3. **自動操作**: `enigo`でクリック・キーボード操作
4. **システムトレイ**: `tray-item`でトレイアイコン表示

#### 判断基準
- ✅ スムーズに実装できた → Phase 1へ進む
- ❌ 修正ループが多い → C#版に切り替え検討
- ❌ ライブラリが不足 → C#版に切り替え検討

### Phase 1: コア機能（最優先）
**目標**: 基本的な監視・アクション実行機能

#### 1.1 ExecutionModeManager
- 実行モード切り替え（click/chat/keyboard）
- モード別テンプレート・アクション管理
- アクティブモードの状態管理
- テンプレートベースの汎用的な設定

#### 1.2 MonitorEngine
- 効率的な画面キャプチャ（3秒間隔、適応的調整）
- テンプレートマッチング（`imageproc`）
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

#### 2.1 SetupWizard（eGui）
- Step1: 監視領域のドラッグ選択
- Step2: テンプレート画像の取得
- Step3: アクション設定とテスト
- Step4: 設定確認と保存

#### 2.2 ConfigViewer（eGui）
- 現在の設定状態を視覚表示
- マッチング精度のリアルタイム表示
- 設定妥当性チェック
- 環境変化検出と再設定提案

#### 2.3 SystemTray
- 監視状態の表示
- 実行モード切り替え
- 設定画面へのアクセス
- ログ表示

### Phase 3: 高度機能（低優先）
**目標**: カスタマイズ性と保守性向上

#### 3.1 AdvancedTemplateManager
- 複数テンプレートの組み合わせ
- テンプレートの自動更新
- 精度向上のための最適化

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
```

## パフォーマンス最適化

### Rust特有の最適化
- **ゼロコスト抽象化**: 抽象化によるオーバーヘッドなし
- **所有権システム**: ガベージコレクション不要、予測可能なメモリ管理
- **SIMD最適化**: 画像処理の高速化
- **並行処理**: `tokio`による効率的な非同期処理

### 監視効率化
- 適応的監視間隔（通常3秒、検出後0.5秒、高負荷時5秒）
- テンプレート画像のメモリキャッシュ
- 不要な画像処理の削減
- 非同期I/Oによるブロッキング回避

### メモリ管理
- 画面キャプチャの即座解放（所有権システム）
- テンプレート画像の効率的な保存
- ログローテーション

## エラーハンドリング

### Rust型安全なエラー処理
```rust
use thiserror::Error;

#[derive(Error, Debug)]
pub enum AppError {
    #[error("設定ファイル読み込みエラー: {0}")]
    ConfigLoad(#[from] toml::de::Error),

    #[error("画像読み込みエラー: {0}")]
    ImageLoad(#[from] image::ImageError),

    #[error("テンプレートマッチング失敗")]
    MatchingFailed,

    #[error("アクション実行失敗: {0}")]
    ActionFailed(String),

    #[error("Windows API エラー: {0}")]
    WindowsApi(#[from] windows::core::Error),
}

pub type Result<T> = std::result::Result<T, AppError>;
```

### エラー戦略
- **コンパイル時**: 型システムで大部分のエラーを防止
- **実行時**: `Result`型で明示的なエラーハンドリング
- **パニック**: 回復不可能なエラーのみ（最小化）

## テスト戦略

### 単体テスト
```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_monitor_region_validation() {
        let region = MonitorRegion {
            x: 0.1,
            y: 0.2,
            width: 0.8,
            height: 0.6,
        };
        assert!(region.is_valid());
    }
}
```

### 統合テスト
- `tests/` ディレクトリで実際の動作確認
- モック使用による外部依存排除

### ベンチマーク
```rust
use criterion::{black_box, criterion_group, criterion_main, Criterion};

fn benchmark_template_matching(c: &mut Criterion) {
    c.bench_function("template_matching", |b| {
        b.iter(|| {
            // テンプレートマッチング処理
        });
    });
}

criterion_group!(benches, benchmark_template_matching);
criterion_main!(benches);
```

## 実装戦略

### ゼロベース実装（完全作り直し）
1. **作業ブランチ作成**: `feature/v2-rust-rewrite`
2. **既存コード全削除**: クリーンな状態から開始
3. **Cargo.toml設定**: 全依存関係を定義
4. **モダンなベストプラクティス適用**: Rust 2021 Edition
5. **段階的実装**: プロトタイプ → コア → UI → 高度機能

### Git ワークフロー戦略

#### Phase 0: プロトタイプ検証
```bash
# 1. プロトタイプブランチ作成
git checkout -b prototype/rust-feasibility

# 2. 最小限の実装で検証
cargo new ai-restarter --bin
cd ai-restarter

# 3. 検証結果に基づいて判断
# ✅ 成功 → feature/v2-rust-rewrite へ移行
# ❌ 失敗 → C#版検討
```

#### Phase 1: 本実装
```bash
# 1. 作業ブランチ作成
git checkout -b feature/v2-rust-rewrite

# 2. 既存ファイル全削除（git管理下）
git rm -rf src/ tests/ playground/ scripts/
git rm pyproject.toml .flake8 .pylintrc Makefile .pre-commit-config.yaml 2>/dev/null || true

# 3. Rustプロジェクト初期化
cargo init --name ai-restarter

# 4. 実装開始
```

#### Phase 2: 完成後のmainマージ（安全な置き換え）
```bash
# 1. main ブランチに切り替え
git checkout main

# 2. main の既存ファイルを全削除（git除外ファイルの影響を排除）
git rm -rf .
git clean -fdx  # git除外ファイルも完全削除

# 3. 作業ブランチの内容をマージ
git checkout feature/v2-rust-rewrite -- .

# 4. コミット
git add .
git commit -m "feat: complete rewrite in Rust (v2.0.0)"

# 5. タグ付け
git tag -a v2.0.0 -m "Version 2.0.0 - Rust implementation"
```

## 品質保証

### 静的解析
```bash
# Clippy（厳格モード）
cargo clippy -- -D warnings

# フォーマットチェック
cargo fmt -- --check

# 型チェック
cargo check
```

### 継続的インテグレーション
```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
      - run: cargo test --all-features
      - run: cargo clippy -- -D warnings
      - run: cargo fmt -- --check
```

## デプロイメント

### ビルド
```bash
# リリースビルド（最適化）
cargo build --release

# 単一バイナリ: target/release/ai-restarter.exe
# サイズ: 5-10MB（依存関係込み）
```

### 配布
- GitHub Releases による配布
- 単一exeファイル（依存なし）
- 自動ビルドパイプライン（GitHub Actions）

### クロスコンパイル（将来）
```bash
# Linux/macOS対応も可能
cargo build --target x86_64-unknown-linux-gnu
cargo build --target x86_64-apple-darwin
```

## 今後の拡張性

### プラグインシステム
- 動的ライブラリ（.dll）によるプラグイン
- WebAssembly（WASM）プラグイン

### AI機能
- ONNXランタイムによるモデル実行
- ボタンの自動検出
- 最適なアクションの提案

## Rust実装の成功要因

### 必須条件
1. **LLMモデル選択**: Claude 3.5 Sonnet, GPT-4, Gemini 2.0 Flash
2. **段階的実装**: プロトタイプで検証 → 本実装
3. **明確な型設計**: 事前に型を定義、修正ループ回避
4. **テスト駆動**: コンパイルエラーを早期発見

### 推奨プラクティス
- **小さいモジュール**: 1モジュール = 1責務
- **明示的なエラー処理**: `Result`型の徹底
- **ドキュメント**: `///`コメントで型・関数を説明
- **ベンチマーク**: パフォーマンス回帰を防止

## まとめ

Rust実装は、**型安全性・パフォーマンス・配布の簡単さ**で最高の選択肢です。

### 成功の鍵
- ✅ プロトタイプで実装可能性を検証
- ✅ 段階的実装で修正ループを回避
- ✅ Rust対応LLMの活用
- ✅ 明確な型設計

### リスク管理
- ⚠️ プロトタイプで問題発生 → C#版に切り替え
- ⚠️ ライブラリ不足 → C#版に切り替え

この計画により、**最高のパフォーマンスと信頼性**を兼ね備えた現代的なアプリケーションへの進化を実現します。
