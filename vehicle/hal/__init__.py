"""
硬件抽象层 - HAL

提供统一的硬件控制接口，封装HiwonderSDK
"""

import os
import sys

# ===== 设置 TurboPi 路径 =====
# HiwonderSDK 硬编码了 /home/pi/TurboPi/ 路径
# 我们通过设置环境变量或符号链接来解决
# 首先尝试项目相对路径，然后使用标准路径

_TURBOPI_PATH = os.getenv('TURBOPI_PATH')
if _TURBOPI_PATH and os.path.exists(_TURBOPI_PATH):
    sys.path.insert(0, _TURBOPI_PATH)
    sys.path.insert(0, os.path.join(_TURBOPI_PATH, 'HiwonderSDK'))
elif os.path.exists('./TurboPi'):
    sys.path.insert(0, os.path.abspath('./TurboPi'))
    sys.path.insert(0, os.path.abspath('./TurboPi/HiwonderSDK'))
elif os.path.exists('/home/pi/TurboPi'):
    sys.path.insert(0, '/home/pi/TurboPi')
    sys.path.insert(0, '/home/pi/TurboPi/HiwonderSDK')

from .motion_controller import (
    MotionController,
    motion_controller,
    qianjin, houtui, zuopingyi, youpingyi,
    xuanzhuan, fxuanzhuan, tingzhi,
    yidong_angle, yidong_xy,
    set_servo, reset_servos,
    xiaozuozhuan, xiaoyouzhuan,
    dengdai
)

from .sensor_controller import (
    SensorController,
    sensor_controller,
    heshengbo, heshengbo_juli,
    xunxian, xunxian_zhong, xunxian_zuo, xunxian_you,
    dianchi
)

from .gimbal_controller import (
    GimbalController,
    gimbal_controller,
    shang, xia, zuo, you, fuwei,
    yuntai_shang, yuntai_xia, yuntai_zuo, yuntai_you, yuntai_fuwei
)

from .vision_controller import (
    VisionController,
    vision_controller,
    shibieyanse
)

__all__ = [
    # 运动控制器
    'MotionController', 'motion_controller',
    'qianjin', 'houtui', 'zuopingyi', 'youpingyi',
    'xuanzhuan', 'fxuanzhuan', 'tingzhi',
    'xiaozuozhuan', 'xiaoyouzhuan',
    'dengdai',
    'yidong_angle', 'yidong_xy',
    'set_servo', 'reset_servos',

    # 传感器控制器
    'SensorController', 'sensor_controller',
    'heshengbo', 'heshengbo_juli',
    'xunxian', 'xunxian_zhong', 'xunxian_zuo', 'xunxian_you',
    'dianchi',

    # 云台控制器
    'GimbalController', 'gimbal_controller',
    'shang', 'xia', 'zuo', 'you', 'fuwei',
    'yuntai_shang', 'yuntai_xia', 'yuntai_zuo', 'yuntai_you', 'yuntai_fuwei',

    # 视觉控制器
    'VisionController', 'vision_controller',
    'shibieyanse',
]

# 硬件必须可用，否则服务无法启动
HARDWARE_AVAILABLE = True
