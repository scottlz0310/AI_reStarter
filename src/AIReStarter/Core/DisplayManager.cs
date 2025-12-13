using System;
using System.Collections.Generic;
using System.Drawing;
using System.Linq;
using System.Runtime.InteropServices;
using System.Windows.Forms;
using AIReStarter.Config;
using Microsoft.Extensions.Logging;

namespace AIReStarter.Core;

public sealed record DisplayInfo(string DeviceName, Rectangle Bounds, double DpiScaleX, double DpiScaleY);

/// <summary>
/// マルチモニター情報とDPIスケーリングを管理する。
/// </summary>
public sealed class DisplayManager
{
    private readonly ILogger<DisplayManager> _logger;

    public DisplayManager(ILogger<DisplayManager> logger)
    {
        _logger = logger;
    }

    public Rectangle GetVirtualScreenBounds()
    {
        var bounds = SystemInformation.VirtualScreen;
        return Rectangle.FromLTRB(bounds.Left, bounds.Top, bounds.Right, bounds.Bottom);
    }

    public IReadOnlyList<DisplayInfo> GetMonitors()
    {
        var list = new List<DisplayInfo>();

        EnumDisplayMonitors(IntPtr.Zero, IntPtr.Zero, (IntPtr hMonitor, IntPtr hdc, ref Rect rect, IntPtr data) =>
        {
            var info = new MonitorInfoEx();
            info.cbSize = Marshal.SizeOf<MonitorInfoEx>();
            if (!GetMonitorInfo(hMonitor, ref info))
            {
                return true;
            }

            var scale = GetDpiScale(hMonitor);
            var deviceName = info.szDevice.TrimEnd('\0');
            var bounds = Rectangle.FromLTRB(rect.Left, rect.Top, rect.Right, rect.Bottom);

            list.Add(new DisplayInfo(deviceName, bounds, scale, scale));
            return true;
        }, IntPtr.Zero);

        _logger.LogInformation("検出モニター: {Monitors}", list.Select(m => $"{m.DeviceName} ({m.Bounds}) x{m.DpiScaleX:0.00}").ToArray());
        return list;
    }

    public Rectangle GetAbsoluteRegion(MonitorRegion region, string? preferredMonitor)
    {
        var target = ResolveMonitor(preferredMonitor);
        var width = Math.Max(1, (int)Math.Round(target.Width * region.Width));
        var height = Math.Max(1, (int)Math.Round(target.Height * region.Height));
        var x = target.Left + (int)Math.Round(target.Width * region.X);
        var y = target.Top + (int)Math.Round(target.Height * region.Y);

        return new Rectangle(x, y, width, height);
    }

    private Rectangle ResolveMonitor(string? preferredMonitor)
    {
        var monitors = GetMonitors();
        if (!string.IsNullOrWhiteSpace(preferredMonitor))
        {
            var match = monitors.FirstOrDefault(m => string.Equals(m.DeviceName, preferredMonitor, StringComparison.OrdinalIgnoreCase));
            if (match is not null)
            {
                return match.Bounds;
            }
        }

        return GetVirtualScreenBounds();
    }

    private static double GetDpiScale(IntPtr monitorHandle)
    {
        const uint DefaultDpi = 96;
        try
        {
            var hr = GetDpiForMonitor(monitorHandle, MonitorDpiType.EffectiveDpi, out var dpiX, out _);
            if (hr == 0)
            {
                return dpiX / DefaultDpi;
            }
        }
        catch
        {
            // ignore
        }

        using var graphics = Graphics.FromHwnd(IntPtr.Zero);
        return graphics.DpiX / DefaultDpi;
    }

    private delegate bool MonitorEnumProc(IntPtr hMonitor, IntPtr hdcMonitor, ref Rect lprcMonitor, IntPtr dwData);

    [DllImport("user32.dll")]
    private static extern bool EnumDisplayMonitors(IntPtr hdc, IntPtr lprcClip, MonitorEnumProc lpfnEnum, IntPtr dwData);

    [DllImport("user32.dll", CharSet = CharSet.Auto)]
    private static extern bool GetMonitorInfo(IntPtr hMonitor, ref MonitorInfoEx lpmi);

    [DllImport("shcore.dll")]
    private static extern int GetDpiForMonitor(IntPtr hmonitor, MonitorDpiType dpiType, out uint dpiX, out uint dpiY);
}

[StructLayout(LayoutKind.Sequential)]
internal struct Rect
{
    public int Left;
    public int Top;
    public int Right;
    public int Bottom;
}

[StructLayout(LayoutKind.Sequential, CharSet = CharSet.Auto)]
internal struct MonitorInfoEx
{
    public int cbSize;
    public Rect rcMonitor;
    public Rect rcWork;
    public uint dwFlags;

    [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)]
    public string szDevice;
}

internal enum MonitorDpiType
{
    EffectiveDpi = 0,
    AngularDpi = 1,
    RawDpi = 2,
    Default = EffectiveDpi
}
