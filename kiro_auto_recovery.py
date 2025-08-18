#!/usr/bin/env python3
"""
Kiro-IDE自動復旧システム
エラー発生時に画面キャプチャで検知し、自動でチャット再開指示を送信
"""

import json
import logging
import os
import threading
import time
from typing import Optional

import cv2
import numpy as np

# pyperclipライブラリを条件付きでインポート（クリップボード入力用）
try:
    import pyperclip

    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False
except Exception:
    PYPERCLIP_AVAILABLE = False

# keyboardライブラリを条件付きでインポート
try:
    import keyboard

    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False
except Exception:
    KEYBOARD_AVAILABLE = False

# win32guiライブラリを条件付きでインポート（Windows環境でのフォーカス制御）
try:
    import win32con
    import win32gui

    WIN32GUI_AVAILABLE = True
except ImportError:
    WIN32GUI_AVAILABLE = False
except Exception:
    WIN32GUI_AVAILABLE = False

# pyautoguiは条件付きでインポート（WSL環境での問題回避）
try:
    import pyautogui

    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False
except Exception:
    PYAUTOGUI_AVAILABLE = False

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("kiro_recovery.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


class KiroAutoRecovery:
    def __init__(self, config_file: str = "kiro_config.json"):
        """
        初期化
        Args:
            config_file: 設定ファイルのパス
        """
        self.config = self.load_config(config_file)
        self.monitoring = False
        self.error_templates: dict[str, np.ndarray] = {}
        self.last_error_time = 0
        self.recovery_attempts = 0
        self.max_recovery_attempts = self.config.get("max_recovery_attempts", 3)

        # ライブラリ利用可能性をログ出力
        self._log_library_status()

        # PyAutoGUIの設定
        if PYAUTOGUI_AVAILABLE:
            pyautogui.PAUSE = self.config.get("action_delay", 0.5)
            pyautogui.FAILSAFE = True

        # エラーテンプレート画像を読み込み
        self.load_error_templates()

    def _log_library_status(self) -> None:
        """ライブラリの利用可能性をログ出力"""
        if not PYPERCLIP_AVAILABLE:
            logger.warning(
                "pyperclipが利用できません。クリップボード入力機能は無効です。"
            )
        if not KEYBOARD_AVAILABLE:
            logger.warning(
                "keyboardライブラリが利用できません。ホットキー機能は無効です。"
            )
        if not WIN32GUI_AVAILABLE:
            logger.warning("win32guiが利用できません。強制フォーカス機能は無効です。")
        if not PYAUTOGUI_AVAILABLE:
            logger.warning("pyautoguiが利用できません。画面キャプチャ機能は無効です。")

    def load_config(self, config_file: str) -> dict:
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
        except Exception as e:
            logger.warning(f"設定ファイル読み込みエラー: {e}")

        return default_config

    def load_error_templates(self) -> None:
        """エラー検出用のテンプレート画像を読み込み"""
        templates_dir = self.config["error_templates_dir"]
        if not os.path.exists(templates_dir):
            os.makedirs(templates_dir)
            logger.info(f"テンプレートディレクトリを作成: {templates_dir}")
            return

        for filename in os.listdir(templates_dir):
            if filename.lower().endswith((".png", ".jpg", ".jpeg")):
                template_path = os.path.join(templates_dir, filename)
                try:
                    template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
                    if template is not None:
                        template_name = os.path.splitext(filename)[0]
                        self.error_templates[template_name] = template
                        logger.info(f"エラーテンプレート読み込み: {template_name}")
                except Exception as e:
                    logger.error(f"テンプレート読み込みエラー {filename}: {e}")

    def capture_screen(
        self, region: Optional[tuple[int, int, int, int]] = None
    ) -> np.ndarray:
        """
        画面をキャプチャ
        Args:
            region: キャプチャする領域 (x, y, width, height)
        Returns:
            キャプチャした画像（グレースケール）
        """
        if not PYAUTOGUI_AVAILABLE:
            raise RuntimeError(
                "pyautoguiが利用できません。画面キャプチャ機能は無効です。"
            )

        if region:
            screenshot = pyautogui.screenshot(region=region)
        else:
            screenshot = pyautogui.screenshot()

        # OpenCV形式に変換（グレースケール）
        screenshot_np = np.array(screenshot)
        screenshot_gray = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2GRAY)

        return screenshot_gray  # type: ignore[no-any-return]

    def detect_error(self, screenshot: np.ndarray) -> Optional[str]:
        """
        エラーを検出
        Args:
            screenshot: スクリーンショット画像
        Returns:
            検出されたエラーの種類（なければNone）
        """
        threshold = self.config["template_threshold"]

        for error_name, template in self.error_templates.items():
            # テンプレートマッチング
            result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            if max_val >= threshold:
                logger.info(f"エラー検出: {error_name} (信頼度: {max_val:.3f})")
                return error_name

        return None

    def force_focus_kiro_window(self) -> bool:
        """
        Kiro-IDEウィンドウに強制フォーカス
        Returns:
            フォーカス成功フラグ
        """
        if not WIN32GUI_AVAILABLE:
            return False

        try:
            # Kiro-IDEウィンドウを探す
            windows = pyautogui.getAllWindows()
            kiro_windows = [w for w in windows if "kiro" in w.title.lower()]

            # Qt-Theme-StudioのKiroウィンドウを優先
            target_window = None
            for window in kiro_windows:
                if (
                    "qt-theme-studio" in window.title.lower()
                    or "qt-theme" in window.title.lower()
                ):
                    target_window = window
                    break

            if not target_window and kiro_windows:
                target_window = kiro_windows[0]

            if not target_window:
                logger.warning("Kiro-IDEウィンドウが見つかりません")
                return False

            # ウィンドウを前面に移動
            target_window.activate()
            time.sleep(0.5)

            # ウィンドウハンドルを取得して強制フォーカス
            hwnd = win32gui.FindWindow(None, target_window.title)
            if hwnd:
                win32gui.SetForegroundWindow(hwnd)
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                time.sleep(0.5)
                logger.info(
                    f"Kiro-IDEウィンドウに強制フォーカス: {target_window.title}"
                )
                return True
            else:
                logger.warning(
                    f"ウィンドウハンドルが見つかりません: {target_window.title}"
                )
                return False

        except Exception as e:
            logger.error(f"強制フォーカスエラー: {e}")
            return False

    def send_recovery_command(self, error_type: Optional[str] = None) -> bool:
        """
        復旧コマンドを送信
        Args:
            error_type: 検出されたエラーの種類
        Returns:
            送信成功フラグ
        """
        try:
            # チャット入力欄の位置を取得
            chat_position = self.config.get("chat_input_position")
            if not chat_position:
                # チャット入力欄を自動検出を試行
                chat_position = self.find_chat_input()
                if not chat_position:
                    logger.error("チャット入力欄が見つかりません")
                    return False

            # Kiro-IDEウィンドウを探す（フォーカスは行わない）
            windows = pyautogui.getAllWindows()
            kiro_windows = [w for w in windows if "kiro" in w.title.lower()]

            target_hwnd = None
            for window in kiro_windows:
                if (
                    "qt-theme-studio" in window.title.lower()
                    or "qt-theme" in window.title.lower()
                ):
                    target_hwnd = win32gui.FindWindow(None, window.title)
                    break

            if not target_hwnd and kiro_windows:
                target_hwnd = win32gui.FindWindow(None, kiro_windows[0].title)

            if not target_hwnd:
                logger.error("Kiro-IDEウィンドウが見つかりません")
                return False

            # チャット入力欄をクリック（フォーカスは行わない）
            pyautogui.click(chat_position[0], chat_position[1])
            time.sleep(1.0)

            # 復旧コマンドを選択
            recovery_commands = self.config["recovery_commands"]
            command = recovery_commands[0]  # デフォルトコマンド

            # エラータイプに応じてコマンドを選択
            if error_type and error_type in self.config.get("custom_commands", {}):
                command = self.config["custom_commands"][error_type]

            # PostMessageを使用してテキストを送信
            for char in command:
                win32gui.PostMessage(target_hwnd, win32con.WM_CHAR, ord(char), 0)
                time.sleep(0.1)

            time.sleep(0.5)

            # Enterキーで送信（PostMessageを使用）
            win32gui.PostMessage(
                target_hwnd, win32con.WM_KEYDOWN, win32con.VK_RETURN, 0
            )
            win32gui.PostMessage(target_hwnd, win32con.WM_KEYUP, win32con.VK_RETURN, 0)

            logger.info(f"復旧コマンド送信: {command}")
            return True

        except Exception as e:
            logger.error(f"復旧コマンド送信エラー: {e}")
            return False

    def find_chat_input(self) -> Optional[tuple[int, int]]:
        """
        チャット入力欄を自動検出
        Returns:
            チャット入力欄の座標 (x, y)
        """
        try:
            # チャット入力欄のテンプレートがある場合
            chat_template_path = os.path.join(
                self.config["error_templates_dir"], "chat_input.png"
            )

            if os.path.exists(chat_template_path):
                screenshot = self.capture_screen()
                chat_template = cv2.imread(chat_template_path, cv2.IMREAD_GRAYSCALE)

                result = cv2.matchTemplate(
                    screenshot, chat_template, cv2.TM_CCOEFF_NORMED
                )
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

                if max_val >= 0.7 and chat_template is not None:
                    # テンプレートの中心座標を返す
                    h, w = chat_template.shape
                    center_x = max_loc[0] + w // 2
                    center_y = max_loc[1] + h // 2
                    return (center_x, center_y)

            logger.warning("チャット入力欄の自動検出に失敗")
            return None

        except Exception as e:
            logger.error(f"チャット入力欄検出エラー: {e}")
            return None

    def should_attempt_recovery(self) -> bool:
        """復旧を試行すべきかチェック"""
        current_time = time.time()
        cooldown = self.config["recovery_cooldown"]

        # クールダウン時間チェック
        if current_time - self.last_error_time < cooldown:
            return False

        # 最大試行回数チェック
        if self.recovery_attempts >= self.max_recovery_attempts:
            logger.warning("最大復旧試行回数に達しました")
            return False

        return True

    def monitor_loop(self) -> None:
        """メインの監視ループ"""
        logger.info("監視開始")
        monitor_region = self.config.get("monitor_region")

        while self.monitoring:
            try:
                # 画面をキャプチャ
                screenshot = self.capture_screen(monitor_region)

                # エラーを検出
                error_type = self.detect_error(screenshot)

                if error_type:
                    current_time = time.time()

                    # 復旧を試行すべきかチェック
                    if self.should_attempt_recovery():
                        logger.info(f"復旧を試行: {error_type}")

                        if self.send_recovery_command(error_type):
                            self.last_error_time = int(current_time)
                            self.recovery_attempts += 1
                            logger.info(
                                f"復旧試行回数: "
                                f"{self.recovery_attempts}/{self.max_recovery_attempts}"
                            )
                        else:
                            logger.error("復旧コマンドの送信に失敗")
                    else:
                        logger.info(
                            "復旧をスキップ（クールダウン中または最大試行回数到達）"
                        )

                time.sleep(self.config["monitor_interval"])

            except KeyboardInterrupt:
                logger.info("監視を停止します")
                break
            except Exception as e:
                logger.error(f"監視ループエラー: {e}")
                time.sleep(5)  # エラー時は少し長く待機

        logger.info("監視終了")

    def start_monitoring(self) -> Optional[threading.Thread]:
        """監視開始"""
        if self.monitoring:
            logger.warning("既に監視中です")
            return None

        if not self.error_templates:
            logger.warning("エラーテンプレートが読み込まれていません")
            return None

        self.monitoring = True
        self.recovery_attempts = 0

        # 別スレッドで監視開始
        monitor_thread = threading.Thread(target=self.monitor_loop)
        monitor_thread.daemon = True
        monitor_thread.start()

        return monitor_thread

    def stop_monitoring(self) -> None:
        """監視停止"""
        self.monitoring = False
        logger.info("監視停止要求")

    def setup_hotkeys(self) -> None:
        """ホットキーを設定"""
        if not KEYBOARD_AVAILABLE:
            logger.warning(
                "keyboardライブラリが利用できません。ホットキー機能は無効です。"
            )
            return

        try:
            # 既存のホットキーをクリア
            keyboard.unhook_all()

            # Ctrl + Alt + S: テンプレート保存
            keyboard.add_hotkey("ctrl+alt+s", self.hotkey_save_template, suppress=True)
            logger.info("ホットキー設定: Ctrl+Alt+S (テンプレート保存)")

            # Ctrl + Alt + R: 手動復旧コマンド送信
            keyboard.add_hotkey("ctrl+alt+r", self.hotkey_send_recovery, suppress=True)
            logger.info("ホットキー設定: Ctrl+Alt+R (復旧コマンド送信)")

            # Ctrl + Alt + P: 一時停止/再開
            keyboard.add_hotkey("ctrl+alt+p", self.hotkey_toggle_pause, suppress=True)
            logger.info("ホットキー設定: Ctrl+Alt+P (一時停止/再開)")

            # Ctrl + Alt + Q: 監視停止
            keyboard.add_hotkey(
                "ctrl+alt+q", self.hotkey_stop_monitoring, suppress=True
            )
            logger.info("ホットキー設定: Ctrl+Alt+Q (監視停止)")

            logger.info("✅ ホットキー設定完了")

        except Exception as e:
            logger.error(f"ホットキー設定エラー: {e}")
            logger.error("ホットキー機能は無効です")

    def hotkey_save_template(self) -> None:
        """ホットキー: テンプレート保存"""
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            template_name = f"hotkey_template_{timestamp}"
            self.save_error_template(template_name)
            logger.info(f"ホットキー: テンプレート '{template_name}' を保存しました")
        except Exception as e:
            logger.error(f"ホットキーテンプレート保存エラー: {e}")

    def hotkey_send_recovery(self) -> None:
        """ホットキー: 手動復旧コマンド送信"""
        try:
            success = self.send_recovery_command()
            if success:
                logger.info("ホットキー: 復旧コマンドを送信しました")
            else:
                logger.warning("ホットキー: 復旧コマンド送信に失敗しました")
        except Exception as e:
            logger.error(f"ホットキー復旧コマンド送信エラー: {e}")

    def hotkey_toggle_pause(self) -> None:
        """ホットキー: 一時停止/再開"""
        try:
            self.monitoring = not self.monitoring
            status = "一時停止" if not self.monitoring else "再開"
            logger.info(f"ホットキー: 監視を{status}しました")
            logger.info(f"監視{status}")
        except Exception as e:
            logger.error(f"ホットキー一時停止/再開エラー: {e}")

    def hotkey_stop_monitoring(self) -> None:
        """ホットキー: 監視停止"""
        try:
            self.stop_monitoring()
            logger.info("ホットキー: 監視停止要求を送信しました")
        except Exception as e:
            logger.error(f"ホットキー監視停止エラー: {e}")

    def save_error_template(
        self, template_name: str, region: Optional[tuple[int, int, int, int]] = None
    ) -> None:
        """
        現在の画面からエラーテンプレートを保存
        Args:
            template_name: テンプレート名
            region: キャプチャする領域（Noneの場合は設定ファイルのmonitor_regionを使用）
        """
        try:
            # regionが指定されていない場合は設定ファイルのmonitor_regionを使用
            if region is None:
                region = self.config.get("monitor_region")
                if region:
                    logger.info(f"設定ファイルの監視エリアを使用: {region}")
                else:
                    logger.warning(
                        "監視エリアが設定されていません。画面全体をキャプチャします。"
                    )

            screenshot = self.capture_screen(region)

            template_path = os.path.join(
                self.config["error_templates_dir"], f"{template_name}.png"
            )

            cv2.imwrite(template_path, screenshot)
            logger.info(f"エラーテンプレート保存: {template_path}")

            # テンプレートを再読み込み
            self.error_templates[template_name] = screenshot

        except Exception as e:
            logger.error(f"テンプレート保存エラー: {e}")


