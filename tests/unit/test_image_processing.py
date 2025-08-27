"""
ImageProcessorクラスの単体テスト

画像処理機能をテストします。
"""

import os
import tempfile
from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pytest

from src.utils.image_processing import ImageProcessor


class TestImageProcessor:
    """ImageProcessorクラスのテストクラス"""

    @pytest.fixture
    def processor(self):
        """ImageProcessorのフィクスチャ"""
        return ImageProcessor()

    @pytest.fixture
    def sample_screenshot(self):
        """サンプルスクリーンショットのフィクスチャ"""
        return np.random.randint(0, 255, (200, 300), dtype=np.uint8)

    @pytest.fixture
    def sample_template(self):
        """サンプルテンプレートのフィクスチャ"""
        return np.random.randint(0, 255, (50, 50), dtype=np.uint8)

    @pytest.fixture
    def error_templates(self, sample_template):
        """エラーテンプレート辞書のフィクスチャ"""
        return {
            "compilation_error": sample_template,
            "runtime_error": np.random.randint(0, 255, (40, 60), dtype=np.uint8)
        }

    def test_init(self):
        """初期化テスト"""
        processor = ImageProcessor()
        assert processor is not None

    @patch('src.utils.image_processing.cv2.matchTemplate')
    @patch('src.utils.image_processing.cv2.minMaxLoc')
    def test_detect_error_found(self, mock_min_max_loc, mock_match_template, processor, sample_screenshot, error_templates):
        """エラー検出成功のテスト"""
        # モックの設定
        mock_match_template.return_value = np.array([[0.9]])
        mock_min_max_loc.return_value = (0.1, 0.9, (10, 10), (20, 20))

        result = processor.detect_error(sample_screenshot, error_templates, threshold=0.8)

        assert result == "compilation_error"

    @patch('src.utils.image_processing.cv2.matchTemplate')
    @patch('src.utils.image_processing.cv2.minMaxLoc')
    def test_detect_error_not_found(self, mock_min_max_loc, mock_match_template, processor, sample_screenshot, error_templates):
        """エラー検出失敗のテスト"""
        # モックの設定（信頼度が閾値以下）
        mock_match_template.return_value = np.array([[0.5]])
        mock_min_max_loc.return_value = (0.1, 0.5, (10, 10), (20, 20))

        result = processor.detect_error(sample_screenshot, error_templates, threshold=0.8)

        assert result is None

    def test_detect_error_template_too_large(self, processor, sample_screenshot):
        """テンプレートが大きすぎる場合のテスト"""
        large_template = np.random.randint(0, 255, (400, 500), dtype=np.uint8)
        error_templates = {"large_error": large_template}

        result = processor.detect_error(sample_screenshot, error_templates)

        assert result is None

    @patch('src.utils.image_processing.cv2.matchTemplate')
    def test_detect_error_exception(self, mock_match_template, processor, sample_screenshot, error_templates):
        """エラー検出時の例外処理テスト"""
        mock_match_template.side_effect = Exception("Template matching failed")

        result = processor.detect_error(sample_screenshot, error_templates)

        assert result is None

    @patch('src.utils.image_processing.cv2.matchTemplate')
    @patch('src.utils.image_processing.cv2.minMaxLoc')
    def test_find_template_position_found(self, mock_min_max_loc, mock_match_template, processor, sample_screenshot, sample_template):
        """テンプレート位置検出成功のテスト"""
        # モックの設定
        mock_match_template.return_value = np.array([[0.8]])
        mock_min_max_loc.return_value = (0.1, 0.8, (10, 10), (20, 20))

        position = processor.find_template_position(sample_screenshot, sample_template, threshold=0.7)

        assert position is not None
        assert position == (45, 45)  # 20 + 50//2, 20 + 50//2

    @patch('src.utils.image_processing.cv2.matchTemplate')
    @patch('src.utils.image_processing.cv2.minMaxLoc')
    def test_find_template_position_not_found(self, mock_min_max_loc, mock_match_template, processor, sample_screenshot, sample_template):
        """テンプレート位置検出失敗のテスト"""
        # モックの設定（信頼度が閾値以下）
        mock_match_template.return_value = np.array([[0.5]])
        mock_min_max_loc.return_value = (0.1, 0.5, (10, 10), (20, 20))

        position = processor.find_template_position(sample_screenshot, sample_template, threshold=0.7)

        assert position is None

    def test_find_template_position_template_too_large(self, processor, sample_screenshot):
        """テンプレートが大きすぎる場合の位置検出テスト"""
        large_template = np.random.randint(0, 255, (400, 500), dtype=np.uint8)

        position = processor.find_template_position(sample_screenshot, large_template)

        assert position is None

    @patch('src.utils.image_processing.cv2.matchTemplate')
    def test_find_template_position_exception(self, mock_match_template, processor, sample_screenshot, sample_template):
        """テンプレート位置検出時の例外処理テスト"""
        mock_match_template.side_effect = Exception("Position detection failed")

        position = processor.find_template_position(sample_screenshot, sample_template)

        assert position is None

    @patch('src.utils.image_processing.cv2.imwrite')
    @patch('src.utils.image_processing.os.makedirs')
    def test_save_template_success(self, mock_makedirs, mock_imwrite, processor, sample_template):
        """テンプレート保存成功のテスト"""
        mock_imwrite.return_value = True

        success = processor.save_template(sample_template, "test/template.png")

        assert success is True
        mock_makedirs.assert_called_once()
        mock_imwrite.assert_called_once_with("test/template.png", sample_template)

    @patch('src.utils.image_processing.cv2.imwrite')
    def test_save_template_failure(self, mock_imwrite, processor, sample_template):
        """テンプレート保存失敗のテスト"""
        mock_imwrite.side_effect = Exception("Save failed")

        success = processor.save_template(sample_template, "test/template.png")

        assert success is False

    @patch('src.utils.image_processing.os.path.exists')
    @patch('src.utils.image_processing.os.listdir')
    @patch('src.utils.image_processing.cv2.imread')
    def test_load_templates_success(self, mock_imread, mock_listdir, mock_exists, processor):
        """テンプレート読み込み成功のテスト"""
        mock_exists.return_value = True
        mock_listdir.return_value = ["error1.png", "error2.jpg", "not_image.txt"]
        mock_imread.side_effect = [
            np.random.randint(0, 255, (50, 50), dtype=np.uint8),
            np.random.randint(0, 255, (60, 40), dtype=np.uint8),
            None
        ]

        templates = processor.load_templates("test_templates")

        assert len(templates) == 2
        assert "error1" in templates
        assert "error2" in templates
        assert "not_image" not in templates

    @patch('src.utils.image_processing.os.path.exists')
    @patch('src.utils.image_processing.os.makedirs')
    def test_load_templates_directory_not_exists(self, mock_makedirs, mock_exists, processor):
        """テンプレートディレクトリが存在しない場合のテスト"""
        mock_exists.return_value = False

        templates = processor.load_templates("nonexistent_dir")

        assert len(templates) == 0
        mock_makedirs.assert_called_once_with("nonexistent_dir")

    @patch('src.utils.image_processing.os.path.exists')
    @patch('src.utils.image_processing.os.listdir')
    def test_load_templates_exception(self, mock_listdir, mock_exists, processor):
        """テンプレート読み込み時の例外処理テスト"""
        mock_exists.return_value = True
        mock_listdir.side_effect = Exception("Directory read failed")

        templates = processor.load_templates("test_templates")

        assert len(templates) == 0

    @patch('src.utils.image_processing.logger')
    def test_logging_on_init(self, mock_logger):
        """初期化時のログ出力テスト"""
        ImageProcessor()

        mock_logger.info.assert_called_with("画像処理機能を初期化しました")

    @patch('src.utils.image_processing.logger')
    @patch('src.utils.image_processing.cv2.matchTemplate')
    @patch('src.utils.image_processing.cv2.minMaxLoc')
    def test_logging_on_error_detection(self, mock_min_max_loc, mock_match_template, mock_logger, processor, sample_screenshot, error_templates):
        """エラー検出時のログ出力テスト"""
        mock_match_template.return_value = np.array([[0.9]])
        mock_min_max_loc.return_value = (0.1, 0.9, (10, 10), (20, 20))

        processor.detect_error(sample_screenshot, error_templates, threshold=0.8)

        # ログが出力されることを確認
        mock_logger.debug.assert_called()
        mock_logger.info.assert_called()

    def test_detect_error_with_monitor_region(self, processor, sample_screenshot, error_templates):
        """監視領域指定でのエラー検出テスト"""
        monitor_region = (10, 10, 100, 100)

        with patch('src.utils.image_processing.cv2.matchTemplate') as mock_match, \
             patch('src.utils.image_processing.cv2.minMaxLoc') as mock_min_max_loc:

            mock_match.return_value = np.array([[0.5]])
            mock_min_max_loc.return_value = (0.1, 0.5, (10, 10), (20, 20))

            result = processor.detect_error(sample_screenshot, error_templates, monitor_region=monitor_region)

            assert result is None  # 閾値以下なので検出されない
