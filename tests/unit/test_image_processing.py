"""
画像処理機能のテスト

画像処理ユーティリティの機能をテストします。
"""

from unittest.mock import Mock
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

    def test_preprocess_image_valid(self, processor):
        """有効な画像の前処理テスト"""
        image = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        result = processor.preprocess_image(image)
        assert result is not None
        assert result.shape == (100, 100)

    def test_preprocess_image_none(self, processor):
        """None画像の前処理テスト"""
        result = processor.preprocess_image(None)
        assert result is None

    def test_match_template_basic(self, processor):
        """基本的なテンプレートマッチングテスト"""
        image = np.ones((200, 200), dtype=np.uint8) * 128
        template = np.ones((50, 50), dtype=np.uint8) * 128
        with (
            patch("src.utils.image_processing.cv2.matchTemplate") as mock_match,
            patch("src.utils.image_processing.cv2.minMaxLoc") as mock_min_max_loc,
        ):
            mock_match.return_value = np.ones((150, 150), dtype=np.float32)
            mock_min_max_loc.return_value = (0.1, 0.9, (10, 10), (20, 20))

            result = processor.match_template(image, template, threshold=0.8)

            assert result is not None
            assert result["confidence"] == 0.9
            assert result["position"] == (35, 35)  # 20+25, 20+25

    def test_match_template_low_confidence(self, processor):
        """信頼度が低い場合のテスト"""
        image = np.ones((200, 200), dtype=np.uint8) * 128
        template = np.ones((50, 50), dtype=np.uint8) * 128

        with (
            patch("src.utils.image_processing.cv2.matchTemplate") as mock_match,
            patch("src.utils.image_processing.cv2.minMaxLoc") as mock_min_max_loc,
        ):
            mock_match.return_value = np.ones((150, 150), dtype=np.float32)
            mock_min_max_loc.return_value = (0.1, 0.7, (10, 10), (20, 20))  # 閾値以下

            result = processor.match_template(image, template, threshold=0.8)

            assert result is None
