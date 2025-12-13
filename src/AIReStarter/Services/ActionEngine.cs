using System.Drawing;
using System.Threading;
using System.Threading.Tasks;
using AIReStarter.Config;
using AIReStarter.Core;
using AIReStarter.Input;
using Microsoft.Extensions.Logging;

namespace AIReStarter.Services;

/// <summary>
/// マッチ結果に応じてクリック/キーボード入力を実行する。
/// </summary>
public sealed class ActionEngine
{
    private readonly AppConfig _config;
    private readonly InputSender _inputSender;
    private readonly ILogger<ActionEngine> _logger;

    public ActionEngine(AppConfig config, InputSender inputSender, ILogger<ActionEngine> logger)
    {
        _config = config;
        _inputSender = inputSender;
        _logger = logger;
    }

    public Task ExecuteAsync(ActionConfig action, MatchResult match, CancellationToken cancellationToken)
    {
        return action switch
        {
            ActionConfig.Click click => ExecuteClickAsync(click, match.Location, cancellationToken),
            ActionConfig.Chat chat => ExecuteChatAsync(chat, cancellationToken),
            ActionConfig.Keyboard keyboard => ExecuteKeyboardAsync(keyboard, cancellationToken),
            _ => Task.CompletedTask
        };
    }

    private async Task ExecuteClickAsync(ActionConfig.Click click, Point location, CancellationToken cancellationToken)
    {
        var targetX = location.X + click.OffsetX;
        var targetY = location.Y + click.OffsetY;

        _logger.LogInformation("クリック実行: ({X},{Y})", targetX, targetY);
        await _inputSender.ClickAsync(
            targetX,
            targetY,
            click.RetryCount,
            _config.Global.ActionDelayMilliseconds,
            cancellationToken);
    }

    private async Task ExecuteChatAsync(ActionConfig.Chat chat, CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(chat.Command))
        {
            _logger.LogWarning("チャットコマンドが空のため送信をスキップします。");
            return;
        }

        _logger.LogInformation("チャット送信: {Command}", chat.Command);
        await _inputSender.SendTextAsync(chat.Command, _config.Global.ActionDelayMilliseconds, cancellationToken);
        await _inputSender.SendChordAsync(new[] { "Enter" }, _config.Global.ActionDelayMilliseconds, cancellationToken);
    }

    private Task ExecuteKeyboardAsync(ActionConfig.Keyboard keyboard, CancellationToken cancellationToken)
    {
        _logger.LogInformation("キーボード入力: {Keys}", string.Join("+", keyboard.Keys));
        return _inputSender.SendChordAsync(keyboard.Keys, _config.Global.ActionDelayMilliseconds, cancellationToken);
    }
}
