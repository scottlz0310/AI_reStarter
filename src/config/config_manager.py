"""
設定管理クラス
既存のKiroAutoRecoveryクラスから設定管理機能を分離
"""

import json
import logging
import os
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ConfigManager:
    """設定管理クラス - 既存の設定管理機能を分離"""
    
    def __init__(self, config_file: str = "kiro_config.json"):
        """
        初期化
        Args:
            config_file: 設定ファイルのパス
        """
        self.config_file = config_file
        self.config = self.load_config(config_file)
        logger.info(f"設定ファイル '{config_file}' を読み込みました")
    
    def load_config(self, config_file: str) -> Dict[str, Any]:
        """設定ファイルを読み込み"""
        default_config = {
            "monitor_interval": 2.0,
            "action_delay": 0.5,
            "max_recovery_attempts": 3,
            "recovery_cooldown": 30,
            "error_templates_dir": "error_templates",
            "recovery_commands": [
                "続行してください",
                "エラーを修正して続行",
                "タスクを再開してください",
            ],
            "custom_commands": {
                "compilation_error": "コンパイルエラーを修正して続行してください",
                "runtime_error": "ランタイムエラーを解決して再実行してください",
                "timeout_error": "タイムアウトエラー、再度実行してください",
            },
            "chat_input_position": None,  # [x, y] 座標
            "monitor_region": None,  # [x, y, width, height]
            "template_threshold": 0.8,
        }

        try:
            if os.path.exists(config_file):
                with open(config_file, encoding="utf-8") as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
                    logger.info(f"ユーザー設定を読み込みました: {config_file}")
            else:
                logger.info(f"設定ファイルが存在しません。デフォルト設定を使用します: {config_file}")
        except Exception as e:
            logger.warning(f"設定ファイル読み込みエラー: {e}")

        return default_config
    
    def get_config(self) -> Dict[str, Any]:
        """現在の設定を取得"""
        return self.config.copy()
    
    def get(self, key: str, default: Any = None) -> Any:
        """指定されたキーの設定値を取得"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """設定値を更新"""
        self.config[key] = value
        logger.debug(f"設定を更新: {key} = {value}")
    
    def save_config(self) -> bool:
        """設定をファイルに保存"""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            logger.info(f"設定を保存しました: {self.config_file}")
            return True
        except Exception as e:
            logger.error(f"設定保存エラー: {e}")
            return False
    
    def reload_config(self) -> bool:
        """設定ファイルを再読み込み"""
        try:
            self.config = self.load_config(self.config_file)
            logger.info("設定を再読み込みしました")
            return True
        except Exception as e:
            logger.error(f"設定再読み込みエラー: {e}")
            return False
    
    def create_sample_config(self) -> bool:
        """サンプル設定ファイルを作成"""
        try:
            sample_config = {
                "monitor_interval": 2.0,
                "action_delay": 0.5,
                "max_recovery_attempts": 3,
                "recovery_cooldown": 30,
                "error_templates_dir": "error_templates",
                "recovery_commands": [
                    "続行してください",
                    "エラーを修正して続行",
                    "タスクを再開してください",
                ],
                "custom_commands": {
                    "compilation_error": "コンパイルエラーを修正して続行してください",
                    "runtime_error": "ランタイムエラーを解決して再実行してください",
                    "timeout_error": "タイムアウトエラー、再度実行してください",
                },
                "chat_input_position": [800, 600],
                "monitor_region": [0, 0, 1920, 1080],
                "template_threshold": 0.8,
            }

            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(sample_config, f, ensure_ascii=False, indent=2)

            logger.info(f"サンプル設定ファイル '{self.config_file}' を作成しました")
            return True
        except Exception as e:
            logger.error(f"サンプル設定ファイル作成エラー: {e}")
            return False
