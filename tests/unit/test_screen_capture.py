"""
画面キャプチャ機能のテスト

画面キャプチャ機能をテストします。
"""

from unittest.mock import Mock
from unittest.mock import patch

import numpy as np
import pytest

from src.utils.screen_capture import ScreenCapture


class TestScreenCapture:
    """ScreenCaptureクラスのテストクラス"""

    @pytest.fixture
    def capture(self):
        """ScreenCaptureのフィクスチャ"""
        return ScreenCapture()

    def test_capture_screen_success(self, capture):
        """画面キャプチャ成功のテスト"""
        mock_array = np.random.randint(0, 255, (600, 800, 3), dtype=np.uint8)

        with patch("src.utils.screen_capture.np.array", return_value=mock_array):
            with patch.object(capture, "_convert_to_grayscale") as mock_convert:
                mock_convert.return_value = mock_array

                result = capture.capture_screen()

                assert result is not None
                assert isinstance(result, np.ndarray)

    def test_capture_region_success(self, capture):
        """領域キャプチャ成功のテスト"""
        mock_array = np.random.randint(0, 255, (200, 300, 3), dtype=np.uint8)
        region = (100, 100, 300, 200)

        with patch("src.utils.screen_capture.np.array", return_value=mock_array):
            with patch.object(capture, "_convert_to_grayscale") as mock_convert:
                mock_convert.return_value = mock_array

                result = capture.capture_region(region)

                assert result is not None
                assert isinstance(result, np.ndarray)

    def test_capture_screen_failure(self, capture):
        """画面キャプチャ失敗のテスト"""
        with patch(
            "src.utils.screen_capture.pyautogui.screenshot",
            side_effect=Exception("Capture failed"),
        ):
            result = capture.capture_screen()
            assert result is None
