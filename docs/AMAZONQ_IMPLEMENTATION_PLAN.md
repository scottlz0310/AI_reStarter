# AmazonQ対応機能 実装計画

## 実装概要

既存のKiro-IDE自動復旧システムを拡張し、VSCode拡張のAmazonQに対応します。
▶RUNボタンの自動検出・クリック機能を追加し、モード切り替えで運用できるようにします。

## 実装フェーズ

### Phase 1: 基盤クラス実装

#### 1.1 AmazonQDetectorクラス作成
**ファイル**: `src/plugins/amazonq_detector.py`

```python
class AmazonQDetector(BaseDetector):
    """AmazonQ用の▶RUNボタン検出・クリック機能"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.run_button_templates = {}
        self.load_run_button_templates()
    
    def detect_state(self, screenshot: np.ndarray) -> Optional[DetectionResult]:
        """▶RUNボタンを検出"""
        
    def execute_recovery_action(self, result: DetectionResult) -> bool:
        """▶RUNボタンをクリック"""
```

#### 1.2 BaseDetectorクラス作成
**ファイル**: `src/core/base_detector.py`

```python
from abc import ABC, abstractmethod

class BaseDetector(ABC):
    """検出器の基底クラス"""
    
    @abstractmethod
    def detect_state(self, screenshot: np.ndarray) -> Optional[DetectionResult]:
        """状態を検出"""
        
    @abstractmethod
    def execute_recovery_action(self, result: DetectionResult) -> bool:
        """復旧アクションを実行"""
```

#### 1.3 DetectionResultクラス作成
**ファイル**: `src/core/detection_result.py`

```python
@dataclass
class DetectionResult:
    """検出結果を格納するクラス"""
    state_type: str
    confidence: float
    position: Optional[tuple[int, int]]
    timestamp: float
    metadata: dict
```

### Phase 2: モード管理システム

#### 2.1 ModeManagerクラス作成
**ファイル**: `src/core/mode_manager.py`

```python
class ModeManager:
    """モード管理クラス"""
    
    def __init__(self, config_manager: ConfigManager):
        self.current_mode = "auto"  # "kiro", "amazonq", "auto"
        self.detectors = {}
        self.setup_detectors()
    
    def switch_mode(self, mode: str) -> bool:
        """モードを切り替え"""
        
    def get_active_detectors(self) -> list[BaseDetector]:
        """アクティブな検出器を取得"""
```

#### 2.2 設定ファイル拡張
**ファイル**: `kiro_config.json`に追加

```json
{
  "mode": "auto",
  "amazonq": {
    "enabled": true,
    "monitor_areas": [],
    "run_button_templates_dir": "amazonq_templates",
    "click_delay": 1.0,
    "detection_threshold": 0.8
  }
}
```

### Phase 3: 既存システム統合

#### 3.1 KiroRecoveryクラス拡張
**ファイル**: `src/core/kiro_recovery.py`

- ModeManagerの統合
- 監視ループでのモード別処理
- 既存機能との互換性維持

#### 3.2 MainWindowクラス拡張
**ファイル**: `src/gui/main_window.py`

- モード切り替えUI追加
- AmazonQ用設定ダイアログ
- 状態表示の拡張

### Phase 4: GUI・設定機能

#### 4.1 モード選択ウィジェット
**ファイル**: `src/gui/mode_selector_widget.py`

```python
class ModeSelectorWidget(ttk.Frame):
    """モード選択ウィジェット"""
    
    def __init__(self, parent):
        # ラジオボタンでモード選択
        # - Kiro-IDEモード
        # - AmazonQモード  
        # - 自動モード
```

#### 4.2 AmazonQ設定ダイアログ
**ファイル**: `src/gui/amazonq_settings_dialog.py`

```python
class AmazonQSettingsDialog:
    """AmazonQ用設定ダイアログ"""
    
    def __init__(self, parent, config_manager):
        # 監視エリア設定
        # テンプレート管理
        # クリック設定
```

### Phase 5: テンプレート管理

#### 5.1 テンプレートディレクトリ作成
```
amazonq_templates/
├── run_button.png          # ▶RUNボタンテンプレート
├── running_indicator.png   # 実行中インジケーター
└── completed_indicator.png # 完了インジケーター
```

