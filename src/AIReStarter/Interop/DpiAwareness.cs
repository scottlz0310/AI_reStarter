using System;
using System.Runtime.InteropServices;

namespace AIReStarter.Interop;

internal static class DpiAwareness
{
    private static readonly IntPtr PerMonitorV2Context = new(-4); // DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2

    public static void EnsurePerMonitorV2()
    {
        try
        {
            if (!SetProcessDpiAwarenessContext(PerMonitorV2Context))
            {
                // Windows 8.1 fallback
                SetProcessDpiAwareness(ProcessDpiAwareness.ProcessPerMonitorDpiAware);
            }
        }
        catch
        {
            // Windows 7 fallback
            SetProcessDPIAware();
        }
    }

    [DllImport("user32.dll")]
    private static extern bool SetProcessDpiAwarenessContext(IntPtr value);

    [DllImport("shcore.dll")]
    private static extern int SetProcessDpiAwareness(ProcessDpiAwareness value);

    [DllImport("user32.dll")]
    private static extern bool SetProcessDPIAware();
}

internal enum ProcessDpiAwareness
{
    ProcessDpiUnaware = 0,
    ProcessSystemDpiAware = 1,
    ProcessPerMonitorDpiAware = 2
}
