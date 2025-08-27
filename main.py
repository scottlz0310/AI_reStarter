#!/usr/bin/env python3
"""
AI reStarter - メインエントリーポイント
既存のKiro-IDE自動復旧システムを統合GUIで操作
"""

import logging
import sys
import tkinter as tk
from tkinter import messagebox, ttk

from src.gui.main_window import MainWindow

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("ai_restarter.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)


def main():
    """メインエントリーポイント"""
    try:
        logger.info("AI reStarter を起動しています...")

        # ルートウィンドウの作成
        root = tk.Tk()
        root.title("AI reStarter - AI-IDE自動復旧システム")
        root.geometry("800x600")

        # メインウィンドウの作成
        main_window = MainWindow(root)

        # クローズイベントの設定
        root.protocol("WM_DELETE_WINDOW", main_window.on_closing)

        logger.info("メインウィンドウを表示しました")

        # メインループの開始
        root.mainloop()

    except Exception as e:
        logger.critical(f"アプリケーション起動エラー: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
