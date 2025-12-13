using System;
using AIReStarter.Core;
using FluentAssertions;
using Xunit;

namespace AIReStarter.Tests;

public class MatchGuardTests
{
    [Fact]
    public void ShouldTrigger_AllowsFirstMatches()
    {
        var guard = new MatchGuard();
        var now = DateTimeOffset.UtcNow;

        guard.ShouldTrigger("template", TimeSpan.FromSeconds(10), 2, now).Should().BeTrue();
        guard.ShouldTrigger("template", TimeSpan.FromSeconds(10), 2, now.AddSeconds(1)).Should().BeTrue();
    }

    [Fact]
    public void ShouldTrigger_BlocksAfterMaxConsecutive()
    {
        var guard = new MatchGuard();
        var now = DateTimeOffset.UtcNow;

        guard.ShouldTrigger("template", TimeSpan.FromSeconds(10), 2, now).Should().BeTrue();
        guard.ShouldTrigger("template", TimeSpan.FromSeconds(10), 2, now.AddSeconds(1)).Should().BeTrue();
        guard.ShouldTrigger("template", TimeSpan.FromSeconds(10), 2, now.AddSeconds(2)).Should().BeFalse();
    }

    [Fact]
    public void ShouldTrigger_AllowsAfterCooldown()
    {
        var guard = new MatchGuard();
        var now = DateTimeOffset.UtcNow;

        guard.ShouldTrigger("template", TimeSpan.FromSeconds(2), 1, now).Should().BeTrue();
        guard.ShouldTrigger("template", TimeSpan.FromSeconds(2), 1, now.AddSeconds(1)).Should().BeFalse();
        guard.ShouldTrigger("template", TimeSpan.FromSeconds(2), 1, now.AddSeconds(3)).Should().BeTrue();
    }
}
