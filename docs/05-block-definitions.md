# 积木块定义规范

## 1. 概述

本文档定义了Blockly积木块的视觉规范、配置标准和设计指南，确保所有积木块风格统一、易于6岁儿童理解。

---

## 2. 积木块分类

### 2.1 类别与配色

| 类别 | 名称 | 颜色 | 色值 | 图标 |
|------|------|------|------|------|
| **运动** | 运动控制 | 蓝色 | #4C97FF | 🔵 |
| **传感** | 传感器 | 绿色 | #99CA49 | 🟢 |
| **视觉** | 视觉功能 | 紫色 | #9966FF | 🟣 |
| **逻辑** | 逻辑控制 | 橙色 | #FFAB19 | 🟠 |
| **输出** | 输出控制 | 黄色 | #FFCF00 | 🟡 |
| **高级** | 高级功能 | 红色 | #FF6680 | 🔴 |

### 2.2 工具箱结构

```javascript
const toolbox = {
    contents: [
        {
            kind: 'category',
            name: '运动',
            colour: '#4C97FF',
            contents: [
                { kind: 'block', type: 'motion_forward' },
                { kind: 'block', type: 'motion_backward' },
                { kind: 'block', type: 'motion_left' },
                { kind: 'block', type: 'motion_right' },
                { kind: 'block', type: 'motion_rotate_left' },
                { kind: 'block', type: 'motion_rotate_right' },
                { kind: 'block', type: 'motion_stop' },
                { kind: 'sep' },
                { kind: 'block', type: 'gimbal_up' },
                { kind: 'block', type: 'gimbal_down' },
                { kind: 'block', type: 'gimbal_left' },
                { kind: 'block', type: 'gimbal_right' },
                { kind: 'block', type: 'gimbal_reset' },
            ]
        },
        {
            kind: 'category',
            name: '传感',
            colour: '#99CA49',
            contents: [
                { kind: 'block', type: 'sensor_ultrasonic' },
                { kind: 'block', type: 'sensor_line_follow' },
                { kind: 'block', type: 'sensor_battery' },
            ]
        },
        // ... 其他类别
    ]
};
```

---

## 3. 积木块类型定义

### 3.1 语句积木 (Statement Blocks)

可连接的指令积木，有上连接和下连接。

#### 示例：前进积木

```javascript
Blockly.Blocks['motion_forward'] = {
    init: function() {
        // 积木标签
        this.appendDummyInput()
            .appendField('前进')
            .appendField(new Blockly.FieldDropdown([
                ['慢速', '30'],
                ['中速', '50'],
                ['快速', '70'],
                ['最快', '100']
            ]), 'SPEED');

        // 连接点
        this.setPreviousStatement(true, null);    // 上连接
        this.setNextStatement(true, null);        // 下连接

        // 样式
        this.setColour(230);                      // 蓝色 Hue=230
        this.setTooltip('让小车向前移动');
        this.setHelpUrl('');                      // 帮助链接
    }
};
```

**视觉效果:**
```
┌─────────────────────▼
│   前进  中速 ▼      │
└─────────────────────▶
```

### 3.2 返回值积木 (Value Blocks)

返回数值或状态的积木，没有连接点，可以嵌入其他积木中。

#### 示例：超声波积木

```javascript
Blockly.Blocks['sensor_ultrasonic'] = {
    init: function() {
        // 积木标签
        this.appendDummyInput()
            .appendField('超声波距离');

        // 输出类型
        this.setOutput(true, 'Number');

        // 样式
        this.setColour(120);                      // 绿色 Hue=120
        this.setTooltip('获取前方障碍物的距离（毫米）');
    }
};
```

**视觉效果:**
```
┌─────────────────┐
│ 超声波距离  ◀   │
└─────────────────┘
```

### 3.3 参数输入积木

需要用户输入数值的积木。

#### 示例：等待积木

```javascript
Blockly.Blocks['delay_wait'] = {
    init: function() {
        // 数值输入
        this.appendValueInput('SECONDS')
            .setCheck('Number')
            .appendField('等待');

        this.appendDummyInput()
            .appendField('秒');

        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(330);                      // 橙色 Hue=330
    }
};
```

