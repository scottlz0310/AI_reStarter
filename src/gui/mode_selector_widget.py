"""
モード選択ウィジェット

このモジュールは、Kiro-IDEモード、AmazonQモード、自動モードの選択UIを提供します。
"""

import logging
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

logger = logging.getLogger(__name__)


class ModeSelectorWidget(ttk.Frame):
    """モード選択ウィジェット

    システムの動作モードを選択するためのGUIウィジェットです。
    """

    def __init__(self, parent, mode_manager, on_mode_changed=None):
        """モード選択ウィジェットを初期化

        Args:
            parent: 親ウィジェット
            mode_manager: モード管理オブジェクト
            on_mode_changed: モード変更時のコールバック関数
        """
        super().__init__(parent)
        self.mode_manager = mode_manager
        self.on_mode_changed_callback = on_mode_changed

        self.setup_ui()
        logger.debug("モード選択ウィジェットを初期化しました")

    def setup_ui(self):
        """UIの初期化"""
        # モード選択用の変数
        self.mode_var = tk.StringVar(value=self.mode_manager.get_current_mode())

        # ラジオボタンでモード選択
        modes = [
            ("Kiro-IDEモード", "kiro", "Kiro-IDEのエラー検出・復旧のみ"),
            ("AmazonQモード", "amazonq", "AmazonQの▶RUNボタン検出・クリックのみ"),
            ("自動モード", "auto", "両方の機能を自動判定で実行"),
        ]

        for i, (text, mode, description) in enumerate(modes):
            # ラジオボタン
            rb = ttk.Radiobutton(
                self,
                text=text,
                variable=self.mode_var,
                value=mode,
                command=self.on_mode_changed,
            )
            rb.grid(row=i, column=0, padx=10, pady=2, sticky=tk.W)

            # 説明ラベル
            desc_label = ttk.Label(
                self, text=f"  {description}", font=("", 8), foreground="gray"
            )
            desc_label.grid(row=i, column=1, padx=10, pady=2, sticky=tk.W)

        # モード状態表示ラベル
        self.mode_status_label = ttk.Label(self, text="", font=("", 9, "bold"))
        self.mode_status_label.grid(
            row=len(modes), column=0, columnspan=2, padx=10, pady=10, sticky=tk.W
        )

        self.update_mode_status()

    def on_mode_changed(self):
        """モード変更時の処理"""
        new_mode = self.mode_var.get()

        try:
            if self.mode_manager.switch_mode(new_mode):
                self.update_mode_status()
                logger.info(f"モード切り替え成功: {new_mode}")

                # コールバック関数を呼び出し
                if self.on_mode_changed_callback:
                    self.on_mode_changed_callback(new_mode)

            else:
                # 切り替え失敗時は元のモードに戻す
                self.mode_var.set(self.mode_manager.get_current_mode())
                messagebox.showerror(
                    "エラー", f"モードの切り替えに失敗しました: {new_mode}"
                )
                logger.error(f"モード切り替え失敗: {new_mode}")

        except Exception as e:
            # エラー時は元のモードに戻す
            self.mode_var.set(self.mode_manager.get_current_mode())
            messagebox.showerror("エラー", f"モード切り替えエラー: {e}")
            logger.error(f"モード切り替えエラー: {e}", exc_info=True)

    def update_mode_status(self):
        """モード状態の更新"""
        try:
            status = self.mode_manager.get_mode_status()
            current_mode = status["current_mode"]
            active_detectors = status["active_detectors"]

            # モード名の日本語変換
            mode_names = {
                "kiro": "Kiro-IDEモード",
                "amazonq": "AmazonQモード",
                "auto": "自動モード",
            }

            mode_display = mode_names.get(current_mode, current_mode)
            detectors_display = (
                ", ".join(active_detectors) if active_detectors else "なし"
            )

            status_text = (
                f"現在: {mode_display} | アクティブ検出器: {detectors_display}"
            )
            self.mode_status_label.config(text=status_text)

        except Exception as e:
            logger.error(f"モード状態更新エラー: {e}")
            self.mode_status_label.config(text="状態取得エラー")

    def refresh_mode(self):
        """モード状態を強制更新"""
        current_mode = self.mode_manager.get_current_mode()
        self.mode_var.set(current_mode)
        self.update_mode_status()
        logger.debug(f"モード状態を更新: {current_mode}")

    def get_current_mode(self) -> str:
        """現在選択されているモードを取得

        Returns:
            str: 現在のモード
        """
        return self.mode_var.get()

    def set_enabled(self, enabled: bool):
        """ウィジェットの有効/無効を設定

        Args:
            enabled: 有効にする場合True
        """
        state = tk.NORMAL if enabled else tk.DISABLED

        for child in self.winfo_children():
            if isinstance(child, ttk.Radiobutton):
                child.config(state=state)

        logger.debug(f"モード選択ウィジェット状態変更: {'有効' if enabled else '無効'}")
