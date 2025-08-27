# アーキテクチャリファクタリング設計指針

## 概要

現在のシステムの課題を解決し、より使いやすく保守しやすいアーキテクチャに改善します。メインクラスとエントリーポイントの分離、モジュール化、統合GUIの実装により、ユーザビリティと保守性を大幅に向上させます。

## 現在の課題

### 1. アーキテクチャの問題
- **kiro_auto_recovery.py**がメインクラス兼エントリーポイントとして混在
- 設定GUIとメインアプリケーションが分離されており、起動が煩雑
- 監視状態を把握するGUIが存在しない
- モジュール間の依存関係が不明確

### 2. ユーザビリティの問題
- 設定変更時に複数のアプリケーションを起動する必要がある
- 監視状態がログファイルでのみ確認可能
- リアルタイムでの状態監視ができない
- モード切り替えが設定ファイル編集のみ

### 3. 保守性の問題
- 単一ファイルに複数の責務が混在
- テストが困難
- 機能追加時の影響範囲が不明確

## 改善後のアーキテクチャ

### 1. ファイル構成

```
AI_reStarter/
├── main.py                    # メインエントリーポイント
├── src/                       # ソースコードディレクトリ
│   ├── __init__.py
│   ├── core/                  # コア機能
│   │   ├── __init__.py
│   │   ├── kiro_recovery.py   # Kiro-IDE復旧機能
│   │   ├── amazonq_detector.py # AmazonQ検出機能
│   │   └── base_detector.py   # 基底検出クラス
│   ├── gui/                   # GUI関連
│   │   ├── __init__.py
│   │   ├── main_window.py     # メインウィンドウ
│   │   ├── settings_dialog.py # 設定ダイアログ
│   │   └── monitor_widget.py  # 監視状態ウィジェット
│   ├── config/                # 設定管理
│   │   ├── __init__.py
│   │   ├── config_manager.py  # 設定管理クラス
│   │   └── template_manager.py # テンプレート管理
│   └── utils/                 # ユーティリティ
│       ├── __init__.py
│       ├── screen_capture.py  # 画面キャプチャ
│       ├── image_processing.py # 画像処理
│       └── hotkey_manager.py  # ホットキー管理
├── amazonq_templates/         # AmazonQ用テンプレート
├── error_templates/           # エラー用テンプレート
├── config/                    # 設定ファイル
│   ├── kiro_config.json      # Kiro-IDE設定
│   └── amazonq_config.json   # AmazonQ設定
├── tests/                     # テストコード
├── docs/                      # ドキュメント
├── pyproject.toml            # 依存関係管理
└── README.md                 # プロジェクト説明
```

### 2. クラス設計

#### メインエントリーポイント
```python
# main.py
def main():
    """メインエントリーポイント"""
    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
```

#### メインウィンドウ
```python
# src/gui/main_window.py
class MainWindow(QMainWindow):
    """メインウィンドウ - 統合GUI"""

    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.recovery_system = None
        self.setup_ui()
        self.setup_menu()
        self.setup_status_bar()

    def setup_ui(self):
        """UIの初期化"""
        # メインウィジェット
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # レイアウト
        self.layout = QVBoxLayout(self.central_widget)

        # モード選択
        self.mode_selector = ModeSelectorWidget()
        self.layout.addWidget(self.mode_selector)

        # 監視状態ウィジェット
        self.monitor_widget = MonitorWidget()
        self.layout.addWidget(self.monitor_widget)

        # 制御ボタン
        self.control_buttons = ControlButtonsWidget()
        self.layout.addWidget(self.control_buttons)

    def setup_menu(self):
        """メニューバーの設定"""
        menubar = self.menuBar()

        # ファイルメニュー
        file_menu = menubar.addMenu('ファイル')
        file_menu.addAction('設定', self.open_settings)
        file_menu.addAction('終了', self.close)

        # ツールメニュー
        tools_menu = menubar.addMenu('ツール')
        tools_menu.addAction('テンプレート管理', self.open_template_manager)
        tools_menu.addAction('ログ表示', self.show_logs)

    def open_settings(self):
        """設定ダイアログを開く"""
        dialog = SettingsDialog(self.config_manager, self)
        if dialog.exec_() == QDialog.Accepted:
            self.apply_new_settings()
```

