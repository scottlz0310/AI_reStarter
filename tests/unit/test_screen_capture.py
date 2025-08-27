"""
ScreenCaptureクラスの単体テスト

画面キャプチャ機能をテストします。
"""

from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pytest

from src.utils.screen_capture import ScreenCapture


class TestScreenCapture:
    """ScreenCaptureクラスのテストクラス"""

    @pytest.fixture
    def capture(self):
        """ScreenCaptureのフィクスチャ"""
        return ScreenCapture()

    def test_init_with_pyautogui_available(self):
        """pyautogui利用可能時の初期化テスト"""
        with patch('src.utils.screen_capture.PYAUTOGUI_AVAILABLE', True):
            capture = ScreenCapture()
            assert capture is not None

    def test_init_with_pyautogui_unavailable(self):
        """pyautogui利用不可時の初期化テスト"""
        with patch('src.utils.screen_capture.PYAUTOGUI_AVAILABLE', False):
            capture = ScreenCapture()
            assert capture is not None

    @patch('src.utils.screen_capture.PYAUTOGUI_AVAILABLE', True)
    @patch('src.utils.screen_capture.pyautogui.screenshot')
    def test_capture_screen_full_screen(self, mock_screenshot, capture):
        """全画面キャプチャのテスト"""
        # PIL Imageオブジェクトをモック
        mock_image = Mock()
        mock_screenshot.return_value = mock_image

        # numpy配列をモック
        mock_array = np.random.randint(0, 255, (600, 800, 3), dtype=np.uint8)

        with patch('src.utils.screen_capture.np.array', return_value=mock_array), \
             patch.object(capture, '_convert_to_grayscale') as mock_convert:

            mock_convert.return_value = np.random.randint(0, 255, (600, 800), dtype=np.uint8)

            result = capture.capture_screen()

        assert result is not None
        mock_screenshot.assert_called_once()
        mock_convert.assert_called_once_with(mock_array)

    @patch('src.utils.screen_capture.PYAUTOGUI_AVAILABLE', True)
    @patch('src.utils.screen_capture.pyautogui.screenshot')
    def test_capture_screen_with_region(self, mock_screenshot, capture):
        """領域指定キャプチャのテスト"""
        mock_image = Mock()
        mock_screenshot.return_value = mock_image

        mock_array = np.random.randint(0, 255, (200, 300, 3), dtype=np.uint8)
        region = (100, 100, 300, 200)

        with patch('src.utils.screen_capture.np.array', return_value=mock_array), \
             patch.object(capture, '_convert_to_grayscale') as mock_convert:

            mock_convert.return_value = np.random.randint(0, 255, (200, 300), dtype=np.uint8)

            result = capture.capture_screen(region=region)

        assert result is not None
        mock_screenshot.assert_called_once_with(region=region)

    @patch('src.utils.screen_capture.PYAUTOGUI_AVAILABLE', False)
    def test_capture_screen_pyautogui_unavailable(self, capture):
        """pyautogui利用不可時のキャプチャテスト"""
        with pytest.raises(RuntimeError, match="pyautoguiが利用できません"):
            capture.capture_screen()

    @patch('src.utils.screen_capture.PYAUTOGUI_AVAILABLE', True)
    @patch('src.utils.screen_capture.pyautogui.screenshot')
    def test_capture_screen_exception(self, mock_screenshot, capture):
        """キャプチャ時の例外処理テスト"""
        mock_screenshot.side_effect = Exception("Screenshot failed")

        with pytest.raises(Exception, match="Screenshot failed"):
            capture.capture_screen()

    def test_convert_to_grayscale_rgb(self, capture):
        """RGB画像のグレースケール変換テスト"""
        rgb_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

        # cv2モジュールをモック（インポート時にモック）
        mock_cv2 = Mock()
        gray_image = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        mock_cv2.cvtColor.return_value = gray_image

        with patch('builtins.__import__', return_value=mock_cv2):
            result = capture._convert_to_grayscale(rgb_image)

        assert result is not None
        mock_cv2.cvtColor.assert_called_once()

    def test_convert_to_grayscale_already_gray(self, capture):
        """既にグレースケールの画像の変換テスト"""
        gray_image = np.random.randint(0, 255, (100, 100), dtype=np.uint8)

        result = capture._convert_to_grayscale(gray_image)

        np.testing.assert_array_equal(result, gray_image)

    def test_convert_to_grayscale_opencv_unavailable(self, capture):
        """OpenCV利用不可時のグレースケール変換テスト"""
        rgb_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

        # インポート時にImportErrorを発生させる
        with patch('builtins.__import__', side_effect=ImportError("OpenCV not available")):
            result = capture._convert_to_grayscale(rgb_image)

        # 元の画像がそのまま返される
        np.testing.assert_array_equal(result, rgb_image)

    def test_convert_to_grayscale_exception(self, capture):
        """グレースケール変換時の例外処理テスト"""
        rgb_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

        # cv2モジュールをモック（インポート時にモック）
        mock_cv2 = Mock()
        mock_cv2.cvtColor.side_effect = Exception("Conversion failed")

        with patch('builtins.__import__', return_value=mock_cv2):
            result = capture._convert_to_grayscale(rgb_image)

        # 元の画像がそのまま返される
        np.testing.assert_array_equal(result, rgb_image)

    def test_is_available_true(self, capture):
        """pyautogui利用可能時のis_availableテスト"""
        with patch('src.utils.screen_capture.PYAUTOGUI_AVAILABLE', True):
            assert capture.is_available() is True

    def test_is_available_false(self, capture):
        """pyautogui利用不可時のis_availableテスト"""
        with patch('src.utils.screen_capture.PYAUTOGUI_AVAILABLE', False):
            assert capture.is_available() is False

    @patch('src.utils.screen_capture.PYAUTOGUI_AVAILABLE', True)
    @patch('src.utils.screen_capture.pyautogui.size')
    def test_get_screen_size_success(self, mock_size, capture):
        """画面サイズ取得成功のテスト"""
        mock_size.return_value = (1920, 1080)

        size = capture.get_screen_size()

        assert size == (1920, 1080)
        mock_size.assert_called_once()

    @patch('src.utils.screen_capture.PYAUTOGUI_AVAILABLE', False)
    def test_get_screen_size_pyautogui_unavailable(self, capture):
        """pyautogui利用不可時の画面サイズ取得テスト"""
        size = capture.get_screen_size()

        assert size is None

    @patch('src.utils.screen_capture.PYAUTOGUI_AVAILABLE', True)
    @patch('src.utils.screen_capture.pyautogui.size')
    def test_get_screen_size_exception(self, mock_size, capture):
        """画面サイズ取得時の例外処理テスト"""
        mock_size.side_effect = Exception("Size detection failed")

        size = capture.get_screen_size()

        assert size is None

    @patch('src.utils.screen_capture.logger')
    def test_logging_on_init_available(self, mock_logger):
        """pyautogui利用可能時の初期化ログテスト"""
        with patch('src.utils.screen_capture.PYAUTOGUI_AVAILABLE', True):
            ScreenCapture()

            mock_logger.info.assert_called_with("画面キャプチャ機能を初期化しました")

    @patch('src.utils.screen_capture.logger')
    def test_logging_on_init_unavailable(self, mock_logger):
        """pyautogui利用不可時の初期化ログテスト"""
        with patch('src.utils.screen_capture.PYAUTOGUI_AVAILABLE', False):
            ScreenCapture()

            mock_logger.warning.assert_called_with("pyautoguiが利用できません。画面キャプチャ機能は無効です。")

    @patch('src.utils.screen_capture.logger')
    @patch('src.utils.screen_capture.PYAUTOGUI_AVAILABLE', True)
    @patch('src.utils.screen_capture.pyautogui.screenshot')
    def test_logging_on_capture_success(self, mock_screenshot, mock_logger, capture):
        """キャプチャ成功時のログテスト"""
        mock_image = Mock()
        mock_screenshot.return_value = mock_image
        mock_array = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

        with patch('src.utils.screen_capture.np.array', return_value=mock_array), \
             patch.object(capture, '_convert_to_grayscale', return_value=np.random.randint(0, 255, (100, 100), dtype=np.uint8)):

            capture.capture_screen()

        mock_logger.debug.assert_called_with("画面全体をキャプチャ")

    @patch('src.utils.screen_capture.logger')
    @patch('src.utils.screen_capture.PYAUTOGUI_AVAILABLE', True)
    @patch('src.utils.screen_capture.pyautogui.screenshot')
    def test_logging_on_capture_with_region(self, mock_screenshot, mock_logger, capture):
        """領域指定キャプチャ時のログテスト"""
        mock_image = Mock()
        mock_screenshot.return_value = mock_image
        mock_array = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        region = (10, 10, 100, 100)

        with patch('src.utils.screen_capture.np.array', return_value=mock_array), \
             patch.object(capture, '_convert_to_grayscale', return_value=np.random.randint(0, 255, (100, 100), dtype=np.uint8)):

            capture.capture_screen(region=region)

        mock_logger.debug.assert_called_with(f"指定領域をキャプチャ: {region}")

    @patch('src.utils.screen_capture.logger')
    @patch('src.utils.screen_capture.PYAUTOGUI_AVAILABLE', True)
    @patch('src.utils.screen_capture.pyautogui.screenshot')
    def test_logging_on_capture_error(self, mock_screenshot, mock_logger, capture):
        """キャプチャエラー時のログテスト"""
        mock_screenshot.side_effect = Exception("Capture failed")

        with pytest.raises(Exception, match="Capture failed"):
            capture.capture_screen()

        mock_logger.error.assert_called()

    @patch('src.utils.screen_capture.logger')
    @patch('src.utils.screen_capture.PYAUTOGUI_AVAILABLE', True)
    @patch('src.utils.screen_capture.pyautogui.size')
    def test_logging_on_screen_size_error(self, mock_size, mock_logger, capture):
        """画面サイズ取得エラー時のログテスト"""
        mock_size.side_effect = Exception("Size detection failed")

        capture.get_screen_size()

        mock_logger.error.assert_called()

    @patch('src.utils.screen_capture.logger')
    def test_logging_on_grayscale_conversion_error(self, mock_logger, capture):
        """グレースケール変換エラー時のログテスト"""
        rgb_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

        # cv2モジュールをモック（インポート時にモック）
        mock_cv2 = Mock()
        mock_cv2.cvtColor.side_effect = Exception("Conversion error")

        with patch('builtins.__import__', return_value=mock_cv2):
            capture._convert_to_grayscale(rgb_image)

        mock_logger.error.assert_called()

    @patch('src.utils.screen_capture.logger')
    def test_logging_on_opencv_unavailable(self, mock_logger, capture):
        """OpenCV利用不可時のログテスト"""
        rgb_image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

        # インポート時にImportErrorを発生させる
        with patch('builtins.__import__', side_effect=ImportError("OpenCV not available")):
            capture._convert_to_grayscale(rgb_image)

        mock_logger.warning.assert_called_with("OpenCVが利用できません。グレースケール変換をスキップします")
