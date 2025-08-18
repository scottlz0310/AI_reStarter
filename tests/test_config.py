#!/usr/bin/env python3
"""
設定管理のテスト
"""

import json
import os
import tempfile

from kiro_auto_recovery import KiroAutoRecovery


class TestConfigManagement:
    """設定管理のテスト"""

    def test_default_config_values(self):
        """デフォルト設定値のテスト"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({}, f)
            config_file = f.name

        try:
            recovery = KiroAutoRecovery(config_file)

            assert recovery.config["monitor_interval"] == 2.0
            assert recovery.config["action_delay"] == 0.5
            assert recovery.config["max_recovery_attempts"] == 3
            assert recovery.config["recovery_cooldown"] == 30
            assert recovery.config["template_threshold"] == 0.8
            assert "recovery_commands" in recovery.config
            assert "custom_commands" in recovery.config
        finally:
            os.unlink(config_file)

    def test_custom_config_override(self):
        """カスタム設定の上書きテスト"""
        custom_config = {
            "monitor_interval": 1.5,
            "max_recovery_attempts": 5,
            "template_threshold": 0.9,
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(custom_config, f)
            config_file = f.name

        try:
            recovery = KiroAutoRecovery(config_file)

            assert recovery.config["monitor_interval"] == 1.5
            assert recovery.config["max_recovery_attempts"] == 5
            assert recovery.config["template_threshold"] == 0.9
            # デフォルト値も保持されている
            assert recovery.config["action_delay"] == 0.5
        finally:
            os.unlink(config_file)

    def test_invalid_config_file(self):
        """無効な設定ファイルのテスト"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json content")
            config_file = f.name

        try:
            recovery = KiroAutoRecovery(config_file)
            # デフォルト設定が使用される
            assert recovery.config["monitor_interval"] == 2.0
        finally:
            os.unlink(config_file)

    def test_nonexistent_config_file(self):
        """存在しない設定ファイルのテスト"""
        recovery = KiroAutoRecovery("nonexistent_file.json")
        # デフォルト設定が使用される
        assert recovery.config["monitor_interval"] == 2.0
        assert recovery.config["action_delay"] == 0.5
