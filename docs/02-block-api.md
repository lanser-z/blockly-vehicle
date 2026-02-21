# 积木块API接口规范

## 1. 概述

本文档定义了Blockly积木块与硬件抽象层(HAL)之间的API接口规范。所有积木块通过调用这些API来控制小车硬件。

---

## 2. API设计原则

### 2.1 命名规范
- **全中文**: 函数名使用中文拼音或意译，便于6岁儿童理解
- **简洁性**: 函数名不超过6个字
- **一致性**: 同类操作使用统一前缀

### 2.2 参数规范
- **类型明确**: 使用Python类型注解
- **范围限制**: 所有数值参数有安全范围
- **默认值**: 提供合理的默认参数

### 2.3 返回值规范
- **运动类**: 无返回值 (None)
- **传感器类**: 返回具体数值或状态
- **视觉类**: 返回识别结果或None

---

## 3. 运动控制API

### 3.1 基础移动

```python
def qianjin(speed: int = 50) -> None
"""
前进

参数:
    speed: 速度 (0-100), 默认50

示例:
    qianjin(70)  # 以70的速度前进
"""
```

```python
def houtui(speed: int = 50) -> None
"""
后退

参数:
    speed: 速度 (0-100), 默认50
"""
```

```python
def zuopingyi(speed: int = 50) -> None
"""
左平移（麦克纳姆轮横向移动）

参数:
    speed: 速度 (0-100), 默认50
"""
```

```python
def youpingyi(speed: int = 50) -> None
"""
右平移（麦克纳姆轮横向移动）

参数:
    speed: 速度 (0-100), 默认50
"""
```

```python
def xuanzhuan(speed: int = 50) -> None
"""
原地旋转（顺时针）

参数:
    speed: 旋转速度 (0-100), 默认50
"""
```

```python
def fxuanzhuan(speed: int = 50) -> None
"""
原地旋转（逆时针）

参数:
    speed: 旋转速度 (0-100), 默认50
"""
```

```python
def tingzhi() -> None
"""
停止所有运动
"""
```

### 3.2 高级移动

```python
def yidong_angle(angle: float, speed: int = 50) -> None
"""
按指定角度移动

参数:
    angle: 移动角度 (0-360度), 0为前, 90为右, 180为后, 270为左
    speed: 速度 (0-100), 默认50

示例:
    yidong_angle(45, 60)  # 向右前方45度移动
"""
```

```python
def yidong_xy(vx: float, vy: float) -> None
"""
按X/Y方向移动

参数:
    vx: X方向速度 (-100到100), 正数为右, 负数为左
    vy: Y方向速度 (-100到100), 正数为前, 负数为后
"""
```

### 3.3 云台控制

```python
def yuntai_shang(angle: int = 30) -> None
"""
云台向上转动

参数:
    angle: 转动角度 (0-90), 默认30
"""
```

```python
def yuntai_xia(angle: int = 30) -> None
"""
云台向下转动

参数:
    angle: 转动角度 (0-90), 默认30
"""
```

```python
def yuntai_zuo(angle: int = 30) -> None
"""
云台向左转动

参数:
    angle: 转动角度 (0-90), 默认30
"""
```

```python
def yuntai_you(angle: int = 30) -> None
"""
云台向右转动

参数:
    angle: 转动角度 (0-90), 默认30
"""
```

```python
def yuntai_fuwei() -> None
"""
云台复位到初始位置
"""
```

---

## 4. 传感器API

### 4.1 超声波传感器

```python
def heshengbo() -> int
"""
获取超声波距离

返回:
    距离值 (毫米), 范围: 20-4000mm
    超出范围返回 -1

示例:
    distance = heshengbo()
    if distance < 200:
        tingzhi()  # 距离小于20cm停止
"""
```

```python
def heshengbo_led(color: str) -> None
"""
设置超声波模块LED颜色

参数:
    color: 颜色 ('red', 'green', 'blue', 'yellow', 'pink', 'cyan', 'white')
"""
```

### 4.2 巡线传感器

```python
def xunxian() -> List[bool]
"""
获取四路巡线传感器状态

返回:
    [左外, 左内, 右内, 右外] 四个布尔值
    True表示检测到黑线, False表示白色

示例:
    status = xunxian()
    # [False, True, True, False] -> 在黑线上
    # [True, False, False, False] -> 偏左
    # [False, False, False, True] -> 偏右
"""
```

```python
def xunxian_zhong() -> bool
"""
判断是否在黑线中央（两路中间传感器检测到）

返回:
    True: 在黑线上, False: 偏离黑线
"""
```

### 4.3 电池检测

```python
def dianchi() -> float
"""
获取电池电量

返回:
    电池电压 (V), 范围: 6.5-8.4V
    低于7.0V建议充电
"""
```

---

## 5. 视觉API

### 5.1 颜色识别

```python
def shibie_yanse() -> Optional[str]
"""
识别当前画面中的颜色

返回:
    颜色名称 ('red', 'green', 'blue', 'yellow')
    未识别到返回 None
"""
```

```python
def xunzhao_yanse(target_color: str) -> Optional[dict]
"""
在画面中查找指定颜色

参数:
    target_color: 目标颜色 ('red', 'green', 'blue', 'yellow')

返回:
    {
        'found': bool,        # 是否找到
        'x': int,            # 画面X坐标 (0-320)
        'y': int,            # 画面Y坐标 (0-240)
        'size': int          # 色块大小 (像素)
    }
    未找到返回 None
"""
```

