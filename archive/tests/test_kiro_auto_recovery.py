#!/usr/bin/env python3
"""
KiroAutoRecoveryクラスのテスト
"""

import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

# テスト対象のモジュールをインポート
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kiro_auto_recovery import KiroAutoRecovery, create_sample_config


class TestKiroAutoRecovery(unittest.TestCase):
    """KiroAutoRecoveryクラスのテスト"""

    def setUp(self):
        """テスト前の準備"""
        # 一時ディレクトリを作成
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, "test_config.json")

        # テスト用設定
        self.test_config = {
            "monitor_interval": 1.0,
            "action_delay": 0.1,
            "max_recovery_attempts": 2,
            "recovery_cooldown": 10,
            "error_templates_dir": os.path.join(self.temp_dir, "templates"),
            "recovery_commands": ["テストコマンド"],
            "template_threshold": 0.7,
        }

        # 設定ファイルを作成
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self.test_config, f)

    def tearDown(self):
        """テスト後のクリーンアップ"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("kiro_auto_recovery.PYAUTOGUI_AVAILABLE", False)
    def test_init_without_pyautogui(self):
        """pyautoguiが利用できない場合の初期化テスト"""
        recovery = KiroAutoRecovery(self.config_file)

        self.assertEqual(recovery.config["monitor_interval"], 1.0)
        self.assertEqual(recovery.config["max_recovery_attempts"], 2)
        self.assertFalse(recovery.monitoring)
        self.assertEqual(recovery.error_templates, {})

    def test_load_config(self):
        """設定ファイル読み込みテスト"""
        recovery = KiroAutoRecovery(self.config_file)

        # 設定が正しく読み込まれているか確認
        self.assertEqual(recovery.config["monitor_interval"], 1.0)
        self.assertEqual(recovery.config["action_delay"], 0.1)
        self.assertEqual(recovery.config["max_recovery_attempts"], 2)
        self.assertEqual(recovery.config["recovery_cooldown"], 10)
        self.assertEqual(recovery.config["template_threshold"], 0.7)

    def test_load_config_default(self):
        """デフォルト設定のテスト"""
        # 存在しない設定ファイルで初期化
        recovery = KiroAutoRecovery("nonexistent_config.json")

        # デフォルト値が設定されているか確認
        self.assertEqual(recovery.config["monitor_interval"], 2.0)
        self.assertEqual(recovery.config["action_delay"], 0.5)
        self.assertEqual(recovery.config["max_recovery_attempts"], 3)
        self.assertEqual(recovery.config["recovery_cooldown"], 30)
        self.assertEqual(recovery.config["template_threshold"], 0.8)

    def test_load_error_templates_empty_dir(self):
        """空のテンプレートディレクトリのテスト"""
        recovery = KiroAutoRecovery(self.config_file)

        # テンプレートディレクトリが作成されているか確認
        self.assertTrue(os.path.exists(recovery.config["error_templates_dir"]))
        self.assertEqual(len(recovery.error_templates), 0)

    def test_should_attempt_recovery(self):
        """復旧試行条件のテスト"""
        recovery = KiroAutoRecovery(self.config_file)

        # 初期状態では復旧可能
        self.assertTrue(recovery.should_attempt_recovery())

        # 最大試行回数に達した場合
        recovery.recovery_attempts = 2
        self.assertFalse(recovery.should_attempt_recovery())

        # クールダウン中の場合
        recovery.recovery_attempts = 0
        recovery.last_error_time = 9999999999  # 未来の時間
        self.assertFalse(recovery.should_attempt_recovery())

    def test_detect_error_no_templates(self):
        """テンプレートがない場合のエラー検出テスト"""
        recovery = KiroAutoRecovery(self.config_file)

        # ダミーのスクリーンショット
        screenshot = np.zeros((100, 100), dtype=np.uint8)

        # テンプレートがない場合はNoneを返す
        result = recovery.detect_error(screenshot)
        self.assertIsNone(result)

    @patch("kiro_auto_recovery.PYAUTOGUI_AVAILABLE", False)
    def test_capture_screen_without_pyautogui(self):
        """pyautoguiが利用できない場合の画面キャプチャテスト"""
        recovery = KiroAutoRecovery(self.config_file)

        # pyautoguiが利用できない場合は例外が発生
        with self.assertRaises(RuntimeError):
            recovery.capture_screen()

    def test_start_monitoring_no_templates(self):
        """テンプレートがない場合の監視開始テスト"""
        recovery = KiroAutoRecovery(self.config_file)

        # テンプレートがない場合はNoneを返す
        result = recovery.start_monitoring()
        self.assertIsNone(result)

    def test_stop_monitoring(self):
        """監視停止テスト"""
        recovery = KiroAutoRecovery(self.config_file)

        # 監視を停止
        recovery.stop_monitoring()
        self.assertFalse(recovery.monitoring)


class TestCreateSampleConfig(unittest.TestCase):
    """create_sample_config関数のテスト"""

    def test_create_sample_config(self):
        """サンプル設定ファイル作成テスト"""
        with tempfile.TemporaryDirectory() as temp_dir:
            original_cwd = os.getcwd()
            os.chdir(temp_dir)

            try:
                # サンプル設定ファイルを作成
                create_sample_config()

                # ファイルが作成されているか確認
                self.assertTrue(os.path.exists("kiro_config.json"))

                # 設定内容を確認
                with open("kiro_config.json", encoding="utf-8") as f:
                    config = json.load(f)

                self.assertEqual(config["monitor_interval"], 2.0)
                self.assertEqual(config["action_delay"], 0.5)
                self.assertEqual(config["max_recovery_attempts"], 3)
                self.assertIn("recovery_commands", config)
                self.assertIn("custom_commands", config)

            finally:
                os.chdir(original_cwd)


if __name__ == "__main__":
    unittest.main()
