"""
测试硬件抽象层 - 运动控制器
"""

import pytest
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../vehicle'))

# 设置模拟模式
os.environ['MOCK_HARDWARE'] = 'true'

from hal.motion_controller import (
    MotionController,
    qianjin, houtui, zuopingyi, youpingyi,
    xuanzhuan, fxuanzhuan, tingzhi,
    yidong_angle, yidong_xy,
    set_servo, reset_servos,
    motion_controller
)


class TestMotionController:
    """测试运动控制器"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.controller = MotionController()

    def test_init(self):
        """测试初始化"""
        assert self.controller is not None
        assert self.controller.max_speed == 80
        assert self.controller.servo_max_angle == 180

    def test_clamp_speed(self):
        """测试速度限制"""
        controller = MotionController()
        assert controller._clamp_speed(100) == 80
        assert controller._clamp_speed(-100) == -80
        assert controller._clamp_speed(50) == 50
        assert controller._clamp_speed(0) == 0

    def test_clamp_angle(self):
        """测试角度限制"""
        controller = MotionController()
        assert controller._clamp_angle(200) == 180
        assert controller._clamp_angle(-10) == 0
        assert controller._clamp_angle(90) == 90

    def test_qianjin(self):
        """测试前进"""
        self.controller.qianjin(50)
        assert self.controller._motor_speeds == [50, 50, 50, 50]

    def test_houtui(self):
        """测试后退"""
        self.controller.houtui(50)
        assert self.controller._motor_speeds == [-50, -50, -50, -50]

    def test_zuopingyi(self):
        """测试左平移"""
        self.controller.zuopingyi(50)
        assert self.controller._motor_speeds == [-50, 50, 50, -50]

    def test_youpingyi(self):
        """测试右平移"""
        self.controller.youpingyi(50)
        assert self.controller._motor_speeds == [50, -50, -50, 50]

    def test_xuanzhuan(self):
        """测试顺时针旋转"""
        self.controller.xuanzhuan(50)
        assert self.controller._motor_speeds == [50, -50, 50, -50]

    def test_fxuanzhuan(self):
        """测试逆时针旋转"""
        self.controller.fxuanzhuan(50)
        assert self.controller._motor_speeds == [-50, 50, -50, 50]

    def test_tingzhi(self):
        """测试停止"""
        self.controller.qianjin(50)
        self.controller.tingzhi()
        assert self.controller._motor_speeds == [0, 0, 0, 0]

    def test_speed_limit(self):
        """测试速度限制"""
        self.controller.qianjin(100)
        # 速度应该被限制到80
        assert all(s <= 80 for s in self.controller._motor_speeds)

    def test_set_servo(self):
        """测试设置舵机"""
        # 应该不抛出异常
        self.controller.set_servo(1, 90)
        self.controller.set_servo(6, 180)

    def test_set_servo_invalid_id(self):
        """测试无效舵机ID"""
        with pytest.raises(ValueError):
            self.controller.set_servo(0, 90)
        with pytest.raises(ValueError):
            self.controller.set_servo(7, 90)

    def test_reset_servos(self):
        """测试复位舵机"""
        self.controller.reset_servos()
        # 模拟模式下应该不抛出异常


class TestMotionControllerFunctions:
    """测试运动控制便捷函数"""

    def test_qianjin_function(self):
        """测试前进函数"""
        qianjin(50)
        assert motion_controller._motor_speeds == [50, 50, 50, 50]
        motion_controller.tingzhi()

    def test_houtui_function(self):
        """测试后退函数"""
        houtui(50)
        assert motion_controller._motor_speeds == [-50, -50, -50, -50]
        motion_controller.tingzhi()

    def test_zuopingyi_function(self):
        """测试左平移函数"""
        zuopingyi(50)
        assert motion_controller._motor_speeds == [-50, 50, 50, -50]
        motion_controller.tingzhi()

    def test_youpingyi_function(self):
        """测试右平移函数"""
        youpingyi(50)
        assert motion_controller._motor_speeds == [50, -50, -50, 50]
        motion_controller.tingzhi()

    def test_xuanzhuan_function(self):
        """测试旋转函数"""
        xuanzhuan(50)
        assert motion_controller._motor_speeds == [50, -50, 50, -50]
        motion_controller.tingzhi()

    def test_fxuanzhuan_function(self):
        """测试反转函数"""
        fxuanzhuan(50)
        assert motion_controller._motor_speeds == [-50, 50, -50, 50]
        motion_controller.tingzhi()

    def test_tingzhi_function(self):
        """测试停止函数"""
        qianjin(50)
        tingzhi()
        assert motion_controller._motor_speeds == [0, 0, 0, 0]

    def test_yidong_angle_function(self):
        """测试按角度移动函数"""
        yidong_angle(90, 50)
        # 模拟模式下只验证不抛出异常

    def test_yidong_xy_function(self):
        """测试按XY移动函数"""
        yidong_xy(50, 30)
        # yidong_xy(50, 30) 计算: [vy+vx, vy-vx, vy-vx, vy+vx] = [30+50, 30-50, 30-50, 30+50]
        assert motion_controller._motor_speeds == [80, -20, -20, 80]
        motion_controller.tingzhi()  # 清理状态

    def test_set_servo_function(self):
        """测试设置舵机函数"""
        set_servo(1, 90)
        # 模拟模式下只验证不抛出异常

    def test_reset_servos_function(self):
        """测试复位舵机函数"""
        reset_servos()
        # 模拟模式下只验证不抛出异常
