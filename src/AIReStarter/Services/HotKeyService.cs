using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Threading;
using System.Windows.Input;
using System.Windows.Interop;
using Microsoft.Extensions.Logging;

namespace AIReStarter.Services;

/// <summary>
/// RegisterHotKeyで安全停止用のホットキーを提供する。
/// </summary>
public sealed class HotKeyService : IDisposable
{
    private const int WmHotKey = 0x0312;

    private readonly ILogger<HotKeyService> _logger;
    private readonly HwndSource _hwndSource;
    private readonly Dictionary<int, Action> _handlers = new();
    private int _currentId;

    public HotKeyService(ILogger<HotKeyService> logger)
    {
        _logger = logger;

        var parameters = new HwndSourceParameters("AIReStarter.HotKeySink")
        {
            Width = 0,
            Height = 0,
            PositionX = 0,
            PositionY = 0,
            WindowStyle = unchecked((int)0x80000000) // WS_DISABLED
        };

        _hwndSource = new HwndSource(parameters);
        _hwndSource.AddHook(WndProc);
    }

    public void Register(Key key, ModifierKeys modifiers, Action handler)
    {
        var id = Interlocked.Increment(ref _currentId);
        var virtualKey = KeyInterop.VirtualKeyFromKey(key);

        if (!RegisterHotKey(_hwndSource.Handle, id, (uint)modifiers, (uint)virtualKey))
        {
            throw new InvalidOperationException($"ホットキーの登録に失敗しました: {modifiers}+{key}");
        }

        _handlers[id] = handler;
        _logger.LogInformation("ホットキーを登録しました: {Modifiers}+{Key}", modifiers, key);
    }

    private IntPtr WndProc(IntPtr hwnd, int msg, IntPtr wParam, IntPtr lParam, ref bool handled)
    {
        if (msg == WmHotKey)
        {
            var id = wParam.ToInt32();
            if (_handlers.TryGetValue(id, out var handler))
            {
                handler();
                handled = true;
            }
        }

        return IntPtr.Zero;
    }

    public void Dispose()
    {
        foreach (var handler in _handlers)
        {
            UnregisterHotKey(_hwndSource.Handle, handler.Key);
        }

        _hwndSource.RemoveHook(WndProc);
        _hwndSource.Dispose();
    }

    [DllImport("user32.dll", SetLastError = true)]
    private static extern bool RegisterHotKey(IntPtr hWnd, int id, uint fsModifiers, uint vk);

    [DllImport("user32.dll", SetLastError = true)]
    private static extern bool UnregisterHotKey(IntPtr hWnd, int id);
}
