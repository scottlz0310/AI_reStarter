"""
設定管理クラス
既存のKiroAutoRecoveryクラスから設定管理機能を分離
"""

import json
import logging
import logging.handlers
import os
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class ConfigManager:
    """設定管理クラス - 既存の設定管理機能を分離"""

    def __init__(self, config_file: str = "config.local.json"):
        """
        初期化
        Args:
            config_file: 設定ファイルのパス
        """
        self.config_file = config_file
        self.config = self.load_config(config_file)
        self._setup_logging()
        logger.info(f"設定ファイル '{config_file}' を読み込みました")

    def load_config(self, config_file: str) -> dict[str, Any]:
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
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file_enabled": True,
                "file_path": "logs/ai_restarter.log",
                "console_enabled": True,
                "max_file_size": "10MB",
                "backup_count": 5,
            },
        }

        try:
            if os.path.exists(config_file):
                with open(config_file, encoding="utf-8") as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
                    logger.info(f"ユーザー設定を読み込みました: {config_file}")
            else:
                # テンプレートファイルから読み込み
                template_file = "config.template.json"
                if os.path.exists(template_file):
                    with open(template_file, encoding="utf-8") as f:
                        template_config = json.load(f)
                        default_config.update(template_config)
                    logger.info(f"テンプレート設定を読み込みました: {template_file}")

                logger.info(
                    f"設定ファイルが存在しません。デフォルト設定を使用し、設定ファイルを作成します: {config_file}"
                )
                # デフォルト設定で設定ファイルを作成
                try:
                    with open(config_file, "w", encoding="utf-8") as f:
                        json.dump(default_config, f, ensure_ascii=False, indent=2)
                    logger.info(f"デフォルト設定ファイルを作成しました: {config_file}")
                except Exception as create_error:
                    logger.warning(f"設定ファイル作成に失敗: {create_error}")
        except Exception as e:
            logger.warning(f"設定ファイル読み込みエラー: {e}")

        return default_config

    def get_config(self) -> dict[str, Any]:
        """現在の設定を取得"""
        return self.config.copy()

    def get(self, key: str, default: Any = None) -> Any:
        """指定されたキーの設定値を取得（ドット記法もサポート）"""
        if "." in key:
            # ドット記法での階層アクセス（例: "amazonq.enabled"）
            keys = key.split(".")
            value = self.config
            for k in keys:
                if isinstance(value, dict) and k in value:
                    value = value[k]
                else:
                    return default
            return value
        else:
            return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """設定値を更新"""
        # 設定値の妥当性をチェック
        if self._validate_setting(key, value):
            self.config[key] = value
            logger.debug(f"設定を更新: {key} = {value}")
        else:
            logger.warning(f"設定値の妥当性チェックに失敗: {key} = {value}")

    def _validate_setting(self, key: str, value: Any) -> bool:
        """設定値の妥当性をチェック"""
        try:
            if key == "monitor_interval":
                return isinstance(value, int | float) and 0.1 <= value <= 60.0
            elif key == "action_delay":
                return isinstance(value, int | float) and 0.1 <= value <= 10.0
            elif key == "max_recovery_attempts":
                return isinstance(value, int) and 1 <= value <= 10
            elif key == "recovery_cooldown":
                return isinstance(value, int | float) and 5 <= value <= 300
            elif key == "template_threshold":
                return isinstance(value, int | float) and 0.1 <= value <= 1.0
            elif key == "chat_input_position":
                if value is None:
                    return True
                if isinstance(value, list | tuple) and len(value) == 2:
                    x, y = value[0], value[1]
                    return (
                        isinstance(x, int | float)
                        and isinstance(y, int | float)
                        and x >= 0
                        and y >= 0
                    )
                return False
            elif key == "monitor_region":
                if value is None:
                    return True
                if isinstance(value, list | tuple) and len(value) == 4:
                    x, y, w, h = value[0], value[1], value[2], value[3]
                    return (
                        all(isinstance(v, int | float) for v in [x, y, w, h])
                        and w > 0
                        and h > 0
                    )
                return False
            elif key == "monitor_areas":
                if not isinstance(value, list):
                    return False
                for area in value:
                    if not isinstance(area, dict):
                        return False
                    required_keys = ["name", "x", "y", "width", "height"]
                    if not all(key in area for key in required_keys):
                        return False
                    if not all(
                        isinstance(area[key], int | float)
                        for key in ["x", "y", "width", "height"]
                    ):
                        return False
                    if area["width"] <= 0 or area["height"] <= 0:
                        return False
                return True
            else:
                return True  # その他の設定は検証をスキップ
        except Exception as e:
            logger.error(f"設定値検証エラー ({key}): {e}")
            return False

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
                "logging": {
                    "level": "INFO",
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    "file_enabled": True,
                    "file_path": "logs/ai_restarter.log",
                    "console_enabled": True,
                    "max_file_size": "10MB",
                    "backup_count": 5,
                },
            }

            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(sample_config, f, ensure_ascii=False, indent=2)

            logger.info(f"サンプル設定ファイル '{self.config_file}' を作成しました")
            return True
        except Exception as e:
            logger.error(f"サンプル設定ファイル作成エラー: {e}")
            return False

    def _setup_logging(self) -> None:
        """ログ設定を初期化"""
        log_config = self.config.get("logging", {})

        # ログレベル設定
        level = getattr(logging, log_config.get("level", "INFO").upper())

        # ルートロガーの設定
        root_logger = logging.getLogger()
        root_logger.setLevel(level)

        # 既存のハンドラーをクリア
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        # フォーマッター設定
        formatter = logging.Formatter(
            log_config.get(
                "format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
        )

        # コンソールハンドラー
        if log_config.get("console_enabled", True):
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)

        # ファイルハンドラー
        if log_config.get("file_enabled", True):
            log_path = Path(log_config.get("file_path", "logs/ai_restarter.log"))
            log_path.parent.mkdir(parents=True, exist_ok=True)

            # ファイルサイズの解析
            max_size = log_config.get("max_file_size", "10MB")
            if isinstance(max_size, str) and max_size.endswith("MB"):
                max_bytes = int(max_size[:-2]) * 1024 * 1024
            else:
                max_bytes = 10 * 1024 * 1024

            file_handler = logging.handlers.RotatingFileHandler(
                log_path,
                maxBytes=max_bytes,
                backupCount=log_config.get("backup_count", 5),
                encoding="utf-8",
            )
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
