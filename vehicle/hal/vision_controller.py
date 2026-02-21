"""
硬件抽象层 - 视觉控制器

封装摄像头颜色识别功能
"""

import logging
import os
import sys
from typing import Optional, Tuple

# 配置日志
logger = logging.getLogger(__name__)

# TurboPi路径
TURBOPI_PATH = os.getenv('TURBOPI_PATH', './TurboPi')
if os.path.exists(TURBOPI_PATH):
    sys.path.insert(0, TURBOPI_PATH)
    sys.path.insert(0, os.path.join(TURBOPI_PATH, 'HiwonderSDK'))

# 导入视觉SDK - 必须成功，否则服务无法运行
try:
    import cv2
    import numpy as np
    logger.info("视觉硬件SDK加载成功")
except Exception as e:
    logger.error(f"视觉硬件SDK加载失败: {e}")
    raise RuntimeError(f"视觉硬件SDK加载失败: {e}") from e


# 颜色定义（HSV范围）
# 格式: (颜色名, (H_min, S_min, V_min), (H_max, S_max, V_max))
COLOR_RANGES = {
    'hong': (  # 红色（特殊处理，跨越0°）
        {'lower1': (0, 100, 100), 'upper1': (10, 255, 255),
         'lower2': (170, 100, 100), 'upper2': (180, 255, 255)}
    ),
    'lv': (  # 绿色
        (35, 100, 100), (85, 255, 255)
    ),
    'lan': (  # 蓝色
        (100, 100, 100), (130, 255, 255)
    ),
    'huang': (  # 黄色
        (20, 100, 100), (35, 255, 255)
    ),
    'cheng': (  # 橙色
        (10, 100, 100), (25, 255, 255)
    ),
}

# 颜色中文名映射
COLOR_NAMES_CN = {
    'hong': '红色',
    'lv': '绿色',
    'lan': '蓝色',
    'huang': '黄色',
    'cheng': '橙色',
}


class VisionController:
    """视觉控制器 - 颜色识别"""

    # 检测阈值
    MIN_CONTOUR_AREA = 500  # 最小轮廓面积

    def __init__(self):
        self.camera = cv2.VideoCapture(0)
        if not self.camera.isOpened():
            raise RuntimeError("无法打开摄像头")
        # 设置分辨率
        self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
        self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
        self.current_frame = None
        logger.info("摄像头初始化成功")

    def _read_frame(self) -> bool:
        """读取一帧图像

        Returns:
            bool: 是否成功读取
        """
        ret, frame = self.camera.read()
        if ret:
            self.current_frame = frame
            return True
        return False

    def _detect_color_in_frame(self, frame, color_name: str) -> Tuple[bool, Optional[Tuple[int, int, int]]]:
        """在图像帧中检测指定颜色

        Args:
            frame: OpenCV图像（BGR格式）
            color_name: 颜色名称（'hong', 'lv', 'lan', 'huang', 'cheng'）

        Returns:
            Tuple[bool, Optional[Tuple[int, int, int]]]: (是否检测到, (x, y, area))
        """
        if color_name not in COLOR_RANGES:
            logger.warning(f"未知颜色: {color_name}")
            return False, None

        # 转换为HSV颜色空间
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # 获取颜色范围
        color_range = COLOR_RANGES[color_name]

        # 创建掩码
        if color_name == 'hong':
            # 红色特殊处理（两个范围）
            mask1 = cv2.inRange(hsv, color_range['lower1'], color_range['upper1'])
            mask2 = cv2.inRange(hsv, color_range['lower2'], color_range['upper2'])
            mask = cv2.bitwise_or(mask1, mask2)
        else:
            mask = cv2.inRange(hsv, color_range[0], color_range[1])

        # 形态学操作，去除噪声
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        # 查找轮廓
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # 找到最大的轮廓
        max_area = 0
        max_contour = None
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > max_area:
                max_area = area
                max_contour = contour

        if max_area > self.MIN_CONTOUR_AREA and max_contour is not None:
            # 计算质心
            M = cv2.moments(max_contour)
            if M['m00'] > 0:
                cx = int(M['m10'] / M['m00'])
                cy = int(M['m01'] / M['m00'])
                return True, (cx, cy, max_area)

        return False, None

    def shibieyanse(self, color_name: str) -> bool:
        """识别指定颜色

        Args:
            color_name: 颜色名称（'hong', 'lv', 'lan', 'huang', 'cheng'）

        Returns:
            bool: True表示检测到该颜色
        """
        cn_name = COLOR_NAMES_CN.get(color_name, color_name)

        if not self._read_frame():
            logger.warning("无法读取摄像头图像")
            return False

        detected, _ = self._detect_color_in_frame(self.current_frame, color_name)
        logger.debug(f"颜色识别: {cn_name} -> {'检测到' if detected else '未检测到'}")
        return detected

    def get_color_position(self, color_name: str) -> Optional[Tuple[int, int]]:
        """获取指定颜色的位置

        Args:
            color_name: 颜色名称

        Returns:
            Optional[Tuple[int, int]]: (x, y)坐标，未检测到返回None
        """
        if not self._read_frame():
            return None

        detected, result = self._detect_color_in_frame(self.current_frame, color_name)
        if detected and result:
            return (result[0], result[1])
        return None

    def release(self):
        """释放摄像头资源"""
        if self.camera is not None:
            self.camera.release()
            logger.info("摄像头已释放")


# 全局实例
vision_controller = VisionController()


# 便捷函数
def shibieyanse(color_name: str) -> bool:
    """识别指定颜色

    Args:
        color_name: 颜色名称（'hong'-红色, 'lv'-绿色, 'lan'-蓝色,
                          'huang'-黄色, 'cheng'-橙色）

    Returns:
        bool: True表示检测到该颜色

    示例:
        >>> if vision.shibieyanse('hong'):
        ...     print('检测到红色')
    """
    return vision_controller.shibieyanse(color_name)


def get_color_position(color_name: str) -> Optional[Tuple[int, int]]:
    """获取指定颜色的位置

    Args:
        color_name: 颜色名称

    Returns:
        Optional[Tuple[int, int]]: (x, y)坐标，未检测到返回None
    """
    return vision_controller.get_color_position(color_name)


def release():
    """释放摄像头资源"""
    vision_controller.release()
