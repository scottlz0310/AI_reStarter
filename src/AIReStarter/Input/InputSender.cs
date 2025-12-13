using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.InteropServices;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;
using Microsoft.Extensions.Logging;

namespace AIReStarter.Input;

/// <summary>
/// SendInput/SetCursorPosで確実な入力を行う。
/// </summary>
public sealed class InputSender
{
    private readonly ILogger<InputSender> _logger;

    public InputSender(ILogger<InputSender> logger)
    {
        _logger = logger;
    }

    public async Task ClickAsync(int x, int y, int retryCount, int delayMilliseconds, CancellationToken cancellationToken)
    {
        for (var attempt = 1; attempt <= Math.Max(1, retryCount); attempt++)
        {
            try
            {
                if (!SetCursorPos(x, y))
                {
                    throw new InvalidOperationException("SetCursorPosに失敗しました。");
                }

                var inputs = new[]
                {
                    CreateMouseInput(MouseEventFlags.LEFTDOWN),
                    CreateMouseInput(MouseEventFlags.LEFTUP)
                };

                if (SendInput((uint)inputs.Length, inputs, Marshal.SizeOf<INPUT>()) == 0)
                {
                    throw new InvalidOperationException("SendInputに失敗しました。");
                }

                _logger.LogInformation("クリックを送出しました ({X},{Y})", x, y);
                return;
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "クリック送出に失敗しました。再試行 {Attempt}/{Retry}", attempt, retryCount);
                if (attempt == retryCount)
                {
                    throw;
                }
                await Task.Delay(delayMilliseconds, cancellationToken);
            }
        }
    }

    public async Task SendTextAsync(string text, int delayMilliseconds, CancellationToken cancellationToken)
    {
        foreach (var ch in text)
        {
            cancellationToken.ThrowIfCancellationRequested();
            if (!TryResolveVirtualKey(ch.ToString(), out var keyCode, out var modifiers))
            {
                _logger.LogWarning("未対応の文字です: {Char}", ch);
                continue;
            }

            var inputs = new List<INPUT>();
            foreach (var mod in modifiers)
            {
                inputs.Add(CreateKeyboardInput(mod, false));
            }

            inputs.Add(CreateKeyboardInput(keyCode, false));
            inputs.Add(CreateKeyboardInput(keyCode, true));

            for (var i = modifiers.Count - 1; i >= 0; i--)
            {
                inputs.Add(CreateKeyboardInput(modifiers[i], true));
            }

            if (SendInput((uint)inputs.Count, inputs.ToArray(), Marshal.SizeOf<INPUT>()) == 0)
            {
                _logger.LogWarning("文字送出に失敗しました: {Char}", ch);
            }

            await Task.Delay(delayMilliseconds, cancellationToken);
        }
    }

    public async Task SendChordAsync(IReadOnlyList<string> keys, int delayMilliseconds, CancellationToken cancellationToken)
    {
        if (keys.Count == 0)
        {
            return;
        }

        var modifiers = keys
            .Where(IsModifier)
            .Select(k => ResolveModifier(k))
            .ToList();

        var mainKeys = keys
            .Where(k => !IsModifier(k))
            .ToList();

        if (mainKeys.Count == 0 && modifiers.Count > 0)
        {
            mainKeys.Add(keys[^1]);
            modifiers.RemoveAt(modifiers.Count - 1);
        }

        foreach (var key in mainKeys)
        {
            cancellationToken.ThrowIfCancellationRequested();
            if (!TryResolveVirtualKey(key, out var vk, out var extraModifiers))
            {
                _logger.LogWarning("未対応のキーです: {Key}", key);
                continue;
            }

            var modifiersToPress = modifiers.Concat(extraModifiers).ToList();
            var inputs = new List<INPUT>();

            foreach (var mod in modifiersToPress)
            {
                inputs.Add(CreateKeyboardInput(mod, false));
            }

            inputs.Add(CreateKeyboardInput(vk, false));
            inputs.Add(CreateKeyboardInput(vk, true));

            for (var i = modifiersToPress.Count - 1; i >= 0; i--)
            {
                inputs.Add(CreateKeyboardInput(modifiersToPress[i], true));
            }

            if (SendInput((uint)inputs.Count, inputs.ToArray(), Marshal.SizeOf<INPUT>()) == 0)
            {
                _logger.LogWarning("キー送出に失敗しました: {Key}", key);
            }

            await Task.Delay(delayMilliseconds, cancellationToken);
        }
    }

    private static bool IsModifier(string key)
    {
        var lower = key.ToLowerInvariant();
        return lower is "ctrl" or "control" or "shift" or "alt" or "win" or "lwin" or "rwin";
    }

    private static ushort ResolveModifier(string key)
    {
        var lower = key.ToLowerInvariant();
        return lower switch
        {
            "ctrl" or "control" => (ushort)Keys.ControlKey,
            "shift" => (ushort)Keys.ShiftKey,
            "alt" => (ushort)Keys.Menu,
            _ => (ushort)Keys.LWin
        };
    }

    private static bool TryResolveVirtualKey(string key, out ushort code, out List<ushort> modifiers)
    {
        modifiers = new List<ushort>();

        if (key.Length == 1)
        {
            var vk = VkKeyScan(key[0]);
            if (vk != -1)
            {
                var modFlags = (vk >> 8) & 0xFF;
                if ((modFlags & 1) != 0)
                {
                    modifiers.Add((ushort)Keys.ShiftKey);
                }
                if ((modFlags & 2) != 0)
                {
                    modifiers.Add((ushort)Keys.ControlKey);
                }
                if ((modFlags & 4) != 0)
                {
                    modifiers.Add((ushort)Keys.Menu);
                }

                code = (ushort)(vk & 0xFF);
                return true;
            }
        }

        if (Enum.TryParse<Keys>(key, true, out var parsed))
        {
            code = (ushort)parsed;
            return true;
        }

        switch (key.ToLowerInvariant())
        {
            case "enter":
                code = (ushort)Keys.Return;
                return true;
            case "esc":
            case "escape":
                code = (ushort)Keys.Escape;
                return true;
            case "space":
                code = (ushort)Keys.Space;
                return true;
            default:
                code = 0;
                return false;
        }
    }

    private static INPUT CreateMouseInput(MouseEventFlags flags)
    {
        return new INPUT
        {
            type = InputType.INPUT_MOUSE,
            U = new InputUnion
            {
                mi = new MOUSEINPUT
                {
                    dwFlags = flags,
                    dwExtraInfo = GetMessageExtraInfo()
                }
            }
        };
    }

    private static INPUT CreateKeyboardInput(ushort keyCode, bool keyUp)
    {
        return new INPUT
        {
            type = InputType.INPUT_KEYBOARD,
            U = new InputUnion
            {
                ki = new KEYBDINPUT
                {
                    wVk = keyCode,
                    dwFlags = keyUp ? KeyboardEventFlags.KEYEVENTF_KEYUP : KeyboardEventFlags.KEYEVENTF_KEYDOWN,
                    dwExtraInfo = GetMessageExtraInfo()
                }
            }
        };
    }

    [DllImport("user32.dll")]
    private static extern bool SetCursorPos(int x, int y);

    [DllImport("user32.dll")]
    private static extern uint SendInput(uint nInputs, INPUT[] pInputs, int cbSize);

    [DllImport("user32.dll")]
    private static extern IntPtr GetMessageExtraInfo();

    [DllImport("user32.dll")]
    private static extern short VkKeyScan(char ch);
}

