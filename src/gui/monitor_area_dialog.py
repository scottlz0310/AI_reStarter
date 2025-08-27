"""
監視エリア設定ダイアログ
ドラッグで監視エリアを設定するGUI
"""

import json
import logging
import os
import tkinter as tk
from contextlib import suppress
from tkinter import messagebox, simpledialog, ttk
from typing import Optional

from src.config.config_manager import ConfigManager

logger = logging.getLogger(__name__)


class MonitorAreaDialog:
    """監視エリア設定ダイアログ"""

    def __init__(self, parent: tk.Tk, config_manager: ConfigManager):
        self.parent = parent
        self.config_manager = config_manager
        self.dialog = None
        self.monitor_areas: list[dict] = []
        self.current_area: Optional[dict] = None
        self.drag_start: Optional[tuple[int, int]] = None
        self.drag_end: Optional[tuple[int, int]] = None
        self.is_dragging = False
        self.screenshot_photo = None  # スクリーンショット画像の参照を保持
        self.chat_input_position: Optional[list[int]] = None  # チャット入力欄の位置

        logger.debug("監視エリア設定ダイアログを初期化しました")

    def show(self):
        """監視エリア設定ダイアログを表示"""
        try:
            # ダイアログウィンドウの作成
            self.dialog = tk.Toplevel(self.parent)
            self.dialog.title("監視エリア設定 - AI reStarter")
            self.dialog.geometry("1000x700")
            self.dialog.transient(self.parent)
            self.dialog.grab_set()

            # 最大化ボタンを有効化
            self.dialog.resizable(True, True)
            self.dialog.minsize(800, 600)

            # Windows環境での最大化ボタンを明示的に有効化
            try:
                self.dialog.state('zoomed')  # 最大化状態に設定
                self.dialog.state('normal')  # 通常状態に戻す（これで最大化ボタンが有効になる）
            except tk.TclError:
                # 最大化がサポートされていない環境の場合
                pass

            # ダイアログの位置を親ウィンドウの中央に設定
            x_pos = self.parent.winfo_rootx() + 50
            y_pos = self.parent.winfo_rooty() + 50
            self.dialog.geometry(f"+{x_pos}+{y_pos}")

            # タイトルバーダブルクリックでの最大化を有効化
            # Windows環境でのタイトルバー操作
            try:
                # タイトルバー専用のイベントを設定
                self.dialog.bind("<Map>", self.on_window_map)
                self.dialog.bind("<Unmap>", self.on_window_unmap)

                # ウィンドウの状態変更を監視
                self.dialog.bind("<Configure>", self.on_window_configure)

                # タイトルバーエリアでのダブルクリックを検出
                self.dialog.bind("<Double-Button-1>", self.on_title_bar_double_click)

            except Exception as e:
                logger.warning(f"タイトルバーイベントの設定に失敗: {e}")

            self.setup_ui()
            self.setup_title_bar_events()
            self.load_monitor_areas()
            self.load_chat_input_position()

            logger.info("監視エリア設定ダイアログを表示しました")

        except Exception as e:
            logger.error(f"監視エリア設定ダイアログ表示エラー: {e}")
            messagebox.showerror("エラー", f"監視エリア設定ダイアログの表示に失敗しました: {e}")

    def toggle_maximize(self, event=None):
        """最大化/復元の切り替え"""
        try:
            current_state = self.dialog.state()
            if current_state == 'zoomed':
                self.dialog.state('normal')
                self.maximize_button.config(text="最大化")
                logger.debug("ダイアログを通常サイズに復元しました")
            else:
                self.dialog.state('zoomed')
                self.maximize_button.config(text="復元")
                logger.debug("ダイアログを最大化しました")
        except tk.TclError as e:
            logger.warning(f"最大化切り替えがサポートされていません: {e}")

    def on_window_map(self, event):
        """ウィンドウが表示された時の処理"""
        logger.debug("ウィンドウが表示されました")

    def on_window_unmap(self, event):
        """ウィンドウが非表示になった時の処理"""
        logger.debug("ウィンドウが非表示になりました")

    def on_window_configure(self, event):
        """ウィンドウの設定変更時の処理"""
        # ウィンドウサイズや位置の変更を監視
        if hasattr(event, 'width') and hasattr(event, 'height'):
            logger.debug(f"ウィンドウサイズ変更: {event.width} x {event.height}")

    def on_title_bar_double_click(self, event):
        """タイトルバーでのダブルクリック処理"""
        try:
            # クリック位置がタイトルバーエリアかチェック
            if event.y < 30:  # タイトルバーエリア（上から30ピクセル以内）
                logger.debug("タイトルバーでダブルクリックを検出")
                self.toggle_maximize()
            else:
                logger.debug("タイトルバー以外でダブルクリックを検出")
        except Exception as e:
            logger.warning(f"タイトルバーダブルクリック処理エラー: {e}")

    def setup_title_bar_events(self):
        """タイトルバーイベントの設定（より確実な方法）"""
        try:
            # ウィンドウ全体でのダブルクリックを検出
            self.dialog.bind("<Double-Button-1>", self.on_any_double_click)

            # ウィンドウの状態変更を監視
            self.dialog.bind("<Configure>", self.on_window_configure)

            logger.debug("タイトルバーイベントを設定しました")

        except Exception as e:
            logger.warning(f"タイトルバーイベント設定エラー: {e}")

    def on_any_double_click(self, event):
        """任意の場所でのダブルクリック処理"""
        try:
            # クリック位置をチェック
            if event.y < 30:  # タイトルバーエリア
                logger.debug("タイトルバーエリアでダブルクリックを検出")
                self.toggle_maximize()
            elif event.widget == self.dialog:  # ダイアログウィンドウ自体
                logger.debug("ダイアログウィンドウでダブルクリックを検出")
                # タイトルバーエリアかどうかチェック
                if event.y < 30:
                    self.toggle_maximize()
            else:
                logger.debug("その他の場所でダブルクリックを検出")

        except Exception as e:
            logger.warning(f"ダブルクリック処理エラー: {e}")

    def setup_ui(self):
        """UIの初期化"""
        # メインフレーム
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 左側: 監視エリア一覧
        self.create_area_list_panel(main_frame)

        # 右側: プレビュー・設定
        self.create_preview_panel(main_frame)

        # ボタンフレーム
        self.create_button_frame(main_frame)

    def create_area_list_panel(self, parent):
        """監視エリア一覧パネルの作成"""
        list_frame = ttk.LabelFrame(parent, text="監視エリア一覧", padding="10")
        list_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        # ツールバー
        toolbar = ttk.Frame(list_frame)
        toolbar.pack(fill=tk.X, pady=(0, 10))

        add_button = ttk.Button(toolbar, text="新規追加", command=self.add_new_area)
        add_button.pack(side=tk.LEFT, padx=(0, 5))

        delete_button = ttk.Button(toolbar, text="削除", command=self.delete_selected_area)
        delete_button.pack(side=tk.LEFT, padx=(0, 5))

        # 監視エリアリスト
        self.area_listbox = tk.Listbox(list_frame, width=30, height=15)
        self.area_listbox.pack(fill=tk.BOTH, expand=True)
        self.area_listbox.bind("<<ListboxSelect>>", self.on_area_selected)

        # スクロールバー
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.area_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.area_listbox.configure(yscrollcommand=scrollbar.set)

    def create_preview_panel(self, parent):
        """プレビュー・設定パネルの作成"""
        preview_frame = ttk.LabelFrame(parent, text="プレビュー・設定", padding="10")
        preview_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # プレビューエリア
        self.create_preview_area(preview_frame)

        # 設定エリア
        self.create_settings_area(preview_frame)

    def create_preview_area(self, parent):
        """プレビューエリアの作成"""
        preview_frame = ttk.LabelFrame(parent, text="画面プレビュー", padding="10")
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # プレビューキャンバス
        self.preview_canvas = tk.Canvas(preview_frame, bg="white", width=600, height=400)
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)

        # マウスイベントの設定
        self.preview_canvas.bind("<Button-1>", self.on_mouse_down)
        self.preview_canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.preview_canvas.bind("<ButtonRelease-1>", self.on_mouse_up)

        # スクロールバー
        v_scrollbar = ttk.Scrollbar(preview_frame, orient=tk.VERTICAL, command=self.preview_canvas.yview)
        h_scrollbar = ttk.Scrollbar(preview_frame, orient=tk.HORIZONTAL, command=self.preview_canvas.xview)
        self.preview_canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # 初期プレビューの描画
        self.draw_screen_preview()

    def create_settings_area(self, parent):
        """設定エリアの作成"""
        settings_frame = ttk.LabelFrame(parent, text="監視エリア設定", padding="10")
        settings_frame.pack(fill=tk.X)

        # 名前設定
        name_frame = ttk.Frame(settings_frame)
        name_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(name_frame, text="名前:").pack(side=tk.LEFT, padx=(0, 10))
        self.name_var = tk.StringVar()
        name_entry = ttk.Entry(name_frame, textvariable=self.name_var, width=30)
        name_entry.pack(side=tk.LEFT)

        # 座標設定
        coord_frame = ttk.Frame(settings_frame)
        coord_frame.pack(fill=tk.X, pady=(0, 10))

        # X座標
        ttk.Label(coord_frame, text="X:").grid(row=0, column=0, padx=(0, 5))
        self.x_var = tk.StringVar()
        x_entry = ttk.Entry(coord_frame, textvariable=self.x_var, width=8)
        x_entry.grid(row=0, column=1, padx=(0, 10))

        # Y座標
        ttk.Label(coord_frame, text="Y:").grid(row=0, column=2, padx=(0, 5))
        self.y_var = tk.StringVar()
        y_entry = ttk.Entry(coord_frame, textvariable=self.y_var, width=8)
        y_entry.grid(row=0, column=3, padx=(0, 10))

        # 幅
        ttk.Label(coord_frame, text="幅:").grid(row=0, column=4, padx=(0, 5))
        self.width_var = tk.StringVar()
        width_entry = ttk.Entry(coord_frame, textvariable=self.width_var, width=8)
        width_entry.grid(row=0, column=5, padx=(0, 10))

        # 高さ
        ttk.Label(coord_frame, text="高さ:").grid(row=0, column=6, padx=(0, 5))
        self.height_var = tk.StringVar()
        height_entry = ttk.Entry(coord_frame, textvariable=self.height_var, width=8)
        height_entry.grid(row=0, column=7)

        # 有効/無効設定
        enable_frame = ttk.Frame(settings_frame)
        enable_frame.pack(fill=tk.X, pady=(0, 10))

        self.enabled_var = tk.BooleanVar(value=True)
        enabled_check = ttk.Checkbutton(enable_frame, text="この監視エリアを有効にする",
                                      variable=self.enabled_var)
        enabled_check.pack(side=tk.LEFT)

        # 説明設定
        desc_frame = ttk.Frame(settings_frame)
        desc_frame.pack(fill=tk.X)

        ttk.Label(desc_frame, text="説明:").pack(anchor=tk.W, pady=(0, 5))
        self.desc_var = tk.StringVar()
        desc_entry = ttk.Entry(desc_frame, textvariable=self.desc_var, width=50)
        desc_entry.pack(fill=tk.X)

    def create_button_frame(self, parent):
        """ボタンフレームの作成"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(20, 0))

        # 左側: 操作ボタン（縦一列）
        left_button_frame = ttk.Frame(button_frame)
        left_button_frame.pack(side=tk.LEFT, fill=tk.Y)

        # スクリーンショット更新ボタン
        refresh_screenshot_button = ttk.Button(left_button_frame, text="画面更新", command=self.refresh_screenshot)
        refresh_screenshot_button.pack(fill=tk.X, pady=(0, 5))

        # 座標変換テストボタン
        coord_test_button = ttk.Button(left_button_frame, text="座標テスト", command=self.test_coordinate_conversion)
        coord_test_button.pack(fill=tk.X, pady=(0, 5))

        # 最大化切り替えボタン
        self.maximize_button = ttk.Button(left_button_frame, text="最大化", command=self.toggle_maximize)
        self.maximize_button.pack(fill=tk.X, pady=(0, 5))

        # テストボタン
        test_button = ttk.Button(left_button_frame, text="テスト", command=self.test_selected_area)
        test_button.pack(fill=tk.X, pady=(0, 5))

        # チャット欄設定ボタン
        chat_setup_button = ttk.Button(left_button_frame, text="チャット欄設定", command=self.setup_chat_input)
        chat_setup_button.pack(fill=tk.X)

        # 右側: 保存・キャンセルボタン（縦一列）
        right_button_frame = ttk.Frame(button_frame)
        right_button_frame.pack(side=tk.RIGHT, fill=tk.Y)

        # 保存ボタン
        save_button = ttk.Button(right_button_frame, text="保存", command=self.save_monitor_areas)
        save_button.pack(fill=tk.X, pady=(0, 5))

        # キャンセルボタン
        cancel_button = ttk.Button(right_button_frame, text="キャンセル", command=self.cancel)
        cancel_button.pack(fill=tk.X)

    def draw_screen_preview(self):
        """画面プレビューの描画"""
        try:
            # キャンバスをクリア
            self.preview_canvas.delete("all")

            # 実際の画面サイズを取得
            try:
                import pyautogui
                screen_width, screen_height = pyautogui.size()
            except ImportError:
                # pyautoguiが利用できない場合は仮の値
                screen_width = 1920
                screen_height = 1080

            # スケールを計算
            canvas_width = self.preview_canvas.winfo_width()
            canvas_height = self.preview_canvas.winfo_height()

            if canvas_width > 1 and canvas_height > 1:
                scale_x = canvas_width / screen_width
                scale_y = canvas_height / screen_height
                scale = min(scale_x, scale_y)

                # 実際のスクリーンショットを表示
                self.display_screenshot(screen_width, screen_height, scale, canvas_width, canvas_height)

                # 既存の監視エリアを描画
                self.draw_existing_areas(0, 0, scale)

                # キャンバスのスクロール領域を設定
                self.preview_canvas.configure(scrollregion=(
                    0, 0, canvas_width, canvas_height
                ))
            else:
                # キャンバスサイズが取得できない場合は基本的な表示
                self.draw_basic_screen_frame(screen_width, screen_height)

        except Exception as e:
            logger.error(f"画面プレビュー描画エラー: {e}")
            # エラー時は基本的な画面枠のみ表示
            self.draw_basic_screen_frame(screen_width, screen_height)

    def display_screenshot(self, screen_width: int, screen_height: int, scale: float, canvas_width: int, canvas_height: int):
        """実際のスクリーンショットを表示"""
        try:
            # スクリーンショットを取得
            import pyautogui
            screenshot = pyautogui.screenshot()

            # PIL画像をPhotoImageに変換
            from PIL import Image, ImageTk

            # キャンバスサイズに合わせてリサイズ
            scaled_width = int(screen_width * scale)
            scaled_height = int(screen_height * scale)

            # 画像をリサイズ
            resized_screenshot = screenshot.resize((scaled_width, scaled_height), Image.Resampling.LANCZOS)

            # PhotoImageに変換
            photo = ImageTk.PhotoImage(resized_screenshot)

            # キャンバスに画像を配置（中央）
            x_offset = (canvas_width - scaled_width) // 2
            y_offset = (canvas_height - scaled_height) // 2

            # 画像を表示
            self.preview_canvas.create_image(x_offset, y_offset, anchor=tk.NW, image=photo)

            # 画像の参照を保持
            self.screenshot_photo = photo

            # 画面の枠を描画
            self.preview_canvas.create_rectangle(
                x_offset, y_offset,
                x_offset + scaled_width, y_offset + scaled_height,
                outline="black", width=2
            )

            # 画面ラベル
            self.preview_canvas.create_text(
                x_offset + scaled_width // 2, y_offset - 20,
                text=f"画面 ({screen_width}x{screen_height})",
                anchor=tk.CENTER, fill="black", font=("TkDefaultFont", 10, "bold")
            )

            logger.debug("スクリーンショットを表示しました")

        except Exception as e:
            logger.error(f"スクリーンショット表示エラー: {e}")
            # エラー時は基本的な画面枠のみ表示
            self.draw_basic_screen_frame(screen_width, screen_height, scale, canvas_width, canvas_height)

    def draw_basic_screen_frame(self, screen_width: int, screen_height: int, scale: float = 1.0, canvas_width: int = 600, canvas_height: int = 400):
        """基本的な画面枠を描画（スクリーンショットが利用できない場合）"""
        try:
            # スケールを計算
            if canvas_width > 1 and canvas_height > 1:
                scale_x = canvas_width / screen_width
                scale_y = canvas_height / screen_height
                scale = min(scale_x, scale_y)

            # 画面の枠を描画
            scaled_width = int(screen_width * scale)
            scaled_height = int(screen_height * scale)

            # 中央に配置
            x_offset = (canvas_width - scaled_width) // 2
            y_offset = (canvas_height - scaled_height) // 2

            # 白い背景の矩形
            self.preview_canvas.create_rectangle(
                x_offset, y_offset,
                x_offset + scaled_width, y_offset + scaled_height,
                outline="black", width=2, fill="white"
            )

            # 画面ラベル
            self.preview_canvas.create_text(
                x_offset + scaled_width // 2, y_offset - 20,
                text=f"画面 ({screen_width}x{screen_height}) - スクリーンショットなし",
                anchor=tk.CENTER, fill="gray"
            )

            # グリッド線を描画（監視エリアの位置を把握しやすくする）
            grid_spacing = 100  # 100ピクセル間隔
            for x in range(0, scaled_width, int(grid_spacing * scale)):
                self.preview_canvas.create_line(
                    x_offset + x, y_offset, x_offset + x, y_offset + scaled_height,
                    fill="lightgray", width=1
                )

            for y in range(0, scaled_height, int(grid_spacing * scale)):
                self.preview_canvas.create_line(
                    x_offset, y_offset + y, x_offset + scaled_width, y_offset + y,
                    fill="lightgray", width=1
                )

            logger.debug("基本的な画面枠を描画しました")

        except Exception as e:
            logger.error(f"基本的な画面枠描画エラー: {e}")

    def draw_existing_areas(self, x_offset: int, y_offset: int, scale: float):
        """既存の監視エリアを描画"""
        for i, area in enumerate(self.monitor_areas):
            if area.get("enabled", True):
                x = int(area["x"] * scale) + x_offset
                y = int(area["y"] * scale) + y_offset
                width = int(area["width"] * scale)
                height = int(area["height"] * scale)

                # 監視エリアを描画
                self.preview_canvas.create_rectangle(
                    x, y, x + width, y + height,
                    outline="red", width=2, fill="red", stipple="gray50",
                    tags="area_rect"
                )

                # ラベル
                self.preview_canvas.create_text(
                    x + width // 2, y - 10,
                    text=area.get("name", f"エリア{i+1}"),
                    anchor=tk.CENTER, fill="red",
                    tags="area_label"
                )

                # 座標情報
                self.preview_canvas.create_text(
                    x + width // 2, y + height + 15,
                    text=f"({area['x']},{area['y']}) {area['width']}x{area['height']}",
                    anchor=tk.CENTER, font=("TkDefaultFont", 8),
                    tags="area_coord"
                )

    def on_mouse_down(self, event):
        """マウスダウン時の処理"""
        self.drag_start = (event.x, event.y)
        self.is_dragging = True

        # ドラッグ中の表示をクリア
        self.preview_canvas.delete("drag_rect")

    def on_mouse_drag(self, event):
        """マウスドラッグ時の処理"""
        if not self.is_dragging or not self.drag_start:
            return

        # ドラッグ中の矩形を描画
        self.preview_canvas.delete("drag_rect")
        self.preview_canvas.delete("drag_info")

        # ドラッグ矩形
        x1, y1 = self.drag_start
        x2, y2 = event.x, event.y
        x = min(x1, x2)
        y = min(y1, y2)
        width = abs(x2 - x1)
        height = abs(y2 - y1)

        self.preview_canvas.create_rectangle(
            x, y, x + width, y + height,
            outline="blue", width=2, dash=(5, 5), tags="drag_rect"
        )

        # ドラッグ情報を表示
        info_text = f"ドラッグ中: {width} x {height}"
        self.preview_canvas.create_text(
            x + width // 2, y - 25,
            text=info_text,
            anchor=tk.CENTER, fill="blue", font=("TkDefaultFont", 9, "bold"),
            tags="drag_info"
        )

    def on_mouse_up(self, event):
        """マウスアップ時の処理"""
        if not self.is_dragging or not self.drag_start:
            return

        self.drag_end = (event.x, event.y)
        self.is_dragging = False

        # ドラッグ中の表示をクリア
        self.preview_canvas.delete("drag_rect")
        self.preview_canvas.delete("drag_info")

        # 新しい監視エリアを作成
        self.create_area_from_drag()

    def create_area_from_drag(self):
        """ドラッグから監視エリアを作成"""
        try:
            # 座標を正規化
            x1, y1 = self.drag_start
            x2, y2 = self.drag_end

            x = min(x1, x2)
            y = min(y1, y2)
            width = abs(x2 - x1)
            height = abs(y2 - y1)

            # 最小サイズチェック（キャンバス座標）
            if width < 20 or height < 20:
                messagebox.showwarning("警告", "監視エリアが小さすぎます。最小20x20ピクセル必要です。")
                return

            # 実際の画面サイズを取得
            try:
                import pyautogui
                screen_width, screen_height = pyautogui.size()
            except ImportError:
                # pyautoguiが利用できない場合は仮の値
                screen_width = 1920
                screen_height = 1080

            # スケールを計算
            canvas_width = self.preview_canvas.winfo_width()
            canvas_height = self.preview_canvas.winfo_height()

            if canvas_width > 1 and canvas_height > 1:
                scale_x = canvas_width / screen_width
                scale_y = canvas_height / screen_height
                scale = min(scale_x, scale_y)

                # キャンバス座標を画面座標に変換
                x_offset = (canvas_width - int(screen_width * scale)) // 2
                y_offset = (canvas_height - int(screen_height * scale)) // 2

                # ドラッグ座標を画面座標に変換（より精度の高い計算）
                screen_x = round((x - x_offset) / scale)
                screen_y = round((y - y_offset) / scale)
                screen_w = round(width / scale)
                screen_h = round(height / scale)

                # 座標変換のデバッグ情報
                logger.debug(f"ドラッグ座標: キャンバス({x},{y},{width},{height})")
                logger.debug(f"オフセット: ({x_offset},{y_offset}), スケール: {scale:.3f}")
                logger.debug(f"変換結果: 画面({screen_x},{screen_y},{screen_w},{screen_h})")

                # 画面範囲内に制限
                screen_x = max(0, min(screen_x, screen_width - screen_w))
                screen_y = max(0, min(screen_y, screen_height - screen_h))
                screen_w = min(screen_w, screen_width - screen_x)
                screen_h = min(screen_h, screen_height - screen_y)

                # 座標の整合性チェック
                if screen_w <= 0 or screen_h <= 0:
                    logger.warning("監視エリアのサイズが無効です")
                    messagebox.showwarning("警告", "監視エリアが画面外にはみ出しています")
                    return

                # 重複チェック：既存の監視エリアと重複していないか確認
                if self._is_area_overlapping(screen_x, screen_y, screen_w, screen_h):
                    logger.warning("既存の監視エリアと重複しています")
                    messagebox.showwarning("警告", "既存の監視エリアと重複しています。別の場所に監視エリアを作成してください。")
                    return

                # 新しい監視エリアを作成
                new_area = {
                    "name": f"監視エリア{len(self.monitor_areas) + 1}",
                    "x": screen_x,
                    "y": screen_y,
                    "width": screen_w,
                    "height": screen_h,
                    "enabled": True,
                    "description": "ドラッグで作成された監視エリア"
                }

                self.monitor_areas.append(new_area)
                self.current_area = new_area

                # UIを更新
                self.update_area_list()
                self.update_settings_display()

                # プレビューを更新（既存エリアの描画のみ）
                self.refresh_preview_areas()

                # リストで選択
                self.area_listbox.selection_clear(0, tk.END)
                self.area_listbox.selection_set(len(self.monitor_areas) - 1)
                self.area_listbox.see(len(self.monitor_areas) - 1)

                logger.info(f"新しい監視エリアを作成しました: {new_area['name']}")
                logger.debug(f"座標変換: キャンバス({x},{y},{width},{height}) -> 画面({screen_x},{screen_y},{screen_w},{screen_h})")
                logger.debug(f"スケール: {scale:.3f}, オフセット: ({x_offset},{y_offset})")

        except Exception as e:
            logger.error(f"ドラッグからの監視エリア作成エラー: {e}")
            messagebox.showerror("エラー", f"監視エリアの作成に失敗しました: {e}")

    def test_coordinate_conversion(self):
        """座標変換のテスト"""
        try:
            # 現在のキャンバスサイズとスケールを取得
            canvas_width = self.preview_canvas.winfo_width()
            canvas_height = self.preview_canvas.winfo_height()

            try:
                import pyautogui
                screen_width, screen_height = pyautogui.size()
            except ImportError:
                screen_width, screen_height = 1920, 1080

            if canvas_width > 1 and canvas_height > 1:
                scale_x = canvas_width / screen_width
                scale_y = canvas_height / screen_height
                scale = min(scale_x, scale_y)

                x_offset = (canvas_width - int(screen_width * scale)) // 2
                y_offset = (canvas_height - int(screen_height * scale)) // 2

                test_info = f"""座標変換テスト結果:

