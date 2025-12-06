use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum ExecutionMode {
    Click,
    Chat,
    Keyboard,
}

impl Default for ExecutionMode {
    fn default() -> Self {
        Self::Click
    }
}
