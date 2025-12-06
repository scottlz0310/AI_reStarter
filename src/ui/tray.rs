use tray_item::TrayItem;
use crate::error::Result;
use crate::core::execution_mode::ExecutionMode;
use std::sync::{Arc, Mutex};

pub struct SystemTray {
    tray: TrayItem,
    current_mode: Arc<Mutex<ExecutionMode>>,
}

use crate::config::loader::AppConfig;
use crate::ui::state::UiState;

impl SystemTray {
    pub fn new(config: Arc<Mutex<AppConfig>>, ui_state: UiState) -> Result<Self> {
        let mut tray = TrayItem::new("AI reStarter", tray_item::IconSource::Resource("app-icon"))?;
        let current_mode = Arc::new(Mutex::new(ExecutionMode::default()));

        tray.add_label("AI reStarter Status")?;
        
        // We do not need config in the callback anymore if we just toggle state
        // But we might need it for other things later.
        let _config_clone = config.clone(); 
        
        let ui_state_clone = ui_state.clone();
        tray.add_menu_item("Start Monitoring", move || {
             if let Ok(mut is_running) = ui_state_clone.is_monitoring.lock() {
                 *is_running = true;
                 tracing::info!("Monitoring STARTED.");
             }
        })?;

        let ui_state_clone = ui_state.clone();
        tray.add_menu_item("Stop Monitoring", move || {
             if let Ok(mut is_running) = ui_state_clone.is_monitoring.lock() {
                 *is_running = false;
                 tracing::info!("Monitoring STOPPED.");
             }
        })?;

        tray.add_label("----------------")?;

        let ui_state_clone = ui_state.clone();
        tray.add_menu_item("Settings...", move || {
            if let Ok(mut is_open) = ui_state_clone.is_open.lock() {
                *is_open = true;
                tracing::info!("Settings requested via Tray. is_open set to true.");
            }
        })?;

        tray.add_menu_item("Mode: Click", || {
            println!("Switch to Click Mode");
        })?;

        tray.add_menu_item("Mode: Chat", || {
            println!("Switch to Chat Mode");
        })?;

        tray.add_menu_item("Mode: Keyboard", || {
            println!("Switch to Keyboard Mode");
        })?;

        tray.add_menu_item("Quit", || {
            std::process::exit(0);
        })?;

        Ok(Self { tray, current_mode })
    }
}