#### 設定ダイアログ
```python
# src/gui/settings_dialog.py
class SettingsDialog(QDialog):
    """設定ダイアログ"""

    def __init__(self, config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = config_manager
        self.setup_ui()
        self.load_current_settings()

    def setup_ui(self):
        """UIの初期化"""
        self.setWindowTitle("設定")
        self.setModal(True)

        layout = QVBoxLayout(self)

        # タブウィジェット
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # 基本設定タブ
        self.general_tab = GeneralSettingsTab()
        self.tab_widget.addTab(self.general_tab, "基本設定")

        # Kiro-IDE設定タブ
        self.kiro_tab = KiroSettingsTab()
        self.tab_widget.addTab(self.kiro_tab, "Kiro-IDE")

        # AmazonQ設定タブ
        self.amazonq_tab = AmazonQSettingsTab()
        self.tab_widget.addTab(self.amazonq_tab, "AmazonQ")

        # ボタン
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("キャンセル")
        self.apply_button = QPushButton("適用")

        button_layout.addWidget(self.apply_button)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)

        layout.addLayout(button_layout)
```

#### 監視状態ウィジェット
```python
# src/gui/monitor_widget.py
class MonitorWidget(QWidget):
    """監視状態を表示するウィジェット"""

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        """UIの初期化"""
        layout = QVBoxLayout(self)

        # 状態表示
        self.status_group = QGroupBox("監視状態")
        status_layout = QGridLayout(self.status_group)

        self.mode_label = QLabel("モード: 未設定")
        self.status_label = QLabel("状態: 停止中")
        self.template_count_label = QLabel("テンプレート: 0個")
        self.last_action_label = QLabel("最終アクション: なし")

        status_layout.addWidget(QLabel("モード:"), 0, 0)
        status_layout.addWidget(self.mode_label, 0, 1)
        status_layout.addWidget(QLabel("状態:"), 1, 0)
        status_layout.addWidget(self.status_label, 1, 1)
        status_layout.addWidget(QLabel("テンプレート:"), 2, 0)
        status_layout.addWidget(self.template_count_label, 2, 1)
        status_layout.addWidget(QLabel("最終アクション:"), 3, 0)
        status_layout.addWidget(self.last_action_label, 3, 1)

        layout.addWidget(self.status_group)

        # ログ表示
        self.log_group = QGroupBox("ログ")
        log_layout = QVBoxLayout(self.log_group)

        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)

        log_layout.addWidget(self.log_text)

        layout.addWidget(self.log_group)

    def update_status(self, mode: str, status: str, template_count: int, last_action: str):
        """状態を更新"""
        self.mode_label.setText(f"モード: {mode}")
        self.status_label.setText(f"状態: {status}")
        self.template_count_label.setText(f"テンプレート: {template_count}個")
        self.last_action_label.setText(f"最終アクション: {last_action}")

    def add_log(self, message: str):
        """ログを追加"""
        timestamp = QDateTime.currentDateTime().toString("HH:mm:ss")
        self.log_text.append(f"[{timestamp}] {message}")
```

#### 設定管理クラス
```python
# src/config/config_manager.py
class ConfigManager:
    """設定管理クラス"""

    def __init__(self):
        self.config_dir = "config"
        self.kiro_config_file = os.path.join(self.config_dir, "kiro_config.json")
        self.amazonq_config_file = os.path.join(self.config_dir, "amazonq_config.json")
        self.general_config_file = os.path.join(self.config_dir, "general_config.json")

        self.ensure_config_directory()
        self.load_all_configs()

    def ensure_config_directory(self):
        """設定ディレクトリの存在確認・作成"""
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)

    def load_all_configs(self):
        """全設定ファイルを読み込み"""
        self.general_config = self.load_config(self.general_config_file, self.get_default_general_config())
        self.kiro_config = self.load_config(self.kiro_config_file, self.get_default_kiro_config())
        self.amazonq_config = self.load_config(self.amazonq_config_file, self.get_default_amazonq_config())

    def get_current_mode(self) -> str:
        """現在のモードを取得"""
        return self.general_config.get("mode", "auto")

    def set_mode(self, mode: str):
        """モードを設定"""
        self.general_config["mode"] = mode
        self.save_config(self.general_config_file, self.general_config)

    def get_monitor_region(self, mode: str) -> Optional[tuple[int, int, int, int]]:
        """指定モードの監視エリアを取得"""
        if mode == "kiro":
            return self.kiro_config.get("monitor_region")
        elif mode == "amazonq":
            return self.amazonq_config.get("monitor_region")
        return None
```

