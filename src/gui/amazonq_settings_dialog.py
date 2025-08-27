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
    """AmazonQ用設定ダイアログ
    
    AmazonQ機能の設定を行うためのダイアログウィンドウです。
    """
    
    def __init__(self, parent, config_manager):
        """AmazonQ設定ダイアログを初期化
        
        Args:
            parent: 親ウィンドウ
            config_manager: 設定管理オブジェクト
        """
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
        
        self.threshold_label = ttk.Label(threshold_frame, text="0.8")\n        self.threshold_label.pack(side=tk.LEFT, padx=(10, 0))\n        \n        # 閾値変更時のコールバック\n        self.detection_threshold_var.trace('w', self.on_threshold_changed)\n        \n        # クリック遅延\n        ttk.Label(detection_frame, text=\"クリック遅延 (秒):\").grid(row=1, column=0, padx=10, pady=5, sticky=tk.W)\n        ttk.Spinbox(\n            detection_frame,\n            from_=0.1,\n            to=5.0,\n            increment=0.1,\n            textvariable=self.click_delay_var,\n            width=10\n        ).grid(row=1, column=1, padx=10, pady=5, sticky=tk.W)\n        \n        # テンプレート設定セクション\n        template_frame = ttk.LabelFrame(main_frame, text=\"テンプレート設定\")\n        template_frame.pack(fill=tk.X, pady=(0, 10))\n        \n        # テンプレートディレクトリ\n        ttk.Label(template_frame, text=\"テンプレートディレクトリ:\").grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)\n        \n        dir_frame = ttk.Frame(template_frame)\n        dir_frame.grid(row=0, column=1, padx=10, pady=5, sticky=tk.EW)\n        template_frame.columnconfigure(1, weight=1)\n        \n        ttk.Entry(\n            dir_frame,\n            textvariable=self.templates_dir_var,\n            width=30\n        ).pack(side=tk.LEFT, fill=tk.X, expand=True)\n        \n        ttk.Button(\n            dir_frame,\n            text=\"参照\",\n            command=self.browse_templates_dir\n        ).pack(side=tk.RIGHT, padx=(5, 0))\n        \n        # テンプレート管理ボタン\n        ttk.Button(\n            template_frame,\n            text=\"テンプレート管理\",\n            command=self.open_template_manager\n        ).grid(row=1, column=1, padx=10, pady=5, sticky=tk.E)\n        \n        # ボタンフレーム\n        button_frame = ttk.Frame(main_frame)\n        button_frame.pack(fill=tk.X, pady=(10, 0))\n        \n        ttk.Button(\n            button_frame,\n            text=\"OK\",\n            command=self.on_ok\n        ).pack(side=tk.RIGHT, padx=(5, 0))\n        \n        ttk.Button(\n            button_frame,\n            text=\"キャンセル\",\n            command=self.on_cancel\n        ).pack(side=tk.RIGHT)\n        \n        ttk.Button(\n            button_frame,\n            text=\"デフォルトに戻す\",\n            command=self.reset_to_defaults\n        ).pack(side=tk.LEFT)\n    \n    def load_settings(self):\n        \"\"\"設定値を読み込み\"\"\"\n        try:\n            # 現在の設定値を取得\n            self.enabled_var.set(self.config_manager.get(\"amazonq.enabled\", True))\n            self.detection_threshold_var.set(self.config_manager.get(\"amazonq.detection_threshold\", 0.8))\n            self.click_delay_var.set(self.config_manager.get(\"amazonq.click_delay\", 1.0))\n            self.templates_dir_var.set(self.config_manager.get(\"amazonq.run_button_templates_dir\", \"amazonq_templates\"))\n            \n            # 閾値ラベルを更新\n            self.on_threshold_changed()\n            \n            logger.debug(\"AmazonQ設定を読み込みました\")\n            \n        except Exception as e:\n            logger.error(f\"設定読み込みエラー: {e}\")\n            messagebox.showerror(\"エラー\", f\"設定の読み込みに失敗しました: {e}\")\n    \n    def on_threshold_changed(self, *args):\n        \"\"\"検出閾値変更時の処理\"\"\"\n        threshold = self.detection_threshold_var.get()\n        self.threshold_label.config(text=f\"{threshold:.2f}\")\n    \n    def browse_templates_dir(self):\n        \"\"\"テンプレートディレクトリを参照\"\"\"\n        current_dir = self.templates_dir_var.get()\n        if not os.path.exists(current_dir):\n            current_dir = os.getcwd()\n        \n        selected_dir = filedialog.askdirectory(\n            title=\"テンプレートディレクトリを選択\",\n            initialdir=current_dir\n        )\n        \n        if selected_dir:\n            self.templates_dir_var.set(selected_dir)\n            logger.debug(f\"テンプレートディレクトリを選択: {selected_dir}\")\n    \n    def open_template_manager(self):\n        \"\"\"テンプレート管理を開く\"\"\"\n        try:\n            from .template_manager import TemplateManager\n            template_manager = TemplateManager(self.dialog, self.config_manager)\n            template_manager.show()\n            logger.info(\"テンプレート管理を開きました\")\n        except Exception as e:\n            logger.error(f\"テンプレート管理表示エラー: {e}\")\n            messagebox.showerror(\"エラー\", f\"テンプレート管理の表示に失敗しました: {e}\")\n    \n    def reset_to_defaults(self):\n        \"\"\"デフォルト値に戻す\"\"\"\n        if messagebox.askyesno(\"確認\", \"設定をデフォルト値に戻しますか？\"):\n            self.enabled_var.set(True)\n            self.detection_threshold_var.set(0.8)\n            self.click_delay_var.set(1.0)\n            self.templates_dir_var.set(\"amazonq_templates\")\n            \n            logger.info(\"AmazonQ設定をデフォルト値に戻しました\")\n    \n    def validate_settings(self) -> bool:\n        \"\"\"設定値の妥当性をチェック\n        \n        Returns:\n            bool: 妥当な場合True\n        \"\"\"\n        try:\n            # 検出閾値のチェック\n            threshold = self.detection_threshold_var.get()\n            if not (0.1 <= threshold <= 1.0):\n                messagebox.showerror(\"エラー\", \"検出閾値は0.1から1.0の間で設定してください\")\n                return False\n            \n            # クリック遅延のチェック\n            delay = self.click_delay_var.get()\n            if not (0.1 <= delay <= 5.0):\n                messagebox.showerror(\"エラー\", \"クリック遅延は0.1から5.0秒の間で設定してください\")\n                return False\n            \n            # テンプレートディレクトリのチェック\n            templates_dir = self.templates_dir_var.get().strip()\n            if not templates_dir:\n                messagebox.showerror(\"エラー\", \"テンプレートディレクトリを指定してください\")\n                return False\n            \n            return True\n            \n        except Exception as e:\n            logger.error(f\"設定値検証エラー: {e}\")\n            messagebox.showerror(\"エラー\", f\"設定値の検証中にエラーが発生しました: {e}\")\n            return False\n    \n    def save_settings(self) -> bool:\n        \"\"\"設定を保存\n        \n        Returns:\n            bool: 保存成功/失敗\n        \"\"\"\n        try:\n            # 設定値を更新\n            amazonq_config = {\n                \"enabled\": self.enabled_var.get(),\n                \"detection_threshold\": self.detection_threshold_var.get(),\n                \"click_delay\": self.click_delay_var.get(),\n                \"run_button_templates_dir\": self.templates_dir_var.get().strip()\n            }\n            \n            # 既存のamazonq設定を取得して更新\n            current_amazonq = self.config_manager.get(\"amazonq\", {})\n            current_amazonq.update(amazonq_config)\n            \n            self.config_manager.set(\"amazonq\", current_amazonq)\n            \n            # 設定ファイルに保存\n            if self.config_manager.save_config():\n                logger.info(\"AmazonQ設定を保存しました\")\n                return True\n            else:\n                messagebox.showerror(\"エラー\", \"設定の保存に失敗しました\")\n                return False\n                \n        except Exception as e:\n            logger.error(f\"設定保存エラー: {e}\")\n            messagebox.showerror(\"エラー\", f\"設定の保存中にエラーが発生しました: {e}\")\n            return False\n    \n    def on_ok(self):\n        \"\"\"OKボタン押下時の処理\"\"\"\n        if self.validate_settings():\n            if self.save_settings():\n                self.dialog.destroy()\n                messagebox.showinfo(\"完了\", \"AmazonQ設定を保存しました\")\n    \n    def on_cancel(self):\n        \"\"\"キャンセルボタン押下時の処理\"\"\"\n        self.dialog.destroy()\n        logger.debug(\"AmazonQ設定ダイアログをキャンセルしました\")