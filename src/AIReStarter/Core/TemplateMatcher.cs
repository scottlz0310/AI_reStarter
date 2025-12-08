using System.IO;
using System.Threading;
using System.Threading.Tasks;
using AIReStarter.Config;
using Microsoft.Extensions.Logging;
using OpenCvSharp;
using DrawingPoint = System.Drawing.Point;
using CvPoint = OpenCvSharp.Point;

namespace AIReStarter.Core;

public sealed record MatchResult(DrawingPoint Location, double Score);

/// <summary>
/// OpenCVによるテンプレートマッチングを行う。
/// </summary>
public sealed class TemplateMatcher
{
    private readonly ILogger<TemplateMatcher> _logger;

    public TemplateMatcher(ILogger<TemplateMatcher> logger)
    {
        _logger = logger;
    }

    public async Task<MatchResult?> FindAsync(TemplateConfig template, CaptureResult capture, CancellationToken cancellationToken)
    {
        if (!File.Exists(template.Matching.File))
        {
            _logger.LogWarning("テンプレート画像が見つかりません: {File}", template.Matching.File);
            return null;
        }

        return await Task.Run(() =>
        {
            using var templateImage = Cv2.ImRead(template.Matching.File, ImreadModes.Color);
            if (templateImage.Empty())
            {
                _logger.LogWarning("テンプレート画像の読み込みに失敗しました: {File}", template.Matching.File);
                return null;
            }

            if (templateImage.Width > capture.Frame.Width || templateImage.Height > capture.Frame.Height)
            {
                _logger.LogWarning(
                    "テンプレートサイズがキャプチャ領域より大きいためスキップします: {TemplateSize} vs {CaptureSize}",
                    $"{templateImage.Width}x{templateImage.Height}",
                    $"{capture.Frame.Width}x{capture.Frame.Height}");
                return null;
            }

            using var result = new Mat();
            Cv2.MatchTemplate(capture.Frame, templateImage, result, TemplateMatchModes.CCoeffNormed);
            Cv2.MinMaxLoc(result, out _, out var maxVal, out _, out CvPoint maxLoc);

            if (maxVal < template.Matching.Threshold)
            {
                return null;
            }

            var absolute = new DrawingPoint(capture.Origin.X + maxLoc.X, capture.Origin.Y + maxLoc.Y);
            return new MatchResult(absolute, maxVal);
        }, cancellationToken);
    }
}
