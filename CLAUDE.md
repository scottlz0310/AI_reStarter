# CLAUDE.md

このファイルは、このリポジトリでコードを操作する際にClaude Code (claude.ai/code) にガイダンスを提供します。

## プロジェクト概要

**AI reStarter v2** は、C#で構築されたWindows専用のデスクトップ自動化システム（Proof of Concept）です。OpenCVのテンプレートマッチングを使用して画面上の特定のビジュアルパターンを監視し、プロセスが停止したことを自動検出し、自動入力シミュレーションを通じて中断されたタスクを安全に再開する常駐アプリケーションです。このC#版は、元のPython実装で課題となっていたDPIスケーリングとマルチモニター座標の正規化問題に特に対処しています。

**主要技術**: C# (.NET 10), WPF + Windows Forms, OpenCvSharp4, Serilog

## 必須の開発コマンド

### ビルドとテスト
```bash
# NuGetパッケージの復元
dotnet restore

# プロジェクトのビルド（Releaseモード）
dotnet build --configuration Release

# アプリケーションの実行
dotnet run --project src/AIReStarter

# 全テストの実行
dotnet test

# コードカバレッジ付きテスト実行
dotnet test --configuration Release --collect:"XPlat Code Coverage"

# 特定のテストクラスの実行
dotnet test --filter "FullyQualifiedName~MatchGuardTests"

# コードフォーマットの検証（CIチェック）
dotnet format --verify-no-changes

# コードフォーマットの適用
dotnet format
```

### 設定
- 初回実行前に `profiles.example.toml` を `profiles.toml` にコピー
- テンプレート画像は `templates/` ディレクトリに配置
- 設定は正規化座標（0.0-1.0）を使用したTOML形式

### 単一ファイル実行可能形式の公開
```bash
dotnet publish --configuration Release --runtime win-x64 --self-contained true /p:PublishSingleFile=true
```

## アーキテクチャ概要

### コア座標系: DPI対応仮想スクリーン

アプリケーションは、完全なDPI認識（Per-Monitor DPI v2）を持つWindowsの**仮想スクリーン座標系**で動作します。これは理解が重要です：

- **仮想スクリーン**: すべてのモニターが、負の座標を含む単一の座標空間を形成
- **DPIスケーリング**: 各モニターは異なるDPIスケーリング（100%、125%、150%、200%）を持つ可能性
- **座標フロー**: ユーザー設定（0.0-1.0正規化） → 仮想スクリーンピクセル → DPI補正済み物理ピクセル → テンプレートマッチング

[DisplayManager.cs](src/AIReStarter/Core/DisplayManager.cs) は、モニター列挙、DPI計算、座標正規化を処理する基盤です。他のすべてのコンポーネントは、これが正しく動作することに依存しています。

### コンポーネントアーキテクチャ

**1. Display & Capture レイヤー** ([Core/](src/AIReStarter/Core/))

- [DisplayManager.cs](src/AIReStarter/Core/DisplayManager.cs): モニターの列挙、DPIスケーリングの計算、負のオフセットを含む座標の正規化
- [ScreenCaptureService.cs](src/AIReStarter/Core/ScreenCaptureService.cs): 仮想スクリーンからのDPI対応領域キャプチャ
- [TemplateMatcher.cs](src/AIReStarter/Core/TemplateMatcher.cs): 設定可能な閾値を持つOpenCVベースのテンプレートマッチング
- [MatchGuard.cs](src/AIReStarter/Core/MatchGuard.cs): 連続一致カウントとクールダウン期間による重複アクション防止

**2. Monitoring & Action レイヤー** ([Services/](src/AIReStarter/Services/))

- [MonitorService.cs](src/AIReStarter/Services/MonitorService.cs): キャプチャ → マッチング → ガードチェック → アクション実行を統括するメイン監視ループ
- [ActionEngine.cs](src/AIReStarter/Services/ActionEngine.cs): 3種類のアクションを実行：
  - **Click**: 検出位置でのマウスクリック（オフセットとリトライロジック付き）
  - **Chat**: チャットアプリケーション用のテキスト入力（IME対応）
  - **Keyboard**: グローバルキーボードショートカット（例: Ctrl+Shift+P）
