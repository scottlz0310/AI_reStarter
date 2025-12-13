using System;
using System.Collections.Generic;

namespace AIReStarter.Config;

public enum ExecutionMode
{
    Click,
    Chat,
    Keyboard
}

public sealed record MonitorRegion
{
    public double X { get; init; }
    public double Y { get; init; }
    public double Width { get; init; }
    public double Height { get; init; }

    public bool IsValid()
    {
        return X >= 0 &&
               Y >= 0 &&
               Width > 0 &&
               Height > 0 &&
               X <= 1 &&
               Y <= 1 &&
               X + Width <= 1 &&
               Y + Height <= 1;
    }
}

public sealed record MatchingConfig
{
    public string File { get; init; } = string.Empty;
    public double Threshold { get; init; } = 0.8;
}

public abstract record ActionConfig
{
    public sealed record Click(int OffsetX, int OffsetY, int RetryCount) : ActionConfig;

    public sealed record Chat(string Command, string TargetElement) : ActionConfig;

    public sealed record Keyboard(IReadOnlyList<string> Keys) : ActionConfig;
}

public sealed record TemplateConfig
{
    public string Name { get; init; } = string.Empty;
    public string Description { get; init; } = string.Empty;
    public string? Monitor { get; init; }
    public ExecutionMode ExecutionMode { get; init; } = ExecutionMode.Click;
    public MonitorRegion MonitorRegion { get; init; } = new();
    public MatchingConfig Matching { get; init; } = new();
    public ActionConfig Action { get; init; } = new ActionConfig.Click(0, 0, 1);
}

public sealed record GlobalConfig
{
    public double CheckIntervalSeconds { get; init; } = 2.0;
    public double CooldownSeconds { get; init; } = 15.0;
    public int MaxConsecutiveMatches { get; init; } = 2;
    public int ActionDelayMilliseconds { get; init; } = 250;
    public string LogLevel { get; init; } = "Information";
}

public sealed record AppConfig
{
    public GlobalConfig Global { get; init; } = new();
    public IReadOnlyList<TemplateConfig> Templates { get; init; } = Array.Empty<TemplateConfig>();
}