### 5.2 颜色追踪

```python
def genzong_yanse(target_color: str, speed: int = 50) -> None
"""
追踪指定颜色（持续执行，直到调用停止）

参数:
    target_color: 目标颜色 ('red', 'green', 'blue', 'yellow')
    speed: 移动速度 (0-100), 默认50

注意:
    此函数会阻塞执行，直到丢失目标或手动停止
"""
```

```python
def ting_genzong() -> None
"""
停止颜色追踪
"""
```

### 5.3 视觉巡线

```python
def shijue_xunxian(speed: int = 40) -> None
"""
基于视觉的巡线行驶

参数:
    speed: 行驶速度 (0-100), 默认40

注意:
    此函数会阻塞执行，直到丢失线条或手动停止
"""
```

```python
def ting_xunxian() -> None
"""
停止视觉巡线
"""
```

---

## 6. 输出控制API

### 6.1 LED灯

```python
def led(color: str) -> None
"""
设置RGB LED颜色

参数:
    color: 颜色 ('red', 'green', 'blue', 'yellow', 'pink', 'cyan', 'white', 'off')
"""
```

```python
def led_rgb(r: int, g: int, b: int) -> None
"""
设置RGB LED自定义颜色

参数:
    r: 红色值 (0-255)
    g: 绿色值 (0-255)
    b: 蓝色值 (0-255)
"""
```

### 6.2 蜂鸣器

```python
def fengmingqi(state: bool) -> None
"""
控制蜂鸣器

参数:
    state: True=开启, False=关闭
"""
```

```python
def fengmingqi_shi(duration: float) -> None
"""
蜂鸣器响指定时间

参数:
    duration: 响声持续时间 (秒)
"""
```

---

## 7. 流程控制API

### 7.1 等待

```python
def dengdai(seconds: float) -> None
"""
等待指定时间

参数:
    seconds: 等待时间 (秒), 可以是小数

示例:
    dengdai(2.5)  # 等待2.5秒
"""
```

### 7.2 循环控制

以下由Blockly的逻辑积木实现，不需要单独API:
- `重复执行` -> Python `for/while`
- `条件判断` -> Python `if/else`
- `重复次数` -> Python `for i in range()`

---

## 8. 高级功能API

### 8.1 避障

```python
func bizhang(speed: int = 40) -> None
"""
智能避障行驶

参数:
    speed: 行驶速度 (0-100), 默认40

功能:
    前方检测到障碍物时自动转向避开
"""
```

### 8.2 组合动作

```python
def fangxing() -> None
"""
方形路径行驶
"""
```

```python
def yuanxing(radius: int = 30) -> None
"""
圆形路径行驶

参数:
    radius: 圆形半径 (cm), 默认30
"""
```

---

## 9. 常量定义

```python
# 颜色常量
COLOR_RED = 'red'
COLOR_GREEN = 'green'
COLOR_BLUE = 'blue'
COLOR_YELLOW = 'yellow'
COLOR_WHITE = 'white'
COLOR_OFF = 'off'

# 方向常量
DIR_FORWARD = 0
DIR_RIGHT = 90
DIR_BACKWARD = 180
DIR_LEFT = 270

# 速度常量
SPEED_STOP = 0
SPEED_SLOW = 30
SPEED_MEDIUM = 50
SPEED_FAST = 70
SPEED_MAX = 100
```

---

## 10. 错误处理

### 10.1 异常类型

```python
class HardwareError(Exception):
    """硬件错误基类"""
    pass

class MotorError(HardwareError):
    """电机错误"""
    pass

class SensorError(HardwareError):
    """传感器错误"""
    pass

class CameraError(HardwareError):
    """摄像头错误"""
    pass

class ParameterError(HardwareError):
    """参数错误（超出范围）"""
    pass
```

### 10.2 错误处理示例

```python
# 在生成的代码中自动添加错误处理
try:
    qianjin(80)
except ParameterError as e:
    print(f"参数错误: {e}")
except HardwareError as e:
    print(f"硬件错误: {e}")
```

---

## 11. API与积木块映射

| 积木块 | API函数 | 类别 |
|--------|---------|------|
| 前进 | qianjin(speed) | 运动 |
| 后退 | houtui(speed) | 运动 |
| 左平移 | zuopingyi(speed) | 运动 |
| 右平移 | youpingyi(speed) | 运动 |
| 左旋转 | fxuanzhuan(speed) | 运动 |
| 右旋转 | xuanzhuan(speed) | 运动 |
| 停止 | tingzhi() | 运动 |
| 云台向上 | yuntai_shang(angle) | 运动 |
| 云台向下 | yuntai_xia(angle) | 运动 |
| 云台向左 | yuntai_zuo(angle) | 运动 |
| 云台向右 | yuntai_you(angle) | 运动 |
| 云台复位 | yuntai_fuwei() | 运动 |
| 获取距离 | heshengbo() | 传感器 |
| 巡线状态 | xunxian() | 传感器 |
| 检测颜色 | shibie_yanse() | 视觉 |
| 追踪颜色 | genzong_yanse(color, speed) | 视觉 |
| LED灯 | led(color) | 输出 |
| 蜂鸣器 | fengmingqi(state) | 输出 |
| 等待 | dengdai(seconds) | 流程 |

---

*文档版本: v1.0*
*创建日期: 2026-02-19*
