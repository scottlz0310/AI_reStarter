"""
AmazonQ設定ダイアログ

このモジュールは、AmazonQ機能の詳細設定を行うダイアログを提供します。
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import logging

logger = logging.getLogger(__name__)


class AmazonQSettingsDialog:
    """AmazonQ用設定ダイアログ"""
    
    def __init__(self, parent, config_manager):
        self.parent = parent
        self.config_manager = config_manager
        self.dialog = None
        
        # 設定値を保持する変数
        self.enabled_var = tk.BooleanVar()
        self.detection_threshold_var = tk.DoubleVar()
        self.click_delay_var = tk.DoubleVar()
        self.templates_dir_var = tk.StringVar()
        
        logger.debug("AmazonQ設定ダイアログを初期化しました")
    
    def show(self):
        """ダイアログを表示"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("AmazonQ設定")
        self.dialog.geometry("500x400")
        self.dialog.resizable(False, False)
        
        # モーダルダイアログに設定
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        self.setup_ui()
        self.load_settings()
        
        # ダイアログを中央に配置
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (self.dialog.winfo_width() // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (self.dialog.winfo_height() // 2)
        self.dialog.geometry(f"+{x}+{y}")
        
        logger.info("AmazonQ設定ダイアログを表示しました")
    
    def setup_ui(self):
        """UIの初期化"""
        # メインフレーム
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # 基本設定セクション
        basic_frame = ttk.LabelFrame(main_frame, text="基本設定")
        basic_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 有効/無効チェックボックス
        ttk.Checkbutton(
            basic_frame,
            text="AmazonQ機能を有効にする",
            variable=self.enabled_var
        ).grid(row=0, column=0, columnspan=2, padx=10, pady=10, sticky=tk.W)
        
        # 検出設定セクション
        detection_frame = ttk.LabelFrame(main_frame, text="検出設定")
        detection_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 検出閾値
        ttk.Label(detection_frame, text="検出閾値:").grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)
        threshold_frame = ttk.Frame(detection_frame)
        threshold_frame.grid(row=0, column=1, padx=10, pady=5, sticky=tk.W)
        
        ttk.Scale(
            threshold_frame,
            from_=0.1,
            to=1.0,
            variable=self.detection_threshold_var,
            orient=tk.HORIZONTAL,
            length=200
        ).pack(side=tk.LEFT)
        
        self.threshold_label = ttk.Label(threshold_frame, text="0.8")
        self.threshold_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # 閾値変更時のコールバック
        self.detection_threshold_var.trace('w', self.on_threshold_changed)
        
        # クリック遅延
        ttk.Label(detection_frame, text="クリック遅延 (秒):").grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)
        ttk.Spinbox(
            detection_frame,
            from_=0.1,
            to=5.0,
            increment=0.1,
            textvariable=self.click_delay_var,
            width=10
        ).grid(row=1, column=1, padx=10, pady=5, sticky=tk.W)
        
        # ボタンフレーム
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(
            button_frame,
            text="OK",
            command=self.on_ok
        ).pack(side=tk.RIGHT, padx=(5, 0))
        
        ttk.Button(
            button_frame,
            text="キャンセル",
            command=self.on_cancel
        ).pack(side=tk.RIGHT)
    
    def load_settings(self):
        """設定値を読み込み"""
        try:
            # 現在の設定値を取得
            self.enabled_var.set(self.config_manager.get("amazonq.enabled", True))
            self.detection_threshold_var.set(self.config_manager.get("amazonq.detection_threshold", 0.8))
            self.click_delay_var.set(self.config_manager.get("amazonq.click_delay", 1.0))
            self.templates_dir_var.set(self.config_manager.get("amazonq.run_button_templates_dir", "amazonq_templates"))
            
            # 閾値ラベルを更新
            self.on_threshold_changed()
            
            logger.debug("AmazonQ設定を読み込みました")
            
        except Exception as e:
            logger.error(f"設定読み込みエラー: {e}")
            messagebox.showerror("エラー", f"設定の読み込みに失敗しました: {e}")
    
    def on_threshold_changed(self, *args):
        """検出閾値変更時の処理"""
        threshold = self.detection_threshold_var.get()
        self.threshold_label.config(text=f"{threshold:.2f}")
    
    def validate_settings(self) -> bool:
        """設定値の妥当性をチェック"""
        try:
            # 検出閾値のチェック
            threshold = self.detection_threshold_var.get()
            if not (0.1 <= threshold <= 1.0):
                messagebox.showerror("エラー", "検出閾値は0.1から1.0の間で設定してください")
                return False
            
            # クリック遅延のチェック
            delay = self.click_delay_var.get()
            if not (0.1 <= delay <= 5.0):
                messagebox.showerror("エラー", "クリック遅延は0.1から5.0秒の間で設定してください")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"設定値検証エラー: {e}")
            messagebox.showerror("エラー", f"設定値の検証中にエラーが発生しました: {e}")
            return False
    
    def save_settings(self) -> bool:
        """設定を保存"""
        try:
            # 設定値を更新
            amazonq_config = {
                "enabled": self.enabled_var.get(),
                "detection_threshold": self.detection_threshold_var.get(),
                "click_delay": self.click_delay_var.get(),
                "run_button_templates_dir": self.templates_dir_var.get().strip() if self.templates_dir_var.get() else "amazonq_templates"
            }
            
            # 既存のamazonq設定を取得して更新
            current_amazonq = self.config_manager.get("amazonq", {})
            current_amazonq.update(amazonq_config)
            
            self.config_manager.set("amazonq", current_amazonq)
            
            # 設定ファイルに保存
            if self.config_manager.save_config():
                logger.info("AmazonQ設定を保存しました")
                return True
            else:
                messagebox.showerror("エラー", "設定の保存に失敗しました")
                return False
                
        except Exception as e:
            logger.error(f"設定保存エラー: {e}")
            messagebox.showerror("エラー", f"設定の保存中にエラーが発生しました: {e}")
            return False
    
    def on_ok(self):
        """OKボタン押下時の処理"""
        if self.validate_settings():
            if self.save_settings():
                self.dialog.destroy()
                messagebox.showinfo("完了", "AmazonQ設定を保存しました")
    
    def on_cancel(self):
        """キャンセルボタン押下時の処理"""
        self.dialog.destroy()
        logger.debug("AmazonQ設定ダイアログをキャンセルしました")