- [HotKeyService.cs](src/AIReStarter/Services/HotKeyService.cs): グローバルホットキー（Ctrl+Alt+Pで一時停止/再開、Ctrl+Alt+Qで安全終了）

**3. Input Simulation レイヤー** ([Input/](src/AIReStarter/Input/))

- [InputSender.cs](src/AIReStarter/Input/InputSender.cs): IMEサポートを持つ信頼性の高いマウス/キーボード入力のためにWin32 `SendInput` APIを使用（フックではない）

**4. UI レイヤー** ([UI/](src/AIReStarter/UI/))

- [SystemTrayManager.cs](src/AIReStarter/UI/SystemTrayManager.cs): 開始/停止/終了メニューを持つシステムトレイ統合
- [MainWindow.xaml](src/AIReStarter/MainWindow.xaml) / [MainWindow.xaml.cs](src/AIReStarter/MainWindow.xaml.cs): WPFメインウィンドウ（最小限のUI）

**5. Configuration レイヤー** ([Config/](src/AIReStarter/Config/))

- [ConfigLoader.cs](src/AIReStarter/Config/ConfigLoader.cs): Tomlynを使用したTOML設定パーサー
- [AppConfig.cs](src/AIReStarter/Config/AppConfig.cs): 強く型付けされた設定モデル

### 設定フォーマット (profiles.toml)

設定は、仮想スクリーンに対する**正規化座標（0.0-1.0）**を使用します：

```toml
[global]
check_interval = 2.0           # 監視間隔（秒）
cooldown_seconds = 15.0        # アクション後のクールダウン
max_consecutive_matches = 2    # ガードが起動する前に許容される連続一致回数
action_delay_ms = 250          # 入力操作間の遅延
log_level = "Information"      # Verbose/Debug/Information/Warning/Error/Fatal

[[templates]]
name = "run_button"
monitor = ""                   # 空 = 仮想スクリーン; それ以外は特定のモニター名

[templates.monitor_region]
x = 0.40                       # 正規化座標: 0.0 = 左端, 1.0 = 右端
y = 0.78                       # 仮想スクリーン（すべてのモニターを含む）の範囲
width = 0.20
height = 0.18

[templates.matching]
file = "templates/run_button.png"
threshold = 0.82               # OpenCVマッチング閾値（0.0-1.0）

[templates.action]
type = "click"                 # click / chat / keyboard
offset = [0, 0]                # マッチ位置からのピクセルオフセット
retry_count = 3
```

### 重要な設計判断

1. **なぜマウスフックではなくSendInputか**: SendInputの方が信頼性が高く、他のアプリケーションに干渉しない
2. **なぜ連続一致ガードか**: クリック後にUI状態が変わらない場合の暴走自動化を防止
3. **なぜ仮想スクリーン座標か**: 負の座標を含むマルチモニターセットアップを処理（プライマリの左/上のモニター）
4. **なぜPer-Monitor DPI v2か**: 各モニターが座標の歪みなく異なるスケーリングを持てる
5. **なぜJSONではなくTOMLか**: コメントサポート付きで設定ファイルとして人間に読みやすい

## 開発ガイドライン

### コードスタイル

- **Nullable参照型**: プロジェクト全体で有効化（`<Nullable>enable</Nullable>`）
- **警告をエラーとして扱う**: 厳格なコンパイル（`<TreatWarningsAsErrors>true</TreatWarningsAsErrors>`）
- **コードフォーマット**: コミット前に `dotnet format` を使用（CIで強制）

### Serilogによるログ記録

すべてのコンポーネントは構造化ログ記録にSerilogを使用します。ログレベル：

