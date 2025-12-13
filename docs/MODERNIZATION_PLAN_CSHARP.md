# AI reStarter モダン化実装計画 (C#版)

## プロジェクト概要
Windows画面監視による汎用IDE自動復旧システム。特定パターン検出時の自動アクション実行を目的とする常駐型アプリケーション。

## 言語選択: C# (.NET 8)

### 選択理由
- ✅ **Windows統合**: ネイティブAPI、WinForms, WPF, Win32完全サポート
- ✅ **型安全性**: 強力な型システム、null許容参照型
- ✅ **AI実装容易性**: GitHub Copilot, LLMが非常に得意
- ✅ **豊富なライブラリ**: 画像処理、自動操作、GUIすべて充実
- ✅ **配布**: PublishSingleFile で単一exe化可能
- ✅ **パフォーマンス**: JITコンパイル、AOTコンパイル対応
- ✅ **開発体験**: Visual Studio, Rider の強力なIDE
- ✅ **エコシステム**: NuGet、成熟したツールチェーン

### 懸念点と対策
- ⚠️ **配布サイズ**: .NET Runtime込みで50-100MB
  - **対策**: PublishTrimmed, PublishAot でサイズ削減
- ⚠️ **起動時間**: JIT起動で若干遅い（500ms程度）
  - **対策**: ReadyToRun, AOTコンパイル
- ⚠️ **クロスプラットフォーム**: Windowsに特化
  - **対策**: 要件がWindows専用なので問題なし

## 技術スタック

### パッケージ管理
- **ビルドツール**: .NET SDK 8.0
- **パッケージマネージャー**: NuGet
- **依存関係更新**: Renovate（自動バージョン管理）
- **ロックファイル**: packages.lock.json（再現可能なビルド）

### プロジェクト設定
```xml
<Project Sdk="Microsoft.NET.Sdk">
  <PropertyGroup>
    <OutputType>WinExe</OutputType>
    <TargetFramework>net8.0-windows</TargetFramework>
    <UseWindowsForms>true</UseWindowsForms>
    <Nullable>enable</Nullable>
    <LangVersion>latest</LangVersion>
    <ImplicitUsings>enable</ImplicitUsings>

    <!-- 配布設定 -->
    <PublishSingleFile>true</PublishSingleFile>
    <SelfContained>true</SelfContained>
    <RuntimeIdentifier>win-x64</RuntimeIdentifier>
    <PublishTrimmed>true</PublishTrimmed>
    <EnableCompressionInSingleFile>true</EnableCompressionInSingleFile>

    <!-- 最適化 -->
    <DebugType>embedded</DebugType>
    <DebugSymbols>true</DebugSymbols>
  </PropertyGroup>

  <ItemGroup>
    <!-- 画像処理 -->
    <PackageReference Include="OpenCvSharp4" Version="4.9.0.20240103" />
    <PackageReference Include="OpenCvSharp4.runtime.win" Version="4.9.0.20240103" />

    <!-- システムトレイ -->
    <PackageReference Include="Hardcodet.NotifyIcon.Wpf" Version="1.1.0" />

    <!-- 設定ファイル -->
    <PackageReference Include="Tomlyn" Version="0.17.0" />

    <!-- ログ -->
    <PackageReference Include="Serilog" Version="4.0.0" />
    <PackageReference Include="Serilog.Sinks.File" Version="6.0.0" />
    <PackageReference Include="Serilog.Sinks.Console" Version="6.0.0" />

    <!-- 依存性注入 -->
    <PackageReference Include="Microsoft.Extensions.DependencyInjection" Version="8.0.0" />
    <PackageReference Include="Microsoft.Extensions.Hosting" Version="8.0.0" />

    <!-- テスト -->
    <PackageReference Include="xunit" Version="2.6.6" />
    <PackageReference Include="xunit.runner.visualstudio" Version="2.5.6" />
    <PackageReference Include="Moq" Version="4.20.70" />
    <PackageReference Include="FluentAssertions" Version="6.12.0" />
  </ItemGroup>
</Project>
```

