#!/usr/bin/env python3
"""
エラー検出機能のテスト
"""

import os
import tempfile
from unittest.mock import patch

import numpy as np
import pytest

from kiro_auto_recovery import KiroAutoRecovery


class TestErrorDetection:
    """エラー検出機能のテスト"""

    @pytest.fixture
    def recovery_system(self):
        """テスト用のKiroAutoRecoveryインスタンス"""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = {"error_templates_dir": temp_dir, "template_threshold": 0.8}

            config_file = os.path.join(temp_dir, "config.json")
            import json

            with open(config_file, "w") as f:
                json.dump(config, f)

            yield KiroAutoRecovery(config_file)

    def test_detect_error_no_templates(self, recovery_system):
        """テンプレートがない場合のエラー検出"""
        screenshot = np.zeros((100, 100), dtype=np.uint8)
        result = recovery_system.detect_error(screenshot)
        assert result is None

    def test_detect_error_with_template(self, recovery_system):
        """テンプレートがある場合のエラー検出"""
        # テストテンプレートを作成
        template = np.ones((50, 50), dtype=np.uint8) * 255
        recovery_system.error_templates["test_error"] = template

        # 完全一致のスクリーンショット
        screenshot = np.ones((100, 100), dtype=np.uint8) * 255
        result = recovery_system.detect_error(screenshot)
        assert result == "test_error"

    def test_detect_error_low_confidence(self, recovery_system):
        """信頼度が低い場合のエラー検出"""
        # 特定のパターンのテンプレート
        template = np.random.randint(0, 255, (50, 50), dtype=np.uint8)
        recovery_system.error_templates["test_error"] = template

        # 全く異なるパターンのスクリーンショット
        screenshot = np.random.randint(100, 200, (100, 100), dtype=np.uint8)
        result = recovery_system.detect_error(screenshot)
        assert result is None

    @patch("kiro_auto_recovery.PYAUTOGUI_AVAILABLE", False)
    def test_capture_screen_unavailable(self, recovery_system):
        """pyautoguiが利用できない場合の画面キャプチャ"""
        with pytest.raises(RuntimeError, match="pyautoguiが利用できません"):
            recovery_system.capture_screen()

    def test_should_attempt_recovery_initial(self, recovery_system):
        """初期状態での復旧試行判定"""
        assert recovery_system.should_attempt_recovery() is True

    def test_should_attempt_recovery_max_attempts(self, recovery_system):
        """最大試行回数到達時の復旧試行判定"""
        recovery_system.recovery_attempts = recovery_system.max_recovery_attempts
        assert recovery_system.should_attempt_recovery() is False

    def test_should_attempt_recovery_cooldown(self, recovery_system):
        """クールダウン中の復旧試行判定"""
        import time

        recovery_system.last_error_time = time.time()
        assert recovery_system.should_attempt_recovery() is False
