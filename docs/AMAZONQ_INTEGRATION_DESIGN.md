# AmazonQ対応機能 実装設計ドキュメント

## 概要

既存のKiro-IDE自動復旧システムを拡張し、VSCode拡張のAmazonQにも対応できるようにします。監視エリアで「▶RUN」ボタンを検出した際に自動クリックする機能を追加し、Kiro-IDEモードとAmazonQモードを切り替えて運用できるようにします。

## 機能要件

### 1. モード切り替え機能
- **Kiro-IDEモード**: 既存のエラー検出・復旧機能
- **AmazonQモード**: ▶RUNボタン検出・自動クリック機能
- 実行時または設定ファイルでモードを指定可能

### 2. AmazonQモードの機能
- 監視エリアで「▶RUN」ボタンを画像認識で検出
- 検出時に自動クリック
- クリック後の状態監視（実行中、完了、エラー等）
- 必要に応じて追加のアクション実行

### 3. 設定の拡張
- モード設定
- AmazonQ用の監視エリア設定
- ▶RUNボタンのテンプレート画像管理
- クリック後の待機時間設定

## 技術設計

### 1. アーキテクチャ変更

#### 既存クラスの拡張
```python
class KiroAutoRecovery:
    def __init__(self, config_file: str = "kiro_config.json", mode: str = "auto"):
        self.mode = mode  # "kiro", "amazonq", "auto"
        self.amazonq_detector = AmazonQDetector() if mode in ["amazonq", "auto"] else None
        # ... 既存の初期化処理
```

#### 新しいクラスの追加
```python
class AmazonQDetector:
    """AmazonQ用の検出・実行クラス"""

    def __init__(self, config: dict):
        self.config = config
        self.run_button_templates = {}
        self.state_templates = {}
        self.load_templates()

    def detect_run_button(self, screenshot: np.ndarray) -> Optional[tuple[int, int]]:
        """▶RUNボタンを検出して座標を返す"""
        pass

    def click_run_button(self, position: tuple[int, int]) -> bool:
        """▶RUNボタンをクリック"""
        pass

    def monitor_execution_state(self, screenshot: np.ndarray) -> str:
        """実行状態を監視（実行中、完了、エラー等）"""
        pass
```

### 2. 設定ファイルの拡張

#### 新しい設定項目
```json
{
  "mode": "auto",
  "amazonq": {
    "enabled": true,
    "monitor_region": [0, 0, 1920, 1080],
    "run_button_templates_dir": "amazonq_templates",
    "click_delay": 1.0,
    "execution_timeout": 300,
    "state_detection": {
      "running": "running_state.png",
      "completed": "completed_state.png",
      "error": "error_state.png"
    }
  }
}
```

### 3. 監視ループの拡張

#### モード別の処理分岐
```python
def monitor_loop(self) -> None:
    """メインの監視ループ"""
    logger.info(f"監視開始 - モード: {self.mode}")

    while self.monitoring:
        try:
            screenshot = self.capture_screen(self.get_monitor_region())

            if self.mode == "kiro":
                self.handle_kiro_mode(screenshot)
            elif self.mode == "amazonq":
                self.handle_amazonq_mode(screenshot)
            elif self.mode == "auto":
                self.handle_auto_mode(screenshot)

            time.sleep(self.config["monitor_interval"])

        except Exception as e:
            logger.error(f"監視ループエラー: {e}")
            time.sleep(5)
```

## 実装詳細

### 1. AmazonQDetectorクラス

#### 主要メソッド
- `load_templates()`: ▶RUNボタンと状態テンプレートの読み込み
- `detect_run_button()`: テンプレートマッチングで▶RUNボタンを検出
- `click_run_button()`: 検出された位置をクリック
- `monitor_execution_state()`: 実行状態の監視
- `handle_state_change()`: 状態変化時の処理

#### テンプレート管理
- `amazonq_templates/` ディレクトリに以下を配置
  - `run_button.png`: ▶RUNボタンのテンプレート画像
  - `running_state.png`: 実行中の状態画像
  - `completed_state.png`: 完了状態の画像
  - `error_state.png`: エラー状態の画像

