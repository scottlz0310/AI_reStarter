"""
検出結果を格納するデータクラス

このモジュールは、検出器の結果を統一的に管理するためのデータクラスを提供します。
"""

import logging
import time
from dataclasses import dataclass
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class DetectionResult:
    """検出結果を格納するデータクラス

    検出器が状態を検出した際の結果を統一的に管理します。
    """

    state_type: str  # 検出された状態のタイプ（例: "run_button", "error", "completion"）
    confidence: float  # 検出の信頼度（0.0-1.0）
    position: tuple[int, int] | None  # 検出された位置の座標（x, y）
    timestamp: float  # 検出時刻のタイムスタンプ
    metadata: dict[str, Any]  # 追加のメタデータ

    def __post_init__(self) -> None:
        """初期化後の処理"""
        if self.timestamp == 0:
            self.timestamp = time.time()

        logger.debug(
            f"検出結果作成: {self.state_type} "
            f"(信頼度: {self.confidence:.3f}, 位置: {self.position})"
        )

    @classmethod
    def create_run_button_result(
        cls,
        confidence: float,
        position: tuple[int, int],
        template_name: str = "unknown",
    ) -> "DetectionResult":
        """▶RUNボタン検出結果を作成

        Args:
            confidence: 検出の信頼度
            position: ボタンの位置
            template_name: 使用されたテンプレート名

        Returns:
            DetectionResult: 作成された検出結果
        """
        return cls(
            state_type="run_button",
            confidence=confidence,
            position=position,
            timestamp=time.time(),
            metadata={"template_name": template_name},
        )

    @classmethod
    def create_error_result(
        cls,
        confidence: float,
        error_type: str,
        position: tuple[int, int] | None = None,
    ) -> "DetectionResult":
        """エラー検出結果を作成

        Args:
            confidence: 検出の信頼度
            error_type: エラーのタイプ
            position: エラーの位置（オプション）

        Returns:
            DetectionResult: 作成された検出結果
        """
        return cls(
            state_type="error",
            confidence=confidence,
            position=position,
            timestamp=time.time(),
            metadata={"error_type": error_type},
        )

    def is_valid(self) -> bool:
        """検出結果が有効かどうかを確認

        Returns:
            bool: 有効な場合True
        """
        return (
            self.confidence > 0.0
            and self.state_type is not None
            and len(self.state_type) > 0
        )

    def get_age_seconds(self) -> float:
        """検出結果の経過時間を秒で取得

        Returns:
            float: 検出からの経過時間（秒）
        """
        return time.time() - self.timestamp

    def to_dict(self) -> dict[str, Any]:
        """検出結果を辞書形式に変換

        Returns:
            dict: 検出結果の辞書表現
        """
        return {
            "state_type": self.state_type,
            "confidence": self.confidence,
            "position": self.position,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DetectionResult":
        """辞書から検出結果を復元

        Args:
            data: 検出結果の辞書データ

        Returns:
            DetectionResult: 復元された検出結果
        """
        return cls(
            state_type=data["state_type"],
            confidence=data["confidence"],
            position=data.get("position"),
            timestamp=data["timestamp"],
            metadata=data.get("metadata", {}),
        )
