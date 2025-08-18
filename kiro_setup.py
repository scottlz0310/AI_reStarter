#!/usr/bin/env python3
"""
Kiro-IDE自動復旧システム設定アプリ
対話的に監視エリアとチャット欄を設定
"""

import json
import os
import time
import tkinter as tk
from tkinter import messagebox

import pyautogui
import win32con
import win32gui


class KiroSetupApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Kiro-IDE自動復旧システム設定")
        self.root.geometry("600x500")
        self.root.resizable(False, False)

        # 設定値
        self.monitor_region = None  # [x, y, width, height]
        self.chat_input_position = None  # [x, y]
        self.config_file = "kiro_config.json"

        # 現在の設定を読み込み
        self.load_current_config()

        # UI作成
        self.create_ui()

    def load_current_config(self) -> None:
        """現在の設定ファイルを読み込み"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, encoding="utf-8") as f:
                    config = json.load(f)
                    self.monitor_region = config.get("monitor_region")
                    self.chat_input_position = config.get("chat_input_position")
        except Exception as e:
            print(f"設定ファイル読み込みエラー: {e}")

    def create_ui(self) -> None:
        """UIを作成"""
        # メインフレーム
        main_frame = tk.Frame(self.root, padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # タイトル
        title_label = tk.Label(
            main_frame, text="Kiro-IDE自動復旧システム設定", font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(0, 20))

        # 監視エリア設定セクション
        monitor_frame = tk.LabelFrame(
            main_frame, text="監視エリア設定", padx=10, pady=10
        )
        monitor_frame.pack(fill=tk.X, pady=(0, 10))

        monitor_desc = tk.Label(
            monitor_frame,
            text="エラーを検出する画面領域を指定してください\n"
            "左上と右下の2点をクリックして範囲を設定します",
            justify=tk.LEFT,
        )
        monitor_desc.pack(anchor=tk.W, pady=(0, 10))

        self.monitor_btn = tk.Button(
            monitor_frame,
            text="監視エリアを設定",
            command=self.set_monitor_region,
            bg="#4CAF50",
            fg="white",
            font=("Arial", 10, "bold"),
        )
        self.monitor_btn.pack(pady=(0, 5))

        self.monitor_label = tk.Label(monitor_frame, text="未設定", fg="red")
        self.monitor_label.pack()

        # チャット欄設定セクション
        chat_frame = tk.LabelFrame(main_frame, text="チャット欄設定", padx=10, pady=10)
        chat_frame.pack(fill=tk.X, pady=(0, 10))

        chat_desc = tk.Label(
            chat_frame,
            text="Kiro-IDEのチャット入力欄を指定してください\n"
            "チャット入力欄をクリックして位置を設定します",
            justify=tk.LEFT,
        )
        chat_desc.pack(anchor=tk.W, pady=(0, 10))

        self.chat_btn = tk.Button(
            chat_frame,
            text="チャット欄を設定",
            command=self.set_chat_position,
            bg="#2196F3",
            fg="white",
            font=("Arial", 10, "bold"),
        )
        self.chat_btn.pack(pady=(0, 5))

        self.chat_label = tk.Label(chat_frame, text="未設定", fg="red")
        self.chat_label.pack()

        # 設定保存セクション
        save_frame = tk.LabelFrame(main_frame, text="設定保存", padx=10, pady=10)
        save_frame.pack(fill=tk.X, pady=(0, 10))

        self.save_btn = tk.Button(
            save_frame,
            text="設定を保存",
            command=self.save_config,
            bg="#FF9800",
            fg="white",
            font=("Arial", 12, "bold"),
            state=tk.DISABLED,
        )
        self.save_btn.pack()

        # テストセクション
        test_frame = tk.LabelFrame(main_frame, text="テスト機能", padx=10, pady=10)
        test_frame.pack(fill=tk.X, pady=(0, 10))

        self.test_btn = tk.Button(
            test_frame,
            text="復旧コマンドテスト",
            command=self.test_recovery,
            bg="#9C27B0",
            fg="white",
            font=("Arial", 10, "bold"),
        )
        self.test_btn.pack()

        # 現在の設定を表示
        self.update_display()

    def set_monitor_region(self) -> None:
        """監視エリアを設定"""
        try:
            # ウィンドウを最小化
            self.root.iconify()
            time.sleep(1)

            # 強制フォーカスをKiro-IDEに
            self.force_focus_kiro()

            messagebox.showinfo(
                "監視エリア設定",
                "監視エリアの左上をクリックしてください\n"
                "OKを押すと3秒後にクリック位置を取得します",
            )

            time.sleep(3)
            top_left = pyautogui.position()

            messagebox.showinfo(
                "監視エリア設定",
                f"左上位置: {top_left}\n\n"
                "次に右下をクリックしてください\n"
                "OKを押すと3秒後にクリック位置を取得します",
            )

            time.sleep(3)
            bottom_right = pyautogui.position()

            # 監視エリアを計算
            x = min(top_left.x, bottom_right.x)
            y = min(top_left.y, bottom_right.y)
            width = abs(bottom_right.x - top_left.x)
            height = abs(bottom_right.y - top_left.y)

            self.monitor_region = [x, y, width, height]

            # ウィンドウを復元
            self.root.deiconify()

            messagebox.showinfo(
                "設定完了",
                f"監視エリアを設定しました:\n"
                f"位置: ({x}, {y})\n"
                f"サイズ: {width} x {height}",
            )

            self.update_display()

        except Exception as e:
            self.root.deiconify()
            messagebox.showerror("エラー", f"監視エリア設定エラー: {e}")

    def set_chat_position(self) -> None:
        """チャット欄位置を設定"""
        try:
            # ウィンドウを最小化
            self.root.iconify()
            time.sleep(1)

            # 強制フォーカスをKiro-IDEに
            self.force_focus_kiro()

            messagebox.showinfo(
                "チャット欄設定",
                "Kiro-IDEのチャット入力欄をクリックしてください\n"
                "OKを押すと3秒後にクリック位置を取得します",
            )

            time.sleep(3)
            chat_pos = pyautogui.position()

            self.chat_input_position = [chat_pos.x, chat_pos.y]

            # ウィンドウを復元
            self.root.deiconify()

            messagebox.showinfo(
                "設定完了",
                f"チャット欄位置を設定しました:\n"
                f"位置: ({chat_pos.x}, {chat_pos.y})",
            )

            self.update_display()

        except Exception as e:
            self.root.deiconify()
            messagebox.showerror("エラー", f"チャット欄設定エラー: {e}")

    def force_focus_kiro(self) -> None:
        """Kiro-IDEウィンドウに強制フォーカス"""
        try:
            windows = pyautogui.getAllWindows()
            kiro_windows = [w for w in windows if "kiro" in w.title.lower()]

            # Qt-Theme-StudioのKiroウィンドウを優先
            target_window = None
            for window in kiro_windows:
                if (
                    "qt-theme-studio" in window.title.lower()
                    or "qt-theme" in window.title.lower()
                ):
                    target_window = window
                    break

            if not target_window and kiro_windows:
                target_window = kiro_windows[0]

            if target_window:
                target_window.activate()
                time.sleep(0.5)

                hwnd = win32gui.FindWindow(None, target_window.title)
                if hwnd:
                    win32gui.SetForegroundWindow(hwnd)
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                    time.sleep(0.5)

        except Exception as e:
            print(f"フォーカスエラー: {e}")

    def update_display(self) -> None:
        """表示を更新"""
        # 監視エリア表示
        if self.monitor_region:
            x, y, w, h = self.monitor_region
            self.monitor_label.config(
                text=f"設定済み: 位置({x}, {y}), サイズ({w} x {h})", fg="green"
            )
        else:
            self.monitor_label.config(text="未設定", fg="red")

        # チャット欄表示
        if self.chat_input_position:
            x, y = self.chat_input_position
            self.chat_label.config(text=f"設定済み: 位置({x}, {y})", fg="green")
        else:
            self.chat_label.config(text="未設定", fg="red")

        # 保存ボタンの有効化
        if self.monitor_region and self.chat_input_position:
            self.save_btn.config(state=tk.NORMAL)
        else:
            self.save_btn.config(state=tk.DISABLED)

    def save_config(self) -> None:
        """設定を保存"""
        try:
            # 現在の設定を読み込み
            config = {}
            if os.path.exists(self.config_file):
                with open(self.config_file, encoding="utf-8") as f:
                    config = json.load(f)

            # 新しい設定を更新
            config["monitor_region"] = self.monitor_region
            config["chat_input_position"] = self.chat_input_position

            # 保存
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)

            messagebox.showinfo("保存完了", "設定を保存しました！")

        except Exception as e:
            messagebox.showerror("エラー", f"設定保存エラー: {e}")

    def test_recovery(self) -> None:
        """復旧コマンドテスト"""
        if not self.chat_input_position:
            messagebox.showwarning("警告", "チャット欄位置が設定されていません")
            return

        try:
            # ウィンドウを最小化
            self.root.iconify()
            time.sleep(1)

            # 強制フォーカスをKiro-IDEに
            self.force_focus_kiro()

            messagebox.showinfo(
                "テスト実行",
                "復旧コマンドテストを実行します\n"
                "OKを押すと3秒後にテストを開始します",
            )

            time.sleep(3)

            # チャット欄をクリック
            pyautogui.click(self.chat_input_position[0], self.chat_input_position[1])
            time.sleep(0.5)

            # テストメッセージを入力
            pyautogui.write("設定テストメッセージ", interval=0.1)
            time.sleep(1)

            # Enterキーで送信
            pyautogui.press("enter")

            # ウィンドウを復元
            self.root.deiconify()

            messagebox.showinfo("テスト完了", "復旧コマンドテストが完了しました")

        except Exception as e:
            self.root.deiconify()
            messagebox.showerror("エラー", f"テストエラー: {e}")

    def run(self) -> None:
        """アプリを実行"""
        self.root.mainloop()


def main() -> None:
    """メイン関数"""
    app = KiroSetupApp()
    app.run()


if __name__ == "__main__":
    main()
