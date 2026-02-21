"""
硬件抽象层 - 运动控制器

封装HiwonderSDK的电机和舵机控制
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

# MOCK_HARDWARE模式 - 开发时不需要真实硬件
MOCK_HARDWARE = os.getenv('MOCK_HARDWARE', 'false').lower() == 'true'

if not MOCK_HARDWARE:
    try:
        import HiwonderSDK.Board as Board
        import HiwonderSDK.mecanum as mecanum
        HARDWARE_AVAILABLE = True
        logger.info("硬件SDK加载成功")
    except ImportError as e:
        logger.warning(f"硬件SDK加载失败: {e}")
        logger.warning("使用模拟模式")
        HARDWARE_AVAILABLE = False
        MOCK_HARDWARE = True
else:
    HARDWARE_AVAILABLE = False
    logger.info("使用模拟硬件模式")


class MotionController:
    """运动控制器"""

    def __init__(self):
        if HARDWARE_AVAILABLE:
            self.chassis = mecanum.MecanumChassis()
        else:
            self.chassis = None
            self._motor_speeds = [0, 0, 0, 0]
            logger.info("运动控制器: 模拟模式")

        # 安全限制
        self.max_speed = int(os.getenv('MOTOR_MAX_SPEED', '80'))
        self.servo_max_angle = int(os.getenv('SERVO_MAX_ANGLE', '180'))

    def _clamp_speed(self, speed: int) -> int:
        """限制速度范围"""
        return max(-self.max_speed, min(self.max_speed, speed))

    def _clamp_angle(self, angle: int) -> int:
        """限制角度范围"""
        return max(0, min(self.servo_max_angle, angle))

    # ===== 基础运动 =====

    def qianjin(self, speed: int = 50) -> None:
        """前进"""
        speed = self._clamp_speed(speed)
        logger.info(f"前进: 速度={speed}")

        if HARDWARE_AVAILABLE:
            self.chassis.set_velocity(velocity=speed * 10, direction=0, angular_rate=0)
        else:
            # 模拟模式
            self._motor_speeds = [speed, speed, speed, speed]
            logger.info(f"  [模拟] 电机速度: {self._motor_speeds}")

    def houtui(self, speed: int = 50) -> None:
        """后退"""
        speed = self._clamp_speed(speed)
        logger.info(f"后退: 速度={speed}")

        if HARDWARE_AVAILABLE:
            self.chassis.set_velocity(velocity=speed * 10, direction=180, angular_rate=0)
        else:
            self._motor_speeds = [-speed, -speed, -speed, -speed]
            logger.info(f"  [模拟] 电机速度: {self._motor_speeds}")

    def zuopingyi(self, speed: int = 50) -> None:
        """左平移"""
        speed = self._clamp_speed(speed)
        logger.info(f"左平移: 速度={speed}")

        if HARDWARE_AVAILABLE:
            self.chassis.set_velocity(velocity=speed * 10, direction=270, angular_rate=0)
        else:
            self._motor_speeds = [-speed, speed, speed, -speed]
            logger.info(f"  [模拟] 电机速度: {self._motor_speeds}")

    def youpingyi(self, speed: int = 50) -> None:
        """右平移"""
        speed = self._clamp_speed(speed)
        logger.info(f"右平移: 速度={speed}")

        if HARDWARE_AVAILABLE:
            self.chassis.set_velocity(velocity=speed * 10, direction=90, angular_rate=0)
        else:
            self._motor_speeds = [speed, -speed, -speed, speed]
            logger.info(f"  [模拟] 电机速度: {self._motor_speeds}")

    def xuanzhuan(self, speed: int = 50) -> None:
        """原地旋转（顺时针）"""
        speed = self._clamp_speed(speed)
        logger.info(f"旋转(顺时针): 速度={speed}")

        if HARDWARE_AVAILABLE:
            self.chassis.set_velocity(velocity=0, direction=0, angular_rate=speed)
        else:
            self._motor_speeds = [speed, -speed, speed, -speed]
            logger.info(f"  [模拟] 电机速度: {self._motor_speeds}")

    def fxuanzhuan(self, speed: int = 50) -> None:
        """原地旋转（逆时针）"""
        speed = self._clamp_speed(speed)
        logger.info(f"旋转(逆时针): 速度={speed}")

        if HARDWARE_AVAILABLE:
            self.chassis.set_velocity(velocity=0, direction=0, angular_rate=-speed)
        else:
            self._motor_speeds = [-speed, speed, -speed, speed]
            logger.info(f"  [模拟] 电机速度: {self._motor_speeds}")

    def tingzhi(self) -> None:
        """停止所有电机"""
        logger.info("停止")

        if HARDWARE_AVAILABLE:
            self.chassis.reset_motors()
        else:
            self._motor_speeds = [0, 0, 0, 0]
            logger.info("  [模拟] 所有电机停止")

    # ===== 高级运动 =====

    def yidong_angle(self, angle: float, speed: int = 50) -> None:
        """按角度移动"""
        speed = self._clamp_speed(speed)
        logger.info(f"按角度移动: 角度={angle}°, 速度={speed}")

        if HARDWARE_AVAILABLE:
            self.chassis.set_velocity(velocity=speed * 10, direction=angle, angular_rate=0)
        else:
            # 简化的模拟实现
            rad = angle * 3.14159 / 180
            vx = int(speed * 10 * 0.707 * (1 if 0 <= angle < 180 else -1))
            vy = int(speed * 10 * 0.707 * (1 if 0 <= angle < 90 or angle >= 270 else -1))
            logger.info(f"  [模拟] vx={vx}, vy={vy}")

    def yidong_xy(self, vx: float, vy: float) -> None:
        """按X/Y方向移动"""
        vx = max(-100, min(100, int(vx)))
        vy = max(-100, min(100, int(vy)))
        logger.info(f"按XY移动: vx={vx}, vy={vy}")

        if HARDWARE_AVAILABLE:
            self.chassis.translation(vx * 10, vy * 10)
        else:
            self._motor_speeds = [vy + vx, vy - vx, vy - vx, vy + vx]
            logger.info(f"  [模拟] 电机速度: {self._motor_speeds}")

    # ===== 舵机控制 =====

    def set_servo(self, servo_id: int, angle: int) -> None:
        """设置舵机角度"""
        if servo_id < 1 or servo_id > 6:
            raise ValueError(f"无效的舵机ID: {servo_id}")

        angle = self._clamp_angle(angle)
        logger.info(f"舵机{servo_id}: 角度={angle}°")

        if HARDWARE_AVAILABLE:
            Board.setPWMServoAngle(servo_id, angle)
        else:
            logger.info(f"  [模拟] 舵机{servo_id}设置为{angle}°")

    def reset_servos(self) -> None:
        """复位所有舵机"""
        logger.info("复位所有舵机")

        if HARDWARE_AVAILABLE:
            for i in range(1, 7):
                Board.setPWMServoAngle(i, 90)
        else:
            logger.info("  [模拟] 所有舵机复位到90°")


# 全局实例
motion_controller = MotionController()


# 便捷函数
def qianjin(speed: int = 50):
    """前进"""
    motion_controller.qianjin(speed)


def houtui(speed: int = 50):
    """后退"""
    motion_controller.houtui(speed)


def zuopingyi(speed: int = 50):
    """左平移"""
    motion_controller.zuopingyi(speed)


def youpingyi(speed: int = 50):
    """右平移"""
    motion_controller.youpingyi(speed)


def xuanzhuan(speed: int = 50):
    """旋转（顺时针）"""
    motion_controller.xuanzhuan(speed)


def fxuanzhuan(speed: int = 50):
    """旋转（逆时针）"""
    motion_controller.fxuanzhuan(speed)


def tingzhi():
    """停止"""
    motion_controller.tingzhi()


def yidong_angle(angle: float, speed: int = 50):
    """按角度移动"""
    motion_controller.yidong_angle(angle, speed)


def yidong_xy(vx: float, vy: float):
    """按X/Y方向移动"""
    motion_controller.yidong_xy(vx, vy)


def set_servo(servo_id: int, angle: int):
    """设置舵机角度"""
    motion_controller.set_servo(servo_id, angle)


def reset_servos():
    """复位所有舵机"""
    motion_controller.reset_servos()
