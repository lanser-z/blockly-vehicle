"""
硬件抽象层 - 传感器控制器

封装HiwonderSDK的传感器读取功能
"""

import logging
import os
import sys
from typing import List

# 配置日志
logger = logging.getLogger(__name__)

# TurboPi路径
TURBOPI_PATH = os.getenv('TURBOPI_PATH', './TurboPi')
if os.path.exists(TURBOPI_PATH):
    sys.path.insert(0, TURBOPI_PATH)
    sys.path.insert(0, os.path.join(TURBOPI_PATH, 'HiwonderSDK'))

# 导入硬件SDK - 必须成功，否则服务无法运行
try:
    import HiwonderSDK.Sonar as Sonar
    import HiwonderSDK.FourInfrared as FourInfrared
    import HiwonderSDK.Board as Board
    HARDWARE_AVAILABLE = True
    logger.info("硬件传感器SDK加载成功")
except Exception as e:
    logger.error(f"硬件传感器SDK加载失败: {e}")
    raise RuntimeError(f"硬件传感器SDK加载失败: {e}") from e


class SensorController:
    """传感器控制器"""

    def __init__(self):
        self.sonar = Sonar.Sonar()
        self.infrared = FourInfrared.FourInfrared()
        logger.info("传感器控制器初始化完成")

    # ===== 超声波传感器 =====

    def heshengbo(self) -> int:
        """获取超声波距离（毫米）

        Returns:
            int: 距离值，单位毫米，范围0-5000
        """
        distance = self.sonar.getDistance()
        logger.debug(f"超声波距离: {distance}mm")
        return distance

    def heshengbo_juli(self) -> float:
        """获取超声波距离（厘米）

        Returns:
            float: 距离值，单位厘米，范围0-500
        """
        return self.heshengbo() / 10.0

    def heshengbo_fuzhi(self, distance: int) -> bool:
        """检测超声波距离是否小于指定值

        Args:
            distance: 距离阈值（毫米）

        Returns:
            bool: True表示距离小于阈值
        """
        current = self.heshengbo()
        result = current < distance
        logger.debug(f"超声波检测: 当前{current}mm < 阈值{distance}mm = {result}")
        return result

    # ===== 巡线传感器 =====

    def xunxian(self) -> List[bool]:
        """读取4路巡线传感器状态

        Returns:
            List[bool]: 4个传感器状态，True表示检测到黑线
                        [左1, 左2, 右2, 右1]
        """
        states = self.infrared.readData()
        logger.debug(f"巡线传感器: {states}")
        return states

    def xunxian_zhong(self) -> bool:
        """检测中间两个传感器是否都检测到黑线

        Returns:
            bool: True表示中间两个传感器都检测到黑线（适合前进）
        """
        states = self.xunxian()
        # states[1]和states[2]是中间两个传感器
        return states[1] and states[2]

    def xunxian_zuo(self) -> bool:
        """检测左侧传感器是否检测到黑线

        Returns:
            bool: True表示左侧检测到黑线（需要右转）
        """
        states = self.xunxian()
        return states[0]

    def xunxian_you(self) -> bool:
        """检测右侧传感器是否检测到黑线

        Returns:
            bool: True表示右侧检测到黑线（需要左转）
        """
        states = self.xunxian()
        return states[3]

    def xunxian_kuaixian(self) -> bool:
        """检测是否所有传感器都检测到黑线（可能是十字路口）

        Returns:
            bool: True表示所有传感器都检测到黑线
        """
        states = self.xunxian()
        return all(states)

    def xunxian_duqu(self) -> bool:
        """检测是否所有传感器都没检测到黑线（脱线）

        Returns:
            bool: True表示脱线
        """
        states = self.xunxian()
        return not any(states)

    # ===== 电池传感器 =====

    def dianchi(self) -> float:
        """获取电池电压

        Returns:
            float: 电池电压，单位V，范围0-5.0
        """
        # Board.getBattery()返回ADC值（mV）
        adc = Board.getBattery()
        # 转换为电压（V）
        voltage = adc / 1000.0
        logger.debug(f"电池电压: {voltage}V")
        return voltage

    def dianchi_dian(self) -> bool:
        """检测电池电量是否低

        Returns:
            bool: True表示电压低于3.5V
        """
        return self.dianchi() < 3.5

    # ===== 综合状态 =====

    def get_all_sensors(self) -> dict:
        """获取所有传感器状态

        Returns:
            dict: 包含所有传感器状态的字典
        """
        return {
            'ultrasonic': {
                'distance_mm': self.heshengbo(),
                'distance_cm': self.heshengbo_juli()
            },
            'line_follower': {
                'sensors': self.xunxian(),
                'on_line': self.xunxian_zhong(),
                'left': self.xunxian_zuo(),
                'right': self.xunxian_you(),
                'intersection': self.xunxian_kuaixian(),
                'lost': self.xunxian_duqu()
            },
            'battery': {
                'voltage': self.dianchi(),
                'low': self.dianchi_dian()
            }
        }


# 全局实例
sensor_controller = SensorController()


# 便捷函数
def heshengbo() -> int:
    """获取超声波距离（毫米）"""
    return sensor_controller.heshengbo()


def heshengbo_juli() -> float:
    """获取超声波距离（厘米）"""
    return sensor_controller.heshengbo_juli()


def xunxian() -> List[bool]:
    """读取4路巡线传感器状态"""
    return sensor_controller.xunxian()


def xunxian(channel: int) -> bool:
    """读取指定通道的巡线传感器状态

    Args:
        channel: 通道号，0-3（对应第1-4路）

    Returns:
        bool: True表示检测到黑线
    """
    if channel < 0 or channel > 3:
        raise ValueError(f"巡线传感器通道号无效: {channel}，范围应为0-3")

    states = sensor_controller.xunxian()
    return states[channel]


def xunxian_zhong() -> bool:
    """检测中间传感器是否在黑线上"""
    return sensor_controller.xunxian_zhong()


def xunxian_zuo() -> bool:
    """检测左侧传感器是否检测到黑线"""
    return sensor_controller.xunxian_zuo()


def xunxian_you() -> bool:
    """检测右侧传感器是否检测到黑线"""
    return sensor_controller.xunxian_you()


def dianchi() -> int:
    """获取电池电量百分比"""
    return sensor_controller.dianchi()
