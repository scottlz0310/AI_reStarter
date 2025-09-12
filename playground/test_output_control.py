#!/usr/bin/env python3
"""
出力制御システムのテスト
標準出力とログウィンドウの制御をテスト
"""

import sys
import time
import tkinter as tk
from pathlib import Path
from tkinter import ttk

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.output_controller import OutputLevel
from src.utils.output_controller import OutputTarget
from src.utils.output_controller import output_controller


def test_output_control():
    """出力制御システムのテスト"""

    # テストウィンドウを作成
    root = tk.Tk()
    root.title("出力制御システムテスト")
    root.geometry("600x400")

    # ログ表示エリア
    log_frame = ttk.LabelFrame(root, text="リアルタイムログ", padding="10")
    log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    log_text = tk.Text(log_frame, font=("Consolas", 9))
    scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=log_text.yview)
    log_text.configure(yscrollcommand=scrollbar.set)

    log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # GUIコールバック関数
    def gui_callback(message: str, level: str):
        """GUIログウィンドウにメッセージを追加"""
        timestamp = time.strftime("%H:%M:%S")
        log_line = f"[{timestamp}] [{level}] {message}\n"
        log_text.insert(tk.END, log_line)
        log_text.see(tk.END)

        # レベル別の色付け
        if level == "ERROR":
            log_text.tag_add(
                "error", f"{log_text.index(tk.END)}-2l", f"{log_text.index(tk.END)}-1l"
            )
            log_text.tag_config("error", foreground="red")
        elif level == "WARNING":
            log_text.tag_add(
                "warning",
                f"{log_text.index(tk.END)}-2l",
                f"{log_text.index(tk.END)}-1l",
            )
            log_text.tag_config("warning", foreground="orange")

    # 出力制御システムにGUIコールバックを設定
    output_controller.set_gui_callback(gui_callback)

    # コントロールパネル
    control_frame = ttk.LabelFrame(root, text="出力制御", padding="10")
    control_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

    # 出力先選択
    target_var = tk.StringVar(value=OutputTarget.ALL.value)

    def change_output_target():
        target = OutputTarget(target_var.get())
        output_controller.set_output_target(target)
        output_controller.info(f"出力先を変更しました: {target.value}", "test")

    ttk.Label(control_frame, text="出力先:").grid(
        row=0, column=0, sticky=tk.W, padx=(0, 10)
    )

    targets = [
        ("全て", OutputTarget.ALL.value),
        ("コンソールのみ", OutputTarget.CONSOLE_ONLY.value),
        ("ログファイルのみ", OutputTarget.LOG_ONLY.value),
        ("GUIのみ", OutputTarget.GUI_ONLY.value),
    ]

    for i, (text, value) in enumerate(targets):
        ttk.Radiobutton(
            control_frame,
            text=text,
            variable=target_var,
            value=value,
            command=change_output_target,
        ).grid(row=0, column=i + 1, sticky=tk.W, padx=(0, 10))

    # テストボタン
    button_frame = ttk.Frame(control_frame)
    button_frame.grid(row=1, column=0, columnspan=5, pady=(10, 0), sticky=tk.W)

    def test_debug():
        output_controller.debug("これはデバッグメッセージです", "test")

    def test_info():
        output_controller.info("これは情報メッセージです", "test")

    def test_warning():
        output_controller.warning("これは警告メッセージです", "test")

    def test_error():
        output_controller.error("これはエラーメッセージです", "test")

    def test_critical():
        output_controller.critical("これは重大エラーメッセージです", "test")

    def test_print():
        print("標準出力のテストメッセージ")

    def test_multiple():
        """複数のメッセージを連続出力"""
        for i in range(5):
            output_controller.info(f"連続メッセージ {i+1}/5", "test")
            time.sleep(0.1)

    ttk.Button(button_frame, text="DEBUG", command=test_debug).pack(
        side=tk.LEFT, padx=(0, 5)
    )
    ttk.Button(button_frame, text="INFO", command=test_info).pack(
        side=tk.LEFT, padx=(0, 5)
    )
    ttk.Button(button_frame, text="WARNING", command=test_warning).pack(
        side=tk.LEFT, padx=(0, 5)
    )
    ttk.Button(button_frame, text="ERROR", command=test_error).pack(
        side=tk.LEFT, padx=(0, 5)
    )
    ttk.Button(button_frame, text="CRITICAL", command=test_critical).pack(
        side=tk.LEFT, padx=(0, 5)
    )
    ttk.Button(button_frame, text="PRINT", command=test_print).pack(
        side=tk.LEFT, padx=(0, 5)
    )
    ttk.Button(button_frame, text="連続出力", command=test_multiple).pack(
        side=tk.LEFT, padx=(0, 5)
    )

    # 標準出力リダイレクト制御
    redirect_frame = ttk.Frame(control_frame)
    redirect_frame.grid(row=2, column=0, columnspan=5, pady=(10, 0), sticky=tk.W)

    redirect_var = tk.BooleanVar(value=False)

    def toggle_redirect():
        if redirect_var.get():
            output_controller.redirect_stdout()
            output_controller.info("標準出力をリダイレクトしました", "test")
        else:
            output_controller.restore_stdout()
            output_controller.info("標準出力を復元しました", "test")

    ttk.Checkbutton(
        redirect_frame,
        text="標準出力をリダイレクト",
        variable=redirect_var,
        command=toggle_redirect,
    ).pack(side=tk.LEFT)

    # 初期メッセージ
    output_controller.info("出力制御システムテストを開始しました", "test")

    # ウィンドウを閉じる時の処理
    def on_closing():
        output_controller.restore_stdout()
        output_controller.info("出力制御システムテストを終了しました", "test")
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)

    # メインループ
    root.mainloop()


if __name__ == "__main__":
    test_output_control()
