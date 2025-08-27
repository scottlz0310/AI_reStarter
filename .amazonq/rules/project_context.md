# AI_reStarter プロジェクト開発ルール

## プロジェクト概要
AI実装で起こる様々な停止状態を自動検出・復旧する汎用的なシステム。
既存のKiro-IDE自動復旧システムを拡張し、AmazonQ対応とAI実装全般への対応を実現。

## アーキテクチャ原則

### 1. 分離構造の厳守
- **絶対にmain_window.pyなどの親モジュールに直接機能を追記しない**
- 新機能は必ず適切なモジュールに分離して実装
- 各クラスは単一責任原則（Single Responsibility Principle）を遵守
- 依存関係は明確に定義し、循環依存を避ける

### 2. モジュール構成
```
src/
├── core/           # コア機能（検出・復旧ロジック）
├── gui/            # GUI関連（ウィジェット、ダイアログ）
├── config/         # 設定管理
├── utils/          # ユーティリティ
└── plugins/        # プラグイン（新機能追加用）
```

### 3. 新機能追加時のルール
- 新機能は必ず`src/plugins/`に新しいファイルとして作成
- 基底クラス`BaseDetector`を継承して実装
- 設定は`src/config/`に分離
- GUI要素は`src/gui/`に分離

## コーディング規約

### 1. 言語・コミュニケーション
- **全てのコメント、ドキュメント、ログメッセージは日本語で記述**
- ユーザー向けメッセージは日本語
- コード内の変数名・関数名は英語（ただし日本語コメント必須）
- コミットメッセージは日本語

### 2. ロガーの使用
- **必ずloggingモジュールを使用**
- 各モジュールで適切なロガーインスタンスを作成
- ログレベルは適切に使い分け（DEBUG, INFO, WARNING, ERROR, CRITICAL）
- ログメッセージは日本語で詳細に記述
- エラー時はスタックトレースも含める

```python
import logging

logger = logging.getLogger(__name__)

def some_function():
    logger.info("処理を開始します")
    try:
        # 処理内容
        logger.debug("詳細な処理情報")
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}", exc_info=True)
        raise
```

### 3. 型ヒント
- 全ての関数・メソッドに型ヒントを記述
- Optional, Union, List等の適切な型を使用
- カスタム型は`src/types/`に定義

### 4. エラーハンドリング
- 適切な例外処理を実装
- ユーザーフレンドリーなエラーメッセージを日本語で表示
- ログに詳細なエラー情報を記録

## 自動テストの実装

### 1. テスト構造
```
tests/
├── unit/           # 単体テスト
├── integration/    # 統合テスト
├── gui/            # GUIテスト
└── fixtures/       # テストデータ
```

### 2. テスト実装ルール
- **全ての新機能には必ずテストを作成**
- テストファイル名は`test_<モジュール名>.py`
- テストクラス名は`Test<クラス名>`
- テストメソッド名は`test_<機能名>`
- モックを使用して外部依存を分離

```python
import pytest
from unittest.mock import Mock, patch
from src.core.base_detector import BaseDetector

class TestBaseDetector:
    def test_detect_state_abstract_method(self):
        """抽象メソッドの実装チェック"""
        with pytest.raises(TypeError):
            BaseDetector()

    @patch('src.core.base_detector.logger')
    def test_logging_in_detection(self, mock_logger):
        """検出処理でのログ出力テスト"""
        # テスト実装
        pass
```

### 3. テスト実行
- `pytest`を使用
- カバレッジ測定必須（`pytest-cov`）
- CI/CDで自動テスト実行
- テスト失敗時は修正完了までコミット禁止

## プラグイン開発ガイドライン

### 1. 新プラグイン作成時
```python
# src/plugins/new_feature_detector.py
from src.core.base_detector import BaseDetector
from src.core.detection_result import DetectionResult
import logging

logger = logging.getLogger(__name__)

class NewFeatureDetector(BaseDetector):
    """新機能の検出・復旧プラグイン"""

    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        logger.info("新機能検出プラグインを初期化しました")

    def detect_state(self, screenshot: np.ndarray) -> Optional[DetectionResult]:
        """状態を検出"""
        logger.debug("新機能の状態検出を開始")
        # 実装内容
        pass

    def execute_recovery_action(self, result: DetectionResult) -> bool:
        """復旧アクションを実行"""
        logger.info(f"復旧アクションを実行: {result.state_type}")
        # 実装内容
        pass
```

