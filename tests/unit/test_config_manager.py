"""
ConfigManagerクラスの単体テスト

設定管理機能の各種操作をテストします。
"""

import json
from unittest.mock import patch

from src.config.config_manager import ConfigManager


class TestConfigManager:
    """ConfigManagerクラスのテストクラス"""

    def test_init_with_existing_config(self, config_file):
        """既存の設定ファイルでの初期化テスト"""
        manager = ConfigManager(str(config_file))

        assert manager.config_file == str(config_file)
        assert manager.config is not None
        assert manager.config["monitor_interval"] == 2.0
        assert manager.config["template_threshold"] == 0.8

    def test_init_with_nonexistent_config(self, temp_dir):
        """存在しない設定ファイルでの初期化テスト"""
        nonexistent_path = temp_dir / "nonexistent.json"

        manager = ConfigManager(str(nonexistent_path))

        assert manager.config_file == str(nonexistent_path)
        assert manager.config is not None
        # デフォルト設定が読み込まれることを確認
        assert "monitor_interval" in manager.config
        assert "template_threshold" in manager.config

    def test_load_config_success(self, config_file):
        """設定ファイルの正常読み込みテスト"""
        manager = ConfigManager()

        loaded_config = manager.load_config(str(config_file))

        assert loaded_config is not None
        assert loaded_config["monitor_interval"] == 2.0
        assert loaded_config["recovery_commands"] is not None
        assert len(loaded_config["recovery_commands"]) > 0

    def test_load_config_file_not_found(self, temp_dir):
        """設定ファイルが見つからない場合のテスト"""
        nonexistent_path = temp_dir / "missing.json"
        manager = ConfigManager()

        config = manager.load_config(str(nonexistent_path))

        # デフォルト設定が返されることを確認
        assert config is not None
        assert "monitor_interval" in config

    def test_load_config_invalid_json(self, temp_dir):
        """不正なJSONファイルの読み込みテスト"""
        invalid_json_path = temp_dir / "invalid.json"
        with open(invalid_json_path, "w", encoding="utf-8") as f:
            f.write("{ invalid json content")

        manager = ConfigManager()
        config = manager.load_config(str(invalid_json_path))

        # デフォルト設定が返されることを確認
        assert config is not None
        assert "monitor_interval" in config

    def test_get_config(self, config_file):
        """設定の取得テスト"""
        manager = ConfigManager(str(config_file))

        config = manager.get_config()

        assert isinstance(config, dict)
        assert config["monitor_interval"] == 2.0
        # コピーが返されることを確認
        config["test_key"] = "test_value"
        assert "test_key" not in manager.config

    def test_get_simple_key(self, config_file):
        """単純キーの値取得テスト"""
        manager = ConfigManager(str(config_file))

        value = manager.get("monitor_interval")

        assert value == 2.0

    def test_get_nonexistent_key(self, config_file):
        """存在しないキーの値取得テスト"""
        manager = ConfigManager(str(config_file))

        value = manager.get("nonexistent_key")

        assert value is None

    def test_get_with_default(self, config_file):
        """デフォルト値付きの値取得テスト"""
        manager = ConfigManager(str(config_file))

        value = manager.get("nonexistent_key", "default_value")

        assert value == "default_value"

    def test_get_nested_key(self, config_file):
        """ネストしたキーの値取得テスト"""
        manager = ConfigManager(str(config_file))

        value = manager.get("amazonq_config.enabled")

        assert value is True

    def test_get_nested_nonexistent_key(self, config_file):
        """存在しないネストキーの値取得テスト"""
        manager = ConfigManager(str(config_file))

        value = manager.get("amazonq_config.nonexistent")

        assert value is None

    def test_set_value(self, config_file):
        """設定値の更新テスト"""
        manager = ConfigManager(str(config_file))
        original_value = manager.get("monitor_interval")

        manager.set("monitor_interval", 5.0)

        assert manager.get("monitor_interval") == 5.0
        assert manager.get("monitor_interval") != original_value

    def test_set_new_key(self, config_file):
        """新しいキーの設定テスト"""
        manager = ConfigManager(str(config_file))

        manager.set("new_key", "new_value")

        assert manager.get("new_key") == "new_value"

    def test_validate_setting_monitor_interval(self, config_file):
        """monitor_interval設定値の検証テスト"""
        manager = ConfigManager(str(config_file))

        # 有効な値
        assert manager._validate_setting("monitor_interval", 2.0) is True
        assert manager._validate_setting("monitor_interval", 0.5) is True

        # 無効な値
        assert manager._validate_setting("monitor_interval", 0.05) is False
        assert manager._validate_setting("monitor_interval", 100.0) is False
        assert manager._validate_setting("monitor_interval", "invalid") is False

    def test_validate_setting_template_threshold(self, config_file):
        """template_threshold設定値の検証テスト"""
        manager = ConfigManager(str(config_file))

        # 有効な値
        assert manager._validate_setting("template_threshold", 0.8) is True
        assert manager._validate_setting("template_threshold", 0.1) is True
        assert manager._validate_setting("template_threshold", 1.0) is True

        # 無効な値
        assert manager._validate_setting("template_threshold", 0.05) is False
        assert manager._validate_setting("template_threshold", 1.5) is False

    def test_validate_setting_chat_input_position(self, config_file):
        """chat_input_position設定値の検証テスト"""
        manager = ConfigManager(str(config_file))

        # 有効な値
        assert manager._validate_setting("chat_input_position", None) is True
        assert manager._validate_setting("chat_input_position", [100, 200]) is True
        assert manager._validate_setting("chat_input_position", (150, 250)) is True

        # 無効な値
        assert manager._validate_setting("chat_input_position", [100]) is False
        assert (
            manager._validate_setting("chat_input_position", [100, 200, 300]) is False
        )
        assert manager._validate_setting("chat_input_position", [-10, 200]) is False

    def test_save_config_success(self, temp_dir):
        """設定ファイルの正常保存テスト"""
        config_path = temp_dir / "save_test.json"
        manager = ConfigManager(str(config_path))
        manager.set("test_key", "test_value")

        success = manager.save_config()

        assert success is True
        assert config_path.exists()

        # 保存された内容を確認
        with open(config_path, encoding="utf-8") as f:
            saved_config = json.load(f)

        assert saved_config["test_key"] == "test_value"

    @patch("src.config.config_manager.ConfigManager._setup_logging")
    @patch("builtins.open", side_effect=PermissionError("Permission denied"))
    def test_save_config_permission_error(
        self, mock_file, mock_setup_logging, temp_dir
    ):
        """設定ファイル保存時の権限エラーテスト"""
        config_path = temp_dir / "test.json"
        manager = ConfigManager(str(config_path))

        success = manager.save_config()

        assert success is False

    def test_reload_config(self, config_file):
        """設定の再読み込みテスト"""
        manager = ConfigManager(str(config_file))

        # 設定を変更
        manager.set("test_key", "test_value")
        assert manager.get("test_key") == "test_value"

        # 再読み込み
        success = manager.reload_config()

        assert success is True
        assert manager.get("test_key") is None  # 変更が破棄される

    def test_create_sample_config(self, temp_dir):
        """サンプル設定ファイルの作成テスト"""
        config_path = temp_dir / "sample.json"
        manager = ConfigManager(str(config_path))

        success = manager.create_sample_config()

        assert success is True
        assert config_path.exists()

        # サンプル設定の内容を確認
        with open(config_path, encoding="utf-8") as f:
            sample_config = json.load(f)

        assert "monitor_interval" in sample_config
        assert "recovery_commands" in sample_config
        assert sample_config["chat_input_position"] == [800, 600]

    @patch("src.config.config_manager.logger")
    def test_logging_on_init(self, mock_logger, config_file):
        """初期化時のログ出力テスト"""
        ConfigManager(str(config_file))

        # 情報ログが出力されることを確認
        mock_logger.info.assert_called()

    @patch("src.config.config_manager.logger")
    def test_logging_on_save_success(self, mock_logger, temp_dir):
        """設定保存成功時のログ出力テスト"""
        config_path = temp_dir / "test.json"
        manager = ConfigManager(str(config_path))

        manager.save_config()

        # 成功ログが出力されることを確認
        mock_logger.info.assert_called()

    def test_set_with_validation_failure(self, config_file):
        """設定値検証失敗時のテスト"""
        manager = ConfigManager(str(config_file))
        original_value = manager.get("monitor_interval")

        # 無効な値を設定しようとする
        manager.set("monitor_interval", "invalid_value")

        # 値が変更されていないことを確認
        assert manager.get("monitor_interval") == original_value
