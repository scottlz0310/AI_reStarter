use thiserror::Error;

#[derive(Error, Debug)]
pub enum AppError {
    #[error("Configuration error: {0}")]
    Config(#[from] toml::de::Error),

    #[error("TOML Serialization Error: {0}")]
    TomlSer(#[from] toml::ser::Error),

    #[error("Image processing error: {0}")]
    Image(#[from] image::ImageError),

    #[error("Windows API error: {0}")]
    Windows(#[from] windows::core::Error),

    #[error("IO error: {0}")]
    Io(#[from] std::io::Error),

    #[error("Tray error: {0}")]
    Tray(#[from] tray_item::TIError),

    #[error("Unknown error: {0}")]
    Unknown(String),
}

pub type Result<T> = std::result::Result<T, AppError>;
