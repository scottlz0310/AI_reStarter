"""
設定ダイアログ
既存の設定管理機能をGUIで操作
"""

import logging
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk
from typing import Any

from src.config.config_manager import ConfigManager

logger = logging.getLogger(__name__)


class SettingsDialog:
    """設定ダイアログ"""

    def __init__(self, parent: tk.Tk, config_manager: ConfigManager):
        self.parent = parent
        self.config_manager = config_manager
        self.dialog = None

        logger.debug("設定ダイアログを初期化しました")

    def show(self):
        """設定ダイアログを表示"""
        try:
            # ダイアログウィンドウの作成
            self.dialog = tk.Toplevel(self.parent)
            self.dialog.title("設定 - AI reStarter")
            self.dialog.geometry("600x500")
            self.dialog.transient(self.parent)
            self.dialog.grab_set()

            # ダイアログの位置を親ウィンドウの中央に設定
            x_pos = self.parent.winfo_rootx() + 50
            y_pos = self.parent.winfo_rooty() + 50
            self.dialog.geometry(f"+{x_pos}+{y_pos}")

            self.setup_ui()
            self.load_current_settings()

            logger.info("設定ダイアログを表示しました")

        except Exception as e:
            logger.error(f"設定ダイアログ表示エラー: {e}")
            messagebox.showerror("エラー", f"設定ダイアログの表示に失敗しました: {e}")

    def setup_ui(self):
        """UIの初期化"""
        # メインフレーム
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 設定項目の作成
        self.create_general_settings(main_frame)
        self.create_monitoring_settings(main_frame)
        self.create_recovery_settings(main_frame)
        self.create_hotkey_settings(main_frame)

        # ボタンフレーム
        self.create_button_frame(main_frame)

    def create_general_settings(self, parent):
        """一般設定セクション"""
        frame = ttk.LabelFrame(parent, text="一般設定", padding="10")
        frame.pack(fill=tk.X, pady=(0, 10))

        # ログレベル設定
        ttk.Label(frame, text="ログレベル:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.log_level_var = tk.StringVar(value="INFO")
        log_level_combo = ttk.Combobox(frame, textvariable=self.log_level_var,
                                     values=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                                     state="readonly", width=15)
        log_level_combo.grid(row=0, column=1, sticky=tk.W)

        # 自動起動設定
        self.auto_start_var = tk.BooleanVar(value=False)
        auto_start_check = ttk.Checkbutton(frame, text="起動時に自動で監視を開始",
                                         variable=self.auto_start_var)
        auto_start_check.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))

    def create_monitoring_settings(self, parent):
        """監視設定セクション"""
        frame = ttk.LabelFrame(parent, text="監視設定", padding="10")
        frame.pack(fill=tk.X, pady=(0, 10))

        # 監視間隔設定
        ttk.Label(frame, text="監視間隔 (秒):").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.monitor_interval_var = tk.StringVar(value="2.0")
        monitor_interval_entry = ttk.Entry(frame, textvariable=self.monitor_interval_var, width=10)
        monitor_interval_entry.grid(row=0, column=1, sticky=tk.W)

        # スクリーンショット保存設定
        self.save_screenshots_var = tk.BooleanVar(value=True)
        save_screenshots_check = ttk.Checkbutton(frame, text="エラー時にスクリーンショットを保存",
                                               variable=self.save_screenshots_var)
        save_screenshots_check.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))

        # スクリーンショット保存先
        ttk.Label(frame, text="保存先フォルダ:").grid(row=2, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        self.screenshot_folder_var = tk.StringVar(value="error_templates")
        screenshot_folder_entry = ttk.Entry(frame, textvariable=self.screenshot_folder_var, width=30)
        screenshot_folder_entry.grid(row=2, column=1, sticky=tk.W, pady=(10, 0))

    def create_recovery_settings(self, parent):
        """復旧設定セクション"""
        frame = ttk.LabelFrame(parent, text="復旧設定", padding="10")
        frame.pack(fill=tk.X, pady=(0, 10))

        # 最大復旧試行回数
        ttk.Label(frame, text="最大復旧試行回数:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.max_recovery_attempts_var = tk.StringVar(value="3")
        max_recovery_attempts_entry = ttk.Entry(frame, textvariable=self.max_recovery_attempts_var, width=10)
        max_recovery_attempts_entry.grid(row=0, column=1, sticky=tk.W)

        # 復旧間隔設定
        ttk.Label(frame, text="復旧間隔 (秒):").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        self.recovery_interval_var = tk.StringVar(value="5.0")
        recovery_interval_entry = ttk.Entry(frame, textvariable=self.recovery_interval_var, width=10)
        recovery_interval_entry.grid(row=1, column=1, sticky=tk.W, pady=(10, 0))

        # 自動復旧設定
        self.auto_recovery_var = tk.BooleanVar(value=True)
        auto_recovery_check = ttk.Checkbutton(frame, text="エラー検出時に自動で復旧を実行",
                                            variable=self.auto_recovery_var)
        auto_recovery_check.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))

    def create_hotkey_settings(self, parent):
        """ホットキー設定セクション"""
        frame = ttk.LabelFrame(parent, text="ホットキー設定", padding="10")
        frame.pack(fill=tk.X, pady=(0, 10))

        # ホットキーの有効/無効設定
        self.hotkey_enabled_var = tk.BooleanVar(value=True)
        hotkey_enabled_check = ttk.Checkbutton(frame, text="ホットキーを有効にする",
                                             variable=self.hotkey_enabled_var)
        hotkey_enabled_check.grid(row=0, column=0, columnspan=2, sticky=tk.W)

        # ホットキー一覧表示
        hotkey_info = """
利用可能なホットキー:
• Ctrl+Alt+S: テンプレート保存
• Ctrl+Alt+R: 復旧コマンド送信
• Ctrl+Alt+P: 監視一時停止/再開
• Ctrl+Alt+Q: 監視停止
        """
        hotkey_label = ttk.Label(frame, text=hotkey_info, justify=tk.LEFT)
        hotkey_label.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))

    def create_button_frame(self, parent):
        """ボタンフレームの作成"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(20, 0))

        # 保存ボタン
        save_button = ttk.Button(button_frame, text="保存", command=self.save_settings)
        save_button.pack(side=tk.RIGHT, padx=(5, 0))

        # キャンセルボタン
        cancel_button = ttk.Button(button_frame, text="キャンセル", command=self.cancel)
        cancel_button.pack(side=tk.RIGHT)

        # デフォルト復元ボタン
        restore_button = ttk.Button(button_frame, text="デフォルト復元", command=self.restore_defaults)
        restore_button.pack(side=tk.LEFT)

    def load_current_settings(self):
        """現在の設定を読み込み"""
        try:
            # 設定値を読み込み
            self.log_level_var.set(self.config_manager.get("log_level", "INFO"))
            self.auto_start_var.set(self.config_manager.get("auto_start", False))
            self.monitor_interval_var.set(str(self.config_manager.get("monitor_interval", 2.0)))
            self.save_screenshots_var.set(self.config_manager.get("save_screenshots", True))
            self.screenshot_folder_var.set(self.config_manager.get("screenshot_folder", "error_templates"))
            self.max_recovery_attempts_var.set(str(self.config_manager.get("max_recovery_attempts", 3)))
            self.recovery_interval_var.set(str(self.config_manager.get("recovery_interval", 5.0)))
            self.auto_recovery_var.set(self.config_manager.get("auto_recovery", True))
            self.hotkey_enabled_var.set(self.config_manager.get("hotkey_enabled", True))

            logger.debug("現在の設定を読み込みました")

        except Exception as e:
            logger.error(f"設定読み込みエラー: {e}")
            messagebox.showerror("エラー", f"設定の読み込みに失敗しました: {e}")

    def save_settings(self):
        """設定を保存"""
        try:
            # 設定値を収集
            new_settings = {
                "log_level": self.log_level_var.get(),
                "auto_start": self.auto_start_var.get(),
                "monitor_interval": float(self.monitor_interval_var.get()),
                "save_screenshots": self.save_screenshots_var.get(),
                "screenshot_folder": self.screenshot_folder_var.get(),
                "max_recovery_attempts": int(self.max_recovery_attempts_var.get()),
                "recovery_interval": float(self.recovery_interval_var.get()),
                "auto_recovery": self.auto_recovery_var.get(),
                "hotkey_enabled": self.hotkey_enabled_var.get(),
            }

            # 設定を更新
            for key, value in new_settings.items():
                self.config_manager.set(key, value)

            # 設定ファイルに保存
            self.config_manager.save_config()

            messagebox.showinfo("完了", "設定を保存しました")
            logger.info("設定を保存しました")

            # ダイアログを閉じる
            self.dialog.destroy()

        except ValueError as e:
            logger.error(f"設定値の検証エラー: {e}")
            messagebox.showerror("エラー", "無効な設定値が入力されています。数値フィールドには数値を入力してください。")
        except Exception as e:
            logger.error(f"設定保存エラー: {e}")
            messagebox.showerror("エラー", f"設定の保存に失敗しました: {e}")

    def restore_defaults(self):
        """デフォルト設定を復元"""
        try:
            # デフォルト設定を復元
            self.config_manager.create_sample_config()
            self.config_manager.reload_config()

            # UIを更新
            self.load_current_settings()

            messagebox.showinfo("完了", "デフォルト設定を復元しました")
            logger.info("デフォルト設定を復元しました")

        except Exception as e:
            logger.error(f"デフォルト設定復元エラー: {e}")
            messagebox.showerror("エラー", f"デフォルト設定の復元に失敗しました: {e}")

    def cancel(self):
        """キャンセル処理"""
        logger.info("設定ダイアログをキャンセルしました")
        self.dialog.destroy()