### 開発ツール統一
- **パッケージ管理**: NuGet + Renovate
- **リンター**: Roslyn Analyzers（.NET標準）
- **フォーマッター**: EditorConfig + dotnet format
- **型チェック**: C#コンパイラ（null許容参照型有効）
- **テスト**: xUnit + Moq + FluentAssertions
- **ベンチマーク**: BenchmarkDotNet

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
├── AIReStarter.csproj     # C#プロジェクト設定
├── README.md             # プロジェクト説明
├── MODERNIZATION_PLAN_CSHARP.md # この計画書
└── profiles.toml         # アプリケーション設定
```

## アーキテクチャ設計

### プロジェクト構造
```
AIReStarter/
├── AIReStarter.csproj
├── Program.cs                    # エントリーポイント
├── Core/                         # コア機能
│   ├── ExecutionModeManager.cs   # 実行モード管理
│   ├── MonitorEngine.cs          # 画面監視・マッチング
│   ├── ActionEngine.cs           # 自動アクション実行
│   └── DisplayManager.cs         # マルチモニター・DPI対応
├── UI/                           # ユーザーインターフェース
│   ├── SystemTrayIcon.cs         # システムトレイ
│   ├── SetupWizard.cs            # 設定ウィザード（WPF）
│   └── ConfigViewer.cs           # 設定確認・デバッグ
├── Config/                       # 設定管理
│   ├── TemplateConfig.cs         # テンプレート設定
│   ├── ConfigLoader.cs           # TOML読み込み
│   └── AppSettings.cs            # アプリケーション設定
├── Models/                       # データモデル
│   ├── ExecutionMode.cs          # 実行モード列挙型
│   ├── Template.cs               # テンプレート
│   ├── MonitorRegion.cs          # 監視領域
│   └── ActionConfig.cs           # アクション設定
└── Tests/                        # テストプロジェクト
    ├── Core/
    ├── UI/
    └── Config/
```

### 型設計（重要）

```csharp
// 実行モード
public enum ExecutionMode
{
    Click,
    Chat,
    Keyboard
}

// テンプレート設定
public record Template
{
    public required string Name { get; init; }
    public required string Description { get; init; }
    public required ExecutionMode ExecutionMode { get; init; }
    public required MonitorRegion MonitorRegion { get; init; }
    public required MatchingConfig Matching { get; init; }
    public required ActionConfig Action { get; init; }
}

// 監視領域（相対座標）
public record MonitorRegion
{
    public required float X { get; init; }      // 0.0 - 1.0
    public required float Y { get; init; }      // 0.0 - 1.0
    public required float Width { get; init; }  // 0.0 - 1.0
    public required float Height { get; init; } // 0.0 - 1.0

    public bool IsValid() =>
        X >= 0 && X <= 1 &&
        Y >= 0 && Y <= 1 &&
        Width > 0 && Width <= 1 &&
        Height > 0 && Height <= 1;
}

// マッチング設定
public record MatchingConfig
{
    public required string File { get; init; }
    public required float Threshold { get; init; }  // 0.0 - 1.0
}

// アクション設定（判別共用体パターン）
public abstract record ActionConfig
{
    public record Click(
        int OffsetX,
        int OffsetY,
        int RetryCount
    ) : ActionConfig;

    public record Chat(
        string Command,
        string TargetElement
    ) : ActionConfig;

    public record Keyboard(
        string[] Keys
    ) : ActionConfig;
}

// グローバル設定
public record GlobalConfig
{
    public required float CheckInterval { get; init; }
    public required bool AdaptiveInterval { get; init; }
    public required string LogLevel { get; init; }
    public required ExecutionMode ActiveMode { get; init; }
}

// アプリケーション設定
public record AppConfig
{
    public required GlobalConfig Global { get; init; }
    public required List<Template> Templates { get; init; }
}
```

## 実装フェーズ

### Phase 1: コア機能（最優先）
**目標**: 基本的な監視・アクション実行機能

#### 1.1 ExecutionModeManager
```csharp
public class ExecutionModeManager
{
    private ExecutionMode _currentMode;
    private readonly Dictionary<ExecutionMode, List<Template>> _templatesByMode;

