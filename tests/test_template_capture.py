"""
テンプレート範囲選択機能のテスト
"""

import unittest
from unittest.mock import Mock, patch
import numpy as np
import tkinter as tk

from src.gui.template_capture_dialog import TemplateCaptureDialog


class TestTemplateCaptureDialog(unittest.TestCase):
    """テンプレート範囲選択ダイアログのテスト"""
    
    def setUp(self):
        """テスト前の準備"""
        self.root = tk.Tk()
        self.root.withdraw()  # テスト中は非表示
        
    def tearDown(self):
        """テスト後のクリーンアップ"""
        if self.root:
            self.root.destroy()
    
    @patch('src.gui.template_capture_dialog.ScreenCapture')
    def test_dialog_initialization(self, mock_screen_capture):
        """ダイアログの初期化テスト"""
        dialog = TemplateCaptureDialog(self.root)
        
        self.assertIsNotNone(dialog.parent)
        self.assertIsNotNone(dialog.screen_capture)
        self.assertIsNone(dialog.selected_region)
    
    @patch('src.gui.template_capture_dialog.ScreenCapture')
    def test_coordinate_calculation(self, mock_screen_capture):
        """座標計算のテスト"""
        # モックスクリーンショットを作成
        mock_screenshot = np.zeros((100, 100, 3), dtype=np.uint8)
        mock_screen_capture.return_value.capture_screen.return_value = mock_screenshot
        
        dialog = TemplateCaptureDialog(self.root)
        dialog.screenshot = mock_screenshot
        
        # キャンバスをモックで置き換え
        dialog.canvas = Mock()
        dialog.info_label = Mock()
        
        # マウスイベントをシミュレート
        mock_event = Mock()
        mock_event.x = 10
        mock_event.y = 20
        
        dialog.on_mouse_press(mock_event)
        
        self.assertEqual(dialog.start_x, 10.0)
        self.assertEqual(dialog.start_y, 20.0)


if __name__ == '__main__':
    unittest.main()