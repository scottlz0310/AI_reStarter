#!/usr/bin/env python3
"""
AI reStarter - メインエントリーポイント
既存のKiro-IDE自動復旧システムを統合GUIで操作
"""

import logging
import sys
import tkinter as tk

from src.config.config_manager import ConfigManager
from src.gui.main_window import MainWindow
from src.utils.output_controller import output_controller

logger = logging.getLogger(__name__)


def main():
    """メインエントリーポイント"""
    try:
        # 設定管理システムを初期化（ログ設定も含む）
        config_manager = ConfigManager()

        # 出力制御システムを初期化
        output_controller.set_config_manager(config_manager)
        output_controller.info("AI reStarter を起動しています...", "main")

        # ルートウィンドウの作成
        root = tk.Tk()
        root.title("AI reStarter - AI-IDE自動復旧システム")
        root.geometry("800x600")

        # メインウィンドウの作成
        main_window = MainWindow(root)

        # クローズイベントの設定
        root.protocol("WM_DELETE_WINDOW", main_window.on_closing)

        output_controller.info("メインウィンドウを表示しました", "main")

        # メインループの開始
        root.mainloop()

    except Exception as e:
        output_controller.critical(f"アプリケーション起動エラー: {e}", "main")
        sys.exit(1)


if __name__ == "__main__":
    main()