**视觉效果:**
```
┌────────────────────▼
│   等待 [  1  ] 秒   │
└────────────────────▶
```

### 3.4 条件积木

需要条件判断的积木。

#### 示例：如果积木

```javascript
Blockly.Blocks['logic_if'] = {
    init: function() {
        // 条件输入
        this.appendValueInput('CONDITION')
            .setCheck('Boolean')
            .appendField('如果');

        // 执行分支
        this.appendStatementInput('DO')
            .appendField('就');

        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(330);
    }
};
```

**视觉效果:**
```
┌────────────────────▼
│   如果 <条件>       │
│     ┌──────────────┤
│     │  (执行内容)  │
│     └──────────────▶
└────────────────────▶
```

### 3.5 循环积木

重复执行的积木。

#### 示例：重复积木

```javascript
Blockly.Blocks['controls_repeat'] = {
    init: function() {
        // 次数输入
        this.appendValueInput('TIMES')
            .setCheck('Number')
            .appendField('重复执行');

        // 循环体
        this.appendStatementInput('DO')
            .appendField('次');

        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(330);
    }
};
```

**视觉效果:**
```
┌──────────────────────▼
│   重复执行 [ 3 ] 次   │
│     ┌────────────────┤
│     │  (循环内容)    │
│     └────────────────▶
└──────────────────────▶
```

---

## 4. 积木块设计规范

### 4.1 尺寸规范

| 元素 | 最小尺寸 | 推荐尺寸 |
|------|----------|----------|
| 积木高度 | 24px | 36px |
| 积木边距 | 8px | 12px |
| 文字大小 | 14px | 16px |
| 图标大小 | 24px | 32px |
| 输入框宽度 | 40px | 60px |

### 4.2 图标设计

所有积木块使用SVG矢量图标，保持清晰度。

```javascript
// 图标定义
const motionIcons = {
    forward: '<path d="M12 4l-8 8h16z"/>',
    backward: '<path d="M12 20l8-8h-16z"/>',
    left: '<path d="M4 12l8-8v16z"/>',
    right: '<path d="M20 12l-8-8v16z"/>'
};

// 使用图标
this.appendDummyInput()
    .appendField(new Blockly.FieldImage(
        'data:image/svg+xml;base64,' + btoa(motionIcons.forward),
        24, 24, '前进'
    ));
```

### 4.3 文字规范

- **字体**: 使用圆体或手写风格字体，更亲切
- **大小**: 16px 正文，14px 辅助文字
- **语言**: 全中文，无英文依赖
- **简洁**: 每个积木标签不超过8个字

```css
/* 自定义字体 */
@font-face {
    font-family: 'BlockyFont';
    src: url('/assets/fonts/blocky-font.woff2');
}

.blocklyText {
    font-family: 'BlockyFont', 'Microsoft YaHei', sans-serif;
    font-size: 16px;
    font-weight: 500;
}
```

---

## 5. 完整积木块定义列表

### 5.1 运动控制积木

| 积木类型 | 标签 | 参数 | 类型 |
|---------|------|------|------|
| `motion_forward` | 前进 | 速度(下拉) | 语句 |
| `motion_backward` | 后退 | 速度(下拉) | 语句 |
| `motion_left` | 左平移 | 速度(下拉) | 语句 |
| `motion_right` | 右平移 | 速度(下拉) | 语句 |
| `motion_rotate_left` | 左转 | 速度(下拉) | 语句 |
| `motion_rotate_right` | 右转 | 速度(下拉) | 语句 |
| `motion_stop` | 停止 | 无 | 语句 |
| `gimbal_up` | 云台向上 | 角度(下拉) | 语句 |
| `gimbal_down` | 云台向下 | 角度(下拉) | 语句 |
| `gimbal_left` | 云台向左 | 角度(下拉) | 语句 |
| `gimbal_right` | 云台向右 | 角度(下拉) | 语句 |
| `gimbal_reset` | 云台复位 | 无 | 语句 |

### 5.2 传感器积木