キャンバスサイズ: {canvas_width} x {canvas_height}
画面サイズ: {screen_width} x {screen_height}
スケール: {scale:.3f}
オフセット: ({x_offset}, {y_offset})

テスト座標変換:
キャンバス(100, 100, 200, 150) -> 画面({round((100 - x_offset) / scale)}, {round((100 - y_offset) / scale)}, {round(200 / scale)}, {round(150 / scale)})

逆変換テスト:
画面座標({round((100 - x_offset) / scale)}, {round((100 - y_offset) / scale)}) -> キャンバス({round((round((100 - x_offset) / scale) * scale) + x_offset)}, {round((round((100 - y_offset) / scale) * scale) + y_offset)})
"""

                messagebox.showinfo("座標変換テスト", test_info)
                logger.info("座標変換テストを実行しました")
            else:
                messagebox.showwarning("警告", "キャンバスサイズが取得できません")

        except Exception as e:
            logger.error(f"座標変換テストエラー: {e}")
            messagebox.showerror("エラー", f"座標変換テストに失敗しました: {e}")

    def refresh_preview_areas(self):
        """監視エリアのプレビューのみを更新"""
        try:
            # 既存の監視エリアをクリア
            self.preview_canvas.delete("area_rect")
            self.preview_canvas.delete("area_label")
            self.preview_canvas.delete("area_coord")

            # 現在のスケールとオフセットを取得
            canvas_width = self.preview_canvas.winfo_width()
            canvas_height = self.preview_canvas.winfo_height()

            try:
                import pyautogui
                screen_width, screen_height = pyautogui.size()
            except ImportError:
                screen_width, screen_height = 1920, 1080

            if canvas_width > 1 and canvas_height > 1:
                scale_x = canvas_width / screen_width
                scale_y = canvas_height / screen_height
                scale = min(scale_x, scale_y)

                x_offset = (canvas_width - int(screen_width * scale)) // 2
                y_offset = (canvas_height - int(screen_height * scale)) // 2

                # 既存の監視エリアを描画
                self.draw_existing_areas(x_offset, y_offset, scale)

                logger.debug("監視エリアプレビューを更新しました")

        except Exception as e:
            logger.error(f"プレビュー更新エラー: {e}")

    def add_new_area(self):
        """新規監視エリア追加の準備（ドラッグ作業の開始）"""
        try:
            logger.info("新規監視エリア作成の準備を開始しました")

            # 新規作成ボタンクリック時は、実際の監視エリアは作成しない
            # 代わりに、ドラッグ作業の準備を行う
            messagebox.showinfo("新規作成", "画面をドラッグして監視エリアを作成してください。\n\n新規作成ボタンは、ドラッグ作業の開始を示すものです。")

            # プレビューキャンバスにフォーカスを設定（メッセージ自動入力の阻害を防ぐため一時的にコメントアウト）
            # self.preview_canvas.focus_set()

            logger.info("新規監視エリア作成の準備が完了しました")

        except Exception as e:
            logger.error(f"新規監視エリア作成準備エラー: {e}")
            messagebox.showerror("エラー", f"新規監視エリア作成の準備に失敗しました: {e}")

    def delete_selected_area(self):
        """選択された監視エリアを削除"""
        selection = self.area_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "削除する監視エリアを選択してください")
            return

        index = selection[0]
        area = self.monitor_areas[index]

        if not messagebox.askyesno("確認", f"監視エリア '{area['name']}' を削除しますか？"):
            return

        try:
            deleted_area = self.monitor_areas.pop(index)
            logger.info(f"監視エリアを削除しました: {deleted_area['name']}")

            # UIを更新
            self.update_area_list()
            self.current_area = None
            self.clear_settings_display()
            self.draw_screen_preview()

        except Exception as e:
            logger.error(f"監視エリア削除エラー: {e}")
            messagebox.showerror("エラー", f"監視エリアの削除に失敗しました: {e}")

    def on_area_selected(self, event):
        """監視エリア選択時の処理"""
        selection = self.area_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        self.current_area = self.monitor_areas[index]
        self.update_settings_display()

        logger.debug(f"監視エリアを選択しました: {self.current_area['name']}")

    def update_area_list(self):
        """監視エリアリストを更新"""
        self.area_listbox.delete(0, tk.END)

        for area in self.monitor_areas:
            status = "有効" if area.get("enabled", True) else "無効"
            display_text = f"{area['name']} ({status})"
            self.area_listbox.insert(tk.END, display_text)

    def update_settings_display(self):
        """設定表示を更新"""
        if not self.current_area:
            self.clear_settings_display()
            return

        area = self.current_area

        self.name_var.set(area.get("name", ""))
        self.x_var.set(str(area.get("x", 0)))
        self.y_var.set(str(area.get("y", 0)))
        self.width_var.set(str(area.get("width", 0)))
        self.height_var.set(str(area.get("height", 0)))
        self.enabled_var.set(area.get("enabled", True))
        self.desc_var.set(area.get("description", ""))

    def clear_settings_display(self):
        """設定表示をクリア"""
        self.name_var.set("")
        self.x_var.set("")
        self.y_var.set("")
        self.width_var.set("")
        self.height_var.set("")
        self.enabled_var.set(True)
        self.desc_var.set("")

    def save_monitor_areas(self):
        """監視エリアを保存"""
        try:
            # 現在の設定を反映
            if self.current_area:
                self.update_current_area_from_ui()

            # 監視エリアとチャット入力欄位置を保存
            self.config_manager.set("monitor_areas", self.monitor_areas)
            if self.chat_input_position:
                self.config_manager.set("chat_input_position", self.chat_input_position)
                logger.info(f"チャット入力欄位置も保存: {self.chat_input_position}")

            self.config_manager.save_config()

            messagebox.showinfo("完了", "監視エリア設定とチャット入力欄位置を保存しました")
            logger.info("監視エリア設定とチャット入力欄位置を保存しました")

            # ダイアログを閉じる
            self.dialog.destroy()

        except Exception as e:
            logger.error(f"設定保存エラー: {e}")
            messagebox.showerror("エラー", f"設定の保存に失敗しました: {e}")

    def update_current_area_from_ui(self):
        """UIから現在の監視エリアを更新"""
        if not self.current_area:
            return

        try:
            self.current_area["name"] = self.name_var.get()
            self.current_area["x"] = int(self.x_var.get())
            self.current_area["y"] = int(self.y_var.get())
            self.current_area["width"] = int(self.width_var.get())
            self.current_area["height"] = int(self.height_var.get())
            self.current_area["enabled"] = self.enabled_var.get()
            self.current_area["description"] = self.desc_var.get()

            # リストを更新
            self.update_area_list()
            self.draw_screen_preview()

        except ValueError as e:
            logger.error(f"設定値の検証エラー: {e}")
            messagebox.showerror("エラー", "無効な設定値が入力されています。数値フィールドには数値を入力してください。")
            raise

    def test_selected_area(self):
        """選択された監視エリアをテスト"""
        if not self.current_area:
            messagebox.showwarning("警告", "テストする監視エリアを選択してください")
            return

        try:
            area = self.current_area
            messagebox.showinfo("テスト",
                              f"監視エリア '{area['name']}' のテストを実行します。\n"
                              f"座標: ({area['x']}, {area['y']})\n"
                              f"サイズ: {area['width']} x {area['height']}\n"
                              f"有効: {'はい' if area.get('enabled', True) else 'いいえ'}")

            logger.info(f"監視エリア '{area['name']}' のテストを実行しました")

        except Exception as e:
            logger.error(f"監視エリアテストエラー: {e}")
            messagebox.showerror("エラー", f"監視エリアのテストに失敗しました: {e}")

    def setup_chat_input(self):
        """チャット入力欄の設定"""
        try:
            # 説明ダイアログを表示
            if not self.show_chat_setup_instructions():
                return  # ユーザーがキャンセルした場合

            # ダイアログを非表示（transientウィンドウのためiconifyは使用不可）
            self.dialog.withdraw()

            # 3秒待機
            import time
            time.sleep(3)

            # チャット入力欄の位置を取得
            import pyautogui
            chat_pos = pyautogui.position()

            # 設定を保存
            self.chat_input_position = [chat_pos.x, chat_pos.y]

            # ダイアログを再表示
            self.dialog.deiconify()

            # 完了メッセージ
            messagebox.showinfo(
                "設定完了",
                f"チャット入力欄の位置を設定しました:\n座標: ({chat_pos.x}, {chat_pos.y})"
            )

            logger.info(f"チャット入力欄の位置を設定: ({chat_pos.x}, {chat_pos.y})")

        except Exception as e:
            # エラー時はダイアログを再表示
            with suppress(Exception):
                self.dialog.deiconify()

            logger.error(f"チャット入力欄設定エラー: {e}")
            messagebox.showerror("エラー", f"チャット入力欄の設定に失敗しました: {e}")

    def show_chat_setup_instructions(self) -> bool:
        """チャット欄設定の説明ダイアログを表示"""
        try:
            # 説明ダイアログを作成
            instruction_dialog = tk.Toplevel(self.dialog)
            instruction_dialog.title("チャット欄設定 - 手順説明")
            instruction_dialog.geometry("500x400")
            instruction_dialog.transient(self.dialog)
            instruction_dialog.grab_set()

            # ダイアログの位置を親ダイアログの中央に設定
            x_pos = self.dialog.winfo_rootx() + 100
            y_pos = self.dialog.winfo_rooty() + 100
            instruction_dialog.geometry(f"+{x_pos}+{y_pos}")

            # メインフレーム
            main_frame = ttk.Frame(instruction_dialog, padding="20")
            main_frame.pack(fill=tk.BOTH, expand=True)

            # タイトル
            title_label = ttk.Label(main_frame, text="チャット欄設定の手順",
                                  font=("TkDefaultFont", 14, "bold"))
            title_label.pack(pady=(0, 20))

            # 説明テキスト
            instruction_text = """チャット入力欄の位置を設定するために、以下の手順を実行します：

