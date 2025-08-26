"""
メインウィンドウ
既存のKiro-IDE復旧機能を統合したGUI（tkinter版）
"""

import logging
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

from src.config.config_manager import ConfigManager
from src.core.kiro_recovery import KiroRecovery
from src.utils.hotkey_manager import HotkeyManager
from src.gui.monitor_widget import MonitorWidget
from src.gui.settings_dialog import SettingsDialog
from src.gui.template_manager import TemplateManager
from src.gui.log_viewer import LogViewer
from src.gui.monitor_area_dialog import MonitorAreaDialog

logger = logging.getLogger(__name__)


class MainWindow:
    """メインウィンドウ - 統合GUI（tkinter版）"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.config_manager = ConfigManager()
        self.kiro_recovery = KiroRecovery(self.config_manager)
        self.hotkey_manager = HotkeyManager()
        
        self.setup_ui()
        self.setup_menu()
        self.setup_hotkeys()
        self.setup_timers()
        
        logger.info("メインウィンドウを初期化しました")
    
    def setup_ui(self):
        """UIの初期化"""
        # メインフレーム
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 監視状態ウィジェット
        self.monitor_widget = MonitorWidget(self.main_frame)
        self.monitor_widget.pack(fill=tk.BOTH, expand=True)
        
        # シグナルの接続（tkinterでは直接メソッド呼び出し）
        self.monitor_widget.set_callbacks(
            self.start_monitoring,
            self.stop_monitoring,
            self.save_template,
            self.send_recovery_command
        )
    
    def setup_menu(self):
        """メニューバーの設定"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # ファイルメニュー
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ファイル", menu=file_menu)
        
        # 設定アクション
        file_menu.add_command(label="設定", command=self.open_settings, accelerator="Ctrl+,")
        file_menu.add_separator()
        file_menu.add_command(label="終了", command=self.root.quit, accelerator="Ctrl+Q")
        
        # ツールメニュー
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ツール", menu=tools_menu)
        
        tools_menu.add_command(label="テンプレート管理", command=self.open_template_manager)
        tools_menu.add_command(label="ログ表示", command=self.show_logs)
        tools_menu.add_separator()
        tools_menu.add_command(label="監視エリア設定", command=self.open_monitor_area_settings)
        
        # ヘルプメニュー
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ヘルプ", menu=help_menu)
        
        help_menu.add_command(label="ホットキー一覧", command=self.show_hotkey_list)
        help_menu.add_command(label="バージョン情報", command=self.show_about)
    
    def setup_hotkeys(self):
        """ホットキーの設定"""
        hotkey_handlers = {
            "ctrl+alt+s": self.hotkey_save_template,
            "ctrl+alt+r": self.hotkey_send_recovery,
            "ctrl+alt+p": self.hotkey_toggle_pause,
            "ctrl+alt+q": self.hotkey_stop_monitoring,
        }
        
        if self.hotkey_manager.setup_hotkeys(hotkey_handlers):
            logger.info("ホットキーを設定しました")
        else:
            logger.warning("ホットキーの設定に失敗しました")
    
    def setup_timers(self):
        """タイマーの設定"""
        # 状態更新タイマー
        self.update_status()
    
    def update_status(self):
        """状態の更新"""
        try:
            # KiroRecoveryの状態を取得
            status = self.kiro_recovery.get_status()
            
            # 監視ウィジェットの状態を更新
            self.monitor_widget.update_status(status)
            
        except Exception as e:
            logger.error(f"状態更新エラー: {e}")
        
        # 1秒後に再度実行
        self.root.after(1000, self.update_status)
    
    def start_monitoring(self):
        """監視開始"""
        try:
            if self.kiro_recovery.start_monitoring():
                self.monitor_widget.add_log("監視を開始しました")
                logger.info("監視を開始しました")
            else:
                self.monitor_widget.add_log("監視の開始に失敗しました")
                messagebox.showwarning("警告", "監視の開始に失敗しました")
                logger.error("監視の開始に失敗しました")
        except Exception as e:
            self.monitor_widget.add_log(f"監視開始エラー: {e}")
            messagebox.showerror("エラー", f"監視開始エラー: {e}")
            logger.error(f"監視開始エラー: {e}")
    
    def stop_monitoring(self):
        """監視停止"""
        try:
            self.kiro_recovery.stop_monitoring()
            self.monitor_widget.add_log("監視を停止しました")
            logger.info("監視を停止しました")
        except Exception as e:
            self.monitor_widget.add_log(f"監視停止エラー: {e}")
            logger.error(f"監視停止エラー: {e}")
    
    def save_template(self):
        """テンプレート保存"""
        try:
            # テンプレート名の入力
            template_name = simpledialog.askstring("テンプレート保存", "テンプレート名を入力してください:")
            
            if template_name:
                if self.kiro_recovery.save_error_template(template_name):
                    self.monitor_widget.add_log(f"テンプレート '{template_name}' を保存しました")
                    logger.info(f"テンプレート '{template_name}' を保存しました")
                else:
                    self.monitor_widget.add_log(f"テンプレート '{template_name}' の保存に失敗しました")
                    messagebox.showwarning("警告", f"テンプレート '{template_name}' の保存に失敗しました")
                    logger.error(f"テンプレート '{template_name}' の保存に失敗しました")
        except Exception as e:
            self.monitor_widget.add_log(f"テンプレート保存エラー: {e}")
            messagebox.showerror("エラー", f"テンプレート保存エラー: {e}")
            logger.error(f"テンプレート保存エラー: {e}")
    
    def send_recovery_command(self):
        """復旧コマンド送信"""
        try:
            if self.kiro_recovery.send_recovery_command():
                self.monitor_widget.add_log("復旧コマンドを送信しました")
                logger.info("復旧コマンドを送信しました")
            else:
                self.monitor_widget.add_log("復旧コマンドの送信に失敗しました")
                messagebox.showwarning("警告", "復旧コマンドの送信に失敗しました")
                logger.error("復旧コマンドの送信に失敗しました")
        except Exception as e:
            self.monitor_widget.add_log(f"復旧コマンド送信エラー: {e}")
            messagebox.showerror("エラー", f"復旧コマンド送信エラー: {e}")
            logger.error(f"復旧コマンド送信エラー: {e}")
    
    def open_settings(self):
        """設定ダイアログを開く"""
        try:
            settings_dialog = SettingsDialog(self.root, self.config_manager)
            settings_dialog.show()
            logger.info("設定ダイアログを開きました")
        except Exception as e:
            logger.error(f"設定ダイアログ表示エラー: {e}")
            messagebox.showerror("エラー", f"設定ダイアログの表示に失敗しました: {e}")
    
    def open_template_manager(self):
        """テンプレート管理を開く"""
        try:
            template_manager = TemplateManager(self.root, self.config_manager)
            template_manager.show()
            logger.info("テンプレート管理を開きました")
        except Exception as e:
            logger.error(f"テンプレート管理表示エラー: {e}")
            messagebox.showerror("エラー", f"テンプレート管理の表示に失敗しました: {e}")
    
    def show_logs(self):
        """ログ表示"""
        try:
            log_viewer = LogViewer(self.root)
            log_viewer.show()
            logger.info("ログ表示を開きました")
        except Exception as e:
            logger.error(f"ログ表示表示エラー: {e}")
            messagebox.showerror("エラー", f"ログ表示の表示に失敗しました: {e}")
    
    def open_monitor_area_settings(self):
        """監視エリア設定を開く"""
        try:
            monitor_area_dialog = MonitorAreaDialog(self.root, self.config_manager)
            monitor_area_dialog.show()
            logger.info("監視エリア設定を開きました")
        except Exception as e:
            logger.error(f"監視エリア設定表示エラー: {e}")
            messagebox.showerror("エラー", f"監視エリア設定の表示に失敗しました: {e}")
    
    def show_hotkey_list(self):
        """ホットキー一覧表示"""
        hotkeys = self.hotkey_manager.get_default_hotkeys()
        hotkey_text = "\n".join([f"{key}: {desc}" for key, desc in hotkeys.items()])
        
        messagebox.showinfo("ホットキー一覧", f"利用可能なホットキー:\n\n{hotkey_text}")
        logger.info("ホットキー一覧を表示しました")
    
    def show_about(self):
        """バージョン情報表示"""
        about_text = """AI reStarter - Kiro-IDE自動復旧システム

バージョン: 0.1.0
開発者: Kiro Development Team

既存のKiro-IDE自動復旧システムを
統合GUIで操作できるようにリファクタリングしたバージョンです。"""
        
        messagebox.showinfo("バージョン情報", about_text)
        logger.info("バージョン情報を表示しました")
    
    # ホットキーハンドラー
    def hotkey_save_template(self):
        """ホットキー: テンプレート保存"""
        self.monitor_widget.add_log("ホットキー: テンプレート保存要求")
        self.save_template()
    
    def hotkey_send_recovery(self):
        """ホットキー: 復旧コマンド送信"""
        self.monitor_widget.add_log("ホットキー: 復旧コマンド送信要求")
        self.send_recovery_command()
    
    def hotkey_toggle_pause(self):
        """ホットキー: 一時停止/再開"""
        if self.kiro_recovery.monitoring:
            self.stop_monitoring()
            self.monitor_widget.add_log("ホットキー: 監視を一時停止しました")
        else:
            self.start_monitoring()
            self.monitor_widget.add_log("ホットキー: 監視を再開しました")
    
    def hotkey_stop_monitoring(self):
        """ホットキー: 監視停止"""
        self.monitor_widget.add_log("ホットキー: 監視停止要求")
        self.stop_monitoring()
    
    def on_closing(self):
        """ウィンドウクローズ時の処理"""
        try:
            # 監視を停止
            if self.kiro_recovery.monitoring:
                self.kiro_recovery.stop_monitoring()
            
            # ホットキーをクリア
            self.hotkey_manager.clear_hotkeys()
            
            logger.info("メインウィンドウを閉じました")
            self.root.destroy()
            
        except Exception as e:
            logger.error(f"ウィンドウクローズエラー: {e}")
            self.root.destroy()
