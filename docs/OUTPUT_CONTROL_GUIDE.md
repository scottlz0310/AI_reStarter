# 出力制御システム使用ガイド

AI reStarterの出力制御システムは、標準出力、ログファイル、GUIログウィンドウの表示を統合管理するシステムです。

## 機能概要

### 出力先の制御
- **コンソール出力**: 標準出力/標準エラー出力
- **ログファイル出力**: ファイルベースのログ記録
- **GUIログウィンドウ**: リアルタイムログ表示

### 出力レベル
- `DEBUG`: デバッグ情報
- `INFO`: 一般的な情報
- `WARNING`: 警告メッセージ
- `ERROR`: エラーメッセージ
- `CRITICAL`: 重大なエラー

## 使用方法

### 1. 基本的な出力

```python
from src.utils.output_controller import output_controller

# レベル別の出力
output_controller.debug("デバッグメッセージ", "module_name")
output_controller.info("情報メッセージ", "module_name")
output_controller.warning("警告メッセージ", "module_name")
output_controller.error("エラーメッセージ", "module_name")
output_controller.critical("重大エラーメッセージ", "module_name")
```

### 2. 出力先の制御

```python
from src.utils.output_controller import OutputTarget

# 出力先を設定
output_controller.set_output_target(OutputTarget.ALL)  # 全て
output_controller.set_output_target(OutputTarget.CONSOLE_ONLY)  # コンソールのみ
output_controller.set_output_target(OutputTarget.LOG_ONLY)  # ログファイルのみ
output_controller.set_output_target(OutputTarget.GUI_ONLY)  # GUIのみ
```

### 3. 個別制御

```python
# 個別の出力先を有効/無効
output_controller.enable_console_output(True)  # コンソール出力を有効
output_controller.enable_log_output(False)     # ログファイル出力を無効
output_controller.enable_gui_output(True)      # GUI出力を有効
```

### 4. GUIログウィンドウとの連携

```python
def gui_callback(message: str, level: str):
    """GUIログウィンドウにメッセージを表示"""
    print(f"[{level}] {message}")

# GUIコールバックを設定
output_controller.set_gui_callback(gui_callback)
```

### 5. 標準出力のリダイレクト

```python
# 標準出力をリダイレクト（print文も制御対象に）
output_controller.redirect_stdout()

# 標準出力を復元
output_controller.restore_stdout()
```

## GUI操作

### メインウィンドウから

1. **メニューバー** → **ツール** → **出力制御**
2. 出力制御ダイアログが開きます

### ログビューアーから

1. **メニューバー** → **ツール** → **ログ表示**
2. ログビューアーの「出力制御」ボタンをクリック

### リアルタイムログ表示

1. ログビューアーで「リアルタイム」チェックボックスを有効化
2. アプリケーションの出力がリアルタイムで表示されます

## 出力制御ダイアログ

### 出力先選択
- **コンソールのみ**: 標準出力のみに出力
- **ログファイルのみ**: ログファイルのみに出力
- **GUIログのみ**: GUIログウィンドウのみに出力
- **コンソール + ログファイル**: コンソールとログファイルに出力
- **コンソール + GUIログ**: コンソールとGUIログウィンドウに出力
- **ログファイル + GUIログ**: ログファイルとGUIログウィンドウに出力
- **全て**: 全ての出力先に出力（デフォルト）

### 個別制御
- **コンソール出力**: コンソール出力の有効/無効
- **ログファイル出力**: ログファイル出力の有効/無効
- **GUIログ出力**: GUIログウィンドウ出力の有効/無効

## 実装例

### カスタムモジュールでの使用

```python
# src/custom/my_module.py
import logging
from src.utils.output_controller import output_controller

logger = logging.getLogger(__name__)

class MyModule:
    def __init__(self):
        output_controller.info("MyModuleを初期化しました", "my_module")
    
    def process_data(self, data):
        try:
            output_controller.debug(f"データ処理開始: {len(data)}件", "my_module")
            
            # 処理実行
            result = self._do_process(data)
            
            output_controller.info(f"データ処理完了: {len(result)}件", "my_module")
            return result
            
        except Exception as e:
            output_controller.error(f"データ処理エラー: {e}", "my_module")
            raise
    
    def _do_process(self, data):
        # 実際の処理
        return data
```

### GUIアプリケーションでの統合

```python
# src/gui/my_window.py
import tkinter as tk
from src.utils.output_controller import output_controller

class MyWindow:
    def __init__(self, root):
        self.root = root
        self.setup_ui()
        
        # GUIログウィンドウのコールバックを設定
        output_controller.set_gui_callback(self.add_log_message)
    
    def setup_ui(self):
        # ログ表示エリア
        self.log_text = tk.Text(self.root)
        self.log_text.pack(fill=tk.BOTH, expand=True)
    
    def add_log_message(self, message: str, level: str):
        """ログメッセージをGUIに追加"""
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_line = f"[{timestamp}] [{level}] {message}\n"
        self.log_text.insert(tk.END, log_line)
        self.log_text.see(tk.END)
    
    def on_button_click(self):
        output_controller.info("ボタンがクリックされました", "my_window")
```

## 設定の永続化

出力制御の設定は現在セッション中のみ有効です。アプリケーション再起動時にはデフォルト設定（全て有効）に戻ります。

将来的には設定ファイルでの永続化も検討されています。

## トラブルシューティング

### よくある問題

1. **GUIログウィンドウに表示されない**
   - GUIコールバックが正しく設定されているか確認
   - GUI出力が有効になっているか確認

2. **標準出力が表示されない**
   - コンソール出力が有効になっているか確認
   - 標準出力がリダイレクトされていないか確認

3. **ログファイルに記録されない**
   - ログファイル出力が有効になっているか確認
   - ログファイルの書き込み権限があるか確認

### デバッグ方法

```python
# 現在の設定状態を確認
status = output_controller.get_status()
print(f"出力設定: {status}")

# テストメッセージを送信
output_controller.info("テストメッセージ", "debug")
```

## パフォーマンス考慮事項

- 大量のログ出力時はGUI更新が重くなる可能性があります
- 必要に応じて出力レベルを調整してください
- リアルタイムログ表示は適度にクリアすることを推奨します

## セキュリティ

- ログ出力に機密情報を含めないよう注意してください
- ログファイルのアクセス権限を適切に設定してください

## 今後の拡張予定

- 設定の永続化
- ログローテーション機能
- ネットワーク経由でのログ送信
- ログフィルタリング機能の強化