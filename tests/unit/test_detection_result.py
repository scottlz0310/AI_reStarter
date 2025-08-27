"""
DetectionResultクラスの単体テスト

検出結果データクラスの機能をテストします。
"""

import pytest
import time
from unittest.mock import patch

from src.core.detection_result import DetectionResult


class TestDetectionResult:
    """DetectionResultクラスのテストクラス"""
    
    def test_init_with_all_parameters(self):
        """全パラメータ指定での初期化テスト"""
        timestamp = time.time()
        metadata = {"template_name": "test_template.png"}
        
        result = DetectionResult(
            state_type="compilation_error",
            confidence=0.95,
            position=(100, 200),
            timestamp=timestamp,
            metadata=metadata
        )
        
        assert result.state_type == "compilation_error"
        assert result.confidence == 0.95
        assert result.position == (100, 200)
        assert result.timestamp == timestamp
        assert result.metadata == metadata
    
    def test_init_with_minimal_parameters(self):
        """最小パラメータでの初期化テスト"""
        result = DetectionResult(
            state_type="runtime_error",
            confidence=0.8,
            position=(50, 100),
            timestamp=0,
            metadata={}
        )
        
        assert result.state_type == "runtime_error"
        assert result.confidence == 0.8
        assert result.position == (50, 100)
        assert result.timestamp > 0  # __post_init__で設定される
        assert result.metadata == {}
    
    def test_post_init_timestamp_generation(self):
        """__post_init__でのタイムスタンプ自動生成テスト"""
        result = DetectionResult(
            state_type="test_error",
            confidence=0.9,
            position=(0, 0),
            timestamp=0,  # 0を指定すると自動生成される
            metadata={}
        )
        
        # タイムスタンプが自動生成されることを確認
        assert result.timestamp > 0
        assert isinstance(result.timestamp, float)
    
    def test_create_run_button_result(self):
        """▶RUNボタン検出結果の作成テスト"""
        result = DetectionResult.create_run_button_result(
            confidence=0.95,
            position=(100, 200),
            template_name="run_button.png"
        )
        
        assert result.state_type == "run_button"
        assert result.confidence == 0.95
        assert result.position == (100, 200)
        assert result.timestamp > 0
        assert result.metadata["template_name"] == "run_button.png"
    
    def test_create_run_button_result_default_template(self):
        """デフォルトテンプレート名でのRUNボタン結果作成テスト"""
        result = DetectionResult.create_run_button_result(
            confidence=0.8,
            position=(50, 100)
        )
        
        assert result.state_type == "run_button"
        assert result.confidence == 0.8
        assert result.position == (50, 100)
        assert result.metadata["template_name"] == "unknown"
    
    def test_create_error_result_with_position(self):
        """位置情報付きエラー検出結果の作成テスト"""
        result = DetectionResult.create_error_result(
            confidence=0.9,
            error_type="compilation_error",
            position=(150, 250)
        )
        
        assert result.state_type == "error"
        assert result.confidence == 0.9
        assert result.position == (150, 250)
        assert result.metadata["error_type"] == "compilation_error"
    
    def test_create_error_result_without_position(self):
        """位置情報なしエラー検出結果の作成テスト"""
        result = DetectionResult.create_error_result(
            confidence=0.85,
            error_type="runtime_error"
        )
        
        assert result.state_type == "error"
        assert result.confidence == 0.85
        assert result.position is None
        assert result.metadata["error_type"] == "runtime_error"
    
    def test_is_valid_with_valid_result(self):
        """有効な検出結果の検証テスト"""
        result = DetectionResult(
            state_type="test_error",
            confidence=0.8,
            position=(0, 0),
            timestamp=time.time(),
            metadata={}
        )
        
        assert result.is_valid() is True
    
    def test_is_valid_with_zero_confidence(self):
        """信頼度0の検出結果の検証テスト"""
        result = DetectionResult(
            state_type="test_error",
            confidence=0.0,
            position=(0, 0),
            timestamp=time.time(),
            metadata={}
        )
        
        assert result.is_valid() is False
    
    def test_is_valid_with_empty_state_type(self):
        """空の状態タイプの検出結果の検証テスト"""
        result = DetectionResult(
            state_type="",
            confidence=0.8,
            position=(0, 0),
            timestamp=time.time(),
            metadata={}
        )
        
        assert result.is_valid() is False
    
    def test_is_valid_with_none_state_type(self):
        """None状態タイプの検出結果の検証テスト"""
        result = DetectionResult(
            state_type=None,
            confidence=0.8,
            position=(0, 0),
            timestamp=time.time(),
            metadata={}
        )
        
        assert result.is_valid() is False
    
    def test_get_age_seconds(self):
        """経過時間取得のテスト"""
        past_timestamp = time.time() - 5.0  # 5秒前
        result = DetectionResult(
            state_type="test_error",
            confidence=0.8,
            position=(0, 0),
            timestamp=past_timestamp,
            metadata={}
        )
        
        age = result.get_age_seconds()
        
        # 約5秒経過していることを確認（多少の誤差を許容）
        assert 4.5 <= age <= 5.5
    
    def test_get_age_seconds_recent(self):
        """最近の検出結果の経過時間テスト"""
        result = DetectionResult(
            state_type="test_error",
            confidence=0.8,
            position=(0, 0),
            timestamp=time.time(),
            metadata={}
        )
        
        age = result.get_age_seconds()
        
        # 非常に短い時間であることを確認
        assert age < 1.0
    
    def test_dataclass_equality(self):
        """データクラスの等価性テスト"""
        timestamp = time.time()
        metadata = {"test": "value"}
        
        result1 = DetectionResult(
            state_type="test_error",
            confidence=0.8,
            position=(100, 200),
            timestamp=timestamp,
            metadata=metadata
        )
        
        result2 = DetectionResult(
            state_type="test_error",
            confidence=0.8,
            position=(100, 200),
            timestamp=timestamp,
            metadata=metadata
        )
        
        assert result1 == result2
    
    def test_dataclass_inequality(self):
        """データクラスの非等価性テスト"""
        timestamp = time.time()
        
        result1 = DetectionResult(
            state_type="test_error",
            confidence=0.8,
            position=(100, 200),
            timestamp=timestamp,
            metadata={}
        )
        
        result2 = DetectionResult(
            state_type="different_error",
            confidence=0.8,
            position=(100, 200),
            timestamp=timestamp,
            metadata={}
        )
        
        assert result1 != result2
    
    def test_str_representation(self):
        """文字列表現のテスト"""
        result = DetectionResult(
            state_type="compilation_error",
            confidence=0.95,
            position=(100, 200),
            timestamp=time.time(),
            metadata={"template_name": "error_template.png"}
        )
        
        str_repr = str(result)
        
        assert "compilation_error" in str_repr
        assert "0.95" in str_repr
        assert "(100, 200)" in str_repr
    
    def test_repr_representation(self):
        """repr表現のテスト"""
        result = DetectionResult(
            state_type="runtime_error",
            confidence=0.8,
            position=(50, 100),
            timestamp=time.time(),
            metadata={}
        )
        
        repr_str = repr(result)
        
        assert "DetectionResult" in repr_str
        assert "runtime_error" in repr_str
        assert "0.8" in repr_str
        assert "(50, 100)" in repr_str
    
    @patch('src.core.detection_result.logger')
    def test_logging_on_creation(self, mock_logger):
        """検出結果作成時のログ出力テスト"""
        result = DetectionResult(
            state_type="test_error",
            confidence=0.8,
            position=(0, 0),
            timestamp=time.time(),
            metadata={}
        )
        
        # デバッグログが出力されることを確認
        mock_logger.debug.assert_called_once()
        call_args = mock_logger.debug.call_args[0][0]
        assert "検出結果作成" in call_args
        assert "test_error" in call_args
    
    def test_metadata_modification(self):
        """メタデータの変更テスト"""
        result = DetectionResult(
            state_type="test_error",
            confidence=0.8,
            position=(0, 0),
            timestamp=time.time(),
            metadata={"initial": "value"}
        )
        
        # メタデータを変更
        result.metadata["new_key"] = "new_value"
        result.metadata["initial"] = "modified_value"
        
        assert result.metadata["new_key"] == "new_value"
        assert result.metadata["initial"] == "modified_value"
    
    def test_position_none_handling(self):
        """位置情報がNoneの場合の処理テスト"""
        result = DetectionResult(
            state_type="test_error",
            confidence=0.8,
            position=None,
            timestamp=time.time(),
            metadata={}
        )
        
        assert result.position is None
        assert result.is_valid() is True  # 位置がNoneでも有効
    
    def test_confidence_edge_cases(self):
        """信頼度の境界値テスト"""
        # 信頼度が非常に小さい値
        result1 = DetectionResult(
            state_type="test_error",
            confidence=0.001,
            position=(0, 0),
            timestamp=time.time(),
            metadata={}
        )
        assert result1.is_valid() is True
        
        # 信頼度が1.0
        result2 = DetectionResult(
            state_type="test_error",
            confidence=1.0,
            position=(0, 0),
            timestamp=time.time(),
            metadata={}
        )
        assert result2.is_valid() is True