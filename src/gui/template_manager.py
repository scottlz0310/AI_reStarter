"""
テンプレート管理GUI
既存のテンプレート管理機能をGUIで操作
"""

import logging
import os
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
from tkinter import ttk
from typing import Any

from PIL import Image
from PIL import ImageTk

from src.config.config_manager import ConfigManager

logger = logging.getLogger(__name__)


class TemplateManager:
    """テンプレート管理GUI"""

    def __init__(self, parent: tk.Tk, config_manager: ConfigManager) -> None:
        self.parent = parent
        self.config_manager = config_manager
        self.dialog: tk.Toplevel | None = None
        self.template_folder: str = self.config_manager.get(
            "screenshot_folder", "error_templates"
        )
        self.templates: list[dict[str, Any]] = []

        self.active_tab_mode: str = "kiro"  # デフォルトはKiro-IDEタブ
        logger.debug("テンプレート管理GUIを初期化しました")

    def set_active_tab(self, tab_mode: str) -> None:
        """アクティブにするタブを設定

        Args:
            tab_mode: アクティブにするタブ ("kiro" or "amazonq")
        """
        if tab_mode in ["kiro", "amazonq"]:
            self.active_tab_mode = tab_mode
            logger.debug(f"アクティブタブを設定: {tab_mode}")
        else:
            logger.warning(f"無効なタブモード: {tab_mode}")

    def create_tab_control(self, parent: Any) -> None:
        """タブコントロールを作成"""
        self.notebook: ttk.Notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Kiro-IDEタブ
        self.kiro_frame: ttk.Frame = ttk.Frame(self.notebook)
        self.notebook.add(self.kiro_frame, text="Kiro-IDEテンプレート")
        self.setup_kiro_tab()

        # AmazonQタブ
        self.amazonq_frame: ttk.Frame = ttk.Frame(self.notebook)
        self.notebook.add(self.amazonq_frame, text="AmazonQテンプレート")
        self.setup_amazonq_tab()

        # ステータスバー
        self.create_status_bar(parent)

        # アクティブタブを設定
        if hasattr(self, "active_tab_mode"):
            if self.active_tab_mode == "amazonq":
                self.notebook.select(1)  # type: ignore[no-untyped-call]
            else:
                self.notebook.select(0)  # type: ignore[no-untyped-call]

    def setup_kiro_tab(self) -> None:
        """従来のKiro-IDEタブのセットアップ"""
        self.template_folder = self.config_manager.get(
            "error_templates_dir", "error_templates"
        )

        # ツールバー
        self.create_toolbar(self.kiro_frame)

        # テンプレート一覧
        self.create_template_list(self.kiro_frame)

        # プレビューエリア
        self.create_preview_area(self.kiro_frame)

    def setup_amazonq_tab(self) -> None:
        """AmazonQタブのセットアップ"""
        self.amazonq_folder: str = self.config_manager.get(
            "amazonq.run_button_templates_dir", "amazonq_templates"
        )

        # ツールバー
        self.create_amazonq_toolbar(self.amazonq_frame)

        # テンプレート一覧
        self.create_amazonq_template_list(self.amazonq_frame)

        # プレビューエリア
        self.create_amazonq_preview_area(self.amazonq_frame)

    def show(self) -> None:
        """テンプレート管理GUIを表示"""
        try:
            # ダイアログウィンドウの作成
            self.dialog = tk.Toplevel(self.parent)
            self.dialog.title("テンプレート管理 - AI reStarter")
            self.dialog.geometry("800x600")
            self.dialog.transient(self.parent)
            self.dialog.grab_set()

            # ダイアログの位置を親ウィンドウの中央に設定
            x_pos = self.parent.winfo_rootx() + 50
            y_pos = self.parent.winfo_rooty() + 50
            self.dialog.geometry(f"+{x_pos}+{y_pos}")

            self.setup_ui()
            self.load_templates()
            self.refresh_amazonq_templates()

            logger.info("テンプレート管理GUIを表示しました")

        except Exception as e:
            logger.error(f"テンプレート管理GUI表示エラー: {e}")
            messagebox.showerror(
                "エラー", f"テンプレート管理GUIの表示に失敗しました: {e}"
            )

    def setup_ui(self) -> None:
        """UIの初期化"""
        # メインフレーム
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # タブコントロールを作成
        self.create_tab_control(main_frame)

    def create_toolbar(self, parent: Any) -> None:
        """ツールバーの作成"""
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, pady=(0, 10))

        # 新規追加ボタン
        add_button = ttk.Button(toolbar, text="新規追加", command=self.add_template)
        add_button.pack(side=tk.LEFT, padx=(0, 5))

        # 範囲選択で追加ボタン
        select_button = ttk.Button(
            toolbar, text="範囲選択で追加", command=self.add_template_with_selection
        )
        select_button.pack(side=tk.LEFT, padx=(0, 5))

        # インポートボタン
        import_button = ttk.Button(
            toolbar, text="インポート", command=self.import_template
        )
        import_button.pack(side=tk.LEFT, padx=(0, 5))

        # 削除ボタン
        delete_button = ttk.Button(toolbar, text="削除", command=self.delete_template)
        delete_button.pack(side=tk.LEFT, padx=(0, 5))

        # 編集ボタン
        edit_button = ttk.Button(toolbar, text="編集", command=self.edit_template)
        edit_button.pack(side=tk.LEFT, padx=(0, 5))

        # 更新ボタン
        refresh_button = ttk.Button(
            toolbar, text="更新", command=self.refresh_templates
        )
        refresh_button.pack(side=tk.LEFT, padx=(0, 5))

        # 検索フィールド
        ttk.Label(toolbar, text="検索:").pack(side=tk.RIGHT, padx=(10, 5))
        self.search_var: tk.StringVar = tk.StringVar()
        self.search_var.trace("w", self.filter_templates)  # type: ignore[no-untyped-call]
        search_entry = ttk.Entry(toolbar, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.RIGHT)

    def create_template_list(self, parent: Any) -> None:
        """テンプレート一覧の作成"""
        list_frame = ttk.LabelFrame(parent, text="テンプレート一覧", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # ツリービュー
        columns = ("名前", "サイズ", "作成日", "説明")
        self.template_tree: ttk.Treeview = ttk.Treeview(
            list_frame, columns=columns, show="headings", height=10
        )

        # 列の設定
        for col in columns:
            self.template_tree.heading(col, text=col)
            self.template_tree.column(col, width=150)

        # スクロールバー
        scrollbar = ttk.Scrollbar(
            list_frame, orient=tk.VERTICAL, command=self.template_tree.yview
        )
        self.template_tree.configure(yscrollcommand=scrollbar.set)

        # 配置
        self.template_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 選択イベント
        self.template_tree.bind("<<TreeviewSelect>>", self.on_template_select)

    def create_preview_area(self, parent: Any) -> None:
        """プレビューエリアの作成"""
        preview_frame = ttk.LabelFrame(parent, text="プレビュー", padding="10")
        preview_frame.pack(fill=tk.X, pady=(0, 10))

        # プレビューラベル
        self.preview_label: ttk.Label = ttk.Label(
            preview_frame, text="テンプレートを選択してください"
        )
        self.preview_label.pack(expand=True)

        # 情報表示
        info_frame = ttk.Frame(preview_frame)
        info_frame.pack(fill=tk.X, pady=(10, 0))

        # テンプレート情報
        self.info_text: tk.Text = tk.Text(info_frame, height=4, width=50)
        self.info_text.pack(fill=tk.X)

    def create_status_bar(self, parent: Any) -> None:
        """ステータスバーの作成"""
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X)

        # テンプレート数表示
        self.status_label: ttk.Label = ttk.Label(status_frame, text="テンプレート数: 0")
        self.status_label.pack(side=tk.LEFT)

        # 閉じるボタン
        close_button = ttk.Button(status_frame, text="閉じる", command=self.close)
        close_button.pack(side=tk.RIGHT)

    def load_templates(self) -> None:
        """テンプレートを読み込み"""
        try:
            self.templates.clear()
            self.template_tree.delete(*self.template_tree.get_children())

            if not os.path.exists(self.template_folder):
                logger.warning(
                    f"テンプレートフォルダが存在しません: {self.template_folder}"
                )
                return

            # テンプレートファイルを検索
            for filename in os.listdir(self.template_folder):
                if filename.lower().endswith((".png", ".jpg", ".jpeg", ".bmp")):
                    filepath = os.path.join(self.template_folder, filename)
                    file_stat = os.stat(filepath)

                    template_info = {
                        "name": filename,
                        "path": filepath,
                        "size": file_stat.st_size,
                        "created": file_stat.st_ctime,
                        "modified": file_stat.st_mtime,
                    }

                    self.templates.append(template_info)

                    # ツリービューに追加
                    size_kb = f"{file_stat.st_size / 1024:.1f} KB"
                    created_date = self.format_date(file_stat.st_ctime)

                    self.template_tree.insert(
                        "",
                        "end",
                        values=(filename, size_kb, created_date, "テンプレート画像"),
                    )

            # ステータス更新
            self.status_label.config(text=f"テンプレート数: {len(self.templates)}")
            logger.info(f"{len(self.templates)}個のテンプレートを読み込みました")

        except Exception as e:
            logger.error(f"テンプレート読み込みエラー: {e}")
            messagebox.showerror("エラー", f"テンプレートの読み込みに失敗しました: {e}")

    def format_date(self, timestamp: float) -> str:
        """タイムスタンプを日付文字列に変換"""
        import datetime

        return datetime.datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M")

    def on_template_select(self, event: Any) -> None:
        """テンプレート選択時の処理"""
        selection = self.template_tree.selection()
        if not selection:
            return

        # 選択されたアイテムの情報を取得
        item = self.template_tree.item(selection[0])
        template_name = item["values"][0]

        # テンプレート情報を検索
        template_info = next(
            (t for t in self.templates if t["name"] == template_name), None
        )
        if not template_info:
            return

        # プレビュー表示
        self.show_preview(template_info)

        # 情報表示
        self.show_template_info(template_info)

    def show_preview(self, template_info: dict[str, Any]) -> None:
        """プレビューを表示"""
        try:
            # 画像を読み込み
            image = Image.open(template_info["path"])

            # プレビューサイズにリサイズ（最大200x200）
            max_size = (200, 200)
            image.thumbnail(max_size, Image.Resampling.LANCZOS)

            # PhotoImageに変換
            photo = ImageTk.PhotoImage(image)

            # プレビューレベルを更新
            self.preview_label.config(image=photo, text="")
            self.preview_label.image = photo  # type: ignore[attr-defined]  # 参照を保持

        except Exception as e:
            logger.error(f"プレビュー表示エラー: {e}")
            self.preview_label.config(image="", text="プレビュー表示エラー")

    def show_template_info(self, template_info: dict[str, Any]) -> None:
        """テンプレート情報を表示"""
        try:
            info_text = f"""ファイル名: {template_info["name"]}
パス: {template_info["path"]}
サイズ: {template_info["size"]} バイト
作成日: {self.format_date(template_info["created"])}
更新日: {self.format_date(template_info["modified"])}"""

            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(1.0, info_text)

        except Exception as e:
            logger.error(f"テンプレート情報表示エラー: {e}")

    def add_template(self) -> None:
        """新規テンプレートを追加"""
        try:
            # ファイル選択ダイアログ
            file_path = filedialog.askopenfilename(
                title="テンプレート画像を選択",
                filetypes=[
                    ("画像ファイル", "*.png *.jpg *.jpeg *.bmp"),
                    ("PNGファイル", "*.png"),
                    ("JPEGファイル", "*.jpg *.jpeg"),
                    ("BMPファイル", "*.bmp"),
                    ("全てのファイル", "*.*"),
                ],
            )

            if file_path:
                # ファイルをコピー
                import shutil

                filename = os.path.basename(file_path)
                dest_path = os.path.join(self.template_folder, filename)

                # フォルダが存在しない場合は作成
                os.makedirs(self.template_folder, exist_ok=True)

                shutil.copy2(file_path, dest_path)

                messagebox.showinfo("完了", f"テンプレート '{filename}' を追加しました")
                logger.info(f"テンプレートを追加しました: {filename}")

                # 一覧を更新
                self.load_templates()

        except Exception as e:
            logger.error(f"テンプレート追加エラー: {e}")
            messagebox.showerror("エラー", f"テンプレートの追加に失敗しました: {e}")

    def add_template_with_selection(self) -> None:
        """範囲選択でKiroテンプレートを追加"""
        try:
            from src.gui.template_capture_dialog import TemplateCaptureDialog

            # ダイアログを一時的に隠す
            if self.dialog:
                self.dialog.withdraw()

            # 範囲選択ダイアログを表示
            capture_dialog = TemplateCaptureDialog(self.parent)
            result = capture_dialog.show()

            # ダイアログを再表示
            if self.dialog:
                self.dialog.deiconify()

            if result:
                selected_image, template_name = result

                # テンプレートを保存
                import cv2

                dest_path = os.path.join(self.template_folder, f"{template_name}.png")

                os.makedirs(self.template_folder, exist_ok=True)
                cv2.imwrite(dest_path, selected_image)

                messagebox.showinfo(
                    "完了", f"Kiroテンプレート '{template_name}' を追加しました"
                )
                logger.info(f"範囲選択でKiroテンプレートを追加: {template_name}")

                self.load_templates()

        except Exception as e:
            logger.error(f"範囲選択テンプレート追加エラー: {e}")
            messagebox.showerror(
                "エラー", f"範囲選択テンプレートの追加に失敗しました: {e}"
            )
            # エラー時もダイアログを再表示
            if hasattr(self, "dialog") and self.dialog:
                self.dialog.deiconify()

    def import_template(self) -> None:
        """テンプレートをインポート"""
        # 現在はadd_templateと同じ処理
        self.add_template()

    def delete_template(self) -> None:
        """選択されたテンプレートを削除"""
        selection = self.template_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "削除するテンプレートを選択してください")
            return

        # 確認ダイアログ
        item = self.template_tree.item(selection[0])
        template_name = item["values"][0]

        if not messagebox.askyesno(
            "確認", f"テンプレート '{template_name}' を削除しますか？"
        ):
            return

        try:
            # ファイルを削除
            template_info = next(
                (t for t in self.templates if t["name"] == template_name), None
            )
            if template_info:
                os.remove(template_info["path"])

                messagebox.showinfo(
                    "完了", f"テンプレート '{template_name}' を削除しました"
                )
                logger.info(f"テンプレートを削除しました: {template_name}")

                # 一覧を更新
                self.load_templates()

        except Exception as e:
            logger.error(f"テンプレート削除エラー: {e}")
            messagebox.showerror("エラー", f"テンプレートの削除に失敗しました: {e}")

    def edit_template(self) -> None:
        """テンプレートを編集"""
        selection = self.template_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "編集するテンプレートを選択してください")
            return

        # 現在はファイル名の変更のみ対応
        item = self.template_tree.item(selection[0])
        template_name = item["values"][0]

        # 新しいファイル名を入力
        new_name = tk.simpledialog.askstring(
            "ファイル名変更",
            "新しいファイル名を入力してください:",
            initialvalue=template_name,
        )

        if new_name and new_name != template_name:
            try:
                old_path = os.path.join(self.template_folder, template_name)
                new_path = os.path.join(self.template_folder, new_name)

                os.rename(old_path, new_path)

                messagebox.showinfo("完了", f"ファイル名を '{new_name}' に変更しました")
                logger.info(
                    f"テンプレート名を変更しました: {template_name} -> {new_name}"
                )

                # 一覧を更新
                self.load_templates()

            except Exception as e:
                logger.error(f"テンプレート名変更エラー: {e}")
                messagebox.showerror("エラー", f"ファイル名の変更に失敗しました: {e}")

    def refresh_templates(self) -> None:
        """テンプレート一覧を更新"""
        self.load_templates()
        logger.info("テンプレート一覧を更新しました")

    def filter_templates(self, *args: Any) -> None:
        """テンプレートをフィルタリング"""
        search_term = self.search_var.get().lower()

        # 全てのアイテムを非表示
        for item in self.template_tree.get_children():
            self.template_tree.detach(item)

        # 検索条件に一致するアイテムのみ表示
        for template_info in self.templates:
            if search_term in template_info["name"].lower():
                file_stat = os.stat(template_info["path"])
                size_kb = f"{file_stat.st_size / 1024:.1f} KB"
                created_date = self.format_date(file_stat.st_ctime)

                self.template_tree.insert(
                    "",
                    "end",
                    values=(
                        template_info["name"],
                        size_kb,
                        created_date,
                        "テンプレート画像",
                    ),
                )

    def create_amazonq_toolbar(self, parent: Any) -> None:
        """ツールバーの作成（AmazonQ用）"""
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(toolbar, text="新規追加", command=self.add_amazonq_template).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        ttk.Button(
            toolbar,
            text="範囲選択で追加",
            command=self.add_amazonq_template_with_selection,
        ).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="削除", command=self.delete_amazonq_template).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        ttk.Button(toolbar, text="更新", command=self.refresh_amazonq_templates).pack(
            side=tk.LEFT, padx=(0, 5)
        )

    def create_amazonq_template_list(self, parent: Any) -> None:
        """テンプレート一覧の作成（AmazonQ用）"""
        list_frame = ttk.LabelFrame(parent, text="▶RUNボタンテンプレート", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        columns = ("名前", "サイズ", "作成日")
        self.amazonq_tree: ttk.Treeview = ttk.Treeview(
            list_frame, columns=columns, show="headings", height=10
        )

        for col in columns:
            self.amazonq_tree.heading(col, text=col)
            self.amazonq_tree.column(col, width=150)

        scrollbar_aq = ttk.Scrollbar(
            list_frame, orient=tk.VERTICAL, command=self.amazonq_tree.yview
        )
        self.amazonq_tree.configure(yscrollcommand=scrollbar_aq.set)

        self.amazonq_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_aq.pack(side=tk.RIGHT, fill=tk.Y)

        self.amazonq_tree.bind("<<TreeviewSelect>>", self.on_amazonq_template_select)

    def create_amazonq_preview_area(self, parent: Any) -> None:
        """プレビューエリアの作成（AmazonQ用）"""
        preview_frame = ttk.LabelFrame(parent, text="プレビュー", padding="10")
        preview_frame.pack(fill=tk.X, pady=(0, 10))

        self.amazonq_preview_label: ttk.Label = ttk.Label(
            preview_frame, text="テンプレートを選択してください"
        )
        self.amazonq_preview_label.pack(expand=True)

        info_frame = ttk.Frame(preview_frame)
        info_frame.pack(fill=tk.X, pady=(10, 0))

        self.amazonq_info_text: tk.Text = tk.Text(info_frame, height=4, width=50)
        self.amazonq_info_text.pack(fill=tk.X)

    def add_amazonq_template(self) -> None:
        """新規AmazonQテンプレートを追加"""
        try:
            file_path = filedialog.askopenfilename(
                title="▶RUNボタンテンプレートを選択",
                filetypes=[
                    ("画像ファイル", "*.png *.jpg *.jpeg *.bmp"),
                    ("PNGファイル", "*.png"),
                    ("全てのファイル", "*.*"),
                ],
            )

            if file_path:
                import shutil

                filename = os.path.basename(file_path)
                dest_path = os.path.join(self.amazonq_folder, filename)

                os.makedirs(self.amazonq_folder, exist_ok=True)
                shutil.copy2(file_path, dest_path)

                messagebox.showinfo(
                    "完了", f"▶RUNボタンテンプレート '{filename}' を追加しました"
                )
                logger.info(f"AmazonQテンプレートを追加: {filename}")

                self.refresh_amazonq_templates()

        except Exception as e:
            logger.error(f"AmazonQテンプレート追加エラー: {e}")
            messagebox.showerror("エラー", f"テンプレートの追加に失敗しました: {e}")

    def add_amazonq_template_with_selection(self) -> None:
        """範囲選択でAmazonQテンプレートを追加"""
        try:
            from src.gui.template_capture_dialog import TemplateCaptureDialog

            # ダイアログを一時的に隠す
            if self.dialog:
                self.dialog.withdraw()

            # 範囲選択ダイアログを表示
            capture_dialog = TemplateCaptureDialog(self.parent)
            result = capture_dialog.show()

            # ダイアログを再表示
            if self.dialog:
                self.dialog.deiconify()

            if result:
                selected_image, template_name = result

                # テンプレートを保存
                import cv2

                dest_path = os.path.join(self.amazonq_folder, f"{template_name}.png")

                os.makedirs(self.amazonq_folder, exist_ok=True)
                cv2.imwrite(dest_path, selected_image)

                messagebox.showinfo(
                    "完了", f"▶RUNボタンテンプレート '{template_name}' を追加しました"
                )
                logger.info(f"範囲選択でAmazonQテンプレートを追加: {template_name}")

                self.refresh_amazonq_templates()

        except Exception as e:
            logger.error(f"範囲選択テンプレート追加エラー: {e}")
            messagebox.showerror(
                "エラー", f"範囲選択テンプレートの追加に失敗しました: {e}"
            )
            # エラー時もダイアログを再表示
            if hasattr(self, "dialog") and self.dialog:
                self.dialog.deiconify()

    def delete_amazonq_template(self) -> None:
        """選択されたAmazonQテンプレートを削除"""
        selection = self.amazonq_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "削除するテンプレートを選択してください")
            return

        item = self.amazonq_tree.item(selection[0])
        template_name = item["values"][0]

        if not messagebox.askyesno(
            "確認", f"▶RUNボタンテンプレート '{template_name}' を削除しますか？"
        ):
            return

        try:
            template_path = os.path.join(self.amazonq_folder, template_name)
            if os.path.exists(template_path):
                os.remove(template_path)
                messagebox.showinfo(
                    "完了", f"テンプレート '{template_name}' を削除しました"
                )
                logger.info(f"AmazonQテンプレートを削除: {template_name}")
                self.refresh_amazonq_templates()

        except Exception as e:
            logger.error(f"AmazonQテンプレート削除エラー: {e}")
            messagebox.showerror("エラー", f"テンプレートの削除に失敗しました: {e}")

    def refresh_amazonq_templates(self) -> None:
        """AmazonQテンプレート一覧を更新"""
        try:
            self.amazonq_tree.delete(*self.amazonq_tree.get_children())

            if not os.path.exists(self.amazonq_folder):
                return

            for filename in os.listdir(self.amazonq_folder):
                if filename.lower().endswith((".png", ".jpg", ".jpeg", ".bmp")):
                    filepath = os.path.join(self.amazonq_folder, filename)
                    file_stat = os.stat(filepath)

                    size_kb = f"{file_stat.st_size / 1024:.1f} KB"
                    created_date = self.format_date(file_stat.st_ctime)

                    self.amazonq_tree.insert(
                        "", "end", values=(filename, size_kb, created_date)
                    )

            logger.info("AmazonQテンプレート一覧を更新しました")

        except Exception as e:
            logger.error(f"AmazonQテンプレート更新エラー: {e}")

    def on_amazonq_template_select(self, event: Any) -> None:
        """AmazonQテンプレート選択時の処理"""
        selection = self.amazonq_tree.selection()
        if not selection:
            return

        item = self.amazonq_tree.item(selection[0])
        template_name = item["values"][0]
        template_path = os.path.join(self.amazonq_folder, template_name)

        # プレビュー表示
        try:
            image = Image.open(template_path)
            max_size = (200, 200)
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)

            self.amazonq_preview_label.config(image=photo, text="")
            self.amazonq_preview_label.image = photo  # type: ignore[attr-defined]  # 参照を保持

        except Exception as e:
            logger.error(f"AmazonQプレビュー表示エラー: {e}")
            self.amazonq_preview_label.config(image="", text="プレビュー表示エラー")

        # 情報表示
        try:
            file_stat = os.stat(template_path)
            info_text = f"""ファイル名: {template_name}
パス: {template_path}
サイズ: {file_stat.st_size} バイト
作成日: {self.format_date(file_stat.st_ctime)}"""

            self.amazonq_info_text.delete(1.0, tk.END)
            self.amazonq_info_text.insert(1.0, info_text)

        except Exception as e:
            logger.error(f"AmazonQテンプレート情報表示エラー: {e}")

    def close(self) -> None:
        """ダイアログを閉じる"""
        logger.info("テンプレート管理GUIを閉じました")
        if self.dialog:
            self.dialog.destroy()