    public ExecutionMode CurrentMode => _currentMode;

    public void SwitchMode(ExecutionMode mode)
    {
        _currentMode = mode;
        // モード切り替えロジック
    }

    public IEnumerable<Template> GetActiveTemplates()
    {
        return _templatesByMode[_currentMode];
    }
}
```

#### 1.2 MonitorEngine
```csharp
public class MonitorEngine
{
    private readonly ILogger<MonitorEngine> _logger;
    private readonly DisplayManager _displayManager;

    public async Task<MatchResult?> FindTemplateAsync(
        Template template,
        CancellationToken cancellationToken)
    {
        // 画面キャプチャ
        using var screenshot = CaptureScreen(template.MonitorRegion);

        // テンプレートマッチング（OpenCvSharp）
        using var templateImage = Cv2.ImRead(template.Matching.File);
        using var result = new Mat();

        Cv2.MatchTemplate(screenshot, templateImage, result, TemplateMatchModes.CCoeffNormed);
        Cv2.MinMaxLoc(result, out _, out var maxVal, out _, out var maxLoc);

        if (maxVal >= template.Matching.Threshold)
        {
            return new MatchResult(maxLoc, maxVal);
        }

        return null;
    }
}
```

#### 1.3 ActionEngine
```csharp
public class ActionEngine
{
    public async Task ExecuteAsync(ActionConfig action, Point location)
    {
        switch (action)
        {
            case ActionConfig.Click click:
                await ExecuteClickAsync(location, click);
                break;
            case ActionConfig.Chat chat:
                await ExecuteChatAsync(chat);
                break;
            case ActionConfig.Keyboard keyboard:
                await ExecuteKeyboardAsync(keyboard);
                break;
        }
    }

    private async Task ExecuteClickAsync(Point location, ActionConfig.Click config)
    {
        var targetX = location.X + config.OffsetX;
        var targetY = location.Y + config.OffsetY;

        for (int i = 0; i < config.RetryCount; i++)
        {
            try
            {
                // Windows API でクリック
                SetCursorPos(targetX, targetY);
                mouse_event(MOUSEEVENTF_LEFTDOWN | MOUSEEVENTF_LEFTUP, 0, 0, 0, 0);
                return;
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "クリック失敗 (試行 {Attempt}/{Total})", i + 1, config.RetryCount);
                await Task.Delay(500);
            }
        }
    }

    [DllImport("user32.dll")]
    private static extern bool SetCursorPos(int x, int y);

    [DllImport("user32.dll")]
    private static extern void mouse_event(uint dwFlags, int dx, int dy, uint dwData, int dwExtraInfo);
}
```

#### 1.4 DisplayManager
```csharp
public class DisplayManager
{
    public Rectangle GetAbsoluteRegion(MonitorRegion relativeRegion)
    {
        var screen = Screen.PrimaryScreen.Bounds;

        return new Rectangle(
            (int)(screen.Width * relativeRegion.X),
            (int)(screen.Height * relativeRegion.Y),
            (int)(screen.Width * relativeRegion.Width),
            (int)(screen.Height * relativeRegion.Height)
        );
    }

    public float GetDpiScale()
    {
        using var graphics = Graphics.FromHwnd(IntPtr.Zero);
        return graphics.DpiX / 96.0f;
    }
}
```

### Phase 2: UI・設定機能（中優先）
**目標**: 直感的な設定とデバッグ機能

#### 2.1 SetupWizard（WPF）
```csharp
public partial class SetupWizard : Window
{
    private int _currentStep = 0;

    public SetupWizard()
    {
        InitializeComponent();
    }

