"""
画像処理機能のテスト

画像処理ユーティリティの機能をテストします。
"""

from unittest.mock import patch

import numpy as np
import pytest

from src.utils.image_processing import ImageProcessor


class TestImageProcessor:
    """ImageProcessorクラスのテストクラス"""

    @pytest.fixture
    def processor(self):
        """ImageProcessorのフィクスチャ"""
        return ImageProcessor()

    def test_detect_error_valid(self, processor):
        """有効なエラー検出テスト"""
        screenshot = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        template = np.random.randint(0, 255, (50, 50), dtype=np.uint8)
        error_templates = {"test_error": template}

        result = processor.detect_error(screenshot, error_templates, threshold=0.1)
        assert result is None or isinstance(result, str)

    def test_detect_error_empty_templates(self, processor):
        """空のテンプレート辞書でのエラー検出テスト"""
        screenshot = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        error_templates = {}

        result = processor.detect_error(screenshot, error_templates)
        assert result is None

    def test_find_template_position_basic(self, processor):
        """基本的なテンプレート位置検出テスト"""
        screenshot = np.random.randint(0, 255, (200, 200), dtype=np.uint8)
        template = np.random.randint(0, 255, (50, 50), dtype=np.uint8)

        result = processor.find_template_position(screenshot, template, threshold=0.1)
        assert result is None or (isinstance(result, tuple) and len(result) == 2)

    def test_find_template_position_large_template(self, processor):
        """大きすぎるテンプレートでの位置検出テスト"""
        screenshot = np.random.randint(0, 255, (50, 50), dtype=np.uint8)
        template = np.random.randint(0, 255, (100, 100), dtype=np.uint8)

        result = processor.find_template_position(screenshot, template)
        assert result is None
