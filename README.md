# AI reStarter v2 (C# PoC)

Windows専用の常駐アプリとして、停止した処理を自動検知し安全に再開するC#/.NET 8版のPoCです。Python版で課題だったDPIスケーリングとマルチモニター（負の座標含む）を優先的に解決します。

## ゴール
- DPIスケーリング対応（Per-Monitor v2 / SendInput 前提）
- マルチモニター座標の正規化（仮想スクリーン基準、負の座標も許容）
- SendInputによる信頼性の高いクリック・キー入力（IME前提のテキスト送出）
- グローバルホットキーでの安全停止（Ctrl+Alt+Q）と一時停止/再開（Ctrl+Alt+P）
- 連続一致ガード＋クールダウン、Serilogベースのログ

## 主要コンポーネント
- `src/AIReStarter/Core/DisplayManager.cs` : モニター列挙・DPIスケール計算・座標補正
- `src/AIReStarter/Core/ScreenCaptureService.cs` : DPI補正済み領域キャプチャ
- `src/AIReStarter/Core/TemplateMatcher.cs` : OpenCVテンプレートマッチング
- `src/AIReStarter/Core/MatchGuard.cs` : 連続一致ガードとクールダウン
- `src/AIReStarter/Services/MonitorService.cs` : 監視ループ、ガード判定、アクション実行
- `src/AIReStarter/Services/ActionEngine.cs` : アクション実行の制御
- `src/AIReStarter/Services/HotKeyService.cs` : グローバルホットキー（安全停止用）
- `src/AIReStarter/Input/InputSender.cs` : SendInput/SetCursorPosでのクリック・キー送出
- `src/AIReStarter/UI/SystemTrayManager.cs` : トレイメニューによる開始/停止/終了
- `src/AIReStarter/Config/ConfigLoader.cs` : TOML設定ファイルの読み込み
- `src/AIReStarter/Config/AppConfig.cs` : アプリケーション設定の型定義

## セットアップ
1) 前提: Windows + .NET 8 SDK
2) 依存関係取得
```
dotnet restore
```
3) プロファイル作成
   - `profiles.example.toml` を `profiles.toml` にコピー
   - `matching.file` にテンプレート画像パス、`monitor_region` を 0.0-1.0 の相対座標で調整
4) 実行
```
dotnet run --project src/AIReStarter
```

## ホットキー / 操作
- `Ctrl + Alt + P` : 監視の一時停止/再開
- `Ctrl + Alt + Q` : 安全終了
- トレイメニュー: 開始/停止/終了（デフォルトのアプリケーションアイコン）

## 設定ファイル概要（profiles.toml）
- `[global]` : `check_interval`, `cooldown_seconds`, `max_consecutive_matches`, `action_delay_ms`, `log_level`
- `[[templates]]` :
  - `monitor_region` … 画面に対する相対座標 (0.0-1.0)。複数モニター時は仮想スクリーン基準
  - `matching.file` / `matching.threshold`
  - `action` … `click`(offset/retry)、`chat`(command/target_element)、`keyboard`(keys)
- サンプル: `profiles.example.toml`

## テスト
```
dotnet test
```

## ブランチ方針
- 本ブランチ: `feature/v2-csharp-rewrite`（C# PoC）
- Python版/Rust PoC は別ブランチに保持