    private void NextButton_Click(object sender, RoutedEventArgs e)
    {
        _currentStep++;

        switch (_currentStep)
        {
            case 1:
                ShowRegionSelector();
                break;
            case 2:
                ShowTemplateCapture();
                break;
            case 3:
                ShowActionConfig();
                break;
            case 4:
                ShowConfirmation();
                break;
        }
    }
}
```

#### 2.2 SystemTrayIcon
```csharp
public class SystemTrayIcon : IDisposable
{
    private readonly TaskbarIcon _notifyIcon;
    private readonly ExecutionModeManager _modeManager;

    public SystemTrayIcon(ExecutionModeManager modeManager)
    {
        _modeManager = modeManager;

        _notifyIcon = new TaskbarIcon
        {
            Icon = new Icon("app.ico"),
            ToolTipText = "AI reStarter"
        };

        BuildContextMenu();
    }

    private void BuildContextMenu()
    {
        var contextMenu = new ContextMenu();

        // 実行モード切り替え
        var modeMenu = new MenuItem { Header = "実行モード" };
        foreach (ExecutionMode mode in Enum.GetValues<ExecutionMode>())
        {
            var item = new MenuItem
            {
                Header = mode.ToString(),
                IsCheckable = true,
                IsChecked = mode == _modeManager.CurrentMode
            };
            item.Click += (s, e) => _modeManager.SwitchMode(mode);
            modeMenu.Items.Add(item);
        }
        contextMenu.Items.Add(modeMenu);

        _notifyIcon.ContextMenu = contextMenu;
    }
}
```

### Phase 3: 高度機能（低優先）
**目標**: カスタマイズ性と保守性向上

## 設定ファイル構造

### profiles.toml
```toml
# AI reStarter 設定

[global]
check_interval = 3.0
adaptive_interval = true
log_level = "INFO"
active_mode = "click"

[[templates]]
name = "run_button"
description = "実行ボタン検出用テンプレート"
execution_mode = "click"

[templates.monitor_region]
x = 0.1
y = 0.2
width = 0.8
height = 0.6

[templates.matching]
file = "run_button.png"
threshold = 0.8

[templates.action]
type = "click"
offset = [0, 0]
retry_count = 3
```

### TOML読み込み
```csharp
public class ConfigLoader
{
    public AppConfig LoadConfig(string path)
    {
        var tomlContent = File.ReadAllText(path);
        var model = Toml.ToModel(tomlContent);

        // Tomlynでパース
        return new AppConfig
        {
            Global = ParseGlobalConfig(model["global"]),
            Templates = ParseTemplates(model["templates"])
        };
    }
}
```

## パフォーマンス最適化

### .NET 8 最適化
- **JIT最適化**: Dynamic PGO（Profile-Guided Optimization）
- **AOTコンパイル**: ReadyToRun, NativeAOT
- **SIMD**: Vector<T> による画像処理高速化
- **Span<T>**: ゼロアロケーション処理

### 監視効率化
```csharp
public class AdaptiveMonitor
{
    private TimeSpan _currentInterval = TimeSpan.FromSeconds(3);

    public async Task MonitorAsync(CancellationToken cancellationToken)
    {
        while (!cancellationToken.IsCancellationRequested)
        {
            var result = await _monitorEngine.FindTemplateAsync(template, cancellationToken);

            if (result != null)
            {
                // 検出後は高頻度監視
                _currentInterval = TimeSpan.FromMilliseconds(500);
                await _actionEngine.ExecuteAsync(action, result.Location);
            }
            else
            {
                // 通常は低頻度
                _currentInterval = TimeSpan.FromSeconds(3);
            }

            await Task.Delay(_currentInterval, cancellationToken);
        }
    }
}
```

## エラーハンドリング

### カスタム例外
```csharp
public class AppException : Exception
{
    public AppException(string message) : base(message) { }
    public AppException(string message, Exception inner) : base(message, inner) { }
}

public class ConfigLoadException : AppException
{
    public ConfigLoadException(string message, Exception inner)
        : base($"設定ファイル読み込みエラー: {message}", inner) { }
}

