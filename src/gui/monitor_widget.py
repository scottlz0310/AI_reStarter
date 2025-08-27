"""
監視状態ウィジェット
既存の監視状態を表示するGUIコンポーネント（tkinter版）
"""

import logging
import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class MonitorWidget(ttk.Frame):
    """監視状態を表示するウィジェット（tkinter版）"""

    def __init__(self, parent):
        super().__init__(parent)

        # コールバック関数
        self.start_callback: Optional[Callable] = None
        self.stop_callback: Optional[Callable] = None
        self.save_template_callback: Optional[Callable] = None
        self.send_recovery_callback: Optional[Callable] = None
        self.monitor_area_callback: Optional[Callable] = None
        self.save_template_with_selection_callback: Optional[Callable] = None

        self.setup_ui()
        logger.debug("監視状態ウィジェットを初期化しました")

    def setup_ui(self):
        """UIの初期化"""
        # 状態表示グループ
        self.setup_status_group()

        # 制御ボタングループ
        self.setup_control_group()

        # ログ表示グループ
        self.setup_log_group()

        # 進捗表示グループ
        self.setup_progress_group()

    def setup_status_group(self):
        """状態表示グループの設定"""
        self.status_group = ttk.LabelFrame(self, text="監視状態")
        self.status_group.pack(fill=tk.X, padx=5, pady=5)

        # 状態ラベル
        self.mode_label = ttk.Label(self.status_group, text="モード: Kiro-IDE")
        self.status_label = ttk.Label(self.status_group, text="状態: 停止中")
        self.template_count_label = ttk.Label(self.status_group, text="テンプレート: 0個")
        self.last_action_label = ttk.Label(self.status_group, text="最終アクション: なし")
        self.recovery_attempts_label = ttk.Label(self.status_group, text="復旧試行: 0/3")

        # ラベルをグリッドに配置
        self.mode_label.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        self.status_label.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        self.template_count_label.grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        self.last_action_label.grid(row=3, column=1, sticky=tk.W, padx=5, pady=2)
        self.recovery_attempts_label.grid(row=4, column=1, sticky=tk.W, padx=5, pady=2)

        # ラベルテキスト
        ttk.Label(self.status_group, text="モード:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Label(self.status_group, text="状態:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Label(self.status_group, text="テンプレート:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Label(self.status_group, text="最終アクション:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=2)
        ttk.Label(self.status_group, text="復旧試行:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=2)

    def setup_control_group(self):
        """制御ボタングループの設定"""
        self.control_group = ttk.LabelFrame(self, text="制御")
        self.control_group.pack(fill=tk.X, padx=5, pady=5)

        # ボタンフレームを先に作成
        button_frame1 = ttk.Frame(self.control_group)
        button_frame1.pack(fill=tk.X, padx=5, pady=2)
        
        button_frame2 = ttk.Frame(self.control_group)
        button_frame2.pack(fill=tk.X, padx=5, pady=2)
        
        # 制御ボタン（適切なフレームに配置）
        self.start_button = ttk.Button(button_frame1, text="監視開始", command=self._on_start_clicked)
        self.stop_button = ttk.Button(button_frame1, text="監視停止", command=self._on_stop_clicked)
        self.monitor_area_button = ttk.Button(button_frame1, text="監視エリア設定", command=self._on_monitor_area_clicked)
        
        self.save_template_button = ttk.Button(button_frame2, text="テンプレート保存", command=self._on_save_template_clicked)
        self.save_template_selection_button = ttk.Button(button_frame2, text="範囲選択で保存", command=self._on_save_template_with_selection_clicked)
        self.send_recovery_button = ttk.Button(button_frame2, text="復旧コマンド送信", command=self._on_send_recovery_clicked)

        # ボタンの初期状態設定
        self.stop_button.config(state="disabled")

        # ボタンをフレームに配置
        self.start_button.pack(side=tk.LEFT, padx=2)
        self.stop_button.pack(side=tk.LEFT, padx=2)
        self.monitor_area_button.pack(side=tk.LEFT, padx=2)
        
        self.save_template_button.pack(side=tk.LEFT, padx=2)
        self.save_template_selection_button.pack(side=tk.LEFT, padx=2)
        self.send_recovery_button.pack(side=tk.LEFT, padx=2)

    def setup_log_group(self):
        """ログ表示グループの設定"""
        self.log_group = ttk.LabelFrame(self, text="ログ")
        self.log_group.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # ログテキストエリア
        self.log_text = tk.Text(self.log_group, height=8, font=("Consolas", 9))
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # スクロールバー
        scrollbar = ttk.Scrollbar(self.log_group, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)

        # ログクリアボタン
        self.clear_log_button = ttk.Button(self.log_group, text="ログクリア", command=self.clear_log)
        self.clear_log_button.pack(pady=5)

    def setup_progress_group(self):
        """進捗表示グループの設定"""
        self.progress_group = ttk.LabelFrame(self, text="進捗")
        self.progress_group.pack(fill=tk.X, padx=5, pady=5)

        # 復旧試行進捗バー
        self.recovery_progress = ttk.Progressbar(self.progress_group, length=300, mode='determinate')
        self.recovery_progress.pack(padx=5, pady=5)

        # 進捗ラベル
        self.progress_label = ttk.Label(self.progress_group, text="復旧試行: 0/3")
        self.progress_label.pack(pady=2)

    def set_callbacks(self, start_callback: Callable, stop_callback: Callable,
                     save_template_callback: Callable, send_recovery_callback: Callable,
                     monitor_area_callback: Optional[Callable] = None,
                     save_template_with_selection_callback: Optional[Callable] = None):
        """コールバック関数を設定"""
        self.start_callback = start_callback
        self.stop_callback = stop_callback
        self.save_template_callback = save_template_callback
        self.send_recovery_callback = send_recovery_callback
        self.monitor_area_callback = monitor_area_callback
        self.save_template_with_selection_callback = save_template_with_selection_callback

    def _on_start_clicked(self):
        """開始ボタンクリック時の処理"""
        if self.start_callback:
            self.start_callback()

    def _on_stop_clicked(self):
        """停止ボタンクリック時の処理"""
        if self.stop_callback:
            self.stop_callback()

    def _on_save_template_clicked(self):
        """テンプレート保存ボタンクリック時の処理"""
        if self.save_template_callback:
            self.save_template_callback()

    def _on_send_recovery_clicked(self):
        """復旧コマンド送信ボタンクリック時の処理"""
        if self.send_recovery_callback:
            self.send_recovery_callback()

    def _on_monitor_area_clicked(self):
        """監視エリア設定ボタンクリック時の処理"""
        if self.monitor_area_callback:
            self.monitor_area_callback()
    
    def _on_save_template_with_selection_clicked(self):
        """範囲選択でテンプレート保存ボタンクリック時の処理"""
        if self.save_template_with_selection_callback:
            self.save_template_with_selection_callback()

    def update_status(self, status_data: dict[str, Any]):
        """状態を更新"""
        try:
            # 監視状態の更新
            monitoring = status_data.get("monitoring", False)
            self.status_label.config(text=f"状態: {'監視中' if monitoring else '停止中'}")

            # ボタンの有効/無効切り替え
            self.start_button.config(state="disabled" if monitoring else "normal")
            self.stop_button.config(state="normal" if monitoring else "disabled")

            # テンプレート数の更新
            template_count = status_data.get("template_count", 0)
            self.template_count_label.config(text=f"テンプレート: {template_count}個")

            # 復旧試行回数の更新
            recovery_attempts = status_data.get("recovery_attempts", 0)
            max_attempts = status_data.get("max_recovery_attempts", 3)
            self.recovery_attempts_label.config(text=f"復旧試行: {recovery_attempts}/{max_attempts}")

            # 進捗バーの更新
            self.recovery_progress.config(maximum=max_attempts, value=recovery_attempts)
            self.progress_label.config(text=f"復旧試行: {recovery_attempts}/{max_attempts}")

            logger.debug(f"状態を更新しました: {status_data}")

        except Exception as e:
            logger.error(f"状態更新エラー: {e}")

    def add_log(self, message: str):
        """ログを追加"""
        try:
            import datetime
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            log_entry = f"[{timestamp}] {message}\n"
            self.log_text.insert(tk.END, log_entry)

            # 自動スクロール
            self.log_text.see(tk.END)

            logger.debug(f"ログを追加: {message}")

        except Exception as e:
            logger.error(f"ログ追加エラー: {e}")

    def clear_log(self):
        """ログをクリア"""
        try:
            self.log_text.delete(1.0, tk.END)
            logger.info("ログをクリアしました")
        except Exception as e:
            logger.error(f"ログクリアエラー: {e}")

    def set_last_action(self, action: str):
        """最終アクションを設定"""
        try:
            self.last_action_label.config(text=f"最終アクション: {action}")
            logger.debug(f"最終アクションを更新: {action}")
        except Exception as e:
            logger.error(f"最終アクション更新エラー: {e}")

    def set_mode(self, mode: str):
        """モードを設定"""
        try:
            self.mode_label.config(text=f"モード: {mode}")
            logger.debug(f"モードを更新: {mode}")
        except Exception as e:
            logger.error(f"モード更新エラー: {e}")