### 2. モード自動判定機能

#### 自動モードの動作
1. 監視エリアで▶RUNボタンを検出
2. 検出された場合：AmazonQモードとして動作
3. 検出されない場合：Kiro-IDEモードとして動作
4. モード切り替え時にログ出力

#### 判定ロジック
```python
def auto_detect_mode(self, screenshot: np.ndarray) -> str:
    """スクリーンショットからモードを自動判定"""
    if self.amazonq_detector and self.amazonq_detector.detect_run_button(screenshot):
        return "amazonq"
    return "kiro"
```

### 3. 設定GUIの拡張

#### kiro_setup.pyの拡張
- モード選択（Kiro-IDE / AmazonQ / 自動）
- AmazonQモード用の監視エリア設定
- ▶RUNボタンのテンプレート保存機能
- 状態テンプレートの設定

#### 新しい設定項目
- モード選択ラジオボタン
- AmazonQ用監視エリア設定ボタン
- テンプレート管理タブ

### 4. ホットキーの拡張

#### 新しいホットキー
- `Ctrl+Alt+M`: モード切り替え
- `Ctrl+Alt+A`: AmazonQ用テンプレート保存
- `Ctrl+Alt+T`: 状態テンプレート保存

#### 既存ホットキーの拡張
- `Ctrl+Alt+S`: モードに応じてテンプレート保存
- `Ctrl+Alt+P`: モードに応じて一時停止/再開

## ファイル構成

### 新規作成ファイル
```
amazonq_detector.py          # AmazonQ検出・実行クラス
amazonq_templates/           # AmazonQ用テンプレートディレクトリ
  ├── run_button.png        # ▶RUNボタンテンプレート
  ├── running_state.png     # 実行中状態テンプレート
  ├── completed_state.png   # 完了状態テンプレート
  └── error_state.png       # エラー状態テンプレート
```

### 既存ファイルの変更
```
kiro_auto_recovery.py        # メインクラスの拡張
kiro_setup.py               # 設定GUIの拡張
kiro_config.json            # 設定ファイルの拡張
README.md                   # ドキュメントの更新
```

## 実装順序

### Phase 1: 基盤実装
1. AmazonQDetectorクラスの作成
2. 設定ファイルの拡張
3. 基本的な▶RUNボタン検出機能

### Phase 2: 統合実装
1. メインクラスへの統合
2. モード切り替え機能
3. 監視ループの拡張

### Phase 3: UI・設定拡張
1. 設定GUIの拡張
2. ホットキーの拡張
3. テンプレート管理機能

### Phase 4: テスト・最適化
1. 動作テスト
2. パフォーマンス最適化
3. エラーハンドリングの改善

## 設定例

### 基本的なAmazonQ設定
```json
{
  "mode": "amazonq",
  "monitor_interval": 1.0,
  "amazonq": {
    "enabled": true,
    "monitor_region": [100, 200, 800, 600],
    "click_delay": 1.0,
    "execution_timeout": 300
  }
}
```

### 自動モード設定
```json
{
  "mode": "auto",
  "monitor_interval": 1.5,
  "amazonq": {
    "enabled": true,
    "monitor_region": [0, 0, 1920, 1080],
    "click_delay": 1.0
  }
}
```

## 注意事項

### 1. パフォーマンス
- 画像認識の頻度を適切に設定
- テンプレート画像のサイズ最適化
- 監視間隔の調整

### 2. 互換性
- 既存のKiro-IDE機能への影響を最小限に抑制
- 設定ファイルの後方互換性を維持
- エラー時の適切なフォールバック

### 3. セキュリティ
- 自動クリック機能の安全性確保
- 誤動作防止のための確認機能
- ログ出力での動作追跡

## 今後の拡張可能性

### 1. 追加のIDE対応
- IntelliJ IDEA
- Eclipse
- Visual Studio
- その他の開発環境

### 2. 高度な状態管理
- 機械学習による状態認識
- 動的なテンプレート更新
- ユーザー行動パターンの学習

### 3. クラウド連携
- 設定のクラウド同期
- テンプレートの共有・配布
- 統計情報の収集・分析
