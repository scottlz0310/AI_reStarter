"""
出力制御システム
標準出力とログウィンドウの表示を統合管理
"""

import logging
import sys
import threading
from collections.abc import Callable
from enum import Enum
from typing import Any
from typing import Optional


class OutputLevel(Enum):
    """出力レベル"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class OutputController:
    """出力制御システム"""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self._gui_callback: Callable[[str, str], None] | None = None
        self._console_enabled = True
        self._log_enabled = True
        self._gui_enabled = True
        self._lock = threading.Lock()
        self._config_manager: Any = None

        # 元の標準出力を保存
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr

        self.logger.debug("出力制御システムを初期化しました")

    def set_gui_callback(self, callback: Callable[[str, str], None]) -> None:
        """GUIログウィンドウのコールバックを設定"""
        with self._lock:
            self._gui_callback = callback
            self.logger.debug("GUIコールバックを設定しました")

    def set_config_manager(self, config_manager: Any) -> None:
        """設定マネージャーを設定"""
        self._config_manager = config_manager
        if config_manager:
            log_config = config_manager.get("logging", {})
            self._console_enabled = log_config.get("console_enabled", True)
            self._log_enabled = log_config.get("file_enabled", True)
            self._gui_enabled = log_config.get("gui_enabled", True)

    def enable_console_output(self, enabled: bool = True) -> None:
        """コンソール出力の有効/無効を設定"""
        with self._lock:
            self._console_enabled = enabled
            self._save_output_settings()
            self.logger.debug(f"コンソール出力: {'有効' if enabled else '無効'}")

    def enable_log_output(self, enabled: bool = True) -> None:
        """ログファイル出力の有効/無効を設定"""
        with self._lock:
            self._log_enabled = enabled
            self._save_output_settings()
            self.logger.debug(f"ログファイル出力: {'有効' if enabled else '無効'}")

    def enable_gui_output(self, enabled: bool = True) -> None:
        """GUIログウィンドウ出力の有効/無効を設定"""
        with self._lock:
            self._gui_enabled = enabled
            self._save_output_settings()
            self.logger.debug(f"GUIログウィンドウ出力: {'有効' if enabled else '無効'}")

    def output(
        self,
        message: str,
        level: OutputLevel = OutputLevel.INFO,
        module_name: str = "system",
    ) -> None:
        """統合出力メソッド"""
        with self._lock:
            # コンソール出力
            if self._console_enabled:
                self._output_to_console(message, level)

            # ログファイル出力
            if self._log_enabled:
                self._output_to_log(message, level, module_name)

            # GUIログウィンドウ出力
            if self._gui_enabled and self._gui_callback:
                self._output_to_gui(message, level)

    def _output_to_console(self, message: str, level: OutputLevel) -> None:
        """コンソールに出力"""
        try:
            if level in [OutputLevel.ERROR, OutputLevel.CRITICAL]:
                print(f"[{level.value}] {message}", file=self._original_stderr)
            else:
                print(f"[{level.value}] {message}", file=self._original_stdout)
        except Exception as e:
            # コンソール出力エラーは内部ログのみ
            self.logger.error(f"コンソール出力エラー: {e}")

    def _output_to_log(
        self, message: str, level: OutputLevel, module_name: str
    ) -> None:
        """ログファイルに出力"""
        try:
            module_logger = logging.getLogger(module_name)
            log_level = getattr(logging, level.value)
            module_logger.log(log_level, message)
        except Exception as e:
            self.logger.error(f"ログファイル出力エラー: {e}")

    def _output_to_gui(self, message: str, level: OutputLevel) -> None:
        """GUIログウィンドウに出力"""
        try:
            if self._gui_callback:
                self._gui_callback(message, level.value)
        except Exception as e:
            self.logger.error(f"GUIログウィンドウ出力エラー: {e}")

    def debug(self, message: str, module_name: str = "system") -> None:
        """デバッグメッセージを出力"""
        self.output(message, OutputLevel.DEBUG, module_name)

    def info(self, message: str, module_name: str = "system") -> None:
        """情報メッセージを出力"""
        self.output(message, OutputLevel.INFO, module_name)

    def warning(self, message: str, module_name: str = "system") -> None:
        """警告メッセージを出力"""
        self.output(message, OutputLevel.WARNING, module_name)

    def error(self, message: str, module_name: str = "system") -> None:
        """エラーメッセージを出力"""
        self.output(message, OutputLevel.ERROR, module_name)

    def critical(self, message: str, module_name: str = "system") -> None:
        """重大エラーメッセージを出力"""
        self.output(message, OutputLevel.CRITICAL, module_name)

    def redirect_stdout(self) -> None:
        """標準出力をリダイレクト"""
        sys.stdout = OutputRedirector(self, OutputLevel.INFO)
        sys.stderr = OutputRedirector(self, OutputLevel.ERROR)
        self.logger.debug("標準出力をリダイレクトしました")

    def restore_stdout(self) -> None:
        """標準出力を復元"""
        sys.stdout = self._original_stdout
        sys.stderr = self._original_stderr
        self.logger.debug("標準出力を復元しました")

    def get_status(self) -> dict[str, Any]:
        """現在の出力設定状態を取得"""
        return {
            "console_enabled": self._console_enabled,
            "log_enabled": self._log_enabled,
            "gui_enabled": self._gui_enabled,
            "gui_callback_set": self._gui_callback is not None,
        }

    def _save_output_settings(self) -> None:
        """出力設定を設定ファイルに保存"""
        if self._config_manager:
            try:
                config = self._config_manager.get_config()
                if "logging" not in config:
                    config["logging"] = {}

                config["logging"]["console_enabled"] = self._console_enabled
                config["logging"]["file_enabled"] = self._log_enabled
                config["logging"]["gui_enabled"] = self._gui_enabled

                self._config_manager.config = config
                self._config_manager.save_config()

            except Exception as e:
                self.logger.error(f"出力設定保存エラー: {e}")


class OutputRedirector:
    """標準出力リダイレクター"""

    def __init__(self, controller: OutputController, level: OutputLevel):
        self.controller = controller
        self.level = level

    def write(self, message: str) -> None:
        """書き込み処理"""
        if message.strip():  # 空行は無視
            self.controller.output(message.strip(), self.level)

    def flush(self) -> None:
        """フラッシュ処理（何もしない）"""
        pass


# グローバルインスタンス
output_controller = OutputController()
