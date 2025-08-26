"""
Kiro-IDE復旧機能
既存のKiroAutoRecoveryクラスから復旧機能を分離
"""

import logging
import os
import threading
import time
from typing import Dict, Optional, Tuple

import numpy as np

from src.config.config_manager import ConfigManager
from src.utils.screen_capture import ScreenCapture
from src.utils.image_processing import ImageProcessor

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
try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False
except Exception:
    PYPERCLIP_AVAILABLE = False

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
        
        self.monitoring = False
        self.error_templates: Dict[str, np.ndarray] = {}
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
        if not PYPERCLIP_AVAILABLE:
            logger.warning("pyperclipが利用できません。クリップボード入力機能は無効です。")
        if not WIN32GUI_AVAILABLE:
            logger.warning("win32guiが利用できません。強制フォーカス機能は無効です。")
        if not PYAUTOGUI_AVAILABLE:
            logger.warning("pyautoguiが利用できません。画面操作機能は無効です。")
        if not self.screen_capture.is_available():
            logger.warning("画面キャプチャ機能が利用できません。")
    
    def load_error_templates(self) -> None:
        """エラー検出用のテンプレート画像を読み込み"""
        templates_dir = self.config_manager.get("error_templates_dir", "error_templates")
        self.error_templates = self.image_processor.load_templates(templates_dir)
    
    def detect_error(self, screenshot: np.ndarray) -> Optional[str]:
        """
        エラーを検出
        Args:
            screenshot: スクリーンショット画像
        Returns:
            検出されたエラーの種類（なければNone）
        """
        threshold = self.config_manager.get("template_threshold", 0.8)
        return self.image_processor.detect_error(screenshot, self.error_templates, threshold)
    
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
            kiro_windows = [w for w in windows if "kiro" in w.title.lower()]

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
                        logger.info(f"KiroIDEウィンドウに強制フォーカス成功: {target_window.title}")
                        return True
                    else:
                        logger.warning(f"フォーカス設定に失敗: 期待={hwnd}, 実際={foreground_hwnd}")
                        return False
                        
                except Exception as e:
                    logger.error(f"フォーカス処理中にエラー: {e}")
                    return False
            else:
                logger.warning(f"ウィンドウハンドルが見つかりません: {target_window.title}")
                return False

        except Exception as e:
            logger.error(f"強制フォーカスエラー: {e}")
            return False
    
    def send_recovery_command(self, error_type: Optional[str] = None) -> bool:
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
            if not isinstance(chat_position, (list, tuple)) or len(chat_position) != 2:
                logger.error(f"チャット入力欄座標の形式が不正: {chat_position}")
                return False
            
            x, y = chat_position[0], chat_position[1]
            if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
                logger.error(f"チャット入力欄座標の値が不正: x={x} ({type(x)}), y={y} ({type(y)})")
                return False
            
            if x < 0 or y < 0:
                logger.warning(f"チャット入力欄座標が負の値: ({x}, {y})")
            
            logger.info(f"チャット入力欄座標を検証完了: ({x}, {y})")

            # 旧実装と同じ方法でKiroIDEウィンドウを探す（フォーカスは行わない）
            if not PYAUTOGUI_AVAILABLE:
                logger.error("pyautoguiが利用できません。ウィンドウ検索ができません。")
                return False
            
            windows = pyautogui.getAllWindows()
            kiro_windows = [w for w in windows if "kiro" in w.title.lower()]

            target_hwnd = None
            for window in kiro_windows:
                if (
                    "qt-theme-studio" in window.title.lower()
                    or "qt-theme" in window.title.lower()
                ):
                    target_hwnd = win32gui.FindWindow(None, window.title)
                    logger.info(f"Qt-Theme-Studioウィンドウを選択: {window.title}")
                    break

            if not target_hwnd and kiro_windows:
                target_hwnd = win32gui.FindWindow(None, kiro_windows[0].title)
                logger.info(f"最初のKiroIDEウィンドウを選択: {kiro_windows[0].title}")

            if not target_hwnd:
                logger.error("KiroIDEウィンドウが見つかりません")
                return False

            # KiroIDEウィンドウに強制フォーカス（クリック前に必ず実行）
            logger.info("KiroIDEウィンドウに強制フォーカスを実行")
            if not self.force_focus_kiro_window():
                logger.error("KiroIDEウィンドウのフォーカスに失敗しました")
                return False
            
            # フォーカス後の待機時間を増加
            time.sleep(1.0)
            logger.info("フォーカス完了、チャット入力欄をクリックします")
            
            # チャット入力欄をクリック
            logger.info(f"チャット入力欄をクリック: 座標({chat_position[0]}, {chat_position[1]})")
            
            # クリック前のマウス位置を記録
            current_pos = pyautogui.position()
            logger.info(f"クリック前のマウス位置: ({current_pos.x}, {current_pos.y})")
            
            # クリック実行
            pyautogui.click(chat_position[0], chat_position[1])
            logger.info("クリック実行完了")
            
            # クリック後のマウス位置を確認
            after_pos = pyautogui.position()
            logger.info(f"クリック後のマウス位置: ({after_pos.x}, {after_pos.y})")
            
            # クリックが正しく実行されたかチェック
            if after_pos.x == chat_position[0] and after_pos.y == chat_position[1]:
                logger.info("クリック位置が正しく設定されました")
            else:
                logger.warning(f"クリック位置が期待値と異なります: 期待({chat_position[0]}, {chat_position[1]}), 実際({after_pos.x}, {after_pos.y})")
                
                # 代替手段1：win32guiを使用してクリック
                logger.info("代替手段1でクリックを試行: win32gui.SendMessage")
                try:
                    # マウス左ボタンダウン
                    win32gui.SendMessage(target_hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, 
                                       win32gui.MAKELONG(chat_position[0], chat_position[1]))
                    time.sleep(0.1)
                    # マウス左ボタンアップ
                    win32gui.SendMessage(target_hwnd, win32con.WM_LBUTTONUP, 0, 
                                       win32gui.MAKELONG(chat_position[0], chat_position[1]))
                    logger.info("win32guiによるクリック完了")
                except Exception as e:
                    logger.error(f"win32guiによるクリック失敗: {e}")
                    
                    # 代替手段2：PostMessageを使用してクリック
                    logger.info("代替手段2でクリックを試行: win32gui.PostMessage")
                    try:
                        # マウス左ボタンダウン
                        win32gui.PostMessage(target_hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, 
                                           win32gui.MAKELONG(chat_position[0], chat_position[1]))
                        time.sleep(0.1)
                        # マウス左ボタンアップ
                        win32gui.PostMessage(target_hwnd, win32con.WM_LBUTTONUP, 0, 
                                           win32gui.MAKELONG(chat_position[0], chat_position[1]))
                        logger.info("win32gui.PostMessageによるクリック完了")
                    except Exception as e2:
                        logger.error(f"win32gui.PostMessageによるクリックも失敗: {e2}")
            
            time.sleep(1.0)

            # 復旧コマンドを選択
            recovery_commands = self.config_manager.get("recovery_commands", [])
            command = recovery_commands[0] if recovery_commands else "続行してください"

            # エラータイプに応じてコマンドを選択
            custom_commands = self.config_manager.get("custom_commands", {})
            if error_type and error_type in custom_commands:
                command = custom_commands[error_type]

            # PostMessageを使用してテキストを送信（旧実装と同じ）
            for char in command:
                win32gui.PostMessage(target_hwnd, win32con.WM_CHAR, ord(char), 0)
                time.sleep(0.1)

            time.sleep(0.5)

            # Enterキーで送信（PostMessageを使用）
            win32gui.PostMessage(target_hwnd, win32con.WM_KEYDOWN, win32con.VK_RETURN, 0)
            win32gui.PostMessage(target_hwnd, win32con.WM_KEYUP, win32con.VK_RETURN, 0)

            logger.info(f"復旧コマンド送信: {command}")
            return True

        except Exception as e:
            logger.error(f"復旧コマンド送信エラー: {e}")
            return False
    
    def find_kiro_window(self):
        """KiroIDEウィンドウを探す"""
        try:
            import win32gui
            
            # デバッグ用：全てのウィンドウタイトルをログ出力
            def debug_windows_callback(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if title:  # 空でないタイトルのみ
                        windows.append((hwnd, title))
                return True

            all_windows = []
            win32gui.EnumWindows(debug_windows_callback, all_windows)
            
            # デバッグ情報をログ出力
            logger.debug(f"検出されたウィンドウ数: {len(all_windows)}")
            for hwnd, title in all_windows[:10]:  # 最初の10個をログ出力
                logger.debug(f"ウィンドウ: {title} (hwnd: {hwnd})")
            
            # KiroIDEウィンドウを検索
            kiro_windows = []
            def enum_windows_callback(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    # KiroIDE関連の検索条件
                    if (title and (
                        "kiro" in title.lower() or 
                        "qt-theme" in title.lower() or
                        "qt-theme-studio" in title.lower()
                    )):
                        windows.append((hwnd, title))
                return True

            win32gui.EnumWindows(enum_windows_callback, kiro_windows)
            
            if kiro_windows:
                # 見つかったウィンドウの詳細をログ出力
                for hwnd, title in kiro_windows:
                    logger.info(f"KiroIDEウィンドウを発見: '{title}' (hwnd: {hwnd})")
                
                # Qt-Theme-StudioのKiroIDEウィンドウを優先
                for hwnd, title in kiro_windows:
                    if "qt-theme-studio" in title.lower():
                        logger.info(f"Qt-Theme-Studioウィンドウを選択: '{title}'")
                        return hwnd
                
                # 最初に見つかったウィンドウを返す
                return kiro_windows[0][0]
            
            logger.warning("KiroIDEウィンドウが見つかりません")
            return None
            
        except ImportError:
            logger.warning("win32guiが利用できません")
            return None
        except Exception as e:
            logger.error(f"ウィンドウ検索エラー: {e}")
            return None
    
    def find_chat_input(self) -> Optional[Tuple[int, int]]:
        """
        チャット入力欄を自動検出
        Returns:
            チャット入力欄の座標 (x, y)
        """
        try:
            # チャット入力欄のテンプレートがある場合
            templates_dir = self.config_manager.get("error_templates_dir", "error_templates")
            chat_template_path = os.path.join(templates_dir, "chat_input.png")

            if os.path.exists(chat_template_path):
                screenshot = self.screen_capture.capture_screen()
                chat_template = cv2.imread(chat_template_path, cv2.IMREAD_GRAYSCALE)

                return self.image_processor.find_template_position(screenshot, chat_template, 0.7)

            logger.warning("チャット入力欄の自動検出に失敗")
            return None

        except Exception as e:
            logger.error(f"チャット入力欄検出エラー: {e}")
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
        monitor_region = self.config_manager.get("monitor_region")
        monitor_interval = self.config_manager.get("monitor_interval", 2.0)

        while self.monitoring:
            try:
                # 画面をキャプチャ
                screenshot = self.screen_capture.capture_screen(monitor_region)

                # エラーを検出
                error_type = self.detect_error(screenshot)

                if error_type:
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
                        logger.info(
                            "復旧をスキップ（クールダウン中または最大試行回数到達）"
                        )

                time.sleep(monitor_interval)

            except KeyboardInterrupt:
                logger.info("監視を停止します")
                break
            except Exception as e:
                logger.error(f"監視ループエラー: {e}")
                time.sleep(5)  # エラー時は少し長く待機

        logger.info("監視終了")
    
    def start_monitoring(self) -> Optional[threading.Thread]:
        """監視開始"""
        if self.monitoring:
            logger.warning("既に監視中です")
            return None

        if not self.error_templates:
            logger.warning("エラーテンプレートが読み込まれていません")
            return None

        self.monitoring = True
        self.recovery_attempts = 0

        # 別スレッドで監視開始
        monitor_thread = threading.Thread(target=self.monitor_loop)
        monitor_thread.daemon = True
        monitor_thread.start()

        return monitor_thread
    
    def stop_monitoring(self) -> None:
        """監視停止"""
        self.monitoring = False
        logger.info("監視停止要求")
    
    def save_error_template(
        self, 
        template_name: str, 
        region: Optional[Tuple[int, int, int, int]] = None
    ) -> bool:
        """
        現在の画面からエラーテンプレートを保存
        Args:
            template_name: テンプレート名
            region: キャプチャする領域（Noneの場合は設定ファイルのmonitor_regionを使用）
        Returns:
            保存成功フラグ
        """
        try:
            # regionが指定されていない場合は設定ファイルのmonitor_regionを使用
            if region is None:
                region = self.config_manager.get("monitor_region")
                if region:
                    logger.info(f"設定ファイルの監視エリアを使用: {region}")
                else:
                    logger.warning(
                        "監視エリアが設定されていません。画面全体をキャプチャします。"
                    )

            screenshot = self.screen_capture.capture_screen(region)

            templates_dir = self.config_manager.get("error_templates_dir", "error_templates")
            template_path = os.path.join(templates_dir, f"{template_name}.png")

            if self.image_processor.save_template(screenshot, template_path):
                # テンプレートを再読み込み
                self.error_templates[template_name] = screenshot
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"テンプレート保存エラー: {e}")
            return False
    
    def get_status(self) -> Dict[str, any]:
        """現在の状態を取得"""
        return {
            "monitoring": self.monitoring,
            "recovery_attempts": self.recovery_attempts,
            "max_recovery_attempts": self.max_recovery_attempts,
            "template_count": len(self.error_templates),
            "last_error_time": self.last_error_time,
        }
