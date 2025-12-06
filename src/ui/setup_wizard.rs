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
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
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
            if let Ok(mut config) = self.config.lock() {
                let mut remove_index = None;
                for (i, template) in config.templates.iter_mut().enumerate() {
                    ui.group(|ui| {
                        ui.horizontal(|ui| {
                            ui.label(format!("Name: {}", template.name));
                            if ui.button("❌").clicked() {
                                remove_index = Some(i);
                            }
                        });

                        ui.label("Action Type:");
                        ui.horizontal(|ui| {
                            if ui.radio(matches!(template.action, crate::core::action::Action::Click { .. }), "Click").clicked() {
                                template.action = crate::core::action::Action::Click { offset: (0, 0) };
                            }
                            if ui.radio(matches!(template.action, crate::core::action::Action::Chat { .. }), "Chat").clicked() {
                                template.action = crate::core::action::Action::Chat { command: String::new() };
                            }
                            if ui.radio(matches!(template.action, crate::core::action::Action::Keyboard { .. }), "Keyboard").clicked() {
                                template.action = crate::core::action::Action::Keyboard { keys: vec![String::new()] };
                            }
                        });

                        match &mut template.action {
                            crate::core::action::Action::Click { offset } => {
                                ui.horizontal(|ui| {
                                    ui.label("Offset X:");
                                    ui.add(egui::DragValue::new(&mut offset.0));
                                    ui.label("Y:");
                                    ui.add(egui::DragValue::new(&mut offset.1));
                                });
                            }
                            crate::core::action::Action::Chat { command } => {
                                ui.horizontal(|ui| {
                                    ui.label("Command:");
                                    ui.text_edit_singleline(command);
                                });
                            }
                            crate::core::action::Action::Keyboard { keys } => {
                                ui.label("Keys sequence:");
                                let mut remove_key = None;
                                for (k_i, key) in keys.iter_mut().enumerate() {
                                    ui.horizontal(|ui| {
                                        ui.text_edit_singleline(key);
                                        if ui.button("x").clicked() {
                                            remove_key = Some(k_i);
                                        }
                                    });
                                }
                                if let Some(k) = remove_key {
                                    keys.remove(k);
                                }
                                if ui.button("+ Add Key").clicked() {
                                    keys.push(String::new());
                                }
                            }
                        }
                    });
                }

                if let Some(i) = remove_index {
                    config.templates.remove(i);
                }

                if ui.button("💾 Save Changes").clicked() {
                     if let Err(e) = crate::config::loader::ConfigLoader::save("config.toml", &config) {
                        tracing::error!("Failed to save config: {}", e);
                    } else {
                        tracing::info!("Config saved.");
                    }
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