public class TemplateMatchingException : AppException
{
    public TemplateMatchingException(string message)
        : base($"テンプレートマッチング失敗: {message}") { }
}
```

### グローバルエラーハンドラー
```csharp
public class Program
{
    [STAThread]
    public static void Main()
    {
        AppDomain.CurrentDomain.UnhandledException += OnUnhandledException;
        Application.ThreadException += OnThreadException;

        var app = new Application();
        app.Run();
    }

    private static void OnUnhandledException(object sender, UnhandledExceptionEventArgs e)
    {
        Log.Fatal(e.ExceptionObject as Exception, "未処理の例外が発生しました");
        MessageBox.Show("予期しないエラーが発生しました", "エラー", MessageBoxButtons.OK, MessageBoxIcon.Error);
    }
}
```

## テスト戦略

### 単体テスト（xUnit）
```csharp
public class MonitorRegionTests
{
    [Theory]
    [InlineData(0.1f, 0.2f, 0.8f, 0.6f, true)]
    [InlineData(-0.1f, 0.2f, 0.8f, 0.6f, false)]
    [InlineData(0.1f, 0.2f, 1.5f, 0.6f, false)]
    public void IsValid_ReturnsExpectedResult(float x, float y, float width, float height, bool expected)
    {
        // Arrange
        var region = new MonitorRegion { X = x, Y = y, Width = width, Height = height };

        // Act
        var result = region.IsValid();

        // Assert
        result.Should().Be(expected);
    }
}
```

### モックテスト（Moq）
```csharp
public class ActionEngineTests
{
    [Fact]
    public async Task ExecuteAsync_Click_CallsSetCursorPos()
    {
        // Arrange
        var mockLogger = new Mock<ILogger<ActionEngine>>();
        var engine = new ActionEngine(mockLogger.Object);
        var action = new ActionConfig.Click(0, 0, 1);
        var location = new Point(100, 100);

        // Act
        await engine.ExecuteAsync(action, location);

        // Assert
        // Windows APIの呼び出しを検証
    }
}
```

### 統合テスト
```csharp
public class EndToEndTests
{
    [Fact]
    public async Task MonitorAndExecute_DetectsTemplateAndClicks()
    {
        // Arrange
        var config = LoadTestConfig();
        var monitor = new MonitorEngine();
        var action = new ActionEngine();

        // Act
        var result = await monitor.FindTemplateAsync(config.Templates[0], CancellationToken.None);

        // Assert
        result.Should().NotBeNull();
    }
}
```

## 実装戦略

### ゼロベース実装（完全作り直し）
1. **作業ブランチ作成**: `feature/v2-csharp-rewrite`
2. **既存コード全削除**: クリーンな状態から開始
3. **.csproj設定**: 全依存関係を定義
4. **モダンなベストプラクティス適用**: .NET 8, C# 12
5. **依存性注入**: Microsoft.Extensions.DependencyInjection

### Git ワークフロー戦略

#### Phase 1: プロジェクト初期化
```bash
# 1. 作業ブランチ作成
git checkout -b feature/v2-csharp-rewrite

# 2. 既存ファイル全削除（git管理下）
git rm -rf src/ tests/ playground/ scripts/
git rm pyproject.toml .flake8 .pylintrc Makefile .pre-commit-config.yaml 2>/dev/null || true

# 3. .NETプロジェクト作成
dotnet new winforms -n AIReStarter
cd AIReStarter

# 4. 必要なパッケージ追加
dotnet add package OpenCvSharp4
dotnet add package OpenCvSharp4.runtime.win
dotnet add package Hardcodet.NotifyIcon.Wpf
dotnet add package Tomlyn
dotnet add package Serilog
```

#### Phase 2: 完成後のmainマージ
```bash
# 1. main ブランチに切り替え
git checkout main

# 2. main の既存ファイルを全削除
git rm -rf .
git clean -fdx

# 3. 作業ブランチの内容をマージ
git checkout feature/v2-csharp-rewrite -- .

# 4. コミット
git add .
git commit -m "feat: complete rewrite in C# (.NET 8) (v2.0.0)"

