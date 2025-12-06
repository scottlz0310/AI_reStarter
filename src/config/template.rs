use serde::{Deserialize, Serialize};
use crate::core::execution_mode::ExecutionMode;
use crate::core::action::Action;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Template {
    pub name: String,
    pub description: String,
    pub execution_mode: ExecutionMode,
    pub monitor_region: MonitorRegion,
    pub matching: MatchingConfig,
    pub action: Action,
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize)]
pub struct MonitorRegion {
    pub x: f32,
    pub y: f32,
    pub width: f32,
    pub height: f32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MatchingConfig {
    pub file: String,
    pub threshold: f32,
}