- **Verbose**: 詳細なトレース情報（すべてのマッチ試行、座標計算）
- **Debug**: 診断情報（マッチ結果、アクション判断）
- **Information**: 一般的なフロー（監視開始/停止、アクション実行）
- **Warning**: 予期しない状況（マッチ閾値未達、リトライ試行）
- **Error**: 失敗（キャプチャエラー、アクション実行失敗）

### テスト

- **フレームワーク**: xUnit + FluentAssertions
- **カバレッジ**: coverletで追跡（Cobertura形式のcoverage.xml）
- **テスト構造**: [tests/AIReStarter.Tests/](tests/AIReStarter.Tests/)
  - [MatchGuardTests.cs](tests/AIReStarter.Tests/MatchGuardTests.cs): コアガードロジックの検証
  - [ConfigLoaderPathTests.cs](tests/AIReStarter.Tests/ConfigLoaderPathTests.cs): 設定読み込みテスト
  - [TomlParseTests.cs](tests/AIReStarter.Tests/TomlParseTests.cs): TOMLパース検証

### DPIとマルチモニターのデバッグ

座標問題をデバッグする際：

1. DPIスケーリングを確認: [DisplayManager.cs](src/AIReStarter/Core/DisplayManager.cs) が起動時にDPI情報をログ出力
2. 仮想スクリーン境界を確認: 負の座標を含む可能性がある
3. Verboseログを使用して座標変換をトレース
4. テンプレートマッチングは生の画面座標ではなく、DPI補正済みピクセル座標で行われる

## プロジェクトの制約

- **Windows専用**: Win32 APIを使用（SendInput、SetCursorPos、EnumDisplayMonitors）
- **.NET 10必須**: 最新の.NETフレームワーク機能
- **WPF + Windows Formsハイブリッド**: メインウィンドウはWPF、システムトレイはWinForms（NotifyIcon）
- **OpenCV依存**: OpenCvSharp4.runtime.winを介してネイティブOpenCVバイナリを含む

## CI/CDパイプライン

[.github/workflows/](.github/workflows/) 内のGitHub Actionsワークフロー：

- [ci-cd.yml](.github/workflows/ci-cd.yml): Windowsランナーでのビルド、テスト、コードカバレッジ
- [quality-check.yml](.github/workflows/quality-check.yml): `dotnet format` 検証
- [security-check.yml](.github/workflows/security-check.yml): セキュリティスキャン

すべてのワークフローは .NET 10.0.x SDK を持つ `windows-latest` 上で実行されます。

## よくあるトラブルシューティング

### テンプレートマッチングが動作しない

1. テンプレート画像が `templates/` ディレクトリに存在することを確認
2. `matching.threshold` を確認（低い = より寛容、通常0.7-0.9の範囲）
3. Verboseログを有効にしてマッチスコアを確認
4. テンプレートキャプチャと実行時でDPIスケーリングが一致していることを確認

### 座標がターゲットから外れる

1. DPI認識が初期化されていることを確認（[Interop/DpiAwareness.cs](src/AIReStarter/Interop/DpiAwareness.cs)）
2. DisplayManagerログでモニター設定を確認
3. `monitor_region` 座標が正規化されていることを確認（0.0-1.0）
4. 注意: 仮想スクリーンは負の座標を持つ可能性がある

### アクションが実行されない

1. MatchGuardのクールダウン期間を確認（設定の `cooldown_seconds`）
2. `max_consecutive_matches` を超えていないか確認
3. ガード起動メッセージのログを確認
4. UIが応答するのに十分な `action_delay_ms` であることを確認

## ドキュメント参照

- [README.md](README.md): セットアップ手順付き日本語ドキュメント
- [MODERNIZATION_PLAN_CSHARP.md](docs/MODERNIZATION_PLAN_CSHARP.md): 詳細な移行計画とアーキテクチャ判断
- [RELEASE_NOTES.md](RELEASE_NOTES.md): バージョン履歴と変更履歴
- [SECURITY.md](SECURITY.md): セキュリティポリシーと脆弱性報告
