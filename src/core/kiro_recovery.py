"""
Kiro-IDE復旧機能
既存のKiroAutoRecoveryクラスから復旧機能を分離
"""

import logging
import os
import threading
import time
from typing import Optional

import numpy as np

from src.config.config_manager import ConfigManager
from src.core.detection_result import DetectionResult
from src.core.mode_manager import ModeManager
from src.plugins.amazonq_detector import AmazonQDetector
from src.utils.image_processing import ImageProcessor
from src.utils.screen_capture import ScreenCapture

# cv2ライブラリを条件付きでインポート
try:
    import cv2

    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
except Exception:
    CV2_AVAILABLE = False

logger = logging.getLogger(__name__)

# win32guiライブラリを条件付きでインポート（Windows環境でのフォーカス制御）
try:
    import win32con
    import win32gui

    WIN32GUI_AVAILABLE = True
except ImportError:
    WIN32GUI_AVAILABLE = False
except Exception:
    WIN32GUI_AVAILABLE = False

# pyperclipライブラリを条件付きでインポート（クリップボード入力用）
# 現在は使用していないため、コメントアウト
# try:
#     import pyperclip
#     PYPERCLIP_AVAILABLE = True
# except ImportError:
#     PYPERCLIP_AVAILABLE = False
# except Exception:
#     PYPERCLIP_AVAILABLE = False

# pyautoguiライブラリを条件付きでインポート（画面操作用）
try:
    import pyautogui

    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False
except Exception:
    PYAUTOGUI_AVAILABLE = False


