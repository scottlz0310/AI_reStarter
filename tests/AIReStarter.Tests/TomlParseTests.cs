using System.IO;
using FluentAssertions;
using Tomlyn;
using Tomlyn.Model;
using Xunit;

namespace AIReStarter.Tests;

public class TomlParseTests
{
    [Fact]
    public void ProfilesToml_ShouldContainTemplates()
    {
        var path = TestPathHelper.FindRepoFile("profiles.toml");
        var text = File.ReadAllText(path);
        var doc = Toml.Parse(text);

        doc.HasErrors.Should().BeFalse();

        var model = doc.ToModel();
        model.Should().NotBeNull().And.BeOfType<TomlTable>();

        var root = (TomlTable)model;
        root.ContainsKey("templates").Should().BeTrue();

        var templates = root["templates"] as TomlTableArray;
        templates.Should().NotBeNull();
        templates!.Count.Should().BeGreaterThan(0);
    }
}