#### コア機能の分離
```python
# src/core/kiro_recovery.py
class KiroRecovery:
    """Kiro-IDE復旧機能（既存のKiroAutoRecoveryから分離）"""

    def __init__(self, config: dict):
        self.config = config
        self.monitoring = False
        self.error_templates = {}
        self.load_error_templates()

    def start_monitoring(self):
        """監視開始"""
        pass

    def stop_monitoring(self):
        """監視停止"""
        pass

    def detect_error(self, screenshot: np.ndarray) -> Optional[str]:
        """エラー検出"""
        pass

# src/core/amazonq_detector.py
class AmazonQDetector:
    """AmazonQ検出機能"""

    def __init__(self, config: dict):
        self.config = config
        self.run_button_templates = {}
        self.state_templates = {}
        self.load_templates()

    def detect_run_button(self, screenshot: np.ndarray) -> Optional[tuple[int, int]]:
        """▶RUNボタンを検出"""
        pass

    def click_run_button(self, position: tuple[int, int]) -> bool:
        """▶RUNボタンをクリック"""
        pass
```

## 実装の利点

### 1. ユーザビリティの向上
- **統合GUI**: 設定、監視、制御が一つのウィンドウで完結
- **リアルタイム監視**: 現在の状態を視覚的に確認可能
- **ワンクリック操作**: 設定変更から監視開始まで簡単操作
- **モード切り替え**: GUI上でモードを簡単に切り替え

### 2. 保守性の向上
- **責務の分離**: 各クラスが単一の責務を持つ
- **モジュール化**: 機能ごとにファイルが分離
- **依存関係の明確化**: 各モジュール間の依存が明確
- **テスト容易性**: 個別モジュールのテストが可能

### 3. 拡張性の向上
- **プラグイン化**: 新しい検出機能の追加が容易
- **設定の柔軟性**: モード別の設定管理
- **UIのカスタマイズ**: 各ウィジェットの独立した開発
- **国際化対応**: 言語ファイルの分離が容易

## 実装順序

### Phase 1: 基盤構造の構築
1. ディレクトリ構造の作成
2. 設定管理クラスの実装
3. 基本的なGUIフレームワークの構築

### Phase 2: コア機能の分離
1. KiroRecoveryクラスの分離
2. AmazonQDetectorクラスの実装
3. 基底クラスの設計

### Phase 3: GUI統合
1. メインウィンドウの実装
2. 設定ダイアログの実装
3. 監視状態ウィジェットの実装

### Phase 4: 統合・テスト
1. 全モジュールの統合
2. 動作テスト
3. パフォーマンス最適化

## 技術的な考慮事項

### 1. 依存関係の管理
- **PyQt6/PySide6**: モダンなGUIフレームワーク
- **設定ファイル**: JSON形式での設定管理
- **ログ管理**: 構造化されたログ出力

### 2. パフォーマンス
- **非同期処理**: 監視処理の非同期化
- **メモリ管理**: 画像データの適切な管理
- **UI応答性**: 重い処理時のUIブロック防止

### 3. エラーハンドリング
- **例外処理**: 適切な例外処理とログ出力
- **フォールバック**: エラー時の適切なフォールバック
- **ユーザー通知**: エラー状態の視覚的な通知

## 移行戦略

