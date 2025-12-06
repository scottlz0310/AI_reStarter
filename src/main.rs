use ai_restarter::core;
use ai_restarter::ui;
use ai_restarter::config;

use tracing::{info, Level};
use tracing_subscriber::FmtSubscriber;
use std::sync::{Arc, Mutex};
use crate::config::loader::ConfigLoader;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // Initialize logging
    let subscriber = FmtSubscriber::builder()
        .with_max_level(Level::DEBUG)
        .finish();
    tracing::subscriber::set_global_default(subscriber)
        .expect("setting default subscriber failed");

    info!("AI reStarter v2.0.0 starting...");

    // Load Configuration
    let config = ConfigLoader::load("config.toml")?;
    let global_config = Arc::new(Mutex::new(config));

    // Initialize UI State
    let ui_state = ui::state::UiState::new();

    // Initialize System Tray
    // Tray needs to be valid as long as the app runs.
    let _tray = ui::tray::SystemTray::new(global_config.clone(), ui_state.clone())?;

    // Initialize Engines
    let monitor_engine = Arc::new(core::monitor::MonitorEngine::new());
    let _action_engine = Arc::new(Mutex::new(core::action::ActionEngine::new())); // Wrap in mutex/arc if needed shared

    // Spawn Monitoring Loop
    let config_for_loop = global_config.clone();
    let monitor_engine = monitor_engine.clone();
    let ui_state_for_loop = ui_state.clone();
    
    tokio::spawn(async move {
        loop {
            let is_running = if let Ok(state) = ui_state_for_loop.is_monitoring.lock() {
                *state
            } else {
                false
            };

            if is_running {
                // tracing::debug!("Starting monitoring cycle...");
                
                // Capture screen
                match monitor_engine.capture_screen() {
                    Ok(screen) => {
                    // Get active templates from config
                    let templates = {
                         // Careful with locking potential deadlocks if UI holds it long, but should be fine.
                        let config = config_for_loop.lock().unwrap();
                        config.templates.clone()
                    };

                    for template in templates {
                         // Load template image (TODO: Cache)
                         if std::path::Path::new(&template.matching.file).exists() {
                             match image::open(&template.matching.file) {
                                Ok(tmpl_img) => {
                                    if let Some(pos) = monitor_engine.find_template(&screen, &tmpl_img, template.matching.threshold) {
                                        tracing::info!("Template '{}' found at: {:?}", template.name, pos);
                                    }
                                },
                                Err(e) => tracing::error!("Failed to load template image {}: {}", template.matching.file, e),
                             }
                        }
                    }
                }
                Err(e) => {
                    tracing::error!("Failed to capture screen: {}", e);
                }
            }
            } // End is_running check

            // Sleep to prevent high CPU usage
            tokio::time::sleep(tokio::time::Duration::from_millis(500)).await;
        }
    });

    // Run UI on main thread
    if let Err(e) = ui::setup_wizard::SetupWizard::run_app(global_config, ui_state) {
        tracing::error!("Application crashed: {}", e);
    }

    Ok(())
}
