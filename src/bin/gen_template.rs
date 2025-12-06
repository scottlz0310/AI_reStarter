use image::{RgbaImage, Rgba};

fn main() {
    let mut img = RgbaImage::new(50, 50);
    for pixel in img.pixels_mut() {
        *pixel = Rgba([255, 0, 0, 255]); // Red square
    }
    img.save("template.png").expect("Failed to save template.png");
}
