"""
画面キャプチャ機能
既存のKiroAutoRecoveryクラスから画面キャプチャ機能を分離
"""

import logging
from typing import Optional, cast

import numpy as np

logger = logging.getLogger(__name__)

# pyautoguiは条件付きでインポート（WSL環境での問題回避）
try:
    import pyautogui

    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False
except Exception:
    PYAUTOGUI_AVAILABLE = False


class ScreenCapture:
    """画面キャプチャ機能クラス"""

    def __init__(self):
        """初期化"""
        if not PYAUTOGUI_AVAILABLE:
            logger.warning("pyautoguiが利用できません。画面キャプチャ機能は無効です。")
        else:
            logger.info("画面キャプチャ機能を初期化しました")

    def capture_screen(
        self, region: tuple[int, int, int, int] | None = None
    ) -> np.ndarray:
        """
        画面をキャプチャ
        Args:
            region: キャプチャする領域 (x, y, width, height)
        Returns:
            キャプチャした画像（グレースケール）
        """
        if not PYAUTOGUI_AVAILABLE:
            raise RuntimeError(
                "pyautoguiが利用できません。画面キャプチャ機能は無効です。"
            )

        try:
            if region:
                screenshot = pyautogui.screenshot(region=region)
                logger.debug(f"指定領域をキャプチャ: {region}")
            else:
                screenshot = pyautogui.screenshot()
                logger.debug("画面全体をキャプチャ")

            # OpenCV形式に変換（グレースケール）
            screenshot_np = np.array(screenshot)
            screenshot_gray = self._convert_to_grayscale(screenshot_np)

            return cast(np.ndarray, screenshot_gray)

        except Exception as e:
            logger.error(f"画面キャプチャエラー: {e}")
            raise

    def _convert_to_grayscale(self, image: np.ndarray) -> np.ndarray:
        """画像をグレースケールに変換"""
        try:
            # RGBからグレースケールに変換
            if len(image.shape) == 3:
                import cv2

                return cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            else:
                return image
        except ImportError:
            logger.warning("OpenCVが利用できません。グレースケール変換をスキップします")
            return image
        except Exception as e:
            logger.error(f"グレースケール変換エラー: {e}")
            return image

    def is_available(self) -> bool:
        """画面キャプチャ機能が利用可能かチェック"""
        return PYAUTOGUI_AVAILABLE

    def get_screen_size(self) -> tuple[int, int] | None:
        """画面サイズを取得"""
        if not PYAUTOGUI_AVAILABLE:
            return None

        try:
            width, height = pyautogui.size()
            return (width, height)
        except Exception as e:
            logger.error(f"画面サイズ取得エラー: {e}")
            return None
