using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Tomlyn;
using Tomlyn.Model;

namespace AIReStarter.Config;

public sealed class ConfigLoader
{
    public AppConfig Load(string path)
    {
        if (!File.Exists(path))
        {
            throw new ConfigLoadException($"ファイルが見つかりません: {path}");
        }

        var baseDirectory = Path.GetDirectoryName(Path.GetFullPath(path)) ?? Directory.GetCurrentDirectory();
        var text = File.ReadAllText(path);
        var parse = Toml.Parse(text);

        if (parse.HasErrors)
        {
            var details = string.Join("; ", parse.Diagnostics.Select(d => d.ToString()));
            throw new ConfigLoadException($"TOML解析エラー: {details}");
        }

        if (parse.ToModel() is not TomlTable root)
        {
            throw new ConfigLoadException("TOMLの形式が不正です。");
        }

        var global = ParseGlobal(root.TryGetValue("global", out var globalNode) ? globalNode as TomlTable : null);
        var templates = ParseTemplates(
            root.TryGetValue("templates", out var templatesNode) ? templatesNode as TomlArray : null,
            baseDirectory);

        if (templates.Count == 0)
        {
            throw new ConfigLoadException("テンプレートを最低1件定義してください。");
        }

        return new AppConfig
        {
            Global = global,
            Templates = templates
        };
    }

    private static GlobalConfig ParseGlobal(TomlTable? table)
    {
        if (table is null)
        {
            return new GlobalConfig();
        }

        return new GlobalConfig
        {
            CheckIntervalSeconds = GetDouble(table, "check_interval", 2.0),
            CooldownSeconds = GetDouble(table, "cooldown_seconds", 15.0),
            MaxConsecutiveMatches = GetInt(table, "max_consecutive_matches", 2),
            ActionDelayMilliseconds = GetInt(table, "action_delay_ms", 250),
            LogLevel = GetString(table, "log_level", "Information")
        };
    }

    private static List<TemplateConfig> ParseTemplates(TomlArray? array, string baseDirectory)
    {
        var templates = new List<TemplateConfig>();
        if (array is null)
        {
            return templates;
        }

        foreach (var item in array)
        {
            if (item is not TomlTable table)
            {
                continue;
            }

            var name = GetString(table, "name", "unnamed");
            var region = ParseRegion(table.TryGetValue("monitor_region", out var regionNode) ? regionNode as TomlTable : null);
            if (!region.IsValid())
            {
                throw new ConfigLoadException($"テンプレート '{name}' のmonitor_regionが0.0-1.0の範囲外です。");
            }

            var matching = ParseMatching(
                table.TryGetValue("matching", out var matchingNode) ? matchingNode as TomlTable : null,
                baseDirectory);
            var action = ParseAction(table.TryGetValue("action", out var actionNode) ? actionNode as TomlTable : null, name);

            templates.Add(new TemplateConfig
            {
                Name = name,
                Description = GetString(table, "description", string.Empty),
                Monitor = GetString(table, "monitor", null),
                ExecutionMode = ParseExecutionMode(GetString(table, "execution_mode", "click")),
                MonitorRegion = region,
                Matching = matching,
                Action = action
            });
        }

        return templates;
    }

    private static MatchingConfig ParseMatching(TomlTable? table, string baseDirectory)
    {
        if (table is null)
        {
            return new MatchingConfig();
        }

        var path = GetString(table, "file", string.Empty);
        var resolvedPath = Path.IsPathRooted(path)
            ? path
            : Path.GetFullPath(Path.Combine(baseDirectory, path));

        return new MatchingConfig
        {
            File = resolvedPath,
            Threshold = GetDouble(table, "threshold", 0.8)
        };
    }

    private static MonitorRegion ParseRegion(TomlTable? table)
    {
        if (table is null)
        {
            return new MonitorRegion { X = 0, Y = 0, Width = 1, Height = 1 };
        }

        return new MonitorRegion
        {
            X = GetDouble(table, "x", 0),
            Y = GetDouble(table, "y", 0),
            Width = GetDouble(table, "width", 1),
            Height = GetDouble(table, "height", 1)
        };
    }

    private static ActionConfig ParseAction(TomlTable? table, string templateName)
    {
        if (table is null)
        {
            return new ActionConfig.Click(0, 0, 1);
        }

        var type = GetString(table, "type", "click").ToLowerInvariant();
        switch (type)
        {
            case "click":
                var (offsetX, offsetY) = ReadOffset(table);
                return new ActionConfig.Click(
                    offsetX,
                    offsetY,
                    GetInt(table, "retry_count", 3));

            case "chat":
                return new ActionConfig.Chat(
                    GetString(table, "command", string.Empty),
                    GetString(table, "target_element", string.Empty));

            case "keyboard":
                return new ActionConfig.Keyboard(
                    GetStringArray(table, "keys"));

            default:
                throw new ConfigLoadException($"テンプレート '{templateName}' のaction.type='{type}' は未対応です。");
        }
    }

    private static ExecutionMode ParseExecutionMode(string value)
    {
        return value.ToLowerInvariant() switch
        {
            "click" => ExecutionMode.Click,
            "chat" => ExecutionMode.Chat,
            "keyboard" => ExecutionMode.Keyboard,
            _ => ExecutionMode.Click
        };
    }

    private static (int X, int Y) ReadOffset(TomlTable table)
    {
        if (table.TryGetValue("offset", out var offsetNode) && offsetNode is TomlArray offsetArray && offsetArray.Count == 2)
        {
            return (
                Convert.ToInt32(offsetArray[0]),
                Convert.ToInt32(offsetArray[1]));
        }

        return (
            GetInt(table, "offset_x", 0),
            GetInt(table, "offset_y", 0));
    }

    private static string GetString(TomlTable table, string key, string? defaultValue)
    {
        return table.TryGetValue(key, out var value) && value is string str
            ? str
            : defaultValue ?? string.Empty;
    }

    private static double GetDouble(TomlTable table, string key, double defaultValue)
    {
        if (!table.TryGetValue(key, out var value))
        {
            return defaultValue;
        }

        return value switch
        {
            double d => d,
            long l => l,
            int i => i,
            _ => defaultValue
        };
    }

    private static int GetInt(TomlTable table, string key, int defaultValue)
    {
        if (!table.TryGetValue(key, out var value))
        {
            return defaultValue;
        }

        return value switch
        {
            long l => (int)l,
            int i => i,
            double d => (int)d,
            _ => defaultValue
        };
    }

    private static IReadOnlyList<string> GetStringArray(TomlTable table, string key)
    {
        if (table.TryGetValue(key, out var value) && value is TomlArray array)
        {
            return array.OfType<string>().ToArray();
        }

        return Array.Empty<string>();
    }
}

public sealed class ConfigLoadException : Exception
{
    public ConfigLoadException(string message) : base(message)
    {
    }
}
