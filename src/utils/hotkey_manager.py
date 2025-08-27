"""
ホットキー管理機能
既存のKiroAutoRecoveryクラスからホットキー管理機能を分離
"""

import logging
from typing import Callable

logger = logging.getLogger(__name__)

# keyboardライブラリを条件付きでインポート
try:
    import keyboard

    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False
except Exception:
    KEYBOARD_AVAILABLE = False


class HotkeyManager:
    """ホットキー管理クラス"""

    def __init__(self):
        """初期化"""
        if not KEYBOARD_AVAILABLE:
            logger.warning(
                "keyboardライブラリが利用できません。ホットキー機能は無効です。"
            )
        else:
            logger.info("ホットキー管理機能を初期化しました")

    def setup_hotkeys(self, hotkey_handlers: dict[str, Callable]) -> bool:
        """
        ホットキーを設定
        Args:
            hotkey_handlers: ホットキーとハンドラーの辞書
        Returns:
            設定成功フラグ
        """
        if not KEYBOARD_AVAILABLE:
            logger.warning(
                "keyboardライブラリが利用できません。ホットキー機能は無効です。"
            )
            return False

        try:
            # 既存のホットキーをクリア
            keyboard.unhook_all()

            # ホットキーを設定
            for hotkey, handler in hotkey_handlers.items():
                keyboard.add_hotkey(hotkey, handler, suppress=True)
                logger.info(f"ホットキー設定: {hotkey}")

            logger.info("✅ ホットキー設定完了")
            return True

        except Exception as e:
            logger.error(f"ホットキー設定エラー: {e}")
            logger.error("ホットキー機能は無効です")
            return False

    def clear_hotkeys(self) -> None:
        """全てのホットキーをクリア"""
        if KEYBOARD_AVAILABLE:
            try:
                keyboard.unhook_all()
                logger.info("全てのホットキーをクリアしました")
            except Exception as e:
                logger.error(f"ホットキークリアエラー: {e}")

    def is_available(self) -> bool:
        """ホットキー機能が利用可能かチェック"""
        return KEYBOARD_AVAILABLE

    def get_default_hotkeys(self) -> dict[str, str]:
        """デフォルトのホットキー一覧を取得"""
        return {
            "ctrl+alt+s": "テンプレート保存",
            "ctrl+alt+r": "復旧コマンド送信",
            "ctrl+alt+p": "一時停止/再開",
            "ctrl+alt+q": "監視停止",
        }