class KiroRecovery:
    """Kiro-IDE復旧機能クラス（既存のKiroAutoRecoveryから分離）"""

    def __init__(self, config_manager: ConfigManager):
        """
        初期化
        Args:
            config_manager: 設定管理クラス
        """
        self.config_manager = config_manager
        self.screen_capture = ScreenCapture()
        self.image_processor = ImageProcessor()
        self.mode_manager = ModeManager(config_manager)

        self.monitoring = False
        self.error_templates: dict[str, np.ndarray] = {}
        self.last_error_time = 0
        self.recovery_attempts = 0
        self.max_recovery_attempts = self.config_manager.get("max_recovery_attempts", 3)

        # ライブラリ利用可能性をログ出力
        self._log_library_status()

        # エラーテンプレート画像を読み込み
        self.load_error_templates()

        logger.info("Kiro-IDE復旧機能を初期化しました")

    def _log_library_status(self) -> None:
        """ライブラリの利用可能性をログ出力"""
        # pyperclipは現在使用していないため、コメントアウト
        # if not PYPERCLIP_AVAILABLE:
        #     logger.warning("pyperclipが利用できません。クリップボード入力機能は無効です。")
        if not WIN32GUI_AVAILABLE:
            logger.warning("win32guiが利用できません。強制フォーカス機能は無効です。")
        if not PYAUTOGUI_AVAILABLE:
            logger.warning("pyautoguiが利用できません。画面操作機能は無効です。")
        if not self.screen_capture.is_available():
            logger.warning("画面キャプチャ機能が利用できません。")

    def load_error_templates(self) -> None:
        """エラー検出用のテンプレート画像を読み込み"""
        templates_dir = self.config_manager.get(
            "error_templates_dir", "error_templates"
        )
        self.error_templates = self.image_processor.load_templates(templates_dir)

    def reload_error_templates(self) -> None:
        """エラーテンプレートを再読み込み"""
        logger.info("エラーテンプレートを再読み込み中...")
        self.load_error_templates()
        logger.info(
            f"エラーテンプレート再読み込み完了: {len(self.error_templates)}個のテンプレート"
        )

    def detect_error(self, screenshot: np.ndarray) -> str | None:
        """
        エラーを検出
        Args:
            screenshot: スクリーンショット画像
        Returns:
            検出されたエラーの種類（なければNone）
        """
        threshold = self.config_manager.get("template_threshold", 0.8)
        monitor_region = self.config_manager.get("monitor_region")
        return self.image_processor.detect_error(
            screenshot, self.error_templates, threshold, monitor_region
        )

    def force_focus_kiro_window(self) -> bool:
        """
        Kiro-IDEウィンドウに強制フォーカス
        Returns:
            フォーカス成功フラグ
        """
        if not WIN32GUI_AVAILABLE or not PYAUTOGUI_AVAILABLE:
            return False

        try:
            # Kiro-IDEウィンドウを探す
            windows = pyautogui.getAllWindows()
            kiro_windows = [w for w in windows if "- kiro" in w.title.lower()]

            # Qt-Theme-StudioのKiroウィンドウを優先
            target_window = None
            for window in kiro_windows:
                if (
                    "qt-theme-studio" in window.title.lower()
                    or "qt-theme" in window.title.lower()
                ):
                    target_window = window
                    break

            if not target_window and kiro_windows:
                target_window = kiro_windows[0]

            if not target_window:
                logger.warning("Kiro-IDEウィンドウが見つかりません")
                return False

            # ウィンドウを前面に移動
            target_window.activate()
            time.sleep(0.5)

            # ウィンドウハンドルを取得して強制フォーカス
            hwnd = win32gui.FindWindow(None, target_window.title)
            if hwnd:
                # より確実なフォーカス処理
                try:
                    # ウィンドウを最前面に移動
                    win32gui.SetForegroundWindow(hwnd)
                    time.sleep(0.2)

                    # ウィンドウを復元（最小化されている場合）
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                    time.sleep(0.2)

                    # 再度フォーカスを設定
                    win32gui.SetForegroundWindow(hwnd)
                    time.sleep(0.2)

                    # フォーカスが成功したかチェック
                    foreground_hwnd = win32gui.GetForegroundWindow()
                    if foreground_hwnd == hwnd:
                        logger.info(
                            f"KiroIDEウィンドウに強制フォーカス成功: {target_window.title}"
                        )
                        return True
                    else:
                        logger.warning(
                            f"フォーカス設定に失敗: 期待={hwnd}, 実際={foreground_hwnd}"
                        )
                        return False

                except Exception as e:
                    logger.error(f"フォーカス処理中にエラー: {e}")
                    return False
            else:
                logger.warning(
                    f"ウィンドウハンドルが見つかりません: {target_window.title}"
                )
                return False

        except Exception as e:
            logger.error(f"強制フォーカスエラー: {e}")
            return False

    def send_recovery_command(self, error_type: str | None = None) -> bool:
        """
        復旧コマンドを送信（旧実装の動作を完全再現）
        Args:
            error_type: 検出されたエラーの種類
        Returns:
            送信成功フラグ
        """
        try:
            # チャット入力欄の位置を取得
            chat_position = self.config_manager.get("chat_input_position")
            if not chat_position:
                # チャット入力欄を自動検出を試行
                chat_position = self.find_chat_input()
                if not chat_position:
                    logger.error("チャット入力欄が見つかりません")
                    return False

            # 座標の妥当性をチェック
            logger.info(f"取得されたチャット入力欄座標: {chat_position}")
            if not isinstance(chat_position, list | tuple) or len(chat_position) != 2:
                logger.error(f"チャット入力欄座標の形式が不正: {chat_position}")
                return False

            x, y = chat_position[0], chat_position[1]
            if not isinstance(x, int | float) or not isinstance(y, int | float):
                logger.error(
                    f"チャット入力欄座標の値が不正: x={x} ({type(x)}), y={y} ({type(y)})"
                )
                return False

            if x < 0 or y < 0:
                logger.warning(f"チャット入力欄座標が負の値: ({x}, {y})")

            logger.info(f"チャット入力欄座標を検証完了: ({x}, {y})")

            # Kiro-IDEウィンドウを探す（フォーカスは行わない）
            if not PYAUTOGUI_AVAILABLE:
                logger.error("pyautoguiが利用できません。ウィンドウ検索ができません。")
                return False

            windows = pyautogui.getAllWindows()

            kiro_windows = [w for w in windows if "- kiro" in w.title.lower()]
            logger.debug(f"KiroIDE関連ウィンドウ数: {len(kiro_windows)}")

            target_hwnd = None
            # 旧実装と同じシンプルな検索: 最初のKiroウィンドウを使用
            if kiro_windows:
                target_hwnd = win32gui.FindWindow(None, kiro_windows[0].title)
                logger.info(
                    f"KiroIDEウィンドウを選択: {kiro_windows[0].title} -> hwnd: {target_hwnd}"
                )

            if not target_hwnd:
                logger.error("KiroIDEウィンドウが見つかりません")
                return False

            # チャット入力欄をクリック（フォーカスは行わない）
            pyautogui.click(chat_position[0], chat_position[1])
            time.sleep(1.0)

            # 復旧コマンドを選択
            recovery_commands = self.config_manager.get("recovery_commands", [])
            command = recovery_commands[0] if recovery_commands else "続行してください"

            # エラータイプに応じてコマンドを選択
            if error_type and error_type in self.config_manager.get(
                "custom_commands", {}
            ):
                command = self.config_manager.get("custom_commands", {})[error_type]

            # PostMessageを使用してテキストを送信

            for char in command:
                win32gui.PostMessage(target_hwnd, win32con.WM_CHAR, ord(char), 0)
                time.sleep(0.1)

            time.sleep(0.5)

            # Enterキーで送信（PostMessageを使用）
            win32gui.PostMessage(
                target_hwnd, win32con.WM_KEYDOWN, win32con.VK_RETURN, 0
            )
            win32gui.PostMessage(target_hwnd, win32con.WM_KEYUP, win32con.VK_RETURN, 0)

            logger.info(f"復旧コマンド送信: {command}")
            return True

        except Exception as e:
            logger.error(f"復旧コマンド送信エラー: {e}")
            return False

    def find_chat_input(self) -> tuple[int, int] | None:
        """チャット入力欄を自動検出（プレースホルダー実装）"""
        logger.warning("チャット入力欄の自動検出は未実装です")
        return None

    def should_attempt_recovery(self) -> bool:
        """復旧を試行すべきかチェック"""
        current_time = time.time()
        cooldown = self.config_manager.get("recovery_cooldown", 30)

        # クールダウン時間チェック
        if current_time - self.last_error_time < cooldown:
            return False

        # 最大試行回数チェック
        if self.recovery_attempts >= self.max_recovery_attempts:
            logger.warning("最大復旧試行回数に達しました")
            return False

        return True

    def monitor_loop(self) -> None:
        """メインの監視ループ"""
        logger.info("監視開始")
        monitor_interval = self.config_manager.get("monitor_interval", 2.0)

        while self.monitoring:
            try:
                # 監視エリアの設定を取得
                monitor_areas = self.config_manager.get("monitor_areas", [])
                monitor_region = self.config_manager.get("monitor_region")

                if monitor_areas:
                    # 監視エリアが設定されている場合、各エリアを監視
                    for area in monitor_areas:
                        if area.get("enabled", True):
                            area_name = area.get("name", "未命名")
                            x, y, width, height = (
                                area["x"],
                                area["y"],
                                area["width"],
                                area["height"],
                            )
                            region = (x, y, width, height)

                            logger.debug(f"監視エリア '{area_name}' を監視中: {region}")

                            # 画面をキャプチャ
                            screenshot = self.screen_capture.capture_screen(region)

                            # ModeManagerで検出・実行を試行（監視エリアのオフセットを考慮）
                            result = self._detect_and_execute_with_offset(
                                screenshot, (x, y)
                            )
                            if result:
                                logger.info(
                                    f"監視エリア '{area_name}' で状態検出・実行: {result.state_type}"
                                )
                                break  # 検出・実行されたら他のエリアはスキップ

                            # 従来のKiroエラー検出も並行実行
                            error_type = self.detect_error(screenshot)
                            if error_type:
                                logger.info(
                                    f"監視エリア '{area_name}' でエラー検出: {error_type}"
                                )
                                self._handle_error_detection(error_type)
                                break
                elif monitor_region:
                    # 従来のmonitor_regionが設定されている場合
                    logger.debug(f"従来の監視エリアを使用: {monitor_region}")
                    screenshot = self.screen_capture.capture_screen(monitor_region)

                    # ModeManagerで検出・実行を試行
                    result = self.mode_manager.detect_and_execute(screenshot)
                    if result:
                        logger.info(
                            f"従来の監視エリアで状態検出・実行: {result.state_type}"
                        )
                    else:
                        # 従来のKiroエラー検出も実行
                        error_type = self.detect_error(screenshot)
                        if error_type:
                            logger.info(f"従来の監視エリアでエラー検出: {error_type}")
                            self._handle_error_detection(error_type)
                else:
                    # 監視エリアが設定されていない場合、画面全体を監視
                    logger.debug(
                        "監視エリアが設定されていません。画面全体を監視します。"
                    )
                    screenshot = self.screen_capture.capture_screen()

                    # ModeManagerで検出・実行を試行
                    result = self.mode_manager.detect_and_execute(screenshot)
                    if result:
                        logger.info(f"画面全体で状態検出・実行: {result.state_type}")
                    else:
                        # 従来のKiroエラー検出も実行
                        error_type = self.detect_error(screenshot)
                        if error_type:
                            logger.info(f"画面全体でエラー検出: {error_type}")
                            self._handle_error_detection(error_type)

                time.sleep(monitor_interval)

            except KeyboardInterrupt:
                logger.info("監視を停止します")
                break
            except Exception as e:
                logger.error(f"監視ループエラー: {e}")
                time.sleep(5)  # エラー時は少し長く待機

        logger.info("監視終了")

    def _detect_and_execute_with_offset(
        self, screenshot: np.ndarray, region_offset: tuple[int, int]
    ) -> DetectionResult | None:
        """監視エリアのオフセットを考慮した検出・実行

        Args:
            screenshot: 画面キャプチャ
            region_offset: 監視エリアのオフセット (x, y)

        Returns:
            DetectionResult: 実行された検出結果、何も実行されなかった場合はNone
        """
        active_detectors = self.mode_manager.get_active_detectors()

        if not active_detectors:
            logger.debug("アクティブな検出器がありません")
            return None

        # 各検出器で状態検出を試行
        for detector in active_detectors:
            try:
                # AmazonQ検出器の場合はオフセットを考慮
                if isinstance(detector, AmazonQDetector):
                    result = detector.detect_state(screenshot, region_offset)
                else:
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

    def _handle_error_detection(self, error_type: str) -> None:
        """エラー検出時の処理"""
        current_time = time.time()

        # 復旧を試行すべきかチェック
        if self.should_attempt_recovery():
            logger.info(f"復旧を試行: {error_type}")

            if self.send_recovery_command(error_type):
                self.last_error_time = int(current_time)
                self.recovery_attempts += 1
                logger.info(
                    f"復旧試行回数: "
                    f"{self.recovery_attempts}/{self.max_recovery_attempts}"
                )
            else:
                logger.error("復旧コマンドの送信に失敗")
        else:
            logger.info("復旧をスキップ（クールダウン中または最大試行回数到達）")

    def start_monitoring(self) -> threading.Thread | None:
        """監視開始（モードに応じたテンプレートチェック）"""
        if self.monitoring:
            logger.warning("既に監視中です")
            return None

        # 現在のモードに応じてテンプレートの存在をチェック
        current_mode = self.mode_manager.get_current_mode()
        active_detectors = self.mode_manager.get_active_detectors()

        if current_mode == "amazonq":
            # AmazonQモードの場合はAmazonQ検出器のテンプレートをチェック
            amazonq_detector = self.mode_manager.get_detector("amazonq")
            if not amazonq_detector or len(amazonq_detector.run_button_templates) == 0:
                logger.warning("AmazonQテンプレートが読み込まれていません")
                # AmazonQモードでもテンプレートがない場合は監視を続行（テンプレートなしでも動作する）
        elif current_mode == "kiro":
            # Kiroモードの場合はKiroエラーテンプレートをチェック
            if not self.error_templates:
                logger.warning("Kiroエラーテンプレートが読み込まれていません")
                return None
        else:
            # 自動モードの場合はいずれかの検出器が有効であればOK
            if not active_detectors:
                logger.warning("有効な検出器がありません")
                return None

        try:
            self.monitoring = True
            self.recovery_attempts = 0

            # 別スレッドで監視開始
            monitor_thread = threading.Thread(
                target=self.monitor_loop, name="KiroRecovery-Monitor"
            )
            monitor_thread.daemon = True
            monitor_thread.start()

            logger.info(f"監視を開始しました（モード: {current_mode}）")
            return monitor_thread

        except Exception as e:
            logger.error(f"監視開始エラー: {e}")
            self.monitoring = False
            return None

    def stop_monitoring(self) -> None:
        """監視停止"""
        if not self.monitoring:
            logger.warning("監視は開始されていません")
            return

        self.monitoring = False
        logger.info("監視を停止しました")

    def save_error_template(
        self, template_name: str, region: tuple[int, int, int, int] | None = None
    ) -> bool:
        """
        現在の画面からテンプレートを保存（モードに応じたディレクトリを使用）
        Args:
            template_name: テンプレート名
            region: キャプチャする領域（Noneの場合は設定ファイルのmonitor_regionを使用）
        Returns:
            保存成功フラグ
        """
        try:
            # regionが指定されていない場合は設定ファイルのmonitor_areasを使用
            if region is None:
                monitor_areas = self.config_manager.get("monitor_areas", [])
                if monitor_areas and monitor_areas[0].get("enabled", True):
                    area = monitor_areas[0]
                    region = (area["x"], area["y"], area["width"], area["height"])
                    logger.info(f"設定ファイルの監視エリアを使用: {region}")
                else:
                    logger.warning(
                        "監視エリアが設定されていません。画面全体をキャプチャします。"
                    )

            screenshot = self.screen_capture.capture_screen(region)

            # 現在のモードに応じてテンプレート保存先を決定
            current_mode = self.mode_manager.get_current_mode()
            if current_mode == "amazonq":
                # AmazonQモードの場合はamazonq_templatesディレクトリを使用
                templates_dir = self.config_manager.get(
                    "amazonq.run_button_templates_dir", "amazonq_templates"
                )
                # AmazonQ検出器にテンプレートを追加
                amazonq_detector = self.mode_manager.get_detector("amazonq")
                if amazonq_detector:
                    success = amazonq_detector.add_template(template_name, screenshot)
                    if success:
                        logger.info(f"AmazonQテンプレート保存成功: {template_name}")
                    return success
                else:
                    logger.error("AmazonQ検出器が見つかりません")
                    return False
            else:
                # Kiroモードまたは自動モードの場合はerror_templatesディレクトリを使用
                templates_dir = self.config_manager.get(
                    "error_templates_dir", "error_templates"
                )
                template_path = os.path.join(templates_dir, f"{template_name}.png")

                if self.image_processor.save_template(screenshot, template_path):
                    # テンプレートを再読み込み
                    self.reload_error_templates()
                    logger.info(f"Kiroテンプレート保存成功: {template_name}")
                    return True
                else:
                    return False

        except Exception as e:
            logger.error(f"テンプレート保存エラー: {e}")
            return False

    def delete_error_template(self, template_name: str) -> bool:
        """
        テンプレートを削除（モードに応じたディレクトリから）
        Args:
            template_name: 削除するテンプレート名
        Returns:
            削除成功フラグ
        """
        try:
            # 現在のモードに応じてテンプレート削除先を決定
            current_mode = self.mode_manager.get_current_mode()
            if current_mode == "amazonq":
                # AmazonQモードの場合はamazonq_templatesディレクトリから削除
                templates_dir = self.config_manager.get(
                    "amazonq.run_button_templates_dir", "amazonq_templates"
                )
                template_path = os.path.join(templates_dir, f"{template_name}.png")

                if os.path.exists(template_path):
                    os.remove(template_path)
                    logger.info(f"AmazonQテンプレート削除: {template_path}")

                    # AmazonQ検出器のテンプレートを再読み込み
                    amazonq_detector = self.mode_manager.get_detector("amazonq")
                    if amazonq_detector:
                        amazonq_detector._load_run_button_templates()
                    return True
                else:
                    logger.warning(
                        f"AmazonQテンプレートファイルが存在しません: {template_path}"
                    )
                    return False
            else:
                # Kiroモードまたは自動モードの場合はerror_templatesディレクトリから削除
                templates_dir = self.config_manager.get(
                    "error_templates_dir", "error_templates"
                )
                template_path = os.path.join(templates_dir, f"{template_name}.png")

                if os.path.exists(template_path):
                    os.remove(template_path)
                    logger.info(f"Kiroテンプレート削除: {template_path}")

                    # テンプレートを再読み込み
                    self.reload_error_templates()
                    return True
                else:
                    logger.warning(
                        f"Kiroテンプレートファイルが存在しません: {template_path}"
                    )
                    return False

        except Exception as e:
            logger.error(f"テンプレート削除エラー: {e}")
            return False

    def get_status(self) -> dict[str, any]:
        """現在の状態を取得"""
        current_mode = self.mode_manager.get_current_mode()

        # 現在のモードに応じたテンプレート数を取得
        template_count = 0
        if current_mode == "amazonq":
            amazonq_detector = self.mode_manager.get_detector("amazonq")
            if amazonq_detector and hasattr(amazonq_detector, "run_button_templates"):
                template_count = len(amazonq_detector.run_button_templates)
        elif current_mode == "kiro":
            template_count = len(self.error_templates)
        else:  # autoモード
            # 全てのテンプレート数を合計
            template_count = len(self.error_templates)
            amazonq_detector = self.mode_manager.get_detector("amazonq")
            if amazonq_detector and hasattr(amazonq_detector, "run_button_templates"):
                template_count += len(amazonq_detector.run_button_templates)

        logger.debug(
            f"ステータス取得: モード={current_mode}, テンプレート数={template_count}"
        )

        return {
            "monitoring": self.monitoring,
            "recovery_attempts": self.recovery_attempts,
            "max_recovery_attempts": self.max_recovery_attempts,
            "template_count": template_count,
            "last_error_time": self.last_error_time,
            "current_mode": current_mode,
        }
