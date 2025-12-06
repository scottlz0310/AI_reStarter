use std::sync::{Arc, Mutex};
use ai_restarter::config::loader::AppConfig;
use ai_restarter::ui::setup_wizard::SetupWizard;
use ai_restarter::ui::state::UiState;

fn main() {
    tracing_subscriber::fmt::init();
    tracing::info!("Starting test_gui...");
    
    let config = Arc::new(Mutex::new(AppConfig::default()));
    let ui_state = UiState::new();

    // Call run_app on main thread
    if let Err(e) = SetupWizard::run_app(config, ui_state) {
        tracing::error!("Error: {}", e);
    }

    tracing::info!("test_gui finished.");
}
