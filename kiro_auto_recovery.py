#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kiro-IDE自動復旧システム
エラー発生時に画面キャプチャで検知し、自動でチャット再開指示を送信
"""

import json
import logging
import os
import threading
import time
from typing import Optional, Tuple

import cv2
import numpy as np

# pyautoguiは条件付きでインポート（WSL環境での問題回避）
try:
    import pyautogui

    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    print("警告: pyautoguiが利用できません。画面キャプチャ機能は無効です。")
except Exception as e:
    PYAUTOGUI_AVAILABLE = False
    print(f"警告: pyautoguiの初期化に失敗しました: {e}")
    print("画面キャプチャ機能は無効です。")

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
        self.error_templates = {}
        self.last_error_time = 0
        self.recovery_attempts = 0
        self.max_recovery_attempts = self.config.get("max_recovery_attempts", 3)

        # PyAutoGUIの設定
        if PYAUTOGUI_AVAILABLE:
            pyautogui.PAUSE = self.config.get("action_delay", 0.5)
            pyautogui.FAILSAFE = True

        # エラーテンプレート画像を読み込み
        self.load_error_templates()

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
            "chat_input_position": None,  # [x, y] 座標
            "monitor_region": None,  # [x, y, width, height]
            "template_threshold": 0.8,
        }

        try:
            if os.path.exists(config_file):
                with open(config_file, "r", encoding="utf-8") as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
        except Exception as e:
            logger.warning(f"設定ファイル読み込みエラー: {e}")

        return default_config

    def load_error_templates(self):
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
        self, region: Optional[Tuple[int, int, int, int]] = None
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

        return screenshot_gray

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

            # チャット入力欄をクリック
            pyautogui.click(chat_position[0], chat_position[1])
            time.sleep(0.5)

            # 復旧コマンドを選択
            recovery_commands = self.config["recovery_commands"]
            command = recovery_commands[0]  # デフォルトコマンド

            # エラータイプに応じてコマンドを選択
            if error_type and error_type in self.config.get("custom_commands", {}):
                command = self.config["custom_commands"][error_type]

            # コマンドを入力
            pyautogui.write(command, interval=0.05)
            time.sleep(0.5)

            # Enterキーで送信
            pyautogui.press("enter")

            logger.info(f"復旧コマンド送信: {command}")
            return True

        except Exception as e:
            logger.error(f"復旧コマンド送信エラー: {e}")
            return False

    def find_chat_input(self) -> Optional[Tuple[int, int]]:
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

                if max_val >= 0.7:
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

    def monitor_loop(self):
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
                            self.last_error_time = current_time
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

    def start_monitoring(self):
        """監視開始"""
        if self.monitoring:
            logger.warning("既に監視中です")
            return

        if not self.error_templates:
            logger.warning("エラーテンプレートが読み込まれていません")
            return

        self.monitoring = True
        self.recovery_attempts = 0

        # 別スレッドで監視開始
        monitor_thread = threading.Thread(target=self.monitor_loop)
        monitor_thread.daemon = True
        monitor_thread.start()

        return monitor_thread

    def stop_monitoring(self):
        """監視停止"""
        self.monitoring = False
        logger.info("監視停止要求")

    def save_error_template(
        self, template_name: str, region: Optional[Tuple[int, int, int, int]] = None
    ):
        """
        現在の画面からエラーテンプレートを保存
        Args:
            template_name: テンプレート名
            region: キャプチャする領域
        """
        try:
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


def create_sample_config():
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

    print("サンプル設定ファイル 'kiro_config.json' を作成しました")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Kiro-IDE自動復旧システム")
    parser.add_argument(
        "--create-config", action="store_true", help="サンプル設定ファイルを作成"
    )
    parser.add_argument("--config", default="kiro_config.json", help="設定ファイル")
    parser.add_argument("--template", help="エラーテンプレートを保存")

    args = parser.parse_args()

    if args.create_config:
        create_sample_config()
        exit(0)

    # 自動復旧システムを初期化
    recovery_system = KiroAutoRecovery(args.config)

    if args.template:
        print(f"5秒後にエラーテンプレート '{args.template}' を保存します...")
        time.sleep(5)
        recovery_system.save_error_template(args.template)
        print("テンプレート保存完了")
        exit(0)

    try:
        print("Kiro-IDE自動復旧システムを開始します...")
        print("Ctrl+Cで停止")

        monitor_thread = recovery_system.start_monitoring()

        # メインスレッドで待機
        while recovery_system.monitoring:
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n停止中...")
        recovery_system.stop_monitoring()
    except Exception as e:
        logger.error(f"システムエラー: {e}")

    print("システムを終了しました")