[StructLayout(LayoutKind.Sequential)]
internal struct INPUT
{
    public InputType type;
    public InputUnion U;
}

[StructLayout(LayoutKind.Explicit)]
internal struct InputUnion
{
    [FieldOffset(0)] public MOUSEINPUT mi;
    [FieldOffset(0)] public KEYBDINPUT ki;
}

[StructLayout(LayoutKind.Sequential)]
internal struct MOUSEINPUT
{
    public int dx;
    public int dy;
    public uint mouseData;
    public MouseEventFlags dwFlags;
    public uint time;
    public IntPtr dwExtraInfo;
}

[StructLayout(LayoutKind.Sequential)]
internal struct KEYBDINPUT
{
    public ushort wVk;
    public ushort wScan;
    public KeyboardEventFlags dwFlags;
    public uint time;
    public IntPtr dwExtraInfo;
}

internal enum InputType : uint
{
    INPUT_MOUSE = 0,
    INPUT_KEYBOARD = 1
}

[Flags]
internal enum MouseEventFlags : uint
{
    MOVE = 0x0001,
    LEFTDOWN = 0x0002,
    LEFTUP = 0x0004,
    RIGHTDOWN = 0x0008,
    RIGHTUP = 0x0010,
    MIDDLEDOWN = 0x0020,
    MIDDLEUP = 0x0040,
    ABSOLUTE = 0x8000
}

[Flags]
internal enum KeyboardEventFlags : uint
{
    KEYEVENTF_KEYDOWN = 0x0000,
    KEYEVENTF_KEYUP = 0x0002
}
