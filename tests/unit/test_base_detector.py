"""
BaseDetectorクラスの単体テスト

基底クラスの抽象メソッドと共通機能をテストします。
"""

from typing import Optional
from unittest.mock import Mock, patch

import numpy as np
import pytest

from src.core.base_detector import BaseDetector
from src.core.detection_result import DetectionResult


class ConcreteDetector(BaseDetector):
    """テスト用の具象検出クラス"""

    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self.detect_calls = 0
        self.recovery_calls = 0

    def detect_state(self, screenshot: np.ndarray) -> Optional[DetectionResult]:
        """テスト用の検出実装"""
        self.detect_calls += 1
        if self.config.get("should_detect", False):
            return DetectionResult(
                state_type="test_error",
                confidence=0.9,
                position=(100, 200),
                timestamp=0,
                metadata={"template_name": "test_template.png"}
            )
        return None

    def execute_recovery_action(self, result: DetectionResult) -> bool:
        """テスト用の復旧実装"""
        self.recovery_calls += 1
        return self.config.get("recovery_success", True)


class TestBaseDetector:
    """BaseDetectorクラスのテストクラス"""

    def test_abstract_class_cannot_be_instantiated(self):
        """抽象クラスが直接インスタンス化できないことをテスト"""
        with pytest.raises(TypeError):
            BaseDetector()

    def test_concrete_detector_can_be_instantiated(self, sample_config):
        """具象クラスがインスタンス化できることをテスト"""
        detector = ConcreteDetector(sample_config)
        assert detector is not None
        assert detector.config == sample_config
        assert detector.name == "ConcreteDetector"

    def test_detect_state_abstract_method(self, sample_config):
        """detect_stateメソッドが抽象メソッドとして定義されていることをテスト"""
        detector = ConcreteDetector(sample_config)
        screenshot = np.zeros((100, 100, 3), dtype=np.uint8)

        # メソッドが呼び出し可能であることを確認
        detector.detect_state(screenshot)
        assert detector.detect_calls == 1

    def test_execute_recovery_action_abstract_method(self, sample_config):
        """execute_recovery_actionメソッドが抽象メソッドとして定義されていることをテスト"""
        detector = ConcreteDetector(sample_config)
        result = DetectionResult(
            state_type="test_error",
            confidence=0.9,
            position=(100, 200),
            timestamp=0,
            metadata={}
        )

        # メソッドが呼び出し可能であることを確認
        success = detector.execute_recovery_action(result)
        assert detector.recovery_calls == 1
        assert success is True

    def test_detection_with_positive_result(self, sample_config):
        """検出が成功する場合のテスト"""
        config = sample_config.copy()
        config["should_detect"] = True

        detector = ConcreteDetector(config)
        screenshot = np.zeros((100, 100, 3), dtype=np.uint8)

        result = detector.detect_state(screenshot)

        assert result is not None
        assert result.state_type == "test_error"
        assert result.confidence == 0.9
        assert result.position == (100, 200)
        assert result.metadata["template_name"] == "test_template.png"

    def test_detection_with_negative_result(self, sample_config):
        """検出が失敗する場合のテスト"""
        config = sample_config.copy()
        config["should_detect"] = False

        detector = ConcreteDetector(config)
        screenshot = np.zeros((100, 100, 3), dtype=np.uint8)

        result = detector.detect_state(screenshot)

        assert result is None

    def test_recovery_action_success(self, sample_config):
        """復旧アクションが成功する場合のテスト"""
        config = sample_config.copy()
        config["recovery_success"] = True

        detector = ConcreteDetector(config)
        result = DetectionResult(
            state_type="test_error",
            confidence=0.9,
            position=(100, 200),
            timestamp=0,
            metadata={}
        )

        success = detector.execute_recovery_action(result)

        assert success is True
        assert detector.recovery_calls == 1

    def test_recovery_action_failure(self, sample_config):
        """復旧アクションが失敗する場合のテスト"""
        config = sample_config.copy()
        config["recovery_success"] = False

        detector = ConcreteDetector(config)
        result = DetectionResult(
            state_type="test_error",
            confidence=0.9,
            position=(100, 200),
            timestamp=0,
            metadata={}
        )

        success = detector.execute_recovery_action(result)

        assert success is False
        assert detector.recovery_calls == 1

    def test_is_enabled_default(self, sample_config):
        """is_enabledメソッドのデフォルト動作テスト"""
        detector = ConcreteDetector(sample_config)

        assert detector.is_enabled() is True

    def test_name_property(self, sample_config):
        """nameプロパティのテスト"""
        detector = ConcreteDetector(sample_config)

        assert detector.name == "ConcreteDetector"

    @patch('src.core.base_detector.logger')
    def test_logging_on_initialization(self, mock_logger, sample_config):
        """初期化時のログ出力テスト"""
        ConcreteDetector(sample_config)

        # デバッグログが出力されることを確認
        mock_logger.debug.assert_called_once_with("ConcreteDetector検出器を初期化しました")

    def test_multiple_detections(self, sample_config):
        """複数回の検出実行テスト"""
        config = sample_config.copy()
        config["should_detect"] = True

        detector = ConcreteDetector(config)
        screenshot = np.zeros((100, 100, 3), dtype=np.uint8)

        # 複数回検出を実行
        for _ in range(3):
            result = detector.detect_state(screenshot)
            assert result is not None
            assert result.state_type == "test_error"

        assert detector.detect_calls == 3

    def test_multiple_recovery_actions(self, sample_config):
        """複数回の復旧アクション実行テスト"""
        config = sample_config.copy()
        config["recovery_success"] = True

        detector = ConcreteDetector(config)
        result = DetectionResult(
            state_type="test_error",
            confidence=0.9,
            position=(100, 200),
            timestamp=0,
            metadata={}
        )

        # 複数回復旧アクションを実行
        for _ in range(3):
            success = detector.execute_recovery_action(result)
            assert success is True

        assert detector.recovery_calls == 3
