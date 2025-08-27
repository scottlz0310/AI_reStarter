"""
テンプレート範囲選択ダイアログ
ユーザーが画面上で範囲を選択してテンプレートを保存する機能
"""

import logging
import tkinter as tk
from tkinter import messagebox
from tkinter import simpledialog
from typing import Optional

import cv2
import numpy as np
from PIL import Image
from PIL import ImageTk

from src.utils.screen_capture import ScreenCapture

logger = logging.getLogger(__name__)


class TemplateCaptureDialog:
    """テンプレート範囲選択ダイアログ"""

    def __init__(self, parent: tk.Tk):
        self.parent = parent
        self.screen_capture = ScreenCapture()
        self.dialog = None
        self.canvas = None
        self.screenshot = None
        self.photo_image = None
        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None
        self.selection_rect = None
        self.selected_region = None

        logger.debug("テンプレート範囲選択ダイアログを初期化")

    def show(self) -> tuple[np.ndarray, str] | None:
        """
        ダイアログを表示してテンプレート範囲を選択

        Returns:
            Tuple[np.ndarray, str]: (選択された画像, テンプレート名) または None
        """
        try:
            # 画面全体をキャプチャ
            self.screenshot = self.screen_capture.capture_screen()
            if self.screenshot is None:
                messagebox.showerror("エラー", "画面キャプチャに失敗しました")
                return None

            # ダイアログウィンドウを作成
            self.dialog = tk.Toplevel(self.parent)
            self.dialog.title("テンプレート範囲選択")
            self.dialog.geometry("1600x900")  # 固定サイズ
            self.dialog.transient(self.parent)
            self.dialog.grab_set()

            # ESCキーで閉じる
            self.dialog.bind("<Escape>", lambda e: self.cancel())

            self.setup_ui()

            # ダイアログが閉じられるまで待機
            self.dialog.wait_window()

            return self.selected_region

        except Exception as e:
            logger.error(f"テンプレート範囲選択ダイアログ表示エラー: {e}")
            messagebox.showerror("エラー", f"ダイアログの表示に失敗しました: {e}")
            return None

    def setup_ui(self):
        """UIの初期化"""
        # メインフレーム
        main_frame = tk.Frame(self.dialog)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 説明ラベル
        instruction_frame = tk.Frame(main_frame)
        instruction_frame.pack(fill=tk.X, padx=10, pady=5)

        instruction_text = (
            "マウスでドラッグしてテンプレートにしたい範囲を選択してください。\n"
            "選択後、「保存」ボタンをクリックしてテンプレート名を入力してください。"
        )
        tk.Label(instruction_frame, text=instruction_text, font=("Arial", 10)).pack()

        # キャンバスフレーム（スクロール可能、高さ制限）
        canvas_frame = tk.Frame(main_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # キャンバスフレームの高さを制限してボタンエリアを確保
        canvas_frame.pack_propagate(False)
        canvas_frame.config(height=750)  # ボタンエリア用に150px確保

        # スクロールバー
        v_scrollbar = tk.Scrollbar(canvas_frame, orient=tk.VERTICAL)
        h_scrollbar = tk.Scrollbar(canvas_frame, orient=tk.HORIZONTAL)

        # キャンバス
        self.canvas = tk.Canvas(
            canvas_frame,
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set,
            bg="white",
            highlightthickness=0,
            bd=0,
        )

        v_scrollbar.config(command=self.canvas.yview)
        h_scrollbar.config(command=self.canvas.xview)

        # 配置
        self.canvas.grid(row=0, column=0, sticky=tk.NSEW)
        v_scrollbar.grid(row=0, column=1, sticky=tk.NS)
        h_scrollbar.grid(row=1, column=0, sticky=tk.EW)

        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)

        # 画像を表示
        self.display_screenshot()

        # キャンバスをフォーカス可能にする
        self.canvas.config(takefocus=True)
        self.canvas.focus_set()

        # マウスイベントをバインド
        self.canvas.bind("<Button-1>", self.on_mouse_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_release)

        # デバッグ用：マウス移動イベントも追加
        self.canvas.bind("<Motion>", self.on_mouse_motion)

        # 追加のマウスイベント
        self.canvas.bind(
            "<Enter>", lambda e: print("DEBUG: マウスがキャンバスに入った")
        )
        self.canvas.bind(
            "<Leave>", lambda e: print("DEBUG: マウスがキャンバスから出た")
        )

        # ボタンフレーム（最下部に固定配置）
        button_frame = tk.Frame(self.dialog, bg="lightgray", relief="raised", bd=2)
        button_frame.pack(fill=tk.X, padx=10, pady=5, side=tk.BOTTOM, before=main_frame)

        # ボタンを大きくして見やすく
        tk.Button(
            button_frame,
            text="保存",
            command=self.save_template,
            font=("Arial", 12),
            bg="green",
            fg="white",
            width=10,
        ).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(
            button_frame,
            text="キャンセル",
            command=self.cancel,
            font=("Arial", 12),
            bg="red",
            fg="white",
            width=10,
        ).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(
            button_frame,
            text="選択をクリア",
            command=self.clear_selection_full,
            font=("Arial", 12),
            width=12,
        ).pack(side=tk.LEFT, padx=5, pady=5)

        # 選択情報表示
        self.info_label = tk.Label(
            button_frame,
            text="範囲を選択してください",
            font=("Arial", 11),
            bg="lightgray",
        )
        self.info_label.pack(side=tk.RIGHT, padx=5, pady=5)

    def display_screenshot(self):
        """スクリーンショットをキャンバスに表示"""
        try:
            # OpenCVからPILに変換
            if len(self.screenshot.shape) == 3:
                # BGR to RGB
                rgb_image = cv2.cvtColor(self.screenshot, cv2.COLOR_BGR2RGB)
            else:
                rgb_image = self.screenshot

            # 画像サイズを取得
            height, width = rgb_image.shape[:2]
            print(f"DEBUG: 画像サイズ - width={width}, height={height}")

            pil_image = Image.fromarray(rgb_image)
            self.photo_image = ImageTk.PhotoImage(pil_image)

            # キャンバスサイズを画像に合わせて設定
            self.canvas.config(width=min(width, 1200), height=min(height, 800))

            # キャンバスに画像を表示
            self.image_item = self.canvas.create_image(
                0, 0, anchor=tk.NW, image=self.photo_image
            )

            # スクロール領域を設定
            self.canvas.configure(scrollregion=(0, 0, width, height))

            logger.debug(f"スクリーンショット表示完了: {self.screenshot.shape}")
            print(f"DEBUG: キャンバス設定完了 - scrollregion=(0, 0, {width}, {height})")

        except Exception as e:
            logger.error(f"スクリーンショット表示エラー: {e}")
            messagebox.showerror("エラー", f"画像の表示に失敗しました: {e}")

    def on_mouse_press(self, event):
        """マウス押下時の処理"""
        # 既存の選択範囲をクリア（座標設定前に実行）
        self.clear_selection()

        # 直接座標を使用（シンプルな方法）
        self.start_x = float(event.x)
        self.start_y = float(event.y)
        print(f"DEBUG: 座標設定 - start_x={self.start_x}, start_y={self.start_y}")

        # キャンバスにフォーカスを設定
        self.canvas.focus_set()

        logger.debug(f"選択開始: ({self.start_x}, {self.start_y})")
        print(
            f"DEBUG: マウス押下 - event.x={event.x}, event.y={event.y}, start_x={self.start_x}, start_y={self.start_y}"
        )

        # 初期矩形を作成（サイズ0で）
        try:
            self.selection_rect = self.canvas.create_rectangle(
                self.start_x,
                self.start_y,
                self.start_x,
                self.start_y,
                outline="red",
                width=3,
            )
            print(f"DEBUG: 矩形作成成功 - rect_id={self.selection_rect}")
        except Exception as e:
            print(f"DEBUG: 矩形作成エラー - {e}")
            print(
                f"DEBUG: 座標情報 - start_x={self.start_x} ({type(self.start_x)}), start_y={self.start_y} ({type(self.start_y)})"
            )

    def on_mouse_drag(self, event):
        """マウスドラッグ時の処理"""
        if self.start_x is None or self.start_y is None:
            print("DEBUG: ドラッグ中だが開始座標が未設定")
            return

        # 現在の座標
        current_x = float(event.x)
        current_y = float(event.y)

        # print(f"DEBUG: ドラッグ中 - current_x={current_x}, current_y={current_y}")  # コメントアウトして出力を減らす

        # 既存の選択矩形を更新
        if self.selection_rect:
            self.canvas.coords(
                self.selection_rect, self.start_x, self.start_y, current_x, current_y
            )
        else:
            # 矩形が存在しない場合は新規作成
            self.selection_rect = self.canvas.create_rectangle(
                self.start_x,
                self.start_y,
                current_x,
                current_y,
                outline="red",
                width=3,
                fill="",
            )

        # 選択範囲の情報を更新
        width = abs(current_x - self.start_x)
        height = abs(current_y - self.start_y)
        self.info_label.config(text=f"選択範囲: {int(width)} x {int(height)} px")

    def on_mouse_release(self, event):
        """マウス離した時の処理"""
        if self.start_x is None or self.start_y is None:
            return

        self.end_x = float(event.x)
        self.end_y = float(event.y)

        # 選択範囲が小さすぎる場合は無効
        width = abs(self.end_x - self.start_x)
        height = abs(self.end_y - self.start_y)

        if width < 10 or height < 10:
            self.clear_selection()
            self.info_label.config(text="選択範囲が小さすぎます（最小10x10px）")
            return

        logger.debug(
            f"選択完了: ({self.start_x}, {self.start_y}) - ({self.end_x}, {self.end_y})"
        )
        self.info_label.config(text=f"選択完了: {int(width)} x {int(height)} px")

    def clear_selection(self):
        """選択範囲をクリア"""
        if self.selection_rect:
            self.canvas.delete(self.selection_rect)
            self.selection_rect = None

        # 座標はクリアしない（マウス押下時に新しい値が設定される）
        # self.start_x = None
        # self.start_y = None
        self.end_x = None
        self.end_y = None
        if hasattr(self, "info_label"):
            self.info_label.config(text="範囲を選択してください")

    def save_template(self):
        """選択範囲をテンプレートとして保存"""
        if (
            self.start_x is None
            or self.start_y is None
            or self.end_x is None
            or self.end_y is None
        ):
            messagebox.showwarning("警告", "範囲を選択してください")
            return

        try:
            # テンプレート名を入力
            template_name = simpledialog.askstring(
                "テンプレート名",
                "テンプレート名を入力してください:",
                parent=self.dialog,
            )

            if not template_name:
                return

            # 選択範囲を正規化
            x1 = int(min(self.start_x, self.end_x))
            y1 = int(min(self.start_y, self.end_y))
            x2 = int(max(self.start_x, self.end_x))
            y2 = int(max(self.start_y, self.end_y))

            # 画像の境界内に制限
            height, width = self.screenshot.shape[:2]
            x1 = max(0, min(x1, width - 1))
            y1 = max(0, min(y1, height - 1))
            x2 = max(0, min(x2, width - 1))
            y2 = max(0, min(y2, height - 1))

            # 選択範囲を切り出し
            selected_image = self.screenshot[y1:y2, x1:x2]

            if selected_image.size == 0:
                messagebox.showerror("エラー", "選択範囲が無効です")
                return

            # 結果を設定
            self.selected_region = (selected_image, template_name)

            logger.info(
                f"テンプレート範囲選択完了: {template_name} ({x2 - x1}x{y2 - y1})"
            )

            # ダイアログを閉じる
            self.dialog.destroy()

        except Exception as e:
            logger.error(f"テンプレート保存エラー: {e}")
            messagebox.showerror("エラー", f"テンプレートの保存に失敗しました: {e}")

    def on_mouse_motion(self, event):
        """マウス移動時の処理（デバッグ用）"""
        x = float(event.x)
        y = float(event.y)
        # デバッグ情報を少なくする
        if (
            hasattr(self, "_last_motion_log")
            and abs(x - self._last_motion_log[0]) < 50
            and abs(y - self._last_motion_log[1]) < 50
        ):
            return
        self._last_motion_log = (x, y)
        # print(f"DEBUG: マウス移動 - x={x}, y={y}")  # コメントアウトして出力を減らす

    def clear_selection_full(self):
        """完全な選択クリア（ボタン用）"""
        if self.selection_rect:
            self.canvas.delete(self.selection_rect)
            self.selection_rect = None

        self.start_x = None
        self.start_y = None
        self.end_x = None
        self.end_y = None
        self.info_label.config(text="範囲を選択してください")

    def cancel(self):
        """キャンセル"""
        self.selected_region = None
        self.dialog.destroy()
