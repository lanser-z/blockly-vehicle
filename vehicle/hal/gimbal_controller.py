"""
硬件抽象层 - 云台控制器

封装云台舵机控制，云台有2个自由度：
- 舵机1: 水平转动（左右）
- 舵机2: 垂直转动（上下）
"""

import logging
import os
import sys

# 配置日志
logger = logging.getLogger(__name__)

# TurboPi路径
TURBOPI_PATH = os.getenv('TURBOPI_PATH', './TurboPi')
if os.path.exists(TURBOPI_PATH):
    sys.path.insert(0, TURBOPI_PATH)
    sys.path.insert(0, os.path.join(TURBOPI_PATH, 'HiwonderSDK'))

# 导入硬件SDK - 必须成功，否则服务无法运行
try:
    import HiwonderSDK.Board as Board
    logger.info("云台硬件SDK加载成功")
except Exception as e:
    logger.error(f"云台硬件SDK加载失败: {e}")
    raise RuntimeError(f"云台硬件SDK加载失败: {e}") from e


class GimbalController:
    """云台控制器

    使用舵机1和舵机2控制云台：
    - 舵机1: 水平转动（左右），0°-180°，90°为中位
    - 舵机2: 垂直转动（上下），0°-180°，90°为中位
    """

    # 舵机ID配置（物理接线已互换，需要交换ID映射）
    SERVO_HORIZONTAL = 2  # 水平舵机（物理上是舵机2）
    SERVO_VERTICAL = 1    # 垂直舵机（物理上是舵机1）

    # 角度限制
    MIN_ANGLE = 0
    MAX_ANGLE = 180
    CENTER_ANGLE = 90

    # 每次移动的步进角度
    STEP_ANGLE = 10

    def __init__(self):
        self.horizontal_angle = self.CENTER_ANGLE  # 水平角度
        self.vertical_angle = self.CENTER_ANGLE    # 垂直角度

        # 初始化云台到中位
        Board.setPWMServoAngle(self.SERVO_HORIZONTAL, self.CENTER_ANGLE)
        Board.setPWMServoAngle(self.SERVO_VERTICAL, self.CENTER_ANGLE)
        logger.info(f"云台初始化完成: 水平={self.CENTER_ANGLE}°, 垂直={self.CENTER_ANGLE}°")

    def _clamp_angle(self, angle: int) -> int:
        """限制角度范围"""
        return max(self.MIN_ANGLE, min(self.MAX_ANGLE, angle))

    def _move_horizontal(self, delta: int) -> None:
        """水平移动云台

        Args:
            delta: 角度变化量，正数向右，负数向左
        """
        new_angle = self._clamp_angle(self.horizontal_angle + delta)
        logger.info(f"云台水平移动: {self.horizontal_angle}° -> {new_angle}°")
        Board.setPWMServoAngle(self.SERVO_HORIZONTAL, new_angle)
        self.horizontal_angle = new_angle

    def _move_vertical(self, delta: int) -> None:
        """垂直移动云台

        Args:
            delta: 角度变化量，正数向上，负数向下
        """
        new_angle = self._clamp_angle(self.vertical_angle + delta)
        logger.info(f"云台垂直移动: {self.vertical_angle}° -> {new_angle}°")
        Board.setPWMServoAngle(self.SERVO_VERTICAL, new_angle)
        self.vertical_angle = new_angle

    # ===== 基础控制 =====

    def shang(self) -> None:
        """云台向上（摄像头向上看）"""
        self._move_vertical(self.STEP_ANGLE)

    def xia(self) -> None:
        """云台向下（摄像头向下看）"""
        self._move_vertical(-self.STEP_ANGLE)

    def zuo(self) -> None:
        """云台向左"""
        self._move_horizontal(-self.STEP_ANGLE)

    def you(self) -> None:
        """云台向右"""
        self._move_horizontal(self.STEP_ANGLE)

    def fuwei(self) -> None:
        """云台复位到中位"""
        logger.info("云台复位")
        Board.setPWMServoAngle(self.SERVO_HORIZONTAL, self.CENTER_ANGLE)
        Board.setPWMServoAngle(self.SERVO_VERTICAL, self.CENTER_ANGLE)
        self.horizontal_angle = self.CENTER_ANGLE
        self.vertical_angle = self.CENTER_ANGLE

    # ===== 高级控制 =====

    def set_horizontal(self, angle: int) -> None:
        """设置水平角度

        Args:
            angle: 角度值，范围0-180
        """
        angle = self._clamp_angle(angle)
        logger.info(f"设置云台水平角度: {angle}°")
        Board.setPWMServoAngle(self.SERVO_HORIZONTAL, angle)
        self.horizontal_angle = angle

    def set_vertical(self, angle: int) -> None:
        """设置垂直角度

        Args:
            angle: 角度值，范围0-180
        """
        angle = self._clamp_angle(angle)
        logger.info(f"设置云台垂直角度: {angle}°")
        Board.setPWMServoAngle(self.SERVO_VERTICAL, angle)
        self.vertical_angle = angle

    def get_position(self) -> dict:
        """获取云台当前位置

        Returns:
            dict: 包含水平和垂直角度的字典
        """
        return {
            'horizontal': self.horizontal_angle,
            'vertical': self.vertical_angle
        }


# 全局实例
gimbal_controller = GimbalController()


# 便捷函数
def shang():
    """云台向上"""
    gimbal_controller.shang()


def xia():
    """云台向下"""
    gimbal_controller.xia()


def zuo():
    """云台向左"""
    gimbal_controller.zuo()


def you():
    """云台向右"""
    gimbal_controller.you()


def fuwei():
    """云台复位"""
    gimbal_controller.fuwei()


def set_horizontal(angle: int):
    """设置云台水平角度"""
    gimbal_controller.set_horizontal(angle)


def set_vertical(angle: int):
    """设置云台垂直角度"""
    gimbal_controller.set_vertical(angle)


def get_position() -> dict:
    """获取云台位置"""
    return gimbal_controller.get_position()


# ===== 按设计文档添加的API别名 =====
# 设计文档: docs/02-block-api.md
# 这些函数名与设计文档一致，保持API兼容性

def yuntai_shang(angle: int = 30) -> None:
    """云台向上转动（按设计文档命名）

    Args:
        angle: 转动角度 (0-90), 默认30
    """
    angle = max(0, min(90, angle))
    new_angle = gimbal_controller.CENTER_ANGLE + angle
    gimbal_controller.set_vertical(new_angle)


def yuntai_xia(angle: int = 30) -> None:
    """云台向下转动（按设计文档命名）

    Args:
        angle: 转动角度 (0-90), 默认30
    """
    angle = max(0, min(90, angle))
    new_angle = gimbal_controller.CENTER_ANGLE - angle
    gimbal_controller.set_vertical(new_angle)


def yuntai_zuo(angle: int = 30) -> None:
    """云台向左转动（按设计文档命名）

    Args:
        angle: 转动角度 (0-90), 默认30
    """
    angle = max(0, min(90, angle))
    new_angle = gimbal_controller.CENTER_ANGLE - angle
    gimbal_controller.set_horizontal(new_angle)


def yuntai_you(angle: int = 30) -> None:
    """云台向右转动（按设计文档命名）

    Args:
        angle: 转动角度 (0-90), 默认30
    """
    angle = max(0, min(90, angle))
    new_angle = gimbal_controller.CENTER_ANGLE + angle
    gimbal_controller.set_horizontal(new_angle)


def yuntai_fuwei() -> None:
    """云台复位到初始位置（按设计文档命名）"""
    gimbal_controller.fuwei()
