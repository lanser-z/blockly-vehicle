"""
测试硬件抽象层 - 传感器控制器
"""

import pytest
import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../vehicle'))

# 设置模拟模式
os.environ['MOCK_HARDWARE'] = 'true'

from hal.sensor_controller import (
    SensorController,
    heshengbo, heshengbo_juli,
    xunxian, xunxian_zhong, xunxian_zuo, xunxian_you,
    dianchi,
    sensor_controller
)


class TestSensorController:
    """测试传感器控制器"""

    def setup_method(self):
        """每个测试方法前的设置"""
        self.controller = SensorController()

    def test_init(self):
        """测试初始化"""
        assert self.controller is not None
        assert self.controller._mock_distance == 300
        assert self.controller._mock_battery == 75

    def test_heshengbo(self):
        """测试超声波传感器"""
        distance = self.controller.heshengbo()
        assert isinstance(distance, int)
        assert 0 <= distance <= 5000

    def test_heshengbo_juli(self):
        """测试超声波距离（厘米）"""
        distance_cm = self.controller.heshengbo_juli()
        assert isinstance(distance_cm, float)
        assert 0 <= distance_cm <= 500

    def test_heshengbo_fuzhi_true(self):
        """测试超声波距离比较（返回True）"""
        # 模拟距离约300mm
        result = self.controller.heshengbo_fuzhi(400)
        assert result is True

    def test_heshengbo_fuzhi_false(self):
        """测试超声波距离比较（返回False）"""
        # 模拟距离约300mm
        result = self.controller.heshengbo_fuzhi(200)
        assert result is False

    def test_xunxian(self):
        """测试巡线传感器"""
        states = self.controller.xunxian()
        assert isinstance(states, list)
        assert len(states) == 4
        assert all(isinstance(s, bool) for s in states)

    def test_xunxian_zhong_true(self):
        """测试中间传感器检测到线"""
        # 默认模拟状态 [False, True, True, False]
        result = self.controller.xunxian_zhong()
        assert result is True

    def test_xunxian_zuo_false(self):
        """测试左侧传感器"""
        # 默认模拟状态 [False, True, True, False]
        result = self.controller.xunxian_zuo()
        assert result is False

    def test_xunxian_you_false(self):
        """测试右侧传感器"""
        # 默认模拟状态 [False, True, True, False]
        result = self.controller.xunxian_you()
        assert result is False

    def test_dianchi(self):
        """测试电池电量"""
        percentage = self.controller.dianchi()
        assert isinstance(percentage, int)
        assert 0 <= percentage <= 100

    def test_dianchi_dian_false(self):
        """测试电池电量检测（非低电量）"""
        # 模拟电量75%
        result = self.controller.dianchi_dian()
        assert result is False

    def test_get_all_sensors(self):
        """测试获取所有传感器状态"""
        data = self.controller.get_all_sensors()
        assert 'ultrasonic' in data
        assert 'line_follower' in data
        assert 'battery' in data

        # 验证超声波数据
        assert 'distance_mm' in data['ultrasonic']
        assert 'distance_cm' in data['ultrasonic']

        # 验证巡线数据
        assert 'sensors' in data['line_follower']
        assert 'on_line' in data['line_follower']

        # 验证电池数据
        assert 'percentage' in data['battery']
        assert 'low' in data['battery']


class TestSensorControllerFunctions:
    """测试传感器便捷函数"""

    def test_heshengbo_function(self):
        """测试超声波函数"""
        distance = heshengbo()
        assert isinstance(distance, int)
        assert 0 <= distance <= 5000

    def test_heshengbo_juli_function(self):
        """测试超声波厘米函数"""
        distance_cm = heshengbo_juli()
        assert isinstance(distance_cm, float)

    def test_xunxian_function(self):
        """测试巡线函数"""
        states = xunxian()
        assert isinstance(states, list)
        assert len(states) == 4

    def test_xunxian_zhong_function(self):
        """测试巡线中间函数"""
        result = xunxian_zhong()
        assert isinstance(result, bool)

    def test_xunxian_zuo_function(self):
        """测试巡线左侧函数"""
        result = xunxian_zuo()
        assert isinstance(result, bool)

    def test_xunxian_you_function(self):
        """测试巡线右侧函数"""
        result = xunxian_you()
        assert isinstance(result, bool)

    def test_dianchi_function(self):
        """测试电池函数"""
        percentage = dianchi()
        assert isinstance(percentage, int)
        assert 0 <= percentage <= 100


class TestSensorEdgeCases:
    """测试传感器边界情况"""

    def test_ultrasonic_range(self):
        """测试超声波测量范围"""
        controller = SensorController()
        for _ in range(10):
            distance = controller.heshengbo()
            assert 0 <= distance <= 5000

    def test_battery_range(self):
        """测试电池电量范围"""
        controller = SensorController()
        percentage = controller.dianchi()
        assert 0 <= percentage <= 100

    def test_line_follower_states(self):
        """测试巡线传感器状态"""
        controller = SensorController()
        states = controller.xunxian()
        # 应该是4个布尔值
        assert len(states) == 4
        for state in states:
            assert isinstance(state, bool)