### 1. 段階的移行
- 既存機能の動作を維持しながら段階的に移行
- 各フェーズでの動作確認
- ユーザーへの影響を最小限に抑制

### 2. 後方互換性
- 既存の設定ファイルの互換性維持
- 既存のテンプレートファイルの継続利用
- 既存のホットキー機能の維持

### 3. テスト戦略
- 単体テストの充実
- 統合テストの実施
- ユーザビリティテストの実施

## AI実装の停止状態自動復旧への拡張

### 1. 汎用的な監視・復旧フレームワーク

#### プラグインアーキテクチャ
```python
# src/core/base_detector.py
class BaseDetector(ABC):
    """基底検出クラス - 全ての監視機能の基盤"""

    @abstractmethod
    def detect_state(self, screenshot: np.ndarray) -> Optional[DetectionResult]:
        """状態を検出して結果を返す"""
        pass

    @abstractmethod
    def execute_recovery_action(self, detection_result: DetectionResult) -> bool:
        """復旧アクションを実行"""
        pass

    @abstractmethod
    def get_detection_config(self) -> dict:
        """検出設定を取得"""
        pass

# src/core/plugin_manager.py
class PluginManager:
    """プラグイン管理クラス - 動的な機能追加を可能"""

    def __init__(self):
        self.plugins = {}
        self.plugin_configs = {}

    def load_plugin(self, plugin_name: str, plugin_class: type):
        """プラグインを動的に読み込み"""
        if issubclass(plugin_class, BaseDetector):
            self.plugins[plugin_name] = plugin_class()
            logger.info(f"プラグイン '{plugin_name}' を読み込みました")

    def get_available_plugins(self) -> List[str]:
        """利用可能なプラグイン一覧を取得"""
        return list(self.plugins.keys())

    def execute_plugin(self, plugin_name: str, screenshot: np.ndarray) -> Optional[bool]:
        """指定プラグインを実行"""
        if plugin_name in self.plugins:
            plugin = self.plugins[plugin_name]
            result = plugin.detect_state(screenshot)
            if result:
                return plugin.execute_recovery_action(result)
        return None
```

#### 検出結果の統一化
```python
# src/core/detection_result.py
@dataclass
class DetectionResult:
    """検出結果の統一データ構造"""
    state_type: str              # 状態タイプ（"error", "timeout", "stuck", "ready"等）
    confidence: float            # 検出信頼度（0.0-1.0）
    position: Optional[tuple[int, int]] = None  # アクション位置
    metadata: dict = field(default_factory=dict)  # 追加情報
    timestamp: datetime = field(default_factory=datetime.now)

    def is_actionable(self) -> bool:
        """アクション実行可能かチェック"""
        return self.confidence >= 0.7 and self.position is not None

# src/core/state_manager.py
class StateManager:
    """状態管理クラス - 複数の検出結果を統合管理"""

    def __init__(self):
        self.current_states = {}
        self.state_history = []
        self.recovery_actions = {}

    def update_state(self, detector_name: str, result: DetectionResult):
        """状態を更新"""
        self.current_states[detector_name] = result
        self.state_history.append(result)

        # 状態変化の検出
        if self._should_trigger_recovery(result):
            self._schedule_recovery_action(result)

    def _should_trigger_recovery(self, result: DetectionResult) -> bool:
        """復旧アクションをトリガーすべきか判定"""
        # エラー状態、タイムアウト、スタック状態等の判定
        critical_states = ["error", "timeout", "stuck", "crashed"]
        return result.state_type in critical_states and result.is_actionable()
```

### 2. AI実装特有の停止状態への対応

