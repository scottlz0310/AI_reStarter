using System;
using System.IO;
using System.Text;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Input;
using AIReStarter.Config;
using AIReStarter.Interop;
using AIReStarter.Services;
using AIReStarter.UI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Serilog;
using Serilog.Events;
using MessageBox = System.Windows.MessageBox;

namespace AIReStarter;

/// <summary>
/// アプリケーションの起動/終了処理をまとめる。
/// DPI対応とサービス起動を最優先に実行する。
/// </summary>
public partial class App : System.Windows.Application
{
    private IHost? _host;
    private HotKeyService? _hotKeyService;
    private MonitorService? _monitorService;
    private SystemTrayManager? _trayManager;

    protected override async void OnStartup(StartupEventArgs e)
    {
        base.OnStartup(e);

        DpiAwareness.EnsurePerMonitorV2();

        var configPath = File.Exists("profiles.toml") ? "profiles.toml" : "profiles.example.toml";
        var loader = new ConfigLoader();
        AppConfig config;

        try
        {
            config = loader.Load(configPath);
        }
        catch (ConfigLoadException ex)
        {
            MessageBox.Show(
                $"設定ファイルの読み込みに失敗しました: {ex.Message}",
                "AI reStarter (C# PoC)",
                MessageBoxButton.OK,
                MessageBoxImage.Error);
            Shutdown(-1);
            return;
        }

        ConfigureLogging(config.Global.LogLevel);

        _host = Host.CreateDefaultBuilder(e.Args)
            .UseSerilog()
            .ConfigureServices(services =>
            {
                services.AddSingleton(config);
                services.AddSingleton<ConfigLoader>();
                services.AddSingleton<Core.DisplayManager>();
                services.AddSingleton<Core.ScreenCaptureService>();
                services.AddSingleton<Core.TemplateMatcher>();
                services.AddSingleton<Core.MatchGuard>();
                services.AddSingleton<Input.InputSender>();
                services.AddSingleton<ActionEngine>();
                services.AddSingleton<MonitorService>();
                services.AddSingleton<HotKeyService>();
                services.AddSingleton<SystemTrayManager>();
                services.AddSingleton<MainWindow>();
            })
            .Build();

        await _host.StartAsync();

        _monitorService = _host.Services.GetRequiredService<MonitorService>();
        _monitorService.Start();

        _hotKeyService = _host.Services.GetRequiredService<HotKeyService>();
        _hotKeyService.Register(Key.Q, ModifierKeys.Control | ModifierKeys.Alt, async () =>
        {
            Log.Information("停止ホットキーを検出しました。アプリケーションを終了します。");
            await _monitorService.StopAsync();
            Shutdown();
        });
        _hotKeyService.Register(Key.P, ModifierKeys.Control | ModifierKeys.Alt, () =>
        {
            _ = _monitorService.ToggleAsync();
        });

        _trayManager = _host.Services.GetRequiredService<SystemTrayManager>();
        _trayManager.Bind(_monitorService, Shutdown);

        var window = _host.Services.GetRequiredService<MainWindow>();
        window.Show();
    }

    protected override async void OnExit(ExitEventArgs e)
    {
        _hotKeyService?.Dispose();
        _trayManager?.Dispose();

        if (_host is not null)
        {
            await _host.StopAsync(TimeSpan.FromSeconds(5));
            _host.Dispose();
        }

        Log.CloseAndFlush();
        base.OnExit(e);
    }

    private static void ConfigureLogging(string level)
    {
        var logDirectory = Path.Combine(AppContext.BaseDirectory, "logs");
        Directory.CreateDirectory(logDirectory);

        var logLevel = Enum.TryParse<LogEventLevel>(level, true, out var parsedLevel)
            ? parsedLevel
            : LogEventLevel.Information;

        Log.Logger = new LoggerConfiguration()
            .MinimumLevel.Is(logLevel)
            .Enrich.FromLogContext()
            .WriteTo.Console()
            .WriteTo.File(
                Path.Combine(logDirectory, "app.log"),
                rollingInterval: RollingInterval.Day,
                retainedFileCountLimit: 5,
                encoding: Encoding.UTF8)
            .CreateLogger();
    }
}
