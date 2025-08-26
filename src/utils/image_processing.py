"""
画像処理機能
既存のKiroAutoRecoveryクラスから画像処理機能を分離
"""

import logging
import os
from typing import Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class ImageProcessor:
    """画像処理機能クラス"""

    def __init__(self):
        """初期化"""
        logger.info("画像処理機能を初期化しました")

    def detect_error(
        self,
        screenshot: np.ndarray,
        error_templates: dict[str, np.ndarray],
        threshold: float = 0.8,
        monitor_region: Optional[tuple[int, int, int, int]] = None
    ) -> Optional[str]:
        """
        エラーを検出
        Args:
            screenshot: スクリーンショット画像
            error_templates: エラーテンプレート辞書
            threshold: テンプレートマッチングの閾値
        Returns:
            検出されたエラーの種類（なければNone）
        """
        try:
            # スクリーンショットと監視エリアのサイズをログ出力
            logger.debug(f"スクリーンショットサイズ: {screenshot.shape} (H x W)")
            if monitor_region:
                logger.debug(f"監視エリア: {monitor_region} (x, y, width, height)")
            else:
                logger.debug("監視エリア: 全画面")
            
            for error_name, template in error_templates.items():
                # テンプレートのサイズをログ出力
                logger.debug(f"テンプレート '{error_name}' サイズ: {template.shape} (H x W)")
                
                # サイズ比較を詳細にログ出力
                screenshot_h, screenshot_w = screenshot.shape[:2]
                template_h, template_w = template.shape[:2]
                
                logger.debug(f"サイズ比較 '{error_name}': "
                           f"スクリーンショット({screenshot_h}x{screenshot_w}) vs "
                           f"テンプレート({template_h}x{template_w})")
                
                # サイズチェック: テンプレートがスクリーンショットより大きい場合はスキップ
                if template_h > screenshot_h or template_w > screenshot_w:
                    logger.warning(f"テンプレート '{error_name}' がスクリーンショットより大きいためスキップ "
                                 f"(テンプレート: {template_h}x{template_w}, "
                                 f"スクリーンショット: {screenshot_h}x{screenshot_w})")
                    continue

                # テンプレートマッチング
                logger.debug(f"テンプレートマッチング実行: '{error_name}'")
                result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                logger.debug(f"マッチング結果 '{error_name}': 信頼度={max_val:.3f}, 闾値={threshold}")

                if max_val >= threshold:
                    logger.info(f"エラー検出: {error_name} (信頼度: {max_val:.3f})")
                    return error_name

            return None

        except Exception as e:
            logger.error(f"エラー検出エラー: {e}")
            return None

    def find_template_position(
        self,
        screenshot: np.ndarray,
        template: np.ndarray,
        threshold: float = 0.7
    ) -> Optional[tuple[int, int]]:
        """
        テンプレートの位置を検出
        Args:
            screenshot: スクリーンショット画像
            template: 検索するテンプレート
            threshold: マッチング閾値
        Returns:
            テンプレートの中心座標 (x, y) または None
        """
        try:
            # サイズチェック
            if (template.shape[0] > screenshot.shape[0] or 
                template.shape[1] > screenshot.shape[1]):
                logger.debug("テンプレートがスクリーンショットより大きいためスキップ")
                return None

            result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            if max_val >= threshold and template is not None:
                # テンプレートの中心座標を返す
                h, w = template.shape
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2
                return (center_x, center_y)

            return None

        except Exception as e:
            logger.error(f"テンプレート位置検出エラー: {e}")
            return None

    def save_template(
        self,
        image: np.ndarray,
        template_path: str
    ) -> bool:
        """
        テンプレート画像を保存
        Args:
            image: 保存する画像
            template_path: 保存先パス
        Returns:
            保存成功フラグ
        """
        try:
            # ディレクトリが存在しない場合は作成
            os.makedirs(os.path.dirname(template_path), exist_ok=True)

            # 画像を保存
            cv2.imwrite(template_path, image)
            logger.info(f"テンプレート保存: {template_path}")
            return True

        except Exception as e:
            logger.error(f"テンプレート保存エラー: {e}")
            return False

    def load_templates(self, templates_dir: str) -> dict[str, np.ndarray]:
        """
        テンプレート画像を読み込み
        Args:
            templates_dir: テンプレートディレクトリ
        Returns:
            テンプレート辞書
        """
        templates = {}

        try:
            if not os.path.exists(templates_dir):
                os.makedirs(templates_dir)
                logger.info(f"テンプレートディレクトリを作成: {templates_dir}")
                return templates

            for filename in os.listdir(templates_dir):
                if filename.lower().endswith((".png", ".jpg", ".jpeg")):
                    template_path = os.path.join(templates_dir, filename)
                    try:
                        template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
                        if template is not None:
                            template_name = os.path.splitext(filename)[0]
                            templates[template_name] = template
                            logger.info(f"テンプレート読み込み: {template_name}")
                    except Exception as e:
                        logger.error(f"テンプレート読み込みエラー {filename}: {e}")

            return templates

        except Exception as e:
            logger.error(f"テンプレート読み込みエラー: {e}")
            return templates
