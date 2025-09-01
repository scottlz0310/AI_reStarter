"""
テスト用の共通設定とフィクスチャ

このモジュールはpytestの共通設定とテスト全体で使用するフィクスチャを提供します。
"""

import json
import logging
import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import Mock
from unittest.mock import patch

import numpy as np
import pytest
from PIL import Image


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """一時ディレクトリを作成するフィクスチャ"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def sample_config() -> dict[str, Any]:
    """テスト用のサンプル設定を提供するフィクスチャ"""
    return {
        "monitor_interval": 2.0,
        "action_delay": 0.5,
        "max_recovery_attempts": 3,
        "recovery_cooldown": 30,
        "template_threshold": 0.8,
        "recovery_commands": [
            "続行してください",
            "エラーを修正して続行",
            "タスクを再開してください",
        ],
        "custom_commands": {
            "compilation_error": "コンパイルエラーを修正して続行してください",
            "runtime_error": "ランタイムエラーを解決して再実行してください",
        },
        "chat_input_position": [1457, 932],
        "monitor_region": [1431, 777, 480, 217],
        "amazonq_config": {
            "enabled": True,
            "detection_interval": 1.5,
            "template_threshold": 0.85,
        },
    }


@pytest.fixture
def config_file(temp_dir: Path, sample_config: dict[str, Any]) -> Path:
    """テスト用の設定ファイルを作成するフィクスチャ"""
    config_path = temp_dir / "test_config.json"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(sample_config, f, ensure_ascii=False, indent=2)
    return config_path


@pytest.fixture
def sample_image() -> np.ndarray:
    """テスト用のサンプル画像を生成するフィクスチャ"""
    # 100x100のRGB画像を作成
    image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    return image


@pytest.fixture
def sample_template_image(temp_dir: Path) -> Path:
    """テスト用のテンプレート画像ファイルを作成するフィクスチャ"""
    template_path = temp_dir / "test_template.png"

    # 50x50の赤い四角形を作成
    image = Image.new("RGB", (50, 50), color="red")
    image.save(template_path)

    return template_path


@pytest.fixture
def mock_screen_capture():
    """画面キャプチャ機能をモックするフィクスチャ"""

    # デフォルトで100x100の画像を返すモック関数
    def mock_capture_func(*args, **kwargs):
        return np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

    yield mock_capture_func


@pytest.fixture
def mock_pyautogui():
    """pyautoguiをモックするフィクスチャ"""
    with (
        patch("pyautogui.click") as mock_click,
        patch("pyautogui.write") as mock_write,
        patch("pyautogui.press") as mock_press,
    ):
        yield {"click": mock_click, "write": mock_write, "press": mock_press}


@pytest.fixture
def mock_keyboard():
    """keyboardライブラリをモックするフィクスチャ"""
    with (
        patch("keyboard.add_hotkey") as mock_add_hotkey,
        patch("keyboard.remove_hotkey") as mock_remove_hotkey,
    ):
        yield {"add_hotkey": mock_add_hotkey, "remove_hotkey": mock_remove_hotkey}


@pytest.fixture
def mock_logger():
    """ロガーをモックするフィクスチャ"""
    logger = Mock(spec=logging.Logger)
    logger.debug = Mock()
    logger.info = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    logger.critical = Mock()
    return logger


@pytest.fixture
def templates_dir(temp_dir: Path) -> Path:
    """テンプレート保存用ディレクトリを作成するフィクスチャ"""
    templates_path = temp_dir / "templates"
    templates_path.mkdir(exist_ok=True)
    return templates_path


@pytest.fixture(autouse=True)
def setup_test_logging():
    """テスト実行時のログ設定を行うフィクスチャ"""
    # テスト用のログレベルを設定
    logging.getLogger().setLevel(logging.DEBUG)

    # テスト用のハンドラーを追加
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)

    # ルートロガーにハンドラーを追加
    root_logger = logging.getLogger()
    root_logger.addHandler(handler)

    yield

    # テスト後にハンドラーを削除
    root_logger.removeHandler(handler)


@pytest.fixture
def mock_win32gui():
    """win32guiライブラリをモックするフィクスチャ（Windows専用機能）"""
    with (
        patch("win32gui.FindWindow") as mock_find_window,
        patch("win32gui.SetForegroundWindow") as mock_set_foreground,
        patch("win32gui.GetWindowRect") as mock_get_rect,
    ):
        # デフォルトの戻り値を設定
        mock_find_window.return_value = 12345  # ダミーのウィンドウハンドル
        mock_get_rect.return_value = (100, 100, 800, 600)  # ダミーの座標

        yield {
            "find_window": mock_find_window,
            "set_foreground": mock_set_foreground,
            "get_rect": mock_get_rect,
        }


@pytest.fixture
def detection_result_data() -> dict[str, Any]:
    """検出結果のテストデータを提供するフィクスチャ"""
    return {
        "state_type": "compilation_error",
        "confidence": 0.95,
        "position": (100, 200),
        "template_name": "error_template.png",
        "timestamp": "2024-01-01T12:00:00",
        "recovery_action": "コンパイルエラーを修正して続行してください",
    }


# テスト用のマーカーを定義
pytest_plugins = []


def pytest_configure(config):
    """pytestの設定を行う関数"""
    config.addinivalue_line("markers", "unit: 単体テスト用のマーカー")
    config.addinivalue_line("markers", "integration: 統合テスト用のマーカー")
    config.addinivalue_line("markers", "gui: GUIテスト用のマーカー")
    config.addinivalue_line("markers", "slow: 実行時間が長いテスト用のマーカー")