1. 「設定開始」ボタンをクリックすると、このダイアログが非表示になります

2. 3秒後に、設定したいチャット入力欄をクリックしてください
   （例：AmazonQのチャットボックス、Discordのメッセージ入力欄など）

3. クリックした位置の座標が自動的に記録されます

4. 設定が完了すると、このダイアログが再表示されます

注意：
• チャット入力欄が実際にフォーカスされる位置をクリックしてください
• クリック後は、その位置に復旧コマンドが送信されます
• 設定をキャンセルする場合は「キャンセル」ボタンをクリックしてください"""

            instruction_label = ttk.Label(main_frame, text=instruction_text,
                                        justify=tk.LEFT, wraplength=450)
            instruction_label.pack(pady=(0, 20))

            # ボタンフレーム
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill=tk.X, pady=(20, 0))

            # 設定開始ボタン
            start_button = ttk.Button(button_frame, text="設定開始",
                                    command=lambda: self.start_chat_setup(instruction_dialog))
            start_button.pack(side=tk.RIGHT, padx=(10, 0))

            # キャンセルボタン
            cancel_button = ttk.Button(button_frame, text="キャンセル",
                                     command=instruction_dialog.destroy)
            cancel_button.pack(side=tk.RIGHT)

            # ダイアログが閉じられるまで待機
            instruction_dialog.wait_window()

            # 設定開始ボタンがクリックされたかチェック
            return hasattr(self, '_chat_setup_started') and self._chat_setup_started

        except Exception as e:
            logger.error(f"説明ダイアログ表示エラー: {e}")
            return False

    def start_chat_setup(self, instruction_dialog):
        """チャット欄設定を開始"""
        try:
            # 設定開始フラグを設定
            self._chat_setup_started = True

            # 説明ダイアログを閉じる
            instruction_dialog.destroy()

            logger.info("チャット欄設定を開始しました")

        except Exception as e:
            logger.error(f"チャット欄設定開始エラー: {e}")
            self._chat_setup_started = False

    def load_chat_input_position(self):
        """チャット入力欄の位置を読み込み"""
        try:
            position = self.config_manager.get("chat_input_position")
            if position and isinstance(position, list) and len(position) == 2:
                self.chat_input_position = position
                logger.debug(f"チャット入力欄の位置を読み込み: {position}")
            else:
                self.chat_input_position = None
                logger.debug("チャット入力欄の位置が設定されていません")
        except Exception as e:
            logger.error(f"チャット入力欄位置読み込みエラー: {e}")
            self.chat_input_position = None

    def load_monitor_areas(self):
        """監視エリアを読み込み"""
        try:
            # 設定から監視エリアを読み込み
            areas = self.config_manager.get("monitor_areas", [])
            self.monitor_areas = areas if isinstance(areas, list) else []

            # UIを更新
            self.update_area_list()

            if self.monitor_areas:
                # 最初のエリアを選択
                self.area_listbox.selection_set(0)
                self.on_area_selected(None)

            logger.debug(f"{len(self.monitor_areas)}個の監視エリアを読み込みました")

        except Exception as e:
            logger.error(f"監視エリア読み込みエラー: {e}")
            self.monitor_areas = []

    def refresh_screenshot(self):
        """スクリーンショットを更新"""
        try:
            logger.info("スクリーンショットを更新しています...")

            # プレビューを再描画
            self.draw_screen_preview()

            messagebox.showinfo("完了", "スクリーンショットを更新しました")
            logger.info("スクリーンショットを更新しました")

        except Exception as e:
            logger.error(f"スクリーンショット更新エラー: {e}")
            messagebox.showerror("エラー", f"スクリーンショットの更新に失敗しました: {e}")

    def cancel(self):
        """キャンセル処理"""
        logger.info("監視エリア設定ダイアログをキャンセルしました")
        self.dialog.destroy()

    def _is_area_overlapping(self, x: int, y: int, width: int, height: int) -> bool:
        """監視エリアの重複チェック"""
        try:
            # 新しいエリアの境界
            new_left = x
            new_right = x + width
            new_top = y
            new_bottom = y + height

            for existing_area in self.monitor_areas:
                if not existing_area.get("enabled", True):
                    continue  # 無効なエリアはスキップ

                # 既存エリアの境界
                existing_left = existing_area["x"]
                existing_right = existing_area["x"] + existing_area["width"]
                existing_top = existing_area["y"]
                existing_bottom = existing_area["y"] + existing_area["height"]

                # 重複チェック（境界が重なっている場合）
                if not (new_right <= existing_left or new_left >= existing_right or
                       new_bottom <= existing_top or new_top >= existing_bottom):
                    logger.debug(f"重複検出: 新エリア({x},{y},{width},{height}) と 既存エリア({existing_area['x']},{existing_area['y']},{existing_area['width']},{existing_area['height']})")
                    return True

            return False

        except Exception as e:
            logger.error(f"重複チェックエラー: {e}")
            return False  # エラー時は重複なしとして扱う
