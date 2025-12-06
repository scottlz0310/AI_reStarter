use eframe::egui;
use crate::config::template::Template;
use crate::config::loader::AppConfig;
use std::sync::{Arc, Mutex};
use crate::ui::state::UiState;

pub struct SetupWizard {
    config: Arc<Mutex<AppConfig>>,
    ui_state: UiState,
    new_template_name: String,
}

impl SetupWizard {
    pub fn new(_cc: &eframe::CreationContext<'_>, config: Arc<Mutex<AppConfig>>, ui_state: UiState) -> Self {
        Self {
            config,
            ui_state,
            new_template_name: String::new(),
        }
    }

    pub fn run_app(config: Arc<Mutex<AppConfig>>, ui_state: UiState) -> eframe::Result<()> {
        tracing::info!("Starting UI App...");
        let options = eframe::NativeOptions {
             // We can start hidden or just control visibility in update.
             // But eframe always shows a window initially unless configured.
             // We'll rely on update logic to close/hide or show.
             // Actually, if we start main thread with eframe, we want the window.
             // We'll treat this window as the "Settings" window. 
             // If we close it, it hides.
             ..Default::default()
        };
        
        eframe::run_native(
            "AI reStarter Setup",
            options,
            Box::new(move |cc| Ok(Box::new(SetupWizard::new(cc, config, ui_state)))),
        )
    }
}

impl eframe::App for SetupWizard {
    fn update(&mut self, ctx: &egui::Context, frame: &mut eframe::Frame) {
        let mut is_open = false;
        if let Ok(state) = self.ui_state.is_open.lock() {
            is_open = *state;
        }

        if !is_open {
             // If not open, we should hide the window.
             // eframe doesn't strictly support "hiding" the main window easily without closing the context.
             // BUT, we can use `ctx.send_viewport_cmd(egui::ViewportCommand::Visible(false))`
             ctx.send_viewport_cmd(egui::ViewportCommand::Visible(false));
             
             // Sleep a bit to avoid busy loop if eframe keeps polling
             std::thread::sleep(std::time::Duration::from_millis(100));
             return;
        } else {
             ctx.send_viewport_cmd(egui::ViewportCommand::Visible(true));
             // Also need to bring to front if just opened?
        }

        // Handle window close event manually
        // eframe's Window doesn't give us "X" callback directly for the root viewport unless we inspect viewport events.
        // But run_native's default viewport IS the window.
        if ctx.input(|i| i.viewport().close_requested()) {
             // Cancel close and hide instead
             ctx.send_viewport_cmd(egui::ViewportCommand::CancelClose);
             if let Ok(mut state) = self.ui_state.is_open.lock() {
                 *state = false;
             }
             return;
        }

        egui::CentralPanel::default().show(ctx, |ui| {
            ui.heading("AI reStarter Setup");
            
            ui.separator();

            ui.heading("Templates");
            
            // Lock config to access templates
            if let Ok(config) = self.config.lock() {
                for template in &config.templates {
                    ui.label(format!("Name: {}", template.name));
                    // TODO: Edit buttons
                }
            }

            ui.separator();
            ui.horizontal(|ui| {
                ui.label("New Template:");
                ui.text_edit_singleline(&mut self.new_template_name);
                if ui.button("Add").clicked() {
                     if !self.new_template_name.is_empty() {
                        if let Ok(mut config) = self.config.lock() {
                            let new_template = Template {
                                name: self.new_template_name.clone(),
                                description: "Created via Wizard".to_string(),
                                execution_mode: crate::core::execution_mode::ExecutionMode::Click,
                                monitor_region: crate::config::template::MonitorRegion { x: 0.0, y: 0.0, width: 1920.0, height: 1080.0 }, // Default full screen
                                matching: crate::config::template::MatchingConfig { file: "template.png".to_string(), threshold: 0.9 },
                                action: crate::core::action::Action::Click { offset: (10, 10) },
                            };
                            config.templates.push(new_template);
                            
                            // Save config
                            if let Err(e) = crate::config::loader::ConfigLoader::save("config.toml", &config) {
                                tracing::error!("Failed to save config: {}", e);
                            } else {
                                tracing::info!("Config saved with new template.");
                            }
                        }
                        self.new_template_name.clear();
                     }
                }
            });
        });
    }
}