### 2. 設定ファイル分離
```json
// config/new_feature_config.json
{
  "new_feature_detector": {
    "enabled": true,
    "detection_interval": 2.0,
    "threshold": 0.8
  }
}
```

### 3. GUI要素の分離
```python
# src/gui/new_feature_widget.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
import logging

logger = logging.getLogger(__name__)

class NewFeatureWidget(QWidget):
    """新機能用のGUIウィジェット"""

    def __init__(self):
        super().__init__()
        logger.debug("新機能ウィジェットを初期化")
        self.setup_ui()

    def setup_ui(self):
        """UIの初期化"""
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("新機能"))
```

## 設定管理

### 1. 設定ファイル構造
- 各モジュールの設定は独立したJSONファイル
- 設定の検証機能を実装
- デフォルト値の管理
- 設定変更時のログ出力

### 2. 設定変更時の処理
```python
def update_config(self, new_config: dict):
    """設定を更新"""
    logger.info("設定を更新します")
    old_config = self.config.copy()
    self.config.update(new_config)

    # 設定変更の検証
    if self._validate_config():
        logger.info("設定の更新が完了しました")
        self._save_config()
    else:
        logger.error("設定の更新に失敗しました")
        self.config = old_config
```

## パフォーマンス・セキュリティ

### 1. パフォーマンス
- 非同期処理の適切な使用
- メモリリークの防止
- 画像処理の最適化
- 監視間隔の適切な設定

### 2. セキュリティ
- 自動クリック機能の安全性確保
- ユーザー確認機能の実装
- ログ出力での機密情報保護
- エラー時の適切なフォールバック

## ドキュメント

### 1. 必須ドキュメント
- 各モジュールのdocstring（日本語）
- README.md（日本語）
- API仕様書
- 設定ファイル仕様書

### 2. コメント記述ルール
```python
def complex_function(param1: str, param2: int) -> bool:
    """
    複雑な処理を行う関数

    Args:
        param1: 文字列パラメータ（説明）
        param2: 数値パラメータ（説明）

    Returns:
        bool: 処理結果（True: 成功, False: 失敗）

    Raises:
        ValueError: パラメータが無効な場合
        RuntimeError: 処理中にエラーが発生した場合

    Note:
        この関数は重い処理を行うため、非同期での実行を推奨
    """
    logger.info(f"複雑な処理を開始: param1={param1}, param2={param2}")
    # 実装内容
```

## コミット・ブランチ戦略

### 1. ブランチ命名
- `feature/新機能名`: 新機能開発
- `fix/バグ修正内容`: バグ修正
- `refactor/リファクタリング内容`: リファクタリング
- `docs/ドキュメント内容`: ドキュメント更新

### 2. コミットメッセージ
- 日本語で記述
- 変更内容を明確に記述
- 関連するIssue番号を記載

```
feat: AmazonQ検出機能を追加

- BaseDetector基底クラスを実装
- AmazonQDetectorプラグインを作成
- 設定ファイルの分離を実装

Closes #123
```

## 品質保証

### 1. コードレビュー
- 全ての変更はレビュー必須
- 分離構造の遵守を確認
- テストの実装を確認
- ログ出力の適切性を確認

### 2. 静的解析
- `flake8`によるコードスタイルチェック
- `mypy`による型チェック
- `pylint`によるコード品質チェック
- `black`によるコードフォーマット

### 3. 継続的インテグレーション
- 自動テスト実行
- カバレッジ測定
- 静的解析実行
- ビルド確認

## トラブルシューティング

### 1. よくある問題
- 分離構造の違反
- ログ出力の不足
- テストの未実装
- 型ヒントの不足

### 2. 解決方法
- 設計ドキュメントの再確認
- 既存コードの参考
- チームメンバーとの相談
- 段階的な実装

## 開発環境ルール

**重要**: 開発作業時は必ず `development_environment.md` のルールに従い、仮想環境を適用してからコマンドを実行すること。

## 最終確認事項

新機能追加時は以下を必ず確認：
1. **分離構造の遵守** - 親モジュールに直接追記していないか
2. **ログ出力の実装** - 適切なログレベルで日本語メッセージを出力しているか
3. **テストの実装** - 単体テストと統合テストを作成しているか
4. **型ヒントの記述** - 全ての関数・メソッドに型ヒントがあるか
5. **ドキュメントの更新** - docstring、README等を更新しているか
6. **設定の分離** - 設定ファイルを適切に分離しているか
7. **仮想環境での実行** - 全てのコマンドを仮想環境で実行しているか