#### 一般的なAI停止状態の分類
```python
# src/plugins/ai_state_detector.py
class AIStateDetector(BaseDetector):
    """AI実装の停止状態を検出する汎用プラグイン"""

    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self.state_patterns = {
            "training_stuck": {
                "description": "学習処理が停滞",
                "indicators": ["loss_not_decreasing", "accuracy_plateau", "gpu_idle"],
                "recovery_actions": ["restart_training", "adjust_hyperparameters", "clear_cache"]
            },
            "inference_timeout": {
                "description": "推論処理がタイムアウト",
                "indicators": ["long_processing", "memory_high", "cpu_100"],
                "recovery_actions": ["restart_inference", "reduce_batch_size", "clear_memory"]
            },
            "model_loading_error": {
                "description": "モデル読み込みエラー",
                "indicators": ["file_not_found", "memory_error", "version_mismatch"],
                "recovery_actions": ["reload_model", "check_dependencies", "restart_service"]
            },
            "data_pipeline_stuck": {
                "description": "データパイプラインが停滞",
                "indicators": ["queue_full", "processing_delay", "disk_io_high"],
                "recovery_actions": ["restart_pipeline", "clear_queue", "optimize_io"]
            },
            "gpu_memory_error": {
                "description": "GPUメモリエラー",
                "indicators": ["out_of_memory", "gpu_unresponsive", "driver_error"],
                "recovery_actions": ["clear_gpu_memory", "restart_gpu_service", "reduce_batch"]
            }
        }

    def detect_state(self, screenshot: np.ndarray) -> Optional[DetectionResult]:
        """AI実装の状態を検出"""
        for state_name, state_info in self.state_patterns.items():
            if self._detect_state_pattern(screenshot, state_name, state_info):
                return DetectionResult(
                    state_type=state_name,
                    confidence=self._calculate_confidence(screenshot, state_name),
                    metadata={"description": state_info["description"]}
                )
        return None

    def execute_recovery_action(self, result: DetectionResult) -> bool:
        """復旧アクションを実行"""
        state_name = result.state_type
        if state_name in self.state_patterns:
            actions = self.state_patterns[state_name]["recovery_actions"]
            return self._execute_action_sequence(actions)
        return False
```

#### 特定AIフレームワークへの対応
```python
# src/plugins/tensorflow_detector.py
class TensorFlowDetector(BaseDetector):
    """TensorFlow特有の状態を検出・復旧"""

    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self.tf_specific_states = {
            "graph_def_error": "グラフ定義エラー",
            "session_crash": "セッションクラッシュ",
            "memory_growth_failed": "メモリ成長失敗",
            "cudnn_error": "CuDNNエラー"
        }

    def detect_state(self, screenshot: np.ndarray) -> Optional[DetectionResult]:
        """TensorFlow特有の状態を検出"""
        # TensorFlowのエラーメッセージ、ログ、UI状態を検出
        pass

# src/plugins/pytorch_detector.py
class PyTorchDetector(BaseDetector):
    """PyTorch特有の状態を検出・復旧"""

    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self.pytorch_specific_states = {
            "cuda_out_of_memory": "CUDAメモリ不足",
            "autograd_error": "自動微分エラー",
            "dataloader_worker_error": "データローダーワーカーエラー"
        }

# src/plugins/jupyter_detector.py
class JupyterDetector(BaseDetector):
    """Jupyter環境の状態を検出・復旧"""

    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self.jupyter_states = {
            "kernel_dead": "カーネル死亡",
            "cell_hanging": "セル実行中",
            "memory_limit": "メモリ制限到達",
            "timeout_error": "タイムアウトエラー"
        }
```

### 3. 設定による柔軟な動作制御

#### プラグイン設定の例
```json
{
  "plugins": {
    "ai_state_detector": {
      "enabled": true,
      "priority": 1,
      "detection_interval": 2.0,
      "recovery_strategy": "progressive",
      "max_retry_attempts": 3
    },
    "tensorflow_detector": {
      "enabled": true,
      "priority": 2,
      "specific_checks": ["gpu_memory", "session_state", "graph_health"]
    },
    "jupyter_detector": {
      "enabled": true,
      "priority": 3,
      "kernel_restart_delay": 5.0,
      "memory_threshold": 0.9
    }
  },
  "recovery_strategies": {
    "progressive": {
      "description": "段階的な復旧戦略",
      "steps": [
        {"action": "clear_cache", "delay": 1.0},
        {"action": "restart_service", "delay": 5.0},
        {"action": "restart_application", "delay": 10.0}
      ]
    },
    "aggressive": {
      "description": "積極的な復旧戦略",
      "steps": [
        {"action": "force_kill", "delay": 0.0},
        {"action": "restart_application", "delay": 2.0}
      ]
    }
  }
}
```

