"""
硬件抽象层 - HAL

提供统一的硬件控制接口，封装HiwonderSDK
支持模拟模式用于开发测试
"""

from .motion_controller import (
    MotionController,
    motion_controller,
    qianjin, houtui, zuopingyi, youpingyi,
    xuanzhuan, fxuanzhuan, tingzhi,
    yidong_angle, yidong_xy,
    set_servo, reset_servos
)

from .sensor_controller import (
    SensorController,
    sensor_controller,
    heshengbo, heshengbo_juli,
    xunxian, xunxian_zhong, xunxian_zuo, xunxian_you,
    dianchi
)

__all__ = [
    # 运动控制器
    'MotionController', 'motion_controller',
    'qianjin', 'houtui', 'zuopingyi', 'youpingyi',
    'xuanzhuan', 'fxuanzhuan', 'tingzhi',
    'yidong_angle', 'yidong_xy',
    'set_servo', 'reset_servos',

    # 传感器控制器
    'SensorController', 'sensor_controller',
    'heshengbo', 'heshengbo_juli',
    'xunxian', 'xunxian_zhong', 'xunxian_zuo', 'xunxian_you',
    'dianchi',
]

# 硬件可用状态
MOCK_HARDWARE = False

try:
    import os
    MOCK_HARDWARE = os.getenv('MOCK_HARDWARE', 'false').lower() == 'true'
except:
    pass

if not MOCK_HARDWARE:
    try:
        from .motion_controller import HARDWARE_AVAILABLE as MOTION_HW
        from .sensor_controller import HARDWARE_AVAILABLE as SENSOR_HW
        HARDWARE_AVAILABLE = MOTION_HW and SENSOR_HW
    except:
        HARDWARE_AVAILABLE = False
else:
    HARDWARE_AVAILABLE = False