| 积木类型 | 标签 | 返回值 | 类型 |
|---------|------|--------|------|
| `sensor_ultrasonic` | 超声波距离 | 数值(毫米) | 返回值 |
| `sensor_line_status` | 巡线状态 | 数组[4] | 返回值 |
| `sensor_battery` | 电池电量 | 数值(伏特) | 返回值 |

### 5.3 视觉积木

| 积木类型 | 标签 | 参数 | 类型 |
|---------|------|------|------|
| `vision_detect_color` | 检测颜色 | 无 | 返回值 |
| `vision_find_color` | 寻找颜色 | 颜色(下拉) | 返回值 |
| `vision_track_color` | 追踪颜色 | 颜色, 速度 | 语句 |
| `vision_track_stop` | 停止追踪 | 无 | 语句 |

### 5.4 输出积木

| 积木类型 | 标签 | 参数 | 类型 |
|---------|------|------|------|
| `output_led` | LED灯 | 颜色(下拉) | 语句 |
| `output_led_rgb` | LED自定义 | R,G,B(输入) | 语句 |
| `output_buzzer` | 蜂鸣器 | 开关(下拉) | 语句 |
| `output_buzzer_time` | 蜂鸣器响 | 时间(输入) | 语句 |

### 5.5 逻辑积木

| 积木类型 | 标签 | 参数 | 类型 |
|---------|------|------|------|
| `logic_if` | 如果 | 条件, 分支 | 语句 |
| `logic_if_else` | 如果-否则 | 条件, 分支 | 语句 |
| `logic_compare` | 比较 | 操作符, 值 | 返回值 |
| `logic_operation` | 逻辑运算 | 操作符, 值 | 返回值 |
| `controls_repeat` | 重复 | 次数, 循环体 | 语句 |
| `controls_while` | 当循环 | 条件, 循环体 | 语句 |
| `delay_wait` | 等待 | 时间(秒) | 语句 |

---

## 6. 积木块配置示例

### 6.1 运动积木完整定义

```javascript
// 前进积木
Blockly.Blocks['motion_forward'] = {
    init: function() {
        // 下拉选项
        const dropdown = new Blockly.FieldDropdown([
            ['🐢 慢速', '30'],
            ['🚶 中速', '50'],
            ['🏃 快速', '70'],
            ['🚀 最快', '100']
        ]);

        this.appendDummyInput()
            .appendField('⬆️')
            .appendField('前进')
            .appendField(dropdown, 'SPEED');

        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(230);
        this.setTooltip('让小车向前移动');
    }
};

// 代码生成
pythonGenerator.forBlock['motion_forward'] = function(block, generator) {
    const speed = block.getFieldValue('SPEED');
    return `motion.qianjin(${speed})\n`;
};
```

### 6.2 传感器积木完整定义

```javascript
// 超声波积木
Blockly.Blocks['sensor_ultrasonic'] = {
    init: function() {
        this.appendDummyInput()
            .appendField('📡')
            .appendField('超声波距离');

        this.setOutput(true, 'Number');
        this.setColour(120);
        this.setTooltip('获取前方障碍物的距离（毫米）\n范围: 20-4000mm');
    }
};

// 代码生成
pythonGenerator.forBlock['sensor_ultrasonic'] = function(block, generator) {
    const code = 'sensor.heshengbo()';
    return [code, pythonGenerator.ORDER_MEMBER];
};
```

### 6.3 循环积木完整定义

```javascript
// 重复积木
Blockly.Blocks['controls_repeat'] = {
    init: function() {
        this.appendValueInput('TIMES')
            .setCheck('Number')
            .appendField('🔄')
            .appendField('重复执行');

        this.appendStatementInput('DO')
            .appendField('次');

        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(330);
        this.setTooltip('重复执行里面的积木块');
    }
};

// 代码生成
pythonGenerator.forBlock['controls_repeat'] = function(block, generator) {
    const repeats = generator.valueToCode(block, 'TIMES', pythonGenerator.ORDER_NONE) || '0';
    const branch = generator.statementToCode(block, 'DO');
    branch = pythonGenerator.addLoopTrap(branch, block);

    return `for _ in range(${repeats}):\n${branch}\n`;
};
```

---

## 7. 积木块模板

