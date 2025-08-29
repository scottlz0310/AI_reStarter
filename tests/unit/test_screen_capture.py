"""
画面キャプチャ機能のテスト

画面キャプチャ機能をテストします。
"""

from unittest.mock import Mock, patch

import numpy as np
import pytest

from src.utils.screen_capture import ScreenCapture


class TestScreenCapture:
    """ScreenCaptureクラスのテストクラス"""

    @pytest.fixture
    def capture(self):
        """ScreenCaptureのフィクスチャ"""
        return ScreenCapture()

    @patch("src.utils.screen_capture.PYAUTOGUI_AVAILABLE", True)
    @patch("src.utils.screen_capture.pyautogui.screenshot")
    def test_capture_screen_success(self, mock_screenshot, capture):
        """画面キャプチャ成功のテスト"""
        mock_image = Mock()
        mock_screenshot.return_value = mock_image
        mock_array = np.random.randint(0, 255, (600, 800, 3), dtype=np.uint8)

        with (
            patch("src.utils.screen_capture.np.array", return_value=mock_array),
            patch.object(
                capture, "_convert_to_grayscale", return_value=mock_array[:, :, 0]
            ),
        ):
            result = capture.capture_screen()
            assert result is not None
            assert isinstance(result, np.ndarray)

    @patch("src.utils.screen_capture.PYAUTOGUI_AVAILABLE", True)
    @patch("src.utils.screen_capture.pyautogui.screenshot")
    def test_capture_screen_with_region(self, mock_screenshot, capture):
        """領域指定での画面キャプチャテスト"""
        mock_image = Mock()
        mock_screenshot.return_value = mock_image
        mock_array = np.random.randint(0, 255, (200, 300, 3), dtype=np.uint8)
        region = (100, 100, 300, 200)

        with (
            patch("src.utils.screen_capture.np.array", return_value=mock_array),
            patch.object(
                capture, "_convert_to_grayscale", return_value=mock_array[:, :, 0]
            ),
        ):
            result = capture.capture_screen(region)
            assert result is not None
            assert isinstance(result, np.ndarray)

    @patch("src.utils.screen_capture.PYAUTOGUI_AVAILABLE", True)
    @patch("src.utils.screen_capture.pyautogui.screenshot")
    def test_capture_screen_failure(self, mock_screenshot, capture):
        """画面キャプチャ失敗のテスト"""
        mock_screenshot.side_effect = Exception("Capture failed")

        with pytest.raises(Exception):  # noqa: B017
            capture.capture_screen()

    @patch("src.utils.screen_capture.PYAUTOGUI_AVAILABLE", False)
    def test_capture_screen_unavailable(self, capture):
        """ライブラリが利用不可の場合のテスト"""
        with pytest.raises(RuntimeError):
            capture.capture_screen()

    def test_is_available(self, capture):
        """利用可能性チェックテスト"""
        result = capture.is_available()
        assert isinstance(result, bool)