# 5. タグ付け
git tag -a v2.0.0 -m "Version 2.0.0 - C# implementation"
```

## 品質保証

### 静的解析
```bash
# Roslyn Analyzers
dotnet build /p:TreatWarningsAsErrors=true

# フォーマットチェック
dotnet format --verify-no-changes

# コード分析
dotnet build /p:EnableNETAnalyzers=true /p:AnalysisLevel=latest
```

### .editorconfig
```ini
root = true

[*.cs]
# インデント
indent_style = space
indent_size = 4

# 改行
end_of_line = crlf
insert_final_newline = true

# null許容参照型
dotnet_diagnostic.CS8600.severity = error
dotnet_diagnostic.CS8602.severity = error
dotnet_diagnostic.CS8603.severity = error

# 命名規則
dotnet_naming_rule.private_fields_should_be_camel_case.severity = warning
```

### 継続的インテグレーション
```yaml
# .github/workflows/ci.yml
name: CI

on: [push, pull_request]

jobs:
  build:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-dotnet@v4
        with:
          dotnet-version: '8.0.x'
      - run: dotnet restore
      - run: dotnet build --no-restore
      - run: dotnet test --no-build --verbosity normal
      - run: dotnet format --verify-no-changes
```

## デプロイメント

### ビルド
```bash
# リリースビルド（単一exe）
dotnet publish -c Release -r win-x64 \
  --self-contained true \
  /p:PublishSingleFile=true \
  /p:PublishTrimmed=true \
  /p:EnableCompressionInSingleFile=true

# 出力: bin/Release/net8.0-windows/win-x64/publish/AIReStarter.exe
# サイズ: 50-100MB（.NET Runtime込み）
```

### AOTコンパイル（オプション）
```bash
# Native AOT（起動高速化、サイズ削減）
dotnet publish -c Release -r win-x64 \
  /p:PublishAot=true

# サイズ: 10-20MB、起動時間: <100ms
```

### 配布
- GitHub Releases による配布
- 単一exeファイル（.NET Runtime込み）
- 自動ビルドパイプライン（GitHub Actions）
- ClickOnce配布（オプション）

## 今後の拡張性

### プラグインシステム
```csharp
public interface IActionPlugin
{
    string Name { get; }
    Task ExecuteAsync(ActionContext context);
}

public class PluginLoader
{
    public IEnumerable<IActionPlugin> LoadPlugins(string directory)
    {
        var assemblies = Directory.GetFiles(directory, "*.dll")
            .Select(Assembly.LoadFrom);

        return assemblies
            .SelectMany(a => a.GetTypes())
            .Where(t => typeof(IActionPlugin).IsAssignableFrom(t) && !t.IsInterface)
            .Select(t => (IActionPlugin)Activator.CreateInstance(t)!);
    }
}
```

### AI機能
- ML.NET によるモデル実行
- ONNX Runtime統合
- ボタンの自動検出

## C#実装の成功要因

### 必須条件
1. **Visual Studio / Rider**: 強力なIDE
2. **null許容参照型**: 有効化必須
3. **依存性注入**: Microsoft.Extensions.DependencyInjection
4. **ログ**: Serilog

### 推奨プラクティス
- **record型**: イミュータブルなデータモデル
- **パターンマッチング**: switch式の活用
- **async/await**: 非同期処理の徹底
- **LINQ**: データ処理の簡潔化

## まとめ

C#実装は、**Windows統合・AI実装容易性・豊富なライブラリ**で最もバランスの取れた選択肢です。

### 成功の鍵
- ✅ Windows統合が完璧
- ✅ AIが非常に実装しやすい
- ✅ 豊富なライブラリとツール
- ✅ 強力な型システム

### トレードオフ
- ⚠️ 配布サイズが大きい（50-100MB）
- ⚠️ 起動時間がRustより遅い（500ms程度）

この計画により、**信頼性と開発効率**を兼ね備えた現代的なアプリケーションへの進化を実現します。
