#!/usr/bin/env python3
"""
サンプルテンプレート画像作成スクリプト

AmazonQ用の▶RUNボタンテンプレートのサンプル画像を作成します。
"""

import os
import numpy as np
import cv2
import logging

# ログ設定
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def create_run_button_template(width=100, height=30, text="▶ RUN"):
    """▶RUNボタンのサンプルテンプレートを作成

    Args:
        width: ボタンの幅
        height: ボタンの高さ
        text: ボタンのテキスト

    Returns:
        np.ndarray: 作成された画像
    """
    # 背景色（薄いグレー）
    img = np.full((height, width, 3), (240, 240, 240), dtype=np.uint8)

    # ボタンの枠線
    cv2.rectangle(img, (2, 2), (width - 3, height - 3), (100, 100, 100), 1)

    # テキストを描画
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.5
    color = (50, 50, 50)  # 濃いグレー
    thickness = 1

    # テキストサイズを取得
    text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]

    # テキストを中央に配置
    text_x = (width - text_size[0]) // 2
    text_y = (height + text_size[1]) // 2

    cv2.putText(img, text, (text_x, text_y), font, font_scale, color, thickness)

    return img


def create_running_indicator_template(width=80, height=20):
    """実行中インジケーターのサンプルテンプレートを作成

    Args:
        width: インジケーターの幅
        height: インジケーターの高さ

    Returns:
        np.ndarray: 作成された画像
    """
    # 背景色（薄い青）
    img = np.full((height, width, 3), (255, 240, 200), dtype=np.uint8)

    # プログレスバー風の表示
    cv2.rectangle(img, (5, 5), (width - 6, height - 6), (200, 200, 100), -1)
    cv2.rectangle(img, (5, 5), (width // 2, height - 6), (100, 150, 255), -1)

    return img


def create_completed_indicator_template(width=80, height=20):
    """完了インジケーターのサンプルテンプレートを作成

    Args:
        width: インジケーターの幅
        height: インジケーターの高さ

    Returns:
        np.ndarray: 作成された画像
    """
    # 背景色（薄い緑）
    img = np.full((height, width, 3), (240, 255, 240), dtype=np.uint8)

    # チェックマーク風の表示
    cv2.rectangle(img, (2, 2), (width - 3, height - 3), (100, 200, 100), 1)

    # 簡単なチェックマーク
    cv2.line(img, (10, height // 2), (width // 2 - 5, height - 8), (50, 150, 50), 2)
    cv2.line(img, (width // 2 - 5, height - 8), (width - 10, 5), (50, 150, 50), 2)

    return img


def create_sample_templates():
    """サンプルテンプレート画像を作成・保存"""
    templates_dir = "amazonq_templates"

    # ディレクトリを作成
    os.makedirs(templates_dir, exist_ok=True)
    logger.info(f"テンプレートディレクトリを作成: {templates_dir}")

    # 各種テンプレートを作成
    templates = [
        ("run_button.png", create_run_button_template()),
        ("run_button_large.png", create_run_button_template(120, 35, "▶ RUN")),
        ("run_button_small.png", create_run_button_template(80, 25, "▶RUN")),
        ("running_indicator.png", create_running_indicator_template()),
        ("completed_indicator.png", create_completed_indicator_template()),
    ]

    created_count = 0
    for filename, img in templates:
        try:
            filepath = os.path.join(templates_dir, filename)

            # BGRからRGBに変換（OpenCVはBGR形式）
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

            # 画像を保存
            cv2.imwrite(filepath, img_rgb)

            logger.info(f"テンプレート作成: {filepath}")
            created_count += 1

        except Exception as e:
            logger.error(f"テンプレート作成エラー ({filename}): {e}")

    logger.info(f"サンプルテンプレート作成完了: {created_count}個")
    return created_count


def main():
    """メイン関数"""
    logger.info("AmazonQ用サンプルテンプレート作成を開始します")

    try:
        created_count = create_sample_templates()

        if created_count > 0:
            logger.info("🎉 サンプルテンプレートの作成が完了しました！")
            logger.info("テンプレート管理GUIで確認できます。")
        else:
            logger.warning("⚠️ テンプレートが作成されませんでした")

    except Exception as e:
        logger.error(f"❌ サンプルテンプレート作成エラー: {e}")


if __name__ == "__main__":
    main()
