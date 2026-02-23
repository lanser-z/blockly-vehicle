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

# 导入硬件SDK - 必须成功，否则服务无法运行
try:
    import HiwonderSDK.Board as Board
    import HiwonderSDK.mecanum as mecanum
    HARDWARE_AVAILABLE = True
    logger.info("硬件SDK加载成功")
except Exception as e:
    error_msg = f"""
====================================
硬件初始化失败！
====================================
错误: {e}

请检查：
1. 是否在 Raspberry Pi 上运行
2. 是否已安装硬件依赖: pip install RPi.GPIO smbus2 rpi-ws281x
3. 是否有硬件访问权限: sudo usermod -a -G gpio,video,i2c $USER
4. 是否需要重新登录

或使用 sudo 启动: sudo ./vehicle-start.sh
====================================
"""
    logger.error(error_msg)
    raise RuntimeError(f"硬件SDK加载失败: {e}") from e


class MotionController:
    """运动控制器"""

    def __init__(self):
        self.chassis = mecanum.MecanumChassis()

        # 安全限制
        self.max_speed = int(os.getenv('MOTOR_MAX_SPEED', '80'))
        self.servo_max_angle = int(os.getenv('SERVO_MAX_ANGLE', '180'))

        logger.info("运动控制器初始化完成")

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
        # 90度 = 向前（Y轴正方向）
        self.chassis.set_velocity(velocity=speed * 10, direction=90, angular_rate=0)

    def houtui(self, speed: int = 50) -> None:
        """后退"""
        speed = self._clamp_speed(speed)
        logger.info(f"后退: 速度={speed}")
        # 270度 = 向后（Y轴负方向）
        self.chassis.set_velocity(velocity=speed * 10, direction=270, angular_rate=0)

    def zuopingyi(self, speed: int = 50) -> None:
        """左平移"""
        speed = self._clamp_speed(speed)
        logger.info(f"左平移: 速度={speed}")
        # 使用 translation 方法: vx负值向左，vy=0
        self.chassis.translation(-speed * 10, 0)

    def youpingyi(self, speed: int = 50) -> None:
        """右平移"""
        speed = self._clamp_speed(speed)
        logger.info(f"右平移: 速度={speed}")
        # 使用 translation 方法: vx正值向右，vy=0
        self.chassis.translation(speed * 10, 0)

    def xuanzhuan(self, speed: int = 50) -> None:
        """原地旋转（顺时针）"""
        speed = self._clamp_speed(speed)
        logger.info(f"旋转(顺时针): 速度={speed}")
        self.chassis.set_velocity(velocity=0, direction=0, angular_rate=speed)

    def fxuanzhuan(self, speed: int = 50) -> None:
        """原地旋转（逆时针）"""
        speed = self._clamp_speed(speed)
        logger.info(f"旋转(逆时针): 速度={speed}")
        self.chassis.set_velocity(velocity=0, direction=0, angular_rate=-speed)

    def tingzhi(self) -> None:
        """停止所有电机"""
        logger.info("停止")
        self.chassis.reset_motors()

    # ===== 高级运动 =====

    def yidong_angle(self, angle: float, speed: int = 50) -> None:
        """按角度移动"""
        speed = self._clamp_speed(speed)
        logger.info(f"按角度移动: 角度={angle}°, 速度={speed}")
        self.chassis.set_velocity(velocity=speed * 10, direction=angle, angular_rate=0)

    def yidong_xy(self, vx: float, vy: float) -> None:
        """按X/Y方向移动"""
        vx = max(-100, min(100, int(vx)))
        vy = max(-100, min(100, int(vy)))
        logger.info(f"按XY移动: vx={vx}, vy={vy}")
        self.chassis.translation(vx * 10, vy * 10)

    # ===== 舵机控制 =====

    def set_servo(self, servo_id: int, angle: int) -> None:
        """设置舵机角度"""
        if servo_id < 1 or servo_id > 6:
            raise ValueError(f"无效的舵机ID: {servo_id}")

        angle = self._clamp_angle(angle)
        logger.info(f"舵机{servo_id}: 角度={angle}°")
        Board.setPWMServoAngle(servo_id, angle)

    def reset_servos(self) -> None:
        """复位所有舵机"""
        logger.info("复位所有舵机")
        for i in range(1, 7):
            Board.setPWMServoAngle(i, 90)


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


# ===== 新增：左右转弯 =====

def xiaozuozhuan(speed: int = 50):
    """小左转（慢速逆时针旋转）"""
    motion_controller.fxuanzhuan(speed)


def xiaoyouzhuan(speed: int = 50):
    """小右转（慢速顺时针旋转）"""
    motion_controller.xuanzhuan(speed)


# ===== 新增：延时函数 =====

def dengdai(seconds: float):
    """等待指定秒数

    Args:
        seconds: 等待秒数
    """
    import time
    seconds = max(0, min(60, float(seconds)))  # 限制在0-60秒
    logger.info(f"等待: {seconds}秒")
    time.sleep(seconds)