#### 5.2 テンプレート管理機能拡張
**ファイル**: `src/gui/template_manager.py`

- AmazonQ用テンプレート管理タブ追加
- ▶RUNボタンテンプレート保存機能
- テンプレート削除・編集機能

## 実装詳細

### 1. ▶RUNボタン検出ロジック

```python
def detect_run_button(self, screenshot: np.ndarray) -> Optional[tuple[int, int]]:
    """▶RUNボタンを検出して座標を返す"""
    
    for template_name, template in self.run_button_templates.items():
        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        if max_val >= self.detection_threshold:
            # テンプレートの中心座標を計算
            h, w = template.shape
            center_x = max_loc[0] + w // 2
            center_y = max_loc[1] + h // 2
            
            logger.info(f"▶RUNボタン検出: {template_name} (信頼度: {max_val:.3f})")
            return (center_x, center_y)
    
    return None
```

### 2. 自動クリック機能

```python
def click_run_button(self, position: tuple[int, int]) -> bool:
    """▶RUNボタンをクリック"""
    
    try:
        x, y = position
        logger.info(f"▶RUNボタンをクリック: 座標({x}, {y})")
        
        pyautogui.click(x, y)
        time.sleep(self.config_manager.get("amazonq.click_delay", 1.0))
        
        return True
        
    except Exception as e:
        logger.error(f"▶RUNボタンクリックエラー: {e}")
        return False
```

### 3. モード自動判定

```python
def auto_detect_mode(self, screenshot: np.ndarray) -> str:
    """スクリーンショットからモードを自動判定"""
    
    # AmazonQ検出を試行
    if self.amazonq_detector.detect_run_button(screenshot):
        return "amazonq"
    
    # Kiro-IDEエラー検出を試行
    if self.kiro_recovery.detect_error(screenshot):
        return "kiro"
    
    # デフォルトはKiroモード
    return "kiro"
```

## 設定例

### 基本的なAmazonQ設定
```json
{
  "mode": "amazonq",
  "monitor_interval": 1.0,
  "amazonq": {
    "enabled": true,
    "monitor_areas": [
      {
        "name": "AmazonQ実行エリア",
        "x": 100,
        "y": 200,
        "width": 800,
        "height": 600,
        "enabled": true
      }
    ],
    "run_button_templates_dir": "amazonq_templates",
    "click_delay": 1.0,
    "detection_threshold": 0.8
  }
}
```

## 実装スケジュール

### Week 1: 基盤実装
- [ ] BaseDetectorクラス作成
- [ ] DetectionResultクラス作成
- [ ] AmazonQDetectorクラス基本実装
- [ ] 設定ファイル拡張

### Week 2: 統合実装
- [ ] ModeManagerクラス作成
- [ ] KiroRecoveryクラス拡張
- [ ] 監視ループの拡張
- [ ] 基本的な動作テスト

### Week 3: GUI実装
- [ ] ModeSelectorWidget作成
- [ ] AmazonQSettingsDialog作成
- [ ] MainWindow拡張
- [ ] テンプレート管理機能拡張

### Week 4: テスト・最適化
- [ ] 統合テスト
- [ ] パフォーマンス最適化
- [ ] エラーハンドリング改善
- [ ] ドキュメント更新

## 注意事項

### 1. 既存機能への影響
- Kiro-IDE機能は完全に保持
- 設定ファイルの後方互換性維持
- 既存のホットキー機能は継続

### 2. パフォーマンス考慮
- 画像認識の最適化
- 監視間隔の適切な設定
- メモリ使用量の監視

### 3. エラーハンドリング
- 検出失敗時の適切な処理
- クリック失敗時のリトライ機能
- ログ出力の充実

## 今後の拡張

### 1. 高度な状態管理
- 実行状態の詳細監視
- 実行完了の検出
- エラー状態の検出・対応

### 2. 追加IDE対応
- IntelliJ IDEA
- Eclipse
- その他の開発環境

### 3. 機械学習活用
- 動的なテンプレート更新
- ユーザー行動パターンの学習
- 精度向上のための自動調整