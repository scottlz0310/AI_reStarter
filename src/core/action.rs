use enigo::{Enigo, Mouse, Keyboard, Settings, Direction, Key, Button};
use crate::error::Result;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum Action {
    Click { offset: (i32, i32) },
    Chat { command: String },
    Keyboard { keys: Vec<String> },
}

pub struct ActionEngine {
    enigo: Enigo,
}

impl ActionEngine {
    pub fn new() -> Self {
        Self {
            enigo: Enigo::new(&Settings::default()).unwrap(),
        }
    }

    pub fn execute(&mut self, action: &Action, target_pos: (u32, u32)) -> Result<()> {
        match action {
            Action::Click { offset } => {
                let x = target_pos.0 as i32 + offset.0;
                let y = target_pos.1 as i32 + offset.1;
                self.enigo.move_mouse(x, y, enigo::Coordinate::Abs).map_err(|e| crate::error::AppError::Unknown(e.to_string()))?;
                self.enigo.button(Button::Left, Direction::Click).map_err(|e| crate::error::AppError::Unknown(e.to_string()))?;
            }
            Action::Chat { command } => {
                self.enigo.text(command).map_err(|e| crate::error::AppError::Unknown(e.to_string()))?;
                self.enigo.key(Key::Return, Direction::Click).map_err(|e| crate::error::AppError::Unknown(e.to_string()))?;
            }
            Action::Keyboard { keys } => {
                for _key in keys {
                    // TODO: Parse key string to Enigo Key enum
                }
            }
        }
        Ok(())
    }
}
