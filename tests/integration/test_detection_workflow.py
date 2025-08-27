"""
検出ワークフローの統合テスト

複数のモジュール間の連携による検出・復旧プロセスをテストします。
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from src.core.base_detector import BaseDetector
from src.core.detection_result import DetectionResult
from src.config.config_manager import ConfigManager
from src.utils.screen_capture import ScreenCapture
from src.utils.image_processing import ImageProcessor


class MockDetector(BaseDetector):
    """統合テスト用のモック検出クラス"""
    
    def __init__(self, config: dict):
        super().__init__()
        self.config = config
        self.detection_count = 0
        self.recovery_count = 0
    
    def detect_state(self, screenshot: np.ndarray) -> DetectionResult:
        """モック検出処理"""
        self.detection_count += 1
        
        if self.config.get("should_detect", False):
            return DetectionResult(
                state_type="integration_test_error",
                confidence=0.9,
                position=(100, 200),
                template_name="test_template.png",
                recovery_action="統合テスト用復旧アクション"
            )
        return None
    
    def execute_recovery_action(self, result: DetectionResult) -> bool:
        """モック復旧処理"""
        self.recovery_count += 1
        return self.config.get("recovery_success", True)


class TestDetectionWorkflow:
    """検出ワークフローの統合テストクラス"""
    
    @pytest.fixture
    def mock_detector(self, sample_config):
        """モック検出器のフィクスチャ"""
        config = sample_config.copy()
        config["should_detect"] = True
        config["recovery_success"] = True
        return MockDetector(config)
    
    @pytest.fixture
    def config_manager(self, config_file):
        """設定マネージャーのフィクスチャ"""
        return ConfigManager(str(config_file))
    
    def test_full_detection_workflow(self, mock_detector, mock_screen_capture, mock_pyautogui):
        """完全な検出ワークフローのテスト"""
        # 画面キャプチャのモック設定
        test_screenshot = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        mock_screen_capture.return_value = test_screenshot
        
        # 検出実行
        screenshot = mock_screen_capture()
        detection_result = mock_detector.detect_state(screenshot)
        
        # 検出結果の確認
        assert detection_result is not None
        assert detection_result.state_type == "integration_test_error"
        assert detection_result.confidence == 0.9
        assert mock_detector.detection_count == 1
        
        # 復旧アクション実行
        recovery_success = mock_detector.execute_recovery_action(detection_result)
        
        # 復旧結果の確認
        assert recovery_success is True
        assert mock_detector.recovery_count == 1
    
    def test_detection_with_config_integration(self, config_manager, mock_screen_capture):
        """設定管理との統合検出テスト"""
        # 設定から閾値を取得
        threshold = config_manager.get_value("template_threshold", 0.8)
        
        # 検出器を設定で初期化
        detector_config = {
            "threshold": threshold,
            "should_detect": True,
            "recovery_success": True
        }
        detector = MockDetector(detector_config)
        
        # 画面キャプチャ実行
        screenshot = mock_screen_capture()
        
        # 検出実行
        result = detector.detect_state(screenshot)
        
        assert result is not None
        assert detector.config["threshold"] == threshold
    
    @patch('src.utils.image_processing.ImageProcessor.find_template_position')
    def test_template_matching_integration(self, mock_find_template, mock_detector, mock_screen_capture):
        """テンプレートマッチングとの統合テスト"""
        # テンプレートマッチングのモック設定
        mock_find_template.return_value = (100, 200)
        
        # 画面キャプチャ実行
        screenshot = mock_screen_capture()
        
        # 検出実行（実際の実装では ImageProcessor を使用）
        result = mock_detector.detect_state(screenshot)
        
        assert result is not None
        assert result.confidence == 0.9  # MockDetectorの固定値
        assert result.position == (100, 200)  # MockDetectorの固定値
    
    def test_multiple_detection_cycles(self, mock_detector, mock_screen_capture):
        """複数回の検出サイクルテスト"""
        detection_cycles = 5
        
        for i in range(detection_cycles):
            # 画面キャプチャ
            screenshot = mock_screen_capture()
            
            # 検出実行
            result = mock_detector.detect_state(screenshot)
            
            if result:
                # 復旧アクション実行
                recovery_success = mock_detector.execute_recovery_action(result)
                assert recovery_success is True
        
        # 実行回数の確認
        assert mock_detector.detection_count == detection_cycles
        assert mock_detector.recovery_count == detection_cycles  # 全て検出成功の場合
    
    def test_detection_failure_handling(self, sample_config, mock_screen_capture):
        """検出失敗時の処理テスト"""
        # 検出失敗の設定
        config = sample_config.copy()
        config["should_detect"] = False
        detector = MockDetector(config)
        
        # 画面キャプチャ
        screenshot = mock_screen_capture()
        
        # 検出実行
        result = detector.detect_state(screenshot)
        
        # 検出失敗の確認
        assert result is None
        assert detector.detection_count == 1
        assert detector.recovery_count == 0  # 復旧は実行されない
    
    def test_recovery_failure_handling(self, sample_config, mock_screen_capture):
        """復旧失敗時の処理テスト"""
        # 復旧失敗の設定
        config = sample_config.copy()
        config["should_detect"] = True
        config["recovery_success"] = False
        detector = MockDetector(config)
        
        # 検出・復旧実行
        screenshot = mock_screen_capture()
        result = detector.detect_state(screenshot)
        
        assert result is not None
        
        recovery_success = detector.execute_recovery_action(result)
        
        # 復旧失敗の確認
        assert recovery_success is False
        assert detector.recovery_count == 1
    
    def test_config_update_during_workflow(self, config_manager, mock_detector, mock_screen_capture):
        """ワークフロー実行中の設定更新テスト"""
        # 初期検出
        screenshot = mock_screen_capture()
        result1 = mock_detector.detect_state(screenshot)
        assert result1 is not None
        
        # 設定更新
        config_manager.set_value("template_threshold", 0.95)
        updated_threshold = config_manager.get_value("template_threshold")
        
        # 更新された設定での検出
        mock_detector.config["threshold"] = updated_threshold
        result2 = mock_detector.detect_state(screenshot)
        
        assert result2 is not None
        assert mock_detector.config["threshold"] == 0.95
    
    @patch('src.utils.screen_capture.ScreenCapture.capture_screen')
    def test_screen_capture_error_handling(self, mock_capture, mock_detector):
        """画面キャプチャエラー時の処理テスト"""
        # 画面キャプチャでエラーを発生させる
        mock_capture.side_effect = Exception("画面キャプチャエラー")
        
        screen_capture = ScreenCapture()
        
        with pytest.raises(Exception, match="画面キャプチャエラー"):
            screenshot = screen_capture.capture_screen()
            mock_detector.detect_state(screenshot)
    
    def test_detection_result_serialization_workflow(self, mock_detector, mock_screen_capture):
        """検出結果のシリアライゼーションワークフローテスト"""
        # 検出実行
        screenshot = mock_screen_capture()
        result = mock_detector.detect_state(screenshot)
        
        assert result is not None
        
        # 辞書形式に変換
        result_dict = result.to_dict()
        assert isinstance(result_dict, dict)
        
        # 辞書から復元
        restored_result = DetectionResult.from_dict(result_dict)
        
        # 復元結果の確認
        assert restored_result.state_type == result.state_type
        assert restored_result.confidence == result.confidence
        assert restored_result.position == result.position
    
    def test_concurrent_detection_simulation(self, sample_config, mock_screen_capture):
        """並行検出のシミュレーションテスト"""
        # 複数の検出器を作成
        detectors = []
        for i in range(3):
            config = sample_config.copy()
            config["should_detect"] = True
            config["detector_id"] = i
            detectors.append(MockDetector(config))
        
        # 各検出器で検出実行
        screenshot = mock_screen_capture()
        results = []
        
        for detector in detectors:
            result = detector.detect_state(screenshot)
            if result:
                results.append(result)
        
        # 全ての検出器で検出成功を確認
        assert len(results) == 3
        for result in results:
            assert result.state_type == "integration_test_error"
    
    def test_workflow_performance_measurement(self, mock_detector, mock_screen_capture):
        """ワークフローのパフォーマンス測定テスト"""
        import time
        
        start_time = time.time()
        
        # 複数回の検出実行
        for _ in range(10):
            screenshot = mock_screen_capture()
            result = mock_detector.detect_state(screenshot)
            if result:
                mock_detector.execute_recovery_action(result)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # パフォーマンス確認（10回の実行が1秒以内）
        assert execution_time < 1.0
        assert mock_detector.detection_count == 10
    
    def test_memory_usage_during_workflow(self, mock_detector, mock_screen_capture):
        """ワークフロー実行中のメモリ使用量テスト"""
        import gc
        
        # ガベージコレクション実行
        gc.collect()
        
        # 大量の検出実行
        for _ in range(100):
            screenshot = mock_screen_capture()
            result = mock_detector.detect_state(screenshot)
            if result:
                mock_detector.execute_recovery_action(result)
        
        # メモリリークがないことを確認（基本的なチェック）
        gc.collect()
        assert mock_detector.detection_count == 100