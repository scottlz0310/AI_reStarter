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
                for key_str in keys {
                    self.execute_key_sequence(key_str)?;
                }
            }
        }
        Ok(())
    }

    fn execute_key_sequence(&mut self, key_str: &str) -> Result<()> {
        let parts: Vec<&str> = key_str.split('+').map(|s| s.trim()).collect();
        if parts.is_empty() {
            return Ok(());
        }

        let mut modifiers = Vec::new();
        let final_key = parts.last().unwrap();

        // Press modifiers
        for part in &parts[..parts.len() - 1] {
            let key = self.parse_key(part)?;
            self.enigo.key(key, Direction::Press).map_err(|e| crate::error::AppError::Unknown(e.to_string()))?;
            modifiers.push(key);
        }

        // Click final key
        // If final key is 1 char, use text for better layout support, unless it matches a known key name
        if let Ok(key) = self.parse_key(final_key) {
             self.enigo.key(key, Direction::Click).map_err(|e| crate::error::AppError::Unknown(e.to_string()))?;
        } else if final_key.chars().count() == 1 {
             self.enigo.text(final_key).map_err(|e| crate::error::AppError::Unknown(e.to_string()))?;
        } else {
             return Err(crate::error::AppError::Unknown(format!("Unknown key: {}", final_key)));
        }

        // Release modifiers in reverse
        for key in modifiers.iter().rev() {
            self.enigo.key(*key, Direction::Release).map_err(|e| crate::error::AppError::Unknown(e.to_string()))?;
        }

        Ok(())
    }

    fn parse_key(&self, key_name: &str) -> Result<Key> {
        match key_name.to_lowercase().as_str() {
            "ctrl" | "control" => Ok(Key::Control),
            "alt" => Ok(Key::Alt),
            "shift" => Ok(Key::Shift),
            "win" | "meta" | "command" => Ok(Key::Meta),
            "enter" | "return" => Ok(Key::Return),
            "tab" => Ok(Key::Tab),
            "space" => Ok(Key::Space),
            "backspace" => Ok(Key::Backspace),
            "escape" | "esc" => Ok(Key::Escape),
            "delete" | "del" => Ok(Key::Delete),
            "up" => Ok(Key::UpArrow),
            "down" => Ok(Key::DownArrow),
            "left" => Ok(Key::LeftArrow),
            "right" => Ok(Key::RightArrow),
            "f1" => Ok(Key::F1),
            "f2" => Ok(Key::F2),
            "f3" => Ok(Key::F3),
            "f4" => Ok(Key::F4),
            "f5" => Ok(Key::F5),
            "f6" => Ok(Key::F6),
            "f7" => Ok(Key::F7),
            "f8" => Ok(Key::F8),
            "f9" => Ok(Key::F9),
            "f10" => Ok(Key::F10),
            "f11" => Ok(Key::F11),
            "f12" => Ok(Key::F12),
            _ => Err(crate::error::AppError::Unknown(format!("Unknown key: {}", key_name))),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_key() {
        let engine = ActionEngine::new();

        assert_eq!(engine.parse_key("Ctrl").unwrap(), Key::Control);
        assert_eq!(engine.parse_key("enter").unwrap(), Key::Return);
        assert_eq!(engine.parse_key("F1").unwrap(), Key::F1);

        assert!(engine.parse_key("unknown").is_err());
    }

    #[test]
    fn test_key_sequence_parsing() {
        let engine = ActionEngine::new();
        let seq = "Ctrl+C";
        let parts: Vec<&str> = seq.split('+').collect();
        assert_eq!(parts, vec!["Ctrl", "C"]);

        assert!(engine.parse_key(parts[0]).is_ok());
        assert!(engine.parse_key(parts[1]).is_err());
    }
}
