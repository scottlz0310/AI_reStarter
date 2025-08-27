"""
AmazonQ用検出器

このモジュールは、VSCode拡張のAmazonQの▶RUNボタンを検出・クリックする機能を提供します。
"""

import os
import time
from typing import Optional, Dict
import numpy as np
import cv2
import pyautogui
import logging

from ..core.base_detector import BaseDetector
from ..core.detection_result import DetectionResult

logger = logging.getLogger(__name__)


class AmazonQDetector(BaseDetector):
    """AmazonQ用の▶RUNボタン検出・クリック機能
    
    VSCode拡張のAmazonQで表示される▶RUNボタンを自動検出し、
    クリックして実行を開始する機能を提供します。
    """
    
    def __init__(self, config_manager) -> None:
        """AmazonQ検出器を初期化
        
        Args:
            config_manager: 設定管理オブジェクト
        """
        super().__init__()
        self.config_manager = config_manager
        self.run_button_templates: Dict[str, np.ndarray] = {}
        self.detection_threshold = config_manager.get("amazonq.detection_threshold", 0.8)
        self.click_delay = config_manager.get("amazonq.click_delay", 1.0)
        self.templates_dir = config_manager.get("amazonq.run_button_templates_dir", "amazonq_templates")
        
        logger.info(f"AmazonQ検出器を初期化: 閾値={self.detection_threshold}")
        self._load_run_button_templates()
    
    def _load_run_button_templates(self) -> None:
        """▶RUNボタンのテンプレート画像を読み込み"""
        if not os.path.exists(self.templates_dir):
            logger.warning(f"テンプレートディレクトリが存在しません: {self.templates_dir}")
            os.makedirs(self.templates_dir, exist_ok=True)
            return
        
        template_files = [f for f in os.listdir(self.templates_dir) if f.endswith(('.png', '.jpg', '.jpeg'))]
        
        for template_file in template_files:
            template_path = os.path.join(self.templates_dir, template_file)
            try:
                template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
                if template is not None:
                    template_name = os.path.splitext(template_file)[0]
                    self.run_button_templates[template_name] = template
                    logger.debug(f"テンプレート読み込み成功: {template_name}")
                else:
                    logger.warning(f"テンプレート読み込み失敗: {template_path}")
            except Exception as e:
                logger.error(f"テンプレート読み込みエラー: {template_path} - {e}")
        
        logger.info(f"▶RUNボタンテンプレート読み込み完了: {len(self.run_button_templates)}個")
    
    def detect_state(self, screenshot: np.ndarray) -> Optional[DetectionResult]:
        """▶RUNボタンを検出
        
        Args:
            screenshot: 画面キャプチャのnumpy配列
            
        Returns:
            DetectionResult: 検出結果、検出されなかった場合はNone
        """
        if len(self.run_button_templates) == 0:
            logger.debug("▶RUNボタンテンプレートが読み込まれていません")
            return None
        
        # グレースケール変換
        if len(screenshot.shape) == 3:
            gray_screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        else:
            gray_screenshot = screenshot
        
        best_match = None
        best_confidence = 0.0
        best_position = None
        best_template_name = ""
        
        # 各テンプレートでマッチング実行
        for template_name, template in self.run_button_templates.items():
            try:
                result = cv2.matchTemplate(gray_screenshot, template, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                if max_val > best_confidence:
                    best_confidence = max_val
                    best_match = result
                    best_template_name = template_name
                    
                    # テンプレートの中心座標を計算
                    h, w = template.shape
                    center_x = max_loc[0] + w // 2
                    center_y = max_loc[1] + h // 2
                    best_position = (center_x, center_y)
                
                logger.debug(f"テンプレートマッチング: {template_name} - 信頼度: {max_val:.3f}")
                
            except Exception as e:
                logger.error(f"テンプレートマッチングエラー: {template_name} - {e}")
        
        # 閾値を超えた場合のみ検出結果を返す
        if best_confidence >= self.detection_threshold and best_position:
            logger.info(
                f"▶RUNボタン検出成功: {best_template_name} "
                f"(信頼度: {best_confidence:.3f}, 位置: {best_position})"
            )
            return DetectionResult.create_run_button_result(
                confidence=best_confidence,
                position=best_position,
                template_name=best_template_name
            )
        
        logger.debug(f"▶RUNボタン検出失敗: 最高信頼度 {best_confidence:.3f} < 閾値 {self.detection_threshold}")
        return None
    
    def execute_recovery_action(self, result: DetectionResult) -> bool:
        """▶RUNボタンをクリック
        
        Args:
            result: 検出結果
            
        Returns:
            bool: クリック成功/失敗
        """
        if result.state_type != "run_button" or not result.position:
            logger.error(f"無効な検出結果: {result.state_type}")
            return False
        
        try:
            x, y = result.position
            template_name = result.metadata.get("template_name", "unknown")
            
            logger.info(f"▶RUNボタンをクリック: 座標({x}, {y}), テンプレート: {template_name}")
            
            # クリック実行
            pyautogui.click(x, y)
            
            # 設定された遅延時間を待機
            if self.click_delay > 0:
                time.sleep(self.click_delay)
            
            logger.info("▶RUNボタンクリック完了")
            return True
            
        except Exception as e:
            logger.error(f"▶RUNボタンクリックエラー: {e}", exc_info=True)
            return False
    
    def is_enabled(self) -> bool:
        """AmazonQ検出器が有効かどうかを確認
        
        Returns:
            bool: 有効な場合True
        """
        return self.config_manager.get("amazonq.enabled", True)
    
    def add_template(self, template_name: str, template_image: np.ndarray) -> bool:
        """新しい▶RUNボタンテンプレートを追加
        
        Args:
            template_name: テンプレート名
            template_image: テンプレート画像
            
        Returns:
            bool: 追加成功/失敗
        """
        try:
            # グレースケール変換
            if len(template_image.shape) == 3:
                gray_template = cv2.cvtColor(template_image, cv2.COLOR_BGR2GRAY)
            else:
                gray_template = template_image
            
            # メモリに追加
            self.run_button_templates[template_name] = gray_template
            
            # ファイルに保存
            template_path = os.path.join(self.templates_dir, f"{template_name}.png")
            os.makedirs(self.templates_dir, exist_ok=True)
            cv2.imwrite(template_path, gray_template)
            
            logger.info(f"▶RUNボタンテンプレート追加: {template_name}")
            return True
            
        except Exception as e:
            logger.error(f"テンプレート追加エラー: {template_name} - {e}")
            return False