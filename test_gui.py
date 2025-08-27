#!/usr/bin/env python3
"""
GUI機能テストスクリプト

新しく実装したGUI機能の基本動作をテストします。
"""

import sys
import os
import tkinter as tk
import logging

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.config.config_manager import ConfigManager
from src.core.mode_manager import ModeManager
from src.gui.mode_selector_widget import ModeSelectorWidget
from src.gui.amazonq_settings_dialog import AmazonQSettingsDialog

# ログ設定
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def test_mode_selector_widget():
    """ModeSelectorWidgetのテスト"""
    logger.info("=== ModeSelectorWidget テスト開始 ===")

    root = tk.Tk()
    root.title("ModeSelectorWidget テスト")
    root.geometry("600x300")

    # 設定管理とモード管理を初期化
    config_manager = ConfigManager("kiro_config.json")
    mode_manager = ModeManager(config_manager)

    def on_mode_changed(new_mode):
        logger.info(f"モード変更コールバック: {new_mode}")

    # ModeSelectorWidgetを作成
    mode_selector = ModeSelectorWidget(root, mode_manager, on_mode_changed)
    mode_selector.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    # 終了ボタン
    tk.Button(root, text="終了", command=root.quit).pack(pady=10)

    logger.info("ModeSelectorWidgetテストウィンドウを表示します")
    root.mainloop()


def test_amazonq_settings_dialog():
    """AmazonQSettingsDialogのテスト"""
    logger.info("=== AmazonQSettingsDialog テスト開始 ===")

    root = tk.Tk()
    root.title("AmazonQSettingsDialog テスト")
    root.geometry("400x200")

    # 設定管理を初期化
    config_manager = ConfigManager("kiro_config.json")

    def open_settings():
        dialog = AmazonQSettingsDialog(root, config_manager)
        dialog.show()

    # ダイアログを開くボタン
    tk.Button(
        root, text="AmazonQ設定を開く", command=open_settings, font=("", 12)
    ).pack(expand=True)

    # 終了ボタン
    tk.Button(root, text="終了", command=root.quit).pack(pady=10)

    logger.info("AmazonQSettingsDialogテストウィンドウを表示します")
    root.mainloop()


def main():
    """メイン関数"""
    if len(sys.argv) > 1:
        test_type = sys.argv[1]

        if test_type == "mode_selector":
            test_mode_selector_widget()
        elif test_type == "amazonq_settings":
            test_amazonq_settings_dialog()
        else:
            print("使用方法: python test_gui.py [mode_selector|amazonq_settings]")
            sys.exit(1)
    else:
        print("GUIテストスクリプト")
        print("使用方法:")
        print("  python test_gui.py mode_selector      # ModeSelectorWidgetテスト")
        print("  python test_gui.py amazonq_settings   # AmazonQSettingsDialogテスト")


if __name__ == "__main__":
    main()