def create_sample_config() -> None:
    """サンプル設定ファイルを作成"""
    config = {
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

    with open("kiro_config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    logger.info("サンプル設定ファイル 'kiro_config.json' を作成しました")


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Kiro-IDE自動復旧システム")
    parser.add_argument(
        "--create-config", action="store_true", help="サンプル設定ファイルを作成"
    )
    parser.add_argument("--config", default="kiro_config.json", help="設定ファイル")
    parser.add_argument("--template", help="エラーテンプレートを保存")

    args = parser.parse_args()

    if args.create_config:
        create_sample_config()
        sys.exit(0)

    # 自動復旧システムを初期化
    recovery_system = KiroAutoRecovery(args.config)

    if args.template:
        logger.info(f"5秒後にエラーテンプレート '{args.template}' を保存します...")
        time.sleep(5)
        recovery_system.save_error_template(args.template)
        logger.info("テンプレート保存完了")
        sys.exit(0)

    try:
        logger.info("Kiro-IDE自動復旧システムを開始します...")
        logger.info("Ctrl+Cで停止")
        logger.info("\n=== ホットキー一覧 ===")
        logger.info("Ctrl+Alt+S: テンプレート保存")
        logger.info("Ctrl+Alt+R: 復旧コマンド送信")
        logger.info("Ctrl+Alt+P: 一時停止/再開")
        logger.info("Ctrl+Alt+Q: 監視停止")
        logger.info("==================\n")

        # ホットキーを設定
        recovery_system.setup_hotkeys()

        monitor_thread = recovery_system.start_monitoring()

        # メインスレッドで待機
        while recovery_system.monitoring:
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("\n停止中...")
        recovery_system.stop_monitoring()
    except Exception as e:
        logger.error(f"システムエラー: {e}")

    logger.info("システムを終了しました")
