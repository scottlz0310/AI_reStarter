using System;
using System.Collections.Concurrent;

namespace AIReStarter.Core;

/// <summary>
/// 連続一致数とクールダウンを管理する。
/// </summary>
public sealed class MatchGuard
{
    private readonly ConcurrentDictionary<string, MatchState> _states = new();

    public bool ShouldTrigger(string key, TimeSpan cooldown, int maxConsecutive, DateTimeOffset now)
    {
        var state = _states.GetOrAdd(key, _ => new MatchState());

        if (state.CooldownUntil.HasValue && now < state.CooldownUntil.Value)
        {
            return false;
        }

        if (state.LastMatch.HasValue && now - state.LastMatch.Value > cooldown)
        {
            state.Consecutive = 0;
        }

        state.Consecutive++;
        state.LastMatch = now;

        if (state.Consecutive > maxConsecutive)
        {
            state.Consecutive = 0;
            state.CooldownUntil = now + cooldown;
            return false;
        }

        state.CooldownUntil = null;
        return true;
    }

    private sealed class MatchState
    {
        public int Consecutive { get; set; }
        public DateTimeOffset? LastMatch { get; set; }
        public DateTimeOffset? CooldownUntil { get; set; }
    }
}
