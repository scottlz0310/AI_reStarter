using System;
using System.Drawing;
using System.Windows.Forms;
using AIReStarter.Services;
using Microsoft.Extensions.Logging;

namespace AIReStarter.UI;

/// <summary>
/// システムトレイアイコンとコンテキストメニューを管理する。
/// </summary>
public sealed class SystemTrayManager : IDisposable
{
    private readonly ILogger<SystemTrayManager> _logger;
    private readonly NotifyIcon _notifyIcon;

    public SystemTrayManager(ILogger<SystemTrayManager> logger)
    {
        _logger = logger;
        _notifyIcon = new NotifyIcon
        {
            Icon = SystemIcons.Application,
            Visible = true,
            Text = "AI reStarter v2 (C# PoC)"
        };
    }

    public void Bind(MonitorService monitorService, Action shutdown)
    {
        var menu = new ContextMenuStrip();
        menu.Items.Add("監視開始/再開", null, (_, _) => monitorService.Start());
        menu.Items.Add("一時停止", null, async (_, _) => await monitorService.StopAsync());
        menu.Items.Add("終了", null, (_, _) => shutdown());

        _notifyIcon.ContextMenuStrip = menu;
        _logger.LogInformation("システムトレイメニューを初期化しました。");
    }

    public void Dispose()
    {
        _notifyIcon.Visible = false;
        _notifyIcon.Dispose();
    }
}
