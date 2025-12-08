using System;
using System.Threading;
using System.Threading.Tasks;
using AIReStarter.Config;
using AIReStarter.Core;
using Microsoft.Extensions.Logging;

namespace AIReStarter.Services;

/// <summary>
/// 監視ループを管理し、テンプレート検出とアクション実行を仲介する。
/// </summary>
public sealed class MonitorService : IAsyncDisposable
{
    private readonly AppConfig _config;
    private readonly DisplayManager _displayManager;
    private readonly ScreenCaptureService _captureService;
    private readonly TemplateMatcher _matcher;
    private readonly ActionEngine _actionEngine;
    private readonly MatchGuard _guard;
    private readonly ILogger<MonitorService> _logger;

    private CancellationTokenSource? _cts;
    private Task? _worker;

    public MonitorService(
        AppConfig config,
        DisplayManager displayManager,
        ScreenCaptureService captureService,
        TemplateMatcher matcher,
        ActionEngine actionEngine,
        MatchGuard guard,
        ILogger<MonitorService> logger)
    {
        _config = config;
        _displayManager = displayManager;
        _captureService = captureService;
        _matcher = matcher;
        _actionEngine = actionEngine;
        _guard = guard;
        _logger = logger;
    }

    public bool IsRunning => _worker is not null && !_worker.IsCompleted;

    public void Start()
    {
        if (IsRunning)
        {
            return;
        }

        _cts = new CancellationTokenSource();
        _worker = Task.Run(() => RunAsync(_cts.Token));
        _logger.LogInformation("監視を開始しました。");
    }

    public async Task StopAsync()
    {
        if (_cts is null)
        {
            return;
        }

        _cts.Cancel();
        if (_worker is not null)
        {
            try
            {
                await _worker.ConfigureAwait(false);
            }
            catch (OperationCanceledException)
            {
                // expected
            }
        }

        _cts.Dispose();
        _cts = null;
        _worker = null;
        _logger.LogInformation("監視を停止しました。");
    }

    public Task ToggleAsync()
    {
        if (IsRunning)
        {
            return StopAsync();
        }

        Start();
        return Task.CompletedTask;
    }

    private async Task RunAsync(CancellationToken cancellationToken)
    {
        var cooldown = TimeSpan.FromSeconds(_config.Global.CooldownSeconds);
        var interval = TimeSpan.FromSeconds(_config.Global.CheckIntervalSeconds);

        while (!cancellationToken.IsCancellationRequested)
        {
            foreach (var template in _config.Templates)
            {
                cancellationToken.ThrowIfCancellationRequested();

                var bounds = _displayManager.GetAbsoluteRegion(template.MonitorRegion, template.Monitor);
                using var capture = _captureService.Capture(bounds);

                var result = await _matcher.FindAsync(template, capture, cancellationToken).ConfigureAwait(false);
                if (result is null)
                {
                    continue;
                }

                var now = DateTimeOffset.UtcNow;
                if (!_guard.ShouldTrigger(template.Name, cooldown, _config.Global.MaxConsecutiveMatches, now))
                {
                    _logger.LogDebug("ガードにより抑止: {Template}", template.Name);
                    continue;
                }

                _logger.LogInformation("テンプレート一致: {Template} ({Score:P2}) @ {Location}", template.Name, result.Score, result.Location);
                await _actionEngine.ExecuteAsync(template.Action, result, cancellationToken).ConfigureAwait(false);
            }

            try
            {
                await Task.Delay(interval, cancellationToken).ConfigureAwait(false);
            }
            catch (OperationCanceledException)
            {
                // 監視終了
            }
        }
    }

    public async ValueTask DisposeAsync()
    {
        await StopAsync();
    }
}
