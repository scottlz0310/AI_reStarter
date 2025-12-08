using System.IO;
using AIReStarter.Config;
using FluentAssertions;
using Xunit;

namespace AIReStarter.Tests;

public class ConfigLoaderPathTests
{
    [Fact]
    public void Load_ResolvesRelativeTemplatePath_ToAbsolute()
    {
        // Arrange
        var tempDir = Path.Combine(Path.GetTempPath(), Path.GetRandomFileName());
        Directory.CreateDirectory(Path.Combine(tempDir, "templates"));

        var configPath = Path.Combine(tempDir, "profiles.toml");
        File.WriteAllText(configPath, @"
[global]
check_interval = 1.0

[[templates]]
name = ""sample""
execution_mode = ""click""

[templates.monitor_region]
x = 0.0
y = 0.0
width = 1.0
height = 1.0

[templates.matching]
file = ""templates/run_button.png""
threshold = 0.5

[templates.action]
type = ""click""
");

        var loader = new ConfigLoader();

        // Act
        var config = loader.Load(configPath);

        // Assert
        config.Templates.Should().HaveCount(1);
        config.Templates[0].Matching.File.Should().Be(
            Path.Combine(tempDir, "templates", "run_button.png"));
    }

    [Fact]
    public void Load_ProfilesToml_ShouldSucceed()
    {
        var loader = new ConfigLoader();
        var config = loader.Load(TestPathHelper.FindRepoFile("profiles.toml"));

        config.Templates.Should().NotBeNull();
        config.Templates.Should().NotBeEmpty();
    }
}
