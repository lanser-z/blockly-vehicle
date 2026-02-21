"""
Pytest配置文件
"""

import pytest
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 设置测试环境变量
os.environ.setdefault('MOCK_HARDWARE', 'true')
os.environ.setdefault('VEHICLE_ID', 'test-vehicle-001')
os.environ.setdefault('FLASK_ENV', 'testing')
os.environ.setdefault('LOG_LEVEL', 'WARNING')


@pytest.fixture
def mock_hal():
    """模拟HAL模块"""
    os.environ['MOCK_HARDWARE'] = 'true'
    # 重新导入HAL模块以应用模拟模式
    if 'vehicle.hal' in sys.modules:
        del sys.modules['vehicle.hal']
    if 'vehicle.hal.motion_controller' in sys.modules:
        del sys.modules['vehicle.hal.motion_controller']
    if 'vehicle.hal.sensor_controller' in sys.modules:
        del sys.modules['vehicle.hal.sensor_controller']

    import vehicle.hal as hal
    return hal


@pytest.fixture
def sample_code():
    """示例代码"""
    return """
qianjin(50)
print("前进中...")
tingzhi()
print("停止")
"""


@pytest.fixture
def sample_sensor_code():
    """示例传感器代码"""
    return """
distance = heshengbo()
print(f"距离: {distance}mm")

if distance < 100:
    tingzhi()
else:
    qianjin(30)
"""


@pytest.fixture
def sample_loop_code():
    """示例循环代码"""
    return """
for i in range(3):
    print(f"循环: {i}")
    qianjin(30)
"""
