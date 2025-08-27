#!/usr/bin/env python3
"""
AmazonQ統合テストスクリプト

新しく実装したAmazonQ検出機能の基本動作をテストします。
"""

import sys
import os
import logging
import numpy as np

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from src.config.config_manager import ConfigManager
from src.core.mode_manager import ModeManager
from src.core.detection_result import DetectionResult
from src.plugins.amazonq_detector import AmazonQDetector

# ログ設定
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def test_detection_result():
    """DetectionResultクラスのテスト"""
    logger.info("=== DetectionResult テスト開始 ===")

    # ▶RUNボタン検出結果の作成テスト
    result = DetectionResult.create_run_button_result(
        confidence=0.95, position=(100, 200), template_name="test_template"
    )

    assert result.state_type == "run_button"
    assert result.confidence == 0.95
    assert result.position == (100, 200)
    assert result.metadata["template_name"] == "test_template"
    assert result.is_valid()

    logger.info("✓ DetectionResult作成テスト成功")

    # エラー検出結果の作成テスト
    error_result = DetectionResult.create_error_result(
        confidence=0.85, error_type="compilation_error"
    )

    assert error_result.state_type == "error"
    assert error_result.metadata["error_type"] == "compilation_error"

    logger.info("✓ DetectionResultエラー結果テスト成功")


def test_amazonq_detector():
    """AmazonQDetectorクラスのテスト"""
    logger.info("=== AmazonQDetector テスト開始 ===")

    # 設定管理オブジェクトを作成
    config_manager = ConfigManager("kiro_config.json")

    # AmazonQ検出器を初期化
    detector = AmazonQDetector(config_manager)

    assert detector.name == "AmazonQDetector"
    assert detector.is_enabled()

    logger.info("✓ AmazonQDetector初期化テスト成功")

    # ダミー画像での検出テスト（テンプレートがないので検出されないはず）
    dummy_screenshot = np.zeros((600, 800, 3), dtype=np.uint8)
    result = detector.detect_state(dummy_screenshot)

    # テンプレートがないので検出されないはず
    assert result is None

    logger.info("✓ AmazonQDetector検出テスト成功（テンプレートなし）")


def test_mode_manager():
    """ModeManagerクラスのテスト"""
    logger.info("=== ModeManager テスト開始 ===")

    # 設定管理オブジェクトを作成
    config_manager = ConfigManager("kiro_config.json")

    # モード管理システムを初期化
    mode_manager = ModeManager(config_manager)

    # 初期モードの確認
    current_mode = mode_manager.get_current_mode()
    logger.info(f"現在のモード: {current_mode}")

    # モード切り替えテスト
    assert mode_manager.switch_mode("amazonq")
    assert mode_manager.get_current_mode() == "amazonq"

    assert mode_manager.switch_mode("auto")
    assert mode_manager.get_current_mode() == "auto"

    # 無効なモードのテスト
    assert not mode_manager.switch_mode("invalid_mode")

    logger.info("✓ ModeManagerモード切り替えテスト成功")

    # アクティブ検出器の取得テスト
    active_detectors = mode_manager.get_active_detectors()
    logger.info(f"アクティブな検出器数: {len(active_detectors)}")

    # モード状態の取得テスト
    status = mode_manager.get_mode_status()
    logger.info(f"モード状態: {status}")

    logger.info("✓ ModeManager機能テスト成功")


def test_integration():
    """統合テスト"""
    logger.info("=== 統合テスト開始 ===")

    # 設定管理オブジェクトを作成
    config_manager = ConfigManager("kiro_config.json")

    # モード管理システムを初期化
    mode_manager = ModeManager(config_manager)

    # AmazonQモードに切り替え
    mode_manager.switch_mode("amazonq")

    # ダミー画像で検出・実行テスト
    dummy_screenshot = np.zeros((600, 800, 3), dtype=np.uint8)
    result = mode_manager.detect_and_execute(dummy_screenshot)

    # テンプレートがないので何も検出されないはず
    assert result is None

    logger.info("✓ 統合テスト成功")


def test_kiro_recovery_integration():
    """統合テスト: KiroRecoveryとModeManagerの統合"""
    logger.info("=== KiroRecovery統合テスト開始 ===")

    # 設定管理オブジェクトを作成
    config_manager = ConfigManager("kiro_config.json")

    # KiroRecoveryを初期化（ModeManagerが統合されている）
    from src.core.kiro_recovery import KiroRecovery

    kiro_recovery = KiroRecovery(config_manager)

    # ModeManagerが統合されていることを確認
    assert hasattr(kiro_recovery, "mode_manager")
    assert kiro_recovery.mode_manager is not None

    # モード切り替えテスト
    assert kiro_recovery.mode_manager.switch_mode("amazonq")
    assert kiro_recovery.mode_manager.get_current_mode() == "amazonq"

    logger.info("✓ KiroRecovery統合テスト成功")


def main():
    """メイン関数"""
    logger.info("AmazonQ統合テストを開始します")

    try:
        test_detection_result()
        test_amazonq_detector()
        test_mode_manager()
        test_integration()
        test_kiro_recovery_integration()

        logger.info("🎉 全てのテストが成功しました！")

    except Exception as e:
        logger.error(f"❌ テスト失敗: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
