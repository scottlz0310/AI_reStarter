"""
コア機能のテスト（カバレッジ向上）
"""
import os
import tempfile
import threading
import time
from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pytest

from kiro_auto_recovery import KiroAutoRecovery


class TestCoreFunctions:
    """コア機能のテスト"""

    @patch("kiro_auto_recovery.PYAUTOGUI_AVAILABLE", True)
    @patch("kiro_auto_recovery.pyautogui")
    @patch("kiro_auto_recovery.cv2")
    def test_capture_screen_with_region(self, mock_cv2, mock_pyautogui):
        """画面キャプチャ（領域指定）のテスト"""
        # モック設定
        mock_screenshot = Mock()
        mock_pyautogui.screenshot.return_value = mock_screenshot
        mock_array = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_gray = np.zeros((100, 100), dtype=np.uint8)
        
        with patch("numpy.array", return_value=mock_array):
            mock_cv2.cvtColor.return_value = mock_gray
            
            recovery = KiroAutoRecovery()
            result = recovery.capture_screen((10, 20, 100, 200))
            
            mock_pyautogui.screenshot.assert_called_once_with(region=(10, 20, 100, 200))
            mock_cv2.cvtColor.assert_called_once()
            assert isinstance(result, np.ndarray)

    @patch("kiro_auto_recovery.PYAUTOGUI_AVAILABLE", True)
    @patch("kiro_auto_recovery.pyautogui")
    @patch("kiro_auto_recovery.cv2")
    def test_capture_screen_full(self, mock_cv2, mock_pyautogui):
        """画面キャプチャ（全画面）のテスト"""
        mock_screenshot = Mock()
        mock_pyautogui.screenshot.return_value = mock_screenshot
        mock_array = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_gray = np.zeros((100, 100), dtype=np.uint8)
        
        with patch("numpy.array", return_value=mock_array):
            mock_cv2.cvtColor.return_value = mock_gray
            
            recovery = KiroAutoRecovery()
            result = recovery.capture_screen()
            
            mock_pyautogui.screenshot.assert_called_once_with()
            assert isinstance(result, np.ndarray)

    @patch("kiro_auto_recovery.PYAUTOGUI_AVAILABLE", False)
    def test_capture_screen_unavailable(self):
        """pyautogui利用不可時のテスト"""
        recovery = KiroAutoRecovery()
        
        with pytest.raises(RuntimeError, match="pyautoguiが利用できません"):
            recovery.capture_screen()

    @patch("kiro_auto_recovery.cv2")
    def test_detect_error_found(self, mock_cv2):
        """エラー検出（発見）のテスト"""
        recovery = KiroAutoRecovery()
        recovery.error_templates = {
            "test_error": np.zeros((50, 50), dtype=np.uint8)
        }
        
        # マッチング結果をモック
        mock_cv2.matchTemplate.return_value = np.array([[0.9]])
        mock_cv2.minMaxLoc.return_value = (0.1, 0.9, (0, 0), (10, 10))
        
        screenshot = np.zeros((100, 100), dtype=np.uint8)
        result = recovery.detect_error(screenshot)
        
        assert result == "test_error"
        mock_cv2.matchTemplate.assert_called_once()

    @patch("kiro_auto_recovery.cv2")
    def test_detect_error_not_found(self, mock_cv2):
        """エラー検出（未発見）のテスト"""
        recovery = KiroAutoRecovery()
        recovery.error_templates = {
            "test_error": np.zeros((50, 50), dtype=np.uint8)
        }
        
        # 低い信頼度でモック
        mock_cv2.matchTemplate.return_value = np.array([[0.5]])
        mock_cv2.minMaxLoc.return_value = (0.1, 0.5, (0, 0), (10, 10))
        
        screenshot = np.zeros((100, 100), dtype=np.uint8)
        result = recovery.detect_error(screenshot)
        
        assert result is None

    def test_should_attempt_recovery_cooldown(self):
        """復旧試行判定（クールダウン中）のテスト"""
        recovery = KiroAutoRecovery()
        recovery.last_error_time = time.time()  # 現在時刻
        recovery.recovery_attempts = 0
        
        result = recovery.should_attempt_recovery()
        assert result is False

    def test_should_attempt_recovery_max_attempts(self):
        """復旧試行判定（最大試行回数到達）のテスト"""
        recovery = KiroAutoRecovery()
        recovery.last_error_time = 0  # 十分古い時刻
        recovery.recovery_attempts = 3  # 最大値
        recovery.max_recovery_attempts = 3
        
        result = recovery.should_attempt_recovery()
        assert result is False

    def test_should_attempt_recovery_ok(self):
        """復旧試行判定（実行可能）のテスト"""
        recovery = KiroAutoRecovery()
        recovery.last_error_time = 0  # 十分古い時刻
        recovery.recovery_attempts = 1
        recovery.max_recovery_attempts = 3
        
        result = recovery.should_attempt_recovery()
        assert result is True

    @patch("kiro_auto_recovery.WIN32GUI_AVAILABLE", True)
    @patch("kiro_auto_recovery.PYAUTOGUI_AVAILABLE", True)
    @patch("kiro_auto_recovery.pyautogui")
    @patch("kiro_auto_recovery.win32gui")
    def test_send_recovery_command_success(self, mock_win32gui, mock_pyautogui):
        """復旧コマンド送信（成功）のテスト"""
        recovery = KiroAutoRecovery()
        recovery.config["chat_input_position"] = [100, 200]
        
        # ウィンドウ検索のモック
        mock_window = Mock()
        mock_window.title = "Kiro Test Window"
        mock_pyautogui.getAllWindows.return_value = [mock_window]
        mock_win32gui.FindWindow.return_value = 12345
        
        result = recovery.send_recovery_command("test_error")
        
        assert result is True
        mock_pyautogui.click.assert_called_once_with(100, 200)

    @patch("kiro_auto_recovery.PYAUTOGUI_AVAILABLE", True)
    @patch("kiro_auto_recovery.pyautogui")
    def test_send_recovery_command_no_chat_position(self, mock_pyautogui):
        """復旧コマンド送信（チャット位置なし）のテスト"""
        recovery = KiroAutoRecovery()
        recovery.config["chat_input_position"] = None
        
        # find_chat_inputが失敗するようにモック
        with patch.object(recovery, "find_chat_input", return_value=None):
            result = recovery.send_recovery_command()
            
            assert result is False

    @patch("kiro_auto_recovery.os.path.exists")
    @patch("kiro_auto_recovery.cv2")
    def test_find_chat_input_success(self, mock_cv2, mock_exists):
        """チャット入力欄検出（成功）のテスト"""
        recovery = KiroAutoRecovery()
        mock_exists.return_value = True
        
        # テンプレート読み込みのモック
        mock_template = np.zeros((30, 100), dtype=np.uint8)
        mock_cv2.imread.return_value = mock_template
        
        # マッチング結果のモック
        mock_cv2.matchTemplate.return_value = np.array([[0.8]])
        mock_cv2.minMaxLoc.return_value = (0.1, 0.8, (0, 0), (50, 15))
        
        with patch.object(recovery, "capture_screen", return_value=np.zeros((200, 300), dtype=np.uint8)):
            result = recovery.find_chat_input()
            
            assert result == (100, 30)  # 中心座標

    @patch("kiro_auto_recovery.os.path.exists")
    def test_find_chat_input_no_template(self, mock_exists):
        """チャット入力欄検出（テンプレートなし）のテスト"""
        recovery = KiroAutoRecovery()
        mock_exists.return_value = False
        
        result = recovery.find_chat_input()
        assert result is None

    def test_start_monitoring_already_running(self):
        """監視開始（既に実行中）のテスト"""
        recovery = KiroAutoRecovery()
        recovery.monitoring = True
        
        result = recovery.start_monitoring()
        assert result is None

    def test_start_monitoring_no_templates(self):
        """監視開始（テンプレートなし）のテスト"""
        recovery = KiroAutoRecovery()
        recovery.monitoring = False
        recovery.error_templates = {}
        
        result = recovery.start_monitoring()
        assert result is None

    def test_start_monitoring_success(self):
        """監視開始（成功）のテスト"""
        recovery = KiroAutoRecovery()
        recovery.monitoring = False
        recovery.error_templates = {"test": np.zeros((10, 10))}
        
        with patch.object(recovery, "monitor_loop"):
            result = recovery.start_monitoring()
            
            assert isinstance(result, threading.Thread)
            assert recovery.monitoring is True
            assert recovery.recovery_attempts == 0

    def test_stop_monitoring(self):
        """監視停止のテスト"""
        recovery = KiroAutoRecovery()
        recovery.monitoring = True
        
        recovery.stop_monitoring()
        assert recovery.monitoring is False

    @patch("kiro_auto_recovery.cv2")
    def test_save_error_template_with_region(self, mock_cv2):
        """エラーテンプレート保存（領域指定）のテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            recovery = KiroAutoRecovery()
            recovery.config["error_templates_dir"] = temp_dir
            
            mock_screenshot = np.zeros((100, 100), dtype=np.uint8)
            
            with patch.object(recovery, "capture_screen", return_value=mock_screenshot):
                recovery.save_error_template("test_template", (10, 20, 100, 200))
                
                mock_cv2.imwrite.assert_called_once()
                assert "test_template" in recovery.error_templates

    @patch("kiro_auto_recovery.cv2")
    def test_save_error_template_no_region(self, mock_cv2):
        """エラーテンプレート保存（領域なし）のテスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            recovery = KiroAutoRecovery()
            recovery.config["error_templates_dir"] = temp_dir
            recovery.config["monitor_region"] = [0, 0, 800, 600]
            
            mock_screenshot = np.zeros((100, 100), dtype=np.uint8)
            
            with patch.object(recovery, "capture_screen", return_value=mock_screenshot):
                recovery.save_error_template("test_template")
                
                mock_cv2.imwrite.assert_called_once()