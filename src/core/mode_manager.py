"""
モード管理システム

このモジュールは、Kiro-IDEモード、AmazonQモード、自動モードの切り替えと管理を行います。
"""

import logging
from typing import Any
from typing import Optional

import numpy as np

from ..plugins.amazonq_detector import AmazonQDetector
from .base_detector import BaseDetector
from .detection_result import DetectionResult

logger = logging.getLogger(__name__)


class ModeManager:
    """モード管理クラス

    システムの動作モードを管理し、適切な検出器を選択・実行します。

    モード:
    - "kiro": Kiro-IDEエラー検出のみ
    - "amazonq": AmazonQ ▶RUNボタン検出のみ
    - "auto": 自動判定（両方を試行）
    """

    VALID_MODES = ["kiro", "amazonq", "auto"]

    def __init__(self, config_manager: Any) -> None:
        """モード管理システムを初期化

        Args:
            config_manager: 設定管理オブジェクト
        """
        self.config_manager = config_manager
        self.current_mode: str = str(config_manager.get("mode", "auto"))
        self.detectors: dict[str, BaseDetector] = {}

        logger.info(f"モード管理システムを初期化: 初期モード={self.current_mode}")
        self._setup_detectors()

    def _setup_detectors(self) -> None:
        """検出器を初期化・設定"""
        try:
            # AmazonQ検出器を初期化
            self.detectors["amazonq"] = AmazonQDetector(self.config_manager)
            logger.debug("AmazonQ検出器を初期化しました")

            # 将来的にKiro検出器もここで初期化
            # self.detectors["kiro"] = KiroDetector(self.config_manager)

        except Exception as e:
            logger.error(f"検出器初期化エラー: {e}", exc_info=True)

    def switch_mode(self, mode: str) -> bool:
        """モードを切り替え

        Args:
            mode: 切り替え先のモード ("kiro", "amazonq", "auto")

        Returns:
            bool: 切り替え成功/失敗
        """
        if mode not in self.VALID_MODES:
            logger.error(f"無効なモード: {mode}. 有効なモード: {self.VALID_MODES}")
            return False

        old_mode = self.current_mode
        self.current_mode = mode

        # 設定ファイルに保存
        self.config_manager.set("mode", mode)
        self.config_manager.save_config()

        logger.info(f"モード切り替え: {old_mode} -> {mode}")
        return True

    def get_current_mode(self) -> str:
        """現在のモードを取得

        Returns:
            str: 現在のモード
        """
        return self.current_mode

    def get_active_detectors(self) -> list[BaseDetector]:
        """アクティブな検出器のリストを取得

        Returns:
            List[BaseDetector]: アクティブな検出器のリスト
        """
        active_detectors = []

        if self.current_mode == "kiro":
            # Kiro検出器のみ
            if "kiro" in self.detectors and self.detectors["kiro"].is_enabled():
                active_detectors.append(self.detectors["kiro"])

        elif self.current_mode == "amazonq":
            # AmazonQ検出器のみ
            if "amazonq" in self.detectors and self.detectors["amazonq"].is_enabled():
                active_detectors.append(self.detectors["amazonq"])

        elif self.current_mode == "auto":
            # 有効な全ての検出器
            for _, detector in self.detectors.items():
                if detector.is_enabled():
                    active_detectors.append(detector)

        logger.debug(
            f"アクティブな検出器: {len(active_detectors)}個 (モード: {self.current_mode})"
        )
        return active_detectors

    def detect_and_execute(self, screenshot: np.ndarray) -> DetectionResult | None:
        """検出と実行を一括で行う

        Args:
            screenshot: 画面キャプチャ

        Returns:
            DetectionResult: 実行された検出結果、何も実行されなかった場合はNone
        """
        active_detectors = self.get_active_detectors()

        if not active_detectors:
            logger.debug("アクティブな検出器がありません")
            return None

        # 各検出器で状態検出を試行
        for detector in active_detectors:
            try:
                result = detector.detect_state(screenshot)

                if result and result.is_valid():
                    logger.info(f"状態検出成功: {detector.name} - {result.state_type}")

                    # 復旧アクションを実行
                    if detector.execute_recovery_action(result):
                        logger.info(f"復旧アクション実行成功: {detector.name}")
                        return result
                    else:
                        logger.warning(f"復旧アクション実行失敗: {detector.name}")

            except Exception as e:
                logger.error(f"検出器エラー: {detector.name} - {e}", exc_info=True)

        return None

    def auto_detect_mode(self, screenshot: np.ndarray) -> str:
        """スクリーンショットから最適なモードを自動判定

        Args:
            screenshot: 画面キャプチャ

        Returns:
            str: 推奨モード
        """
        # AmazonQ検出を試行
        if "amazonq" in self.detectors:
            amazonq_result = self.detectors["amazonq"].detect_state(screenshot)
            if amazonq_result and amazonq_result.is_valid():
                logger.debug("自動判定: AmazonQモードを推奨")
                return "amazonq"

        # Kiro-IDE検出を試行（将来実装）
        # if "kiro" in self.detectors:
        #     kiro_result = self.detectors["kiro"].detect_state(screenshot)
        #     if kiro_result and kiro_result.is_valid():
        #         logger.debug("自動判定: Kiroモードを推奨")
        #         return "kiro"

        # デフォルトはKiroモード
        logger.debug("自動判定: デフォルトでKiroモードを推奨")
        return "kiro"

    def get_detector(self, detector_name: str) -> BaseDetector | None:
        """指定された検出器を取得

        Args:
            detector_name: 検出器名

        Returns:
            BaseDetector: 検出器オブジェクト、存在しない場合はNone
        """
        return self.detectors.get(detector_name)

    def reload_detectors(self) -> None:
        """検出器を再読み込み"""
        logger.info("検出器を再読み込みします")
        self._setup_detectors()

    def get_mode_status(self) -> dict[str, Any]:
        """現在のモード状態を取得

        Returns:
            Dict: モード状態の詳細情報
        """
        active_detectors = self.get_active_detectors()

        return {
            "current_mode": self.current_mode,
            "valid_modes": self.VALID_MODES,
            "active_detectors": [d.name for d in active_detectors],
            "total_detectors": len(self.detectors),
            "enabled_detectors": {
                name: detector.is_enabled() for name, detector in self.detectors.items()
            },
        }
