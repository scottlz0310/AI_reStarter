"""
ログ表示GUI
既存のログ表示機能をGUIで操作
"""

import logging
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from typing import List, Optional
import datetime

logger = logging.getLogger(__name__)


class LogViewer:
    """ログ表示GUI"""
    
    def __init__(self, parent: tk.Tk):
        self.parent = parent
        self.dialog = None
        self.log_files = []
        self.current_log_file = None
        self.log_content = []
        
        logger.debug("ログ表示GUIを初期化しました")
    
    def show(self):
        """ログ表示GUIを表示"""
        try:
            # ダイアログウィンドウの作成
            self.dialog = tk.Toplevel(self.parent)
            self.dialog.title("ログ表示 - AI reStarter")
            self.dialog.geometry("900x700")
            self.dialog.transient(self.parent)
            self.dialog.grab_set()
            
            # ダイアログの位置を親ウィンドウの中央に設定
            self.dialog.geometry("+%d+%d" % (
                self.parent.winfo_rootx() + 50,
                self.parent.winfo_rooty() + 50
            ))
            
            self.setup_ui()
            self.load_log_files()
            
            logger.info("ログ表示GUIを表示しました")
            
        except Exception as e:
            logger.error(f"ログ表示GUI表示エラー: {e}")
            messagebox.showerror("エラー", f"ログ表示GUIの表示に失敗しました: {e}")
    
    def setup_ui(self):
        """UIの初期化"""
        # メインフレーム
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # ツールバー
        self.create_toolbar(main_frame)
        
        # ログファイル選択
        self.create_log_file_selector(main_frame)
        
        # ログ表示エリア
        self.create_log_display(main_frame)
        
        # フィルター設定
        self.create_filter_settings(main_frame)
        
        # ステータスバー
        self.create_status_bar(main_frame)
    
    def create_toolbar(self, parent):
        """ツールバーの作成"""
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, pady=(0, 10))
        
        # 更新ボタン
        refresh_button = ttk.Button(toolbar, text="更新", command=self.refresh_logs)
        refresh_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # クリアボタン
        clear_button = ttk.Button(toolbar, text="クリア", command=self.clear_log_display)
        clear_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # 保存ボタン
        save_button = ttk.Button(toolbar, text="保存", command=self.save_log)
        save_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # 検索ボタン
        search_button = ttk.Button(toolbar, text="検索", command=self.search_log)
        search_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # 自動更新チェックボックス
        self.auto_refresh_var = tk.BooleanVar(value=False)
        auto_refresh_check = ttk.Checkbutton(toolbar, text="自動更新", 
                                           variable=self.auto_refresh_var,
                                           command=self.toggle_auto_refresh)
        auto_refresh_check.pack(side=tk.RIGHT, padx=(10, 0))
    
    def create_log_file_selector(self, parent):
        """ログファイル選択エリアの作成"""
        selector_frame = ttk.LabelFrame(parent, text="ログファイル選択", padding="10")
        selector_frame.pack(fill=tk.X, pady=(0, 10))
        
        # ログファイル選択コンボボックス
        ttk.Label(selector_frame, text="ログファイル:").pack(side=tk.LEFT, padx=(0, 10))
        self.log_file_var = tk.StringVar()
        self.log_file_combo = ttk.Combobox(selector_frame, textvariable=self.log_file_var, 
                                          state="readonly", width=40)
        self.log_file_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.log_file_combo.bind("<<ComboboxSelected>>", self.on_log_file_selected)
        
        # 手動ファイル選択ボタン
        browse_button = ttk.Button(selector_frame, text="参照", command=self.browse_log_file)
        browse_button.pack(side=tk.LEFT)
    
    def create_log_display(self, parent):
        """ログ表示エリアの作成"""
        display_frame = ttk.LabelFrame(parent, text="ログ内容", padding="10")
        display_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # ログテキストエリア
        self.log_text = tk.Text(display_frame, font=("Consolas", 9), wrap=tk.NONE)
        
        # スクロールバー
        v_scrollbar = ttk.Scrollbar(display_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        h_scrollbar = ttk.Scrollbar(display_frame, orient=tk.HORIZONTAL, command=self.log_text.xview)
        self.log_text.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # 配置
        self.log_text.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        display_frame.grid_rowconfigure(0, weight=1)
        display_frame.grid_columnconfigure(0, weight=1)
    
    def create_filter_settings(self, parent):
        """フィルター設定エリアの作成"""
        filter_frame = ttk.LabelFrame(parent, text="フィルター設定", padding="10")
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        # ログレベルフィルター
        ttk.Label(filter_frame, text="ログレベル:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.log_level_var = tk.StringVar(value="ALL")
        log_level_combo = ttk.Combobox(filter_frame, textvariable=self.log_level_var,
                                      values=["ALL", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
                                      state="readonly", width=15)
        log_level_combo.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        log_level_combo.bind("<<ComboboxSelected>>", self.apply_filters)
        
        # 日時フィルター
        ttk.Label(filter_frame, text="開始日時:").grid(row=0, column=2, sticky=tk.W, padx=(0, 10))
        self.start_date_var = tk.StringVar()
        start_date_entry = ttk.Entry(filter_frame, textvariable=self.start_date_var, width=20)
        start_date_entry.grid(row=0, column=3, sticky=tk.W, padx=(0, 10))
        
        ttk.Label(filter_frame, text="終了日時:").grid(row=0, column=4, sticky=tk.W, padx=(0, 10))
        self.end_date_var = tk.StringVar()
        end_date_entry = ttk.Entry(filter_frame, textvariable=self.end_date_var, width=20)
        end_date_entry.grid(row=0, column=5, sticky=tk.W)
        
        # キーワードフィルター
        ttk.Label(filter_frame, text="キーワード:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(10, 0))
        self.keyword_var = tk.StringVar()
        keyword_entry = ttk.Entry(filter_frame, textvariable=self.keyword_var, width=30)
        keyword_entry.grid(row=1, column=1, columnspan=2, sticky=tk.W, pady=(10, 0))
        keyword_entry.bind("<KeyRelease>", self.apply_filters)
        
        # フィルター適用ボタン
        apply_filter_button = ttk.Button(filter_frame, text="フィルター適用", command=self.apply_filters)
        apply_filter_button.grid(row=1, column=3, padx=(20, 0), pady=(10, 0))
        
        # フィルタークリアボタン
        clear_filter_button = ttk.Button(filter_frame, text="フィルタークリア", command=self.clear_filters)
        clear_filter_button.grid(row=1, column=4, padx=(10, 0), pady=(10, 0))
    
    def create_status_bar(self, parent):
        """ステータスバーの作成"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X)
        
        # ログ行数表示
        self.status_label = ttk.Label(status_frame, text="ログ行数: 0")
        self.status_label.pack(side=tk.LEFT)
        
        # 閉じるボタン
        close_button = ttk.Button(status_frame, text="閉じる", command=self.close)
        close_button.pack(side=tk.RIGHT)
    
    def load_log_files(self):
        """ログファイルを読み込み"""
        try:
            self.log_files.clear()
            
            # 現在のディレクトリからログファイルを検索
            current_dir = os.getcwd()
            for filename in os.listdir(current_dir):
                if filename.endswith('.log'):
                    self.log_files.append(filename)
            
            # デフォルトのログファイルを追加
            default_logs = ["ai_restarter.log", "kiro_recovery.log"]
            for log_file in default_logs:
                if log_file not in self.log_files and os.path.exists(log_file):
                    self.log_files.append(log_file)
            
            # コンボボックスを更新
            self.log_file_combo['values'] = self.log_files
            
            if self.log_files:
                # 最初のログファイルを選択
                self.log_file_combo.set(self.log_files[0])
                self.on_log_file_selected(None)
            
            logger.debug(f"{len(self.log_files)}個のログファイルを検出しました")
            
        except Exception as e:
            logger.error(f"ログファイル読み込みエラー: {e}")
    
    def on_log_file_selected(self, event):
        """ログファイル選択時の処理"""
        selected_file = self.log_file_var.get()
        if selected_file and os.path.exists(selected_file):
            self.current_log_file = selected_file
            self.load_log_content()
        else:
            self.current_log_file = None
            self.log_text.delete(1.0, tk.END)
            self.log_text.insert(tk.END, "ログファイルが見つかりません")
    
    def browse_log_file(self):
        """ログファイルを参照"""
        file_path = filedialog.askopenfilename(
            title="ログファイルを選択",
            filetypes=[
                ("ログファイル", "*.log"),
                ("テキストファイル", "*.txt"),
                ("全てのファイル", "*.*")
            ]
        )
        
        if file_path:
            filename = os.path.basename(file_path)
            if filename not in self.log_files:
                self.log_files.append(filename)
                self.log_file_combo['values'] = self.log_files
            
            self.log_file_combo.set(filename)
            self.on_log_file_selected(None)
    
    def load_log_content(self):
        """ログ内容を読み込み"""
        try:
            if not self.current_log_file:
                return
            
            self.log_content.clear()
            self.log_text.delete(1.0, tk.END)
            
            with open(self.current_log_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line_num, line in enumerate(f, 1):
                    self.log_content.append({
                        'line_num': line_num,
                        'content': line.rstrip(),
                        'timestamp': self.extract_timestamp(line),
                        'level': self.extract_log_level(line)
                    })
            
            # ログ内容を表示
            self.display_log_content()
            
            # ステータス更新
            self.status_label.config(text=f"ログ行数: {len(self.log_content)}")
            
            logger.debug(f"ログファイル '{self.current_log_file}' から {len(self.log_content)} 行を読み込みました")
            
        except Exception as e:
            logger.error(f"ログ内容読み込みエラー: {e}")
            self.log_text.delete(1.0, tk.END)
            self.log_text.insert(tk.END, f"ログファイルの読み込みに失敗しました: {e}")
    
    def extract_timestamp(self, line):
        """ログ行からタイムスタンプを抽出"""
        try:
            # 一般的なログ形式のタイムスタンプを検出
            import re
            timestamp_patterns = [
                r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})',
                r'(\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2})',
                r'(\d{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2})'
            ]
            
            for pattern in timestamp_patterns:
                match = re.search(pattern, line)
                if match:
                    return match.group(1)
            
            return None
        except:
            return None
    
    def extract_log_level(self, line):
        """ログ行からログレベルを抽出"""
        try:
            import re
            level_pattern = r'(\b(?:DEBUG|INFO|WARNING|ERROR|CRITICAL)\b)'
            match = re.search(level_pattern, line.upper())
            return match.group(1) if match else None
        except:
            return None
    
    def display_log_content(self):
        """ログ内容を表示"""
        try:
            self.log_text.delete(1.0, tk.END)
            
            for log_entry in self.log_content:
                # フィルターを適用
                if not self.should_display_log(log_entry):
                    continue
                
                # 行番号と内容を表示
                line_text = f"{log_entry['line_num']:4d}: {log_entry['content']}\n"
                self.log_text.insert(tk.END, line_text)
            
            # 自動スクロール
            self.log_text.see(tk.END)
            
        except Exception as e:
            logger.error(f"ログ内容表示エラー: {e}")
    
    def should_display_log(self, log_entry):
        """ログエントリを表示すべきか判定"""
        # ログレベルフィルター
        if self.log_level_var.get() != "ALL":
            if not log_entry['level'] or log_entry['level'] != self.log_level_var.get():
                return False
        
        # キーワードフィルター
        keyword = self.keyword_var.get().strip()
        if keyword and keyword.lower() not in log_entry['content'].lower():
            return False
        
        # 日時フィルター
        if log_entry['timestamp']:
            try:
                log_time = datetime.datetime.strptime(log_entry['timestamp'], "%Y-%m-%d %H:%M:%S")
                
                if self.start_date_var.get().strip():
                    start_time = datetime.datetime.strptime(self.start_date_var.get(), "%Y-%m-%d %H:%M:%S")
                    if log_time < start_time:
                        return False
                
                if self.end_date_var.get().strip():
                    end_time = datetime.datetime.strptime(self.end_date_var.get(), "%Y-%m-%d %H:%M:%S")
                    if log_time > end_time:
                        return False
                        
            except ValueError:
                pass  # 日時解析に失敗した場合はフィルターを適用しない
        
        return True
    
    def apply_filters(self, event=None):
        """フィルターを適用"""
        self.display_log_content()
        logger.debug("ログフィルターを適用しました")
    
    def clear_filters(self):
        """フィルターをクリア"""
        self.log_level_var.set("ALL")
        self.keyword_var.set("")
        self.start_date_var.set("")
        self.end_date_var.set("")
        self.display_log_content()
        logger.debug("ログフィルターをクリアしました")
    
    def refresh_logs(self):
        """ログを更新"""
        if self.current_log_file:
            self.load_log_content()
            logger.debug("ログを更新しました")
    
    def clear_log_display(self):
        """ログ表示をクリア"""
        self.log_text.delete(1.0, tk.END)
        logger.debug("ログ表示をクリアしました")
    
    def save_log(self):
        """ログを保存"""
        try:
            if not self.current_log_file:
                messagebox.showwarning("警告", "保存するログファイルが選択されていません")
                return
            
            # 保存先を選択
            save_path = filedialog.asksaveasfilename(
                title="ログを保存",
                defaultextension=".log",
                filetypes=[
                    ("ログファイル", "*.log"),
                    ("テキストファイル", "*.txt"),
                    ("全てのファイル", "*.*")
                ]
            )
            
            if save_path:
                with open(save_path, 'w', encoding='utf-8') as f:
                    f.write(self.log_text.get(1.0, tk.END))
                
                messagebox.showinfo("完了", f"ログを保存しました: {save_path}")
                logger.info(f"ログを保存しました: {save_path}")
                
        except Exception as e:
            logger.error(f"ログ保存エラー: {e}")
            messagebox.showerror("エラー", f"ログの保存に失敗しました: {e}")
    
    def search_log(self):
        """ログを検索"""
        try:
            # 検索ダイアログ
            search_term = tk.simpledialog.askstring("ログ検索", "検索する文字列を入力してください:")
            
            if search_term:
                # 検索実行
                self.log_text.tag_remove("search", "1.0", tk.END)
                
                start_pos = "1.0"
                while True:
                    pos = self.log_text.search(search_term, start_pos, tk.END)
                    if not pos:
                        break
                    
                    end_pos = f"{pos}+{len(search_term)}c"
                    self.log_text.tag_add("search", pos, end_pos)
                    start_pos = end_pos
                
                # 検索結果をハイライト
                self.log_text.tag_config("search", background="yellow")
                
                # 最初の検索結果にスクロール
                first_match = self.log_text.tag_ranges("search")
                if first_match:
                    self.log_text.see(first_match[0])
                
                logger.debug(f"ログ検索を実行しました: '{search_term}'")
                
        except Exception as e:
            logger.error(f"ログ検索エラー: {e}")
    
    def toggle_auto_refresh(self):
        """自動更新の切り替え"""
        if self.auto_refresh_var.get():
            self.start_auto_refresh()
        else:
            self.stop_auto_refresh()
    
    def start_auto_refresh(self):
        """自動更新を開始"""
        self.auto_refresh_timer = self.dialog.after(5000, self.auto_refresh_callback)
        logger.debug("ログの自動更新を開始しました")
    
    def stop_auto_refresh(self):
        """自動更新を停止"""
        if hasattr(self, 'auto_refresh_timer'):
            self.dialog.after_cancel(self.auto_refresh_timer)
            logger.debug("ログの自動更新を停止しました")
    
    def auto_refresh_callback(self):
        """自動更新コールバック"""
        if self.auto_refresh_var.get():
            self.refresh_logs()
            self.auto_refresh_timer = self.dialog.after(5000, self.auto_refresh_callback)
    
    def close(self):
        """ダイアログを閉じる"""
        self.stop_auto_refresh()
        logger.info("ログ表示GUIを閉じました")
        self.dialog.destroy()
