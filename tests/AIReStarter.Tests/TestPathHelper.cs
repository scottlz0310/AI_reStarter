using System;
using System.IO;

namespace AIReStarter.Tests;

internal static class TestPathHelper
{
    public static string FindRepoFile(string fileName)
    {
        var dir = Directory.GetCurrentDirectory();

        for (var i = 0; i < 8 && dir is not null; i++)
        {
            var candidate = Path.Combine(dir, fileName);
            if (File.Exists(candidate))
            {
                return candidate;
            }

            dir = Directory.GetParent(dir)?.FullName;
        }

        throw new FileNotFoundException($"テスト用のファイルが見つかりません: {fileName}");
    }
}
