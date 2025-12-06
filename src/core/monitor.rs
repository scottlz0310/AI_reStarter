use image::DynamicImage;
use imageproc::template_matching::match_template;
use imageproc::template_matching::MatchTemplateMethod;
use crate::error::Result;
use windows::Win32::Graphics::Gdi::{
    BitBlt, CreateCompatibleBitmap, CreateCompatibleDC, DeleteDC, DeleteObject, GetDC, GetDIBits,
    ReleaseDC, SelectObject, BITMAPINFO, BITMAPINFOHEADER, BI_RGB, DIB_RGB_COLORS, SRCCOPY,
};
use windows::Win32::UI::WindowsAndMessaging::GetDesktopWindow;
use std::ffi::c_void;

pub struct MonitorEngine;

impl MonitorEngine {
    pub fn new() -> Self {
        Self
    }

    pub fn capture_screen(&self) -> Result<DynamicImage> {
        unsafe {
            let hwnd = GetDesktopWindow();
            let hdc_screen = GetDC(Some(hwnd));
            let hdc_mem = CreateCompatibleDC(Some(hdc_screen));

            let (width, height) = crate::core::display::DisplayManager::get_screen_size();
            
            let hbitmap = CreateCompatibleBitmap(hdc_screen, width, height);
            let old_obj = SelectObject(hdc_mem, hbitmap.into());

            BitBlt(hdc_mem, 0, 0, width, height, Some(hdc_screen), 0, 0, SRCCOPY)?;

            let mut bi = BITMAPINFO {
                bmiHeader: BITMAPINFOHEADER {
                    biSize: std::mem::size_of::<BITMAPINFOHEADER>() as u32,
                    biWidth: width,
                    biHeight: -height, // Top-down
                    biPlanes: 1,
                    biBitCount: 32,
                    biCompression: BI_RGB.0,
                    ..Default::default()
                },
                ..Default::default()
            };

            let mut pixels = vec![0u8; (width * height * 4) as usize];
            
            GetDIBits(
                hdc_mem,
                hbitmap,
                0,
                height as u32,
                Some(pixels.as_mut_ptr() as *mut c_void),
                &mut bi,
                DIB_RGB_COLORS,
            );

            SelectObject(hdc_mem, old_obj);
            DeleteObject(hbitmap.into());
            DeleteDC(hdc_mem);
            ReleaseDC(Some(hwnd), hdc_screen);

            // Convert BGRA to RGBA
            for chunk in pixels.chunks_exact_mut(4) {
                let b = chunk[0];
                let r = chunk[2];
                chunk[0] = r;
                chunk[2] = b;
                // chunk[3] is alpha, usually 255 or 0 depending on GDI, force 255?
                chunk[3] = 255;
            }

            Ok(DynamicImage::ImageRgba8(
                image::RgbaImage::from_raw(width as u32, height as u32, pixels)
                    .ok_or_else(|| crate::error::AppError::Unknown("Failed to create image buffer".to_string()))?
            ))
        }
    }

    pub fn find_template(
        &self,
        screen: &DynamicImage,
        template: &DynamicImage,
        threshold: f32,
    ) -> Option<(u32, u32)> {
        let screen_luma = screen.to_luma8();
        let template_luma = template.to_luma8();

        let result = match_template(
            &screen_luma,
            &template_luma,
            MatchTemplateMethod::CrossCorrelationNormalized,
        );

        // Find the maximum value and location
        let mut max_val = -1.0;
        let mut max_loc = (0, 0);

        for (x, y, pixel) in result.enumerate_pixels() {
            let val = pixel[0];
            if val > max_val {
                max_val = val;
                max_loc = (x, y);
            }
        }

        tracing::debug!("Max match value: {}, at {:?}", max_val, max_loc);

        if max_val >= threshold {
            Some(max_loc)
        } else {
            None
        }
    }
}
