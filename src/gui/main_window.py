"""
メインウィンドウ
既存のKiro-IDE復旧機能を統合したGUI（tkinter版）
"""

import logging
import tkinter as tk
from tkinter import messagebox
from tkinter import simpledialog
from tkinter import ttk

from src.config.config_manager import ConfigManager
from src.core.kiro_recovery import KiroRecovery
from src.gui.log_viewer import LogViewer
from src.gui.monitor_area_dialog import MonitorAreaDialog
from src.gui.monitor_widget import MonitorWidget
from src.gui.settings_dialog import SettingsDialog
from src.gui.template_manager import TemplateManager
from src.utils.hotkey_manager import HotkeyManager
from src.utils.output_controller import output_controller

logger = logging.getLogger(__name__)


class MainWindow:
    """メインウィンドウ - 統合GUI（tkinter版）"""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.config_manager = ConfigManager("config.local.json")
        self.kiro_recovery = KiroRecovery(self.config_manager)
        self.mode_manager = self.kiro_recovery.mode_manager
        self.hotkey_manager = HotkeyManager()

        self.setup_ui()
        self.setup_menu()
        self.setup_hotkeys()
        self.setup_timers()
        self.setup_output_controller()

        logger.info("メインウィンドウを初期化しました")

    def setup_mode_selector(self) -> None:
        """モード選択ウィジェットのセットアップ"""
        # モード選択用の変数
        self.mode_var = tk.StringVar(value=self.mode_manager.get_current_mode())

        # ラジオボタンでモード選択
        modes = [
            ("Kiro-IDEモード", "kiro"),
            ("AmazonQモード", "amazonq"),
            ("自動モード", "auto"),
        ]

        for i, (text, mode) in enumerate(modes):
            rb = ttk.Radiobutton(
                self.mode_frame,
                text=text,
                variable=self.mode_var,
                value=mode,
                command=self.on_mode_changed,
            )
            rb.grid(row=0, column=i, padx=10, pady=5, sticky=tk.W)

        # モード状態表示ラベル
        self.mode_status_label = ttk.Label(self.mode_frame, text="")
        self.mode_status_label.grid(
            row=1, column=0, columnspan=3, padx=10, pady=5, sticky=tk.W
        )

        self.update_mode_status()

    def on_mode_changed(self) -> None:
        """モード変更時の処理"""
        new_mode = self.mode_var.get()
        if self.mode_manager.switch_mode(new_mode):
            self.monitor_widget.add_log(f"モードを切り替えました: {new_mode}")
            self.update_mode_status()
            logger.info(f"モード切り替え: {new_mode}")
        else:
            # 切り替え失敗時は元のモードに戻す
            self.mode_var.set(self.mode_manager.get_current_mode())
            messagebox.showerror(
                "エラー", f"モードの切り替えに失敗しました: {new_mode}"
            )

    def update_mode_status(self) -> None:
        """モード状態の更新"""
        status = self.mode_manager.get_mode_status()
        current_mode = status["current_mode"]
        active_detectors = status["active_detectors"]

        status_text = f"現在のモード: {current_mode} | アクティブな検出器: {', '.join(active_detectors) if active_detectors else 'なし'}"
        self.mode_status_label.config(text=status_text)

    def setup_ui(self) -> None:
        """UIの初期化"""
        # メインフレーム
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # モード選択フレーム
        self.mode_frame = ttk.LabelFrame(self.main_frame, text="動作モード")
        self.mode_frame.pack(fill=tk.X, pady=(0, 10))
        self.setup_mode_selector()

        # 監視状態ウィジェット
        self.monitor_widget = MonitorWidget(self.main_frame)
        self.monitor_widget.pack(fill=tk.BOTH, expand=True)

        # シグナルの接続（tkinterでは直接メソッド呼び出し）
        self.monitor_widget.set_callbacks(
            self.start_monitoring,
            self.stop_monitoring,
            self.save_template,
            self.send_recovery_command,
            self.open_monitor_area_settings,
            self.save_template_with_selection,  # 範囲選択コールバックを追加
        )

    def setup_menu(self) -> None:
        """メニューバーの設定"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # ファイルメニュー
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ファイル", menu=file_menu)

        # 設定アクション
        file_menu.add_command(
            label="設定", command=self.open_settings, accelerator="Ctrl+,"
        )
        file_menu.add_separator()
        file_menu.add_command(
            label="終了", command=self.root.quit, accelerator="Ctrl+Q"
        )

        # ツールメニュー
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ツール", menu=tools_menu)

        tools_menu.add_command(
            label="テンプレート管理", command=self.open_template_manager
        )
        tools_menu.add_command(label="ログ表示", command=self.show_logs)
        tools_menu.add_separator()
        tools_menu.add_command(
            label="監視エリア設定", command=self.open_monitor_area_settings
        )
        tools_menu.add_command(label="AmazonQ設定", command=self.open_amazonq_settings)
        tools_menu.add_separator()
        tools_menu.add_command(label="出力制御", command=self.show_output_control)

        # ヘルプメニュー
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ヘルプ", menu=help_menu)

        help_menu.add_command(label="ホットキー一覧", command=self.show_hotkey_list)
        help_menu.add_command(label="バージョン情報", command=self.show_about)

    def setup_hotkeys(self) -> None:
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

    def setup_timers(self) -> None:
        """タイマーの設定"""
        # 状態更新タイマー
        self.update_status()

    def setup_output_controller(self) -> None:
        """出力制御システムの設定"""
        try:
            # 出力制御システムを初期化
            output_controller.info("出力制御システムを初期化しました", "main_window")
            logger.debug("出力制御システムを設定しました")
        except Exception as e:
            logger.error(f"出力制御システム設定エラー: {e}")

    def update_status(self) -> None:
        """状態の更新"""
        try:
            # KiroRecoveryの状態を取得
            status = self.kiro_recovery.get_status()

            # 監視ウィジェットの状態を更新
            self.monitor_widget.update_status(status)

            # モード状態も更新
            self.update_mode_status()

        except Exception as e:
            logger.error(f"状態更新エラー: {e}")

        # 1秒後に再度実行
        self.root.after(1000, self.update_status)

    def start_monitoring(self) -> None:
        """監視開始"""
        try:
            if self.kiro_recovery.start_monitoring():
                self.monitor_widget.add_log("監視を開始しました")
                output_controller.info("監視を開始しました", "main_window")
            else:
                self.monitor_widget.add_log("監視の開始に失敗しました")
                messagebox.showwarning("警告", "監視の開始に失敗しました")
                output_controller.error("監視の開始に失敗しました", "main_window")
        except Exception as e:
            self.monitor_widget.add_log(f"監視開始エラー: {e}")
            messagebox.showerror("エラー", f"監視開始エラー: {e}")
            output_controller.error(f"監視開始エラー: {e}", "main_window")

    def stop_monitoring(self) -> None:
        """監視停止"""
        try:
            self.kiro_recovery.stop_monitoring()
            self.monitor_widget.add_log("監視を停止しました")
            output_controller.info("監視を停止しました", "main_window")
        except Exception as e:
            self.monitor_widget.add_log(f"監視停止エラー: {e}")
            output_controller.error(f"監視停止エラー: {e}", "main_window")

    def save_template(self) -> None:
        """テンプレート保存（現在のモードに応じたテンプレートを保存）"""
        try:
            # 現在のモードを取得
            current_mode = self.mode_manager.get_current_mode()

            # モードに応じたメッセージを表示
            if current_mode == "amazonq":
                dialog_title = "AmazonQテンプレート保存"
                dialog_message = "▶RUNボタンテンプレート名を入力してください:"
            else:
                dialog_title = "Kiroエラーテンプレート保存"
                dialog_message = "エラーテンプレート名を入力してください:"

            # テンプレート名の入力
            template_name = simpledialog.askstring(dialog_title, dialog_message)

            if template_name:
                if self.kiro_recovery.save_error_template(template_name):
                    if current_mode == "amazonq":
                        success_msg = f"AmazonQテンプレート '{template_name}' をamazonq_templates/に保存しました"
                    else:
                        success_msg = f"Kiroテンプレート '{template_name}' をerror_templates/に保存しました"

                    self.monitor_widget.add_log(success_msg)
                    logger.info(success_msg)
                else:
                    error_msg = f"テンプレート '{template_name}' の保存に失敗しました"
                    self.monitor_widget.add_log(error_msg)
                    messagebox.showwarning("警告", error_msg)
                    logger.error(error_msg)
        except Exception as e:
            self.monitor_widget.add_log(f"テンプレート保存エラー: {e}")
            messagebox.showerror("エラー", f"テンプレート保存エラー: {e}")
            logger.error(f"テンプレート保存エラー: {e}")

    def save_template_with_selection(self) -> None:
        """範囲選択でテンプレート保存（テンプレート管理と同じ処理）"""
        try:
            from src.gui.template_manager import TemplateManager

            # テンプレート管理を開く
            template_manager = TemplateManager(self.root, self.config_manager)

            # 現在のモードに応じてアクティブタブを設定
            current_mode = self.mode_manager.get_current_mode()
            if current_mode == "amazonq":
                template_manager.set_active_tab("amazonq")
            else:
                template_manager.set_active_tab("kiro")

            template_manager.show()

            # 範囲選択を直接呼び出し
            if current_mode == "amazonq":
                template_manager.add_amazonq_template_with_selection()
            else:
                template_manager.add_template_with_selection()

        except Exception as e:
            logger.error(f"範囲選択テンプレート保存エラー: {e}")
            messagebox.showerror(
                "エラー", f"範囲選択テンプレートの保存に失敗しました: {e}"
            )

    def send_recovery_command(self) -> None:
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

    def open_settings(self) -> None:
        """設定ダイアログを開く"""
        try:
            settings_dialog = SettingsDialog(self.root, self.config_manager)
            settings_dialog.show()
            logger.info("設定ダイアログを開きました")
        except Exception as e:
            logger.error(f"設定ダイアログ表示エラー: {e}")
            messagebox.showerror("エラー", f"設定ダイアログの表示に失敗しました: {e}")

    def open_template_manager(self) -> None:
        """テンプレート管理を開く（現在のモードに応じたタブをアクティブに）"""
        try:
            template_manager = TemplateManager(self.root, self.config_manager)

            # 現在のモードに応じてアクティブタブを設定
            current_mode = self.mode_manager.get_current_mode()
            if current_mode == "amazonq":
                # AmazonQモードの場合はAmazonQタブをアクティブに
                template_manager.set_active_tab("amazonq")
                logger.info("AmazonQテンプレート管理を開きました")
            else:
                # Kiroモードまたは自動モードの場合はKiro-IDEタブをアクティブに
                template_manager.set_active_tab("kiro")
                logger.info("Kiro-IDEテンプレート管理を開きました")

            template_manager.show()

        except Exception as e:
            logger.error(f"テンプレート管理表示エラー: {e}")
            messagebox.showerror("エラー", f"テンプレート管理の表示に失敗しました: {e}")

    def show_logs(self) -> None:
        """ログ表示"""
        try:
            log_viewer = LogViewer(self.root)
            log_viewer.show()  # type: ignore[no-untyped-call]
            output_controller.info("ログ表示を開きました", "main_window")
        except Exception as e:
            output_controller.error(f"ログ表示表示エラー: {e}", "main_window")
            messagebox.showerror("エラー", f"ログ表示の表示に失敗しました: {e}")

    def show_output_control(self) -> None:
        """出力制御ダイアログを表示"""
        try:
            from src.gui.log_viewer import OutputControlDialog

            control_dialog = OutputControlDialog(self.root, output_controller)  # type: ignore[arg-type]
            control_dialog.show()  # type: ignore[no-untyped-call]
            output_controller.info("出力制御ダイアログを開きました", "main_window")
        except Exception as e:
            output_controller.error(f"出力制御ダイアログ表示エラー: {e}", "main_window")
            messagebox.showerror(
                "エラー", f"出力制御ダイアログの表示に失敗しました: {e}"
            )

    def open_monitor_area_settings(self) -> None:
        """監視エリア設定を開く"""
        try:
            monitor_area_dialog = MonitorAreaDialog(self.root, self.config_manager)
            monitor_area_dialog.show()  # type: ignore[no-untyped-call]
            logger.info("監視エリア設定を開きました")
        except Exception as e:
            logger.error(f"監視エリア設定表示エラー: {e}")
            messagebox.showerror("エラー", f"監視エリア設定の表示に失敗しました: {e}")

    def open_amazonq_settings(self) -> None:
        """AmazonQ設定ダイアログを開く"""
        try:
            from src.gui.amazonq_settings_dialog import AmazonQSettingsDialog

            amazonq_dialog = AmazonQSettingsDialog(self.root, self.config_manager)
            amazonq_dialog.show()
            logger.info("AmazonQ設定ダイアログを開きました")
        except Exception as e:
            logger.error(f"AmazonQ設定ダイアログ表示エラー: {e}")
            messagebox.showerror(
                "エラー", f"AmazonQ設定ダイアログの表示に失敗しました: {e}"
            )

    def show_hotkey_list(self) -> None:
        """ホットキー一覧表示"""
        hotkeys = self.hotkey_manager.get_default_hotkeys()
        hotkey_text = "\n".join([f"{key}: {desc}" for key, desc in hotkeys.items()])

        messagebox.showinfo("ホットキー一覧", f"利用可能なホットキー:\n\n{hotkey_text}")
        logger.info("ホットキー一覧を表示しました")

    def show_about(self) -> None:
        """バージョン情報表示"""
        about_text = """AI reStarter - AI-IDE自動復旧システム

