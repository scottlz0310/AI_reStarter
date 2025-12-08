using System.ComponentModel;
using System.Collections.ObjectModel;
using System.Windows;
using AIReStarter.Core;
using AIReStarter.Services;

namespace AIReStarter;

public partial class MainWindow : Window
{
    private readonly MonitorService _monitorService;
    private readonly DisplayManager _displayManager;
    private bool _allowClose;

    public ObservableCollection<string> Monitors { get; } = new();

    public MainWindow(MonitorService monitorService, DisplayManager displayManager)
    {
        InitializeComponent();
        _monitorService = monitorService;
        _displayManager = displayManager;

        DataContext = this;
        RefreshMonitors();
        UpdateStatus();
    }

    protected override void OnClosing(CancelEventArgs e)
    {
        if (!_allowClose)
        {
            e.Cancel = true;
            Hide();
            return;
        }

        base.OnClosing(e);
    }

    private void RefreshMonitors()
    {
        Monitors.Clear();
        foreach (var display in _displayManager.GetMonitors())
        {
            Monitors.Add($"{display.DeviceName} | {display.Bounds.Left},{display.Bounds.Top} {display.Bounds.Width}x{display.Bounds.Height} | DPI x{display.DpiScaleX:0.00}");
        }

        var virtualScreen = _displayManager.GetVirtualScreenBounds();
        Monitors.Add($"Virtual: {virtualScreen.Left},{virtualScreen.Top} {virtualScreen.Width}x{virtualScreen.Height}");
    }

    private void UpdateStatus()
    {
        StatusText.Text = _monitorService.IsRunning ? "状態: 監視中" : "状態: 停止中";
    }

    private void OnStartClicked(object sender, RoutedEventArgs e)
    {
        _monitorService.Start();
        UpdateStatus();
    }

    private async void OnPauseClicked(object sender, RoutedEventArgs e)
    {
        await _monitorService.StopAsync();
        UpdateStatus();
    }

    public void ShowFromTray()
    {
        if (Visibility != Visibility.Visible)
        {
            Show();
        }

        if (WindowState == WindowState.Minimized)
        {
            WindowState = WindowState.Normal;
        }

        Activate();
        Focus();
        UpdateStatus();
    }

    public void AllowClose()
    {
        _allowClose = true;
    }
}
