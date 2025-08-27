"""
AmazonQDetectorクラスの単体テスト

AmazonQ専用検出器の機能をテストします。
"""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

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
            "amazonq.enabled": True
        }.get(key, default)

        return config_manager

    @pytest.fixture
    def detector(self, mock_config_manager):
        """AmazonQDetectorのフィクスチャ"""
        with patch('src.plugins.amazonq_detector.os.path.exists', return_value=True), \
             patch('src.plugins.amazonq_detector.os.listdir', return_value=[]):
            return AmazonQDetector(mock_config_manager)

    def test_init_with_valid_config(self, mock_config_manager):
        """有効な設定での初期化テスト"""
        with patch('src.plugins.amazonq_detector.os.path.exists', return_value=True), \
             patch('src.plugins.amazonq_detector.os.listdir', return_value=[]):

            detector = AmazonQDetector(mock_config_manager)

            assert detector.config_manager == mock_config_manager
            assert detector.detection_threshold == 0.8
            assert detector.is_enabled() is True

    def test_init_with_disabled_config(self, temp_dir):
        """無効化された設定での初期化テスト"""
        templates_dir = temp_dir / "amazonq_templates"
        templates_dir.mkdir(exist_ok=True)

        config_manager = Mock()
        config_manager.get.side_effect = lambda key, default=None: {
            "amazonq.detection_threshold": 0.8,
            "amazonq.click_delay": 1.0,
            "amazonq.run_button_templates_dir": str(templates_dir),
            "amazonq.enabled": False
        }.get(key, default)

        with patch('src.plugins.amazonq_detector.os.path.exists', return_value=True), \
             patch('src.plugins.amazonq_detector.os.listdir', return_value=[]):

            detector = AmazonQDetector(config_manager)

            assert detector.is_enabled() is False

    @patch('src.plugins.amazonq_detector.cv2.matchTemplate')
    @patch('src.plugins.amazonq_detector.cv2.minMaxLoc')
    @patch('src.plugins.amazonq_detector.cv2.cvtColor')
    def test_detect_state_run_button_found(self, mock_cvt_color, mock_min_max_loc, mock_match_template, detector):
        """▶RUNボタン検出成功のテスト"""
        # テンプレートを手動で追加
        template = np.ones((50, 50), dtype=np.uint8)
        detector.run_button_templates["run"] = template

        # モックの設定
        mock_cvt_color.return_value = np.ones((400, 600), dtype=np.uint8)
        mock_match_template.return_value = np.ones((350, 550), dtype=np.float32)
        mock_min_max_loc.return_value = (0.1, 0.9, (50, 100), (100, 200))

        screenshot = np.random.randint(0, 255, (400, 600, 3), dtype=np.uint8)

        result = detector.detect_state(screenshot)

        assert result is not None
        assert result.state_type == "run_button"
        assert result.confidence == 0.9
        assert result.position == (125, 225)  # 100+25, 200+25 (テンプレート中心)
        assert result.metadata["template_name"] == "run"

    @patch('src.plugins.amazonq_detector.cv2.matchTemplate')
    @patch('src.plugins.amazonq_detector.cv2.minMaxLoc')
    @patch('src.plugins.amazonq_detector.cv2.cvtColor')
    def test_detect_state_run_button_not_found(self, mock_cvt_color, mock_min_max_loc, mock_match_template, detector):
        """▶RUNボタン検出失敗のテスト"""
        # テンプレートを手動で追加
        template = np.ones((50, 50), dtype=np.uint8)
        detector.run_button_templates["run"] = template

        # モックの設定（信頼度が閾値以下）
        mock_cvt_color.return_value = np.ones((400, 600), dtype=np.uint8)
        mock_match_template.return_value = np.ones((350, 550), dtype=np.float32)
        mock_min_max_loc.return_value = (0.1, 0.7, (50, 100), (100, 200))  # 閾値0.8以下

        screenshot = np.random.randint(0, 255, (400, 600, 3), dtype=np.uint8)

        result = detector.detect_state(screenshot)

        assert result is None

    def test_detect_state_template_not_found(self, detector):
        """テンプレートが存在しない場合のテスト"""
        # テンプレートを空にする
        detector.run_button_templates = {}

        screenshot = np.random.randint(0, 255, (400, 600, 3), dtype=np.uint8)

        result = detector.detect_state(screenshot)

        assert result is None

    def test_detect_state_disabled_detector(self, temp_dir):
        """無効化された検出器での検出テスト"""
        templates_dir = temp_dir / "amazonq_templates"
        templates_dir.mkdir(exist_ok=True)

        config_manager = Mock()
        config_manager.get.side_effect = lambda key, default=None: {
            "amazonq.detection_threshold": 0.8,
            "amazonq.click_delay": 1.0,
            "amazonq.run_button_templates_dir": str(templates_dir),
            "amazonq.enabled": False
        }.get(key, default)

        with patch('src.plugins.amazonq_detector.os.path.exists', return_value=True), \
             patch('src.plugins.amazonq_detector.os.listdir', return_value=[]):

            detector = AmazonQDetector(config_manager)
            screenshot = np.random.randint(0, 255, (400, 600, 3), dtype=np.uint8)

            # 無効化されていても検出は実行される（is_enabledは別の用途）
            result = detector.detect_state(screenshot)

            assert result is None  # テンプレートがないため

    @patch('src.plugins.amazonq_detector.pyautogui.click')
    def test_execute_recovery_action_run_button(self, mock_click, detector):
        """▶RUNボタンの復旧アクション実行テスト"""
        result = DetectionResult.create_run_button_result(
            confidence=0.9,
            position=(100, 200),
            template_name="run.png"
        )

        success = detector.execute_recovery_action(result)

        assert success is True
        mock_click.assert_called_once_with(100, 200)

    @patch('src.plugins.amazonq_detector.pyautogui.click')
    def test_execute_recovery_action_click_failure(self, mock_click, detector):
        """クリック失敗時の復旧アクションテスト"""
        mock_click.side_effect = Exception("Click failed")

        result = DetectionResult.create_run_button_result(
            confidence=0.9,
            position=(100, 200),
            template_name="run.png"
        )

        success = detector.execute_recovery_action(result)

        assert success is False

    def test_execute_recovery_action_unsupported_state(self, detector):
        """サポートされていない状態タイプの復旧アクションテスト"""
        result = DetectionResult(
            state_type="unsupported_state",
            confidence=0.9,
            position=(100, 200),
            timestamp=0,
            metadata={}
        )

        success = detector.execute_recovery_action(result)

        assert success is False

    def test_is_enabled_true(self, detector):
        """有効状態の確認テスト"""
        assert detector.is_enabled() is True

    def test_is_enabled_false(self, temp_dir):
        """無効状態の確認テスト"""
        templates_dir = temp_dir / "amazonq_templates"
        templates_dir.mkdir(exist_ok=True)

        config_manager = Mock()
        config_manager.get.side_effect = lambda key, default=None: {
            "amazonq.detection_threshold": 0.8,
            "amazonq.click_delay": 1.0,
            "amazonq.run_button_templates_dir": str(templates_dir),
            "amazonq.enabled": False
        }.get(key, default)

        with patch('src.plugins.amazonq_detector.os.path.exists', return_value=True), \
             patch('src.plugins.amazonq_detector.os.listdir', return_value=[]):

            detector = AmazonQDetector(config_manager)

            assert detector.is_enabled() is False

    @patch('src.plugins.amazonq_detector.logger')
    @patch('src.plugins.amazonq_detector.cv2.matchTemplate')
    @patch('src.plugins.amazonq_detector.cv2.minMaxLoc')
    @patch('src.plugins.amazonq_detector.cv2.cvtColor')
    def test_logging_on_detection_success(self, mock_cvt_color, mock_min_max_loc, mock_match_template, mock_logger, detector):
        """検出成功時のログ出力テスト"""
        # テンプレートを手動で追加
        template = np.ones((50, 50), dtype=np.uint8)
        detector.run_button_templates["run"] = template

        # モックの設定
        mock_cvt_color.return_value = np.ones((400, 600), dtype=np.uint8)
        mock_match_template.return_value = np.ones((350, 550), dtype=np.float32)
        mock_min_max_loc.return_value = (0.1, 0.9, (50, 100), (100, 200))

        screenshot = np.random.randint(0, 255, (400, 600, 3), dtype=np.uint8)
        detector.detect_state(screenshot)

        # ログが出力されることを確認
        mock_logger.info.assert_called()

    @patch('src.plugins.amazonq_detector.logger')
    def test_logging_on_recovery_action(self, mock_logger, detector):
        """復旧アクション実行時のログ出力テスト"""
        with patch('src.plugins.amazonq_detector.pyautogui.click'):
            result = DetectionResult.create_run_button_result(
                confidence=0.9,
                position=(100, 200),
                template_name="run.png"
            )

            detector.execute_recovery_action(result)

            # ログが出力されることを確認
            mock_logger.info.assert_called()

    def test_template_threshold_configuration(self, temp_dir):
        """テンプレート閾値設定のテスト"""
        templates_dir = temp_dir / "amazonq_templates"
        templates_dir.mkdir(exist_ok=True)

        config_manager = Mock()
        config_manager.get.side_effect = lambda key, default=None: {
            "amazonq.detection_threshold": 0.95,
            "amazonq.click_delay": 1.0,
            "amazonq.run_button_templates_dir": str(templates_dir),
            "amazonq.enabled": True
        }.get(key, default)

        with patch('src.plugins.amazonq_detector.os.path.exists', return_value=True), \
             patch('src.plugins.amazonq_detector.os.listdir', return_value=[]):

            detector = AmazonQDetector(config_manager)

            assert detector.detection_threshold == 0.95

    def test_templates_directory_configuration(self, temp_dir):
        """テンプレートディレクトリ設定のテスト"""
        custom_templates_dir = temp_dir / "custom_templates"
        custom_templates_dir.mkdir(exist_ok=True)

        config_manager = Mock()
        config_manager.get.side_effect = lambda key, default=None: {
            "amazonq.detection_threshold": 0.8,
            "amazonq.click_delay": 1.0,
            "amazonq.run_button_templates_dir": str(custom_templates_dir),
            "amazonq.enabled": True
        }.get(key, default)

        with patch('src.plugins.amazonq_detector.os.path.exists', return_value=True), \
             patch('src.plugins.amazonq_detector.os.listdir', return_value=[]):

            detector = AmazonQDetector(config_manager)

            assert detector.templates_dir == str(custom_templates_dir)