バージョン: 0.1.0
開発者: AI Development Team

既存のAI-IDE自動復旧システムを
統合GUIで操作できるようにリファクタリングしたバージョンです。"""

        messagebox.showinfo("バージョン情報", about_text)
        logger.info("バージョン情報を表示しました")

    # ホットキーハンドラー
    def hotkey_save_template(self) -> None:
        """ホットキー: テンプレート保存（現在のモードに応じたテンプレート）"""
        current_mode = self.mode_manager.get_current_mode()
        mode_name = "AmazonQ" if current_mode == "amazonq" else "Kiro"
        self.monitor_widget.add_log(f"ホットキー: {mode_name}テンプレート保存要求")
        self.save_template()

    def hotkey_send_recovery(self) -> None:
        """ホットキー: 復旧コマンド送信"""
        self.monitor_widget.add_log("ホットキー: 復旧コマンド送信要求")
        self.send_recovery_command()

    def hotkey_toggle_pause(self) -> None:
        """ホットキー: 一時停止/再開"""
        if self.kiro_recovery.monitoring:
            self.stop_monitoring()
            self.monitor_widget.add_log("ホットキー: 監視を一時停止しました")
        else:
            self.start_monitoring()
            self.monitor_widget.add_log("ホットキー: 監視を再開しました")

    def hotkey_stop_monitoring(self) -> None:
        """ホットキー: 監視停止"""
        self.monitor_widget.add_log("ホットキー: 監視停止要求")
        self.stop_monitoring()

    def on_closing(self) -> None:
        """ウィンドウクローズ時の処理"""
        try:
            # 監視を停止
            if self.kiro_recovery.monitoring:
                self.kiro_recovery.stop_monitoring()

            # ホットキーをクリア
            self.hotkey_manager.clear_hotkeys()

            # 出力制御システムをリセット
            output_controller.restore_stdout()

            output_controller.info("メインウィンドウを閉じました", "main_window")
            self.root.destroy()

        except Exception as e:
            output_controller.error(f"ウィンドウクローズエラー: {e}", "main_window")
            self.root.destroy()
