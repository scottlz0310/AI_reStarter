using System;
using System.Drawing;
using System.Drawing.Imaging;
using DrawingPoint = System.Drawing.Point;
using OpenCvSharp;
using OpenCvSharp.Extensions;

namespace AIReStarter.Core;

public sealed record CaptureResult(Mat Frame, DrawingPoint Origin) : IDisposable
{
    public void Dispose()
    {
        Frame.Dispose();
    }
}

/// <summary>
/// DPI補正後の絶対座標を基にスクリーンキャプチャを実施する。
/// </summary>
public sealed class ScreenCaptureService
{
    public CaptureResult Capture(Rectangle bounds)
    {
        var bitmap = new Bitmap(bounds.Width, bounds.Height, PixelFormat.Format24bppRgb);

        using var graphics = Graphics.FromImage(bitmap);
        graphics.CopyFromScreen(new DrawingPoint(bounds.Left, bounds.Top), DrawingPoint.Empty, bounds.Size, CopyPixelOperation.SourceCopy);

        var mat = BitmapConverter.ToMat(bitmap);
        bitmap.Dispose();

        return new CaptureResult(mat, new DrawingPoint(bounds.Left, bounds.Top));
    }
}