### 4. 監視対象の拡張

#### システムリソース監視
```python
# src/plugins/system_monitor.py
class SystemMonitor(BaseDetector):
    """システムリソースを監視してAI処理の停止を検出"""

    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self.monitoring_targets = {
            "cpu_usage": {"threshold": 0.95, "duration": 60},
            "memory_usage": {"threshold": 0.9, "duration": 30},
            "gpu_usage": {"threshold": 0.98, "duration": 45},
            "disk_io": {"threshold": 100, "duration": 120}
        }

    def detect_state(self, screenshot: np.ndarray) -> Optional[DetectionResult]:
        """システムリソースの異常を検出"""
        # スクリーンショットとシステムメトリクスを組み合わせて検出
        pass
```

#### ネットワーク状態監視
```python
# src/plugins/network_monitor.py
class NetworkMonitor(BaseDetector):
    """ネットワーク状態を監視してAIサービスの停止を検出"""

    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self.network_checks = {
            "api_endpoint": "http://localhost:8000/health",
            "websocket_connection": "ws://localhost:8001/ws",
            "database_connection": "postgresql://localhost:5432/ai_db"
        }
```

### 5. 学習・適応機能

#### パターン学習
```python
# src/plugins/pattern_learner.py
class PatternLearner(BaseDetector):
    """ユーザーの復旧パターンを学習して自動化"""

    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self.learned_patterns = {}
        self.pattern_database = "learned_patterns.json"

    def learn_recovery_pattern(self, state: str, action: str, success: bool):
        """復旧パターンを学習"""
        if state not in self.learned_patterns:
            self.learned_patterns[state] = {}

        if action not in self.learned_patterns[state]:
            self.learned_patterns[state][action] = {"success": 0, "failure": 0}

        if success:
            self.learned_patterns[state][action]["success"] += 1
        else:
            self.learned_patterns[state][action]["failure"] += 1

    def get_best_recovery_action(self, state: str) -> Optional[str]:
        """最適な復旧アクションを取得"""
        if state in self.learned_patterns:
            actions = self.learned_patterns[state]
            best_action = max(actions.items(),
                            key=lambda x: x[1]["success"] / (x[1]["success"] + x[1]["failure"]))
            return best_action[0]
        return None
```

### 6. 統合監視ダッシュボード

#### 拡張されたメインウィンドウ
```python
# src/gui/main_window.py の拡張
class MainWindow(QMainWindow):
    def setup_plugin_tabs(self):
        """プラグイン別の監視タブを設定"""
        self.plugin_tabs = QTabWidget()

        # AI状態監視タブ
        self.ai_monitor_tab = AIMonitorTab(self.plugin_manager)
        self.plugin_tabs.addTab(self.ai_monitor_tab, "AI状態監視")

        # システムリソースタブ
        self.system_tab = SystemMonitorTab(self.plugin_manager)
        self.plugin_tabs.addTab(self.system_tab, "システム監視")

        # 学習パターンタブ
        self.pattern_tab = PatternLearningTab(self.plugin_manager)
        self.plugin_tabs.addTab(self.pattern_tab, "学習パターン")

        self.layout.addWidget(self.plugin_tabs)
```

## 実装の優先順位

### Phase 1: 基盤プラグインシステム
1. BaseDetector基底クラスの実装
2. PluginManagerの実装
3. 基本的なAI状態検出プラグイン

### Phase 2: 特定フレームワーク対応
1. TensorFlow/PyTorch検出プラグイン
2. Jupyter環境検出プラグイン
3. システムリソース監視プラグイン

### Phase 3: 高度な機能
1. パターン学習機能
2. 適応的復旧戦略
3. 統合監視ダッシュボード

### Phase 4: 最適化・拡張
1. パフォーマンス最適化
2. 追加プラグインの開発
3. コミュニティプラグインのサポート
