use std::sync::{Arc, Mutex};

#[derive(Clone)]
pub struct UiState {
    pub is_open: Arc<Mutex<bool>>,
    pub is_monitoring: Arc<Mutex<bool>>,
}

impl UiState {
    pub fn new() -> Self {
        Self {
            is_open: Arc::new(Mutex::new(false)),
            is_monitoring: Arc::new(Mutex::new(false)), // Default to stopped
        }
    }
}
