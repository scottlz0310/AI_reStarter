"""
検出器の基底クラス

このモジュールは、様々な状態検出器の基底クラスを提供します。
"""

from abc import ABC, abstractmethod
from typing import Optional
import numpy as np
import logging

logger = logging.getLogger(__name__)


class BaseDetector(ABC):
    """検出器の基底クラス
    
    すべての検出器はこのクラスを継承し、
    detect_stateとexecute_recovery_actionメソッドを実装する必要があります。
    """
    
    def __init__(self) -> None:
        """基底検出器を初期化"""
        self.name = self.__class__.__name__
        logger.debug(f"{self.name}検出器を初期化しました")
    
    @abstractmethod
    def detect_state(self, screenshot: np.ndarray) -> Optional['DetectionResult']:
        """状態を検出する抽象メソッド
        
        Args:
            screenshot: 画面キャプチャのnumpy配列
            
        Returns:
            DetectionResult: 検出結果、検出されなかった場合はNone
        """
        pass
    
    @abstractmethod
    def execute_recovery_action(self, result: 'DetectionResult') -> bool:
        """復旧アクションを実行する抽象メソッド
        
        Args:
            result: 検出結果
            
        Returns:
            bool: 復旧アクションの成功/失敗
        """
        pass
    
    def is_enabled(self) -> bool:
        """検出器が有効かどうかを確認
        
        Returns:
            bool: 有効な場合True
        """
        return True