### 7.1 语句积木模板

```javascript
// 模板：带速度参数的语句积木
function createMotionBlock(blockName, label, color, apiName) {
    Blockly.Blocks[blockName] = {
        init: function() {
            const dropdown = new Blockly.FieldDropdown([
                ['慢速', '30'],
                ['中速', '50'],
                ['快速', '70']
            ]);

            this.appendDummyInput()
                .appendField(label)
                .appendField(dropdown, 'SPEED');

            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(color);
        }
    };

    pythonGenerator.forBlock[blockName] = function(block, generator) {
        const speed = block.getFieldValue('SPEED');
        return `motion.${apiName}(${speed})\n`;
    };
}

// 使用模板
createMotionBlock('motion_forward', '前进', 230, 'qianjin');
createMotionBlock('motion_backward', '后退', 230, 'houtui');
```

### 7.2 返回值积木模板

```javascript
// 模板：无参数返回值积木
function createSensorBlock(blockName, label, color, apiName) {
    Blockly.Blocks[blockName] = {
        init: function() {
            this.appendDummyInput()
                .appendField(label);

            this.setOutput(true, 'Number');
            this.setColour(color);
        }
    };

    pythonGenerator.forBlock[blockName] = function(block, generator) {
        const code = `sensor.${apiName}()`;
        return [code, pythonGenerator.ORDER_MEMBER];
    };
}

// 使用模板
createSensorBlock('sensor_ultrasonic', '📡 超声波距离', 120, 'heshengbo');
```

---

## 8. 本地化配置

### 8.1 中文消息定义

```javascript
// 积木块中文消息
Blockly.Msg['MOTION_FORWARD'] = '前进';
Blockly.Msg['MOTION_BACKWARD'] = '后退';
Blockly.Msg['SENSOR_ULTRASONIC'] = '超声波距离';
Blockly.Msg['CONTROLS_REPEAT_TITLE'] = '重复执行 %1 次';
Blockly.Msg['CONTROLS_IF_TOOLTIP_1'] = '如果条件为真，就执行后面的积木';
Blockly.Msg['LOGIC_COMPARE_TOOLTIP'] = '比较两个值的大小';
```

### 8.2 动态加载语言

```javascript
// 设置语言
Blockly.setLocale('zh-hans');

// 或者自定义语言文件
import * as zh from './locales/zh.js';
Blockly.setLocale(zh);
```

---

## 9. 样式自定义

### 9.1 自定义CSS

```css
/* 积木块样式 */
.blocklyBlockCanvas .blocklyDraggable {
    cursor: grab;
}

.blocklyBlockCanvas .blocklyDraggable:active {
    cursor: grabbing;
}

/* 积木块阴影 */
.blocklyBlockCanvas .blocklyDraggable > .blocklyPath {
    filter: drop-shadow(2px 2px 4px rgba(0,0,0,0.2));
}

/* 选中效果 */
.blocklySelected > .blocklyPath {
    stroke: #fff !important;
    stroke-width: 3px;
}
```

### 9.2 工作区样式

```javascript
// 工作区配置
const workspace = Blockly.inject('blocklyDiv', {
    toolbox: toolbox,
    theme: customTheme,
    scrollbars: true,
    trashcan: true,
    zoom: {
        controls: true,
        wheel: true,
        startScale: 1.0,
        maxScale: 3,
        minScale: 0.3,
        scaleSpeed: 1.2
    },
    grid: {
        spacing: 20,
        length: 3,
        colour: '#ccc',
        snap: true
    }
});
```

---

## 10. 积木块验证

### 10.1 类型检查

```javascript
// 确保只有数值积木可以连接到速度输入
this.appendValueInput('SPEED')
    .setCheck('Number');
```

### 10.2 参数验证

```javascript
// 生成时验证参数范围
pythonGenerator.forBlock['motion_forward'] = function(block, generator) {
    let speed = block.getFieldValue('SPEED');

    // 验证范围
    speed = Math.max(0, Math.min(100, speed));

    return `motion.qianjin(${speed})\n`;
};
```

---

*文档版本: v1.0*
*创建日期: 2026-02-19*
