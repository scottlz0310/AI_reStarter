"""
AmazonQDetectorクラスの単体テスト

AmazonQ専用検出器の機能をテストします。
"""

from unittest.mock import Mock, patch

import numpy as np
import pytest

from src.core.detection_result import DetectionResult
from src.plugins.amazonq_detector import AmazonQDetector


class TestAmazonQDetector:
    """AmazonQDetectorクラスのテストクラス"""

    @pytest.fixture
    def mock_config_manager(self, temp_dir):
        """モック設定管理のフィクスチャ"""
        templates_dir = temp_dir / "amazonq_templates"
        templates_dir.mkdir(exist_ok=True)

        config_manager = Mock()
        config_manager.get.side_effect = lambda key, default=None: {
            "amazonq.detection_threshold": 0.8,
            "amazonq.click_delay": 1.0,
            "amazonq.run_button_templates_dir": str(templates_dir),
            "amazonq.enabled": True,
        }.get(key, default)

        return config_manager

    @pytest.fixture
    def detector(self, mock_config_manager):
        """AmazonQDetectorのフィクスチャ"""
        with (
            patch("src.plugins.amazonq_detector.os.path.exists", return_value=True),
            patch("src.plugins.amazonq_detector.os.listdir", return_value=[]),
        ):
            return AmazonQDetector(mock_config_manager)

    def test_init_with_valid_config(self, mock_config_manager):
        """有効な設定での初期化テスト"""
        with (
            patch("src.plugins.amazonq_detector.os.path.exists", return_value=True),
            patch("src.plugins.amazonq_detector.os.listdir", return_value=[]),
        ):
            detector = AmazonQDetector(mock_config_manager)

            assert detector.config_manager == mock_config_manager
            assert detector.detection_threshold == 0.8
            assert detector.is_enabled() is True

    def test_detect_state_no_templates(self, detector):
        """テンプレートが存在しない場合のテスト"""
        detector.run_button_templates = {}
        screenshot = np.random.randint(0, 255, (400, 600, 3), dtype=np.uint8)
        result = detector.detect_state(screenshot)
        assert result is None

    @patch("src.plugins.amazonq_detector.cv2.matchTemplate")
    @patch("src.plugins.amazonq_detector.cv2.minMaxLoc")
    @patch("src.plugins.amazonq_detector.cv2.cvtColor")
    def test_detect_state_run_button_found(
        self, mock_cvt_color, mock_min_max_loc, mock_match_template, detector
    ):
        """▶RUNボタン検出成功のテスト"""
        template = np.ones((50, 50), dtype=np.uint8)
        detector.run_button_templates["run"] = template

        mock_cvt_color.return_value = np.ones((400, 600), dtype=np.uint8)
        mock_match_template.return_value = np.ones((350, 550), dtype=np.float32)
        mock_min_max_loc.return_value = (0.1, 0.9, (50, 100), (100, 200))

        screenshot = np.random.randint(0, 255, (400, 600, 3), dtype=np.uint8)
        result = detector.detect_state(screenshot)

        assert result is not None
        assert result.state_type == "run_button"
        assert result.confidence == 0.9

    @patch("src.plugins.amazonq_detector.pyautogui.click")
    def test_execute_recovery_action_run_button(self, mock_click, detector):
        """▶RUNボタンの復旧アクション実行テスト"""
        result = DetectionResult.create_run_button_result(
            confidence=0.9, position=(100, 200), template_name="run.png"
        )

        success = detector.execute_recovery_action(result)

        assert success is True
        mock_click.assert_called_once_with(100, 200)

    def test_is_enabled_true(self, detector):
        """有効状態の確認テスト"""
        assert detector.is_enabled() is True
