use crate::config::template::Template;
use crate::error::Result;
use serde::{Deserialize, Serialize};
use std::fs;

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct AppConfig {
    pub templates: Vec<Template>,
}

pub struct ConfigLoader;

impl ConfigLoader {
    pub fn load(path: &str) -> Result<AppConfig> {
        if !std::path::Path::new(path).exists() {
            return Ok(AppConfig::default());
        }
        let content = fs::read_to_string(path)?;
        let config: AppConfig = toml::from_str(&content)?;
        Ok(config)
    }

    pub fn save(path: &str, config: &AppConfig) -> Result<()> {
        let content = toml::to_string_pretty(config)?;
        fs::write(path, content)?;
        Ok(())
    }
}
