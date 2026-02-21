# 代码生成器架构设计

## 1. 概述

代码生成器负责将Blockly工作区中的积木块模型转换为可执行的Python代码。本文档描述代码生成器的架构、实现细节和扩展机制。

---

## 2. 架构设计

### 2.1 代码生成流程

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Blockly工作区                                 │
│                    (Workspace/Block Tree)                            │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                        代码生成器 (Generator)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  顺序生成器  │  │  作用域管理  │  │  格式化器    │              │
│  │ (Sequential) │  │  (Scoping)   │  │ (Formatter)  │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                        Python代码输出                                 │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │  1. 导入语句                                                      │ │
│  │  2. 初始化代码                                                    │ │
│  │  3. 主逻辑代码                                                    │ │
│  │  4. 清理代码                                                      │ │
│  └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 核心组件

```javascript
// 代码生成器主结构
const pythonGenerator = new Blockly.Generator('Python');

// 配置
pythonGenerator.ORDER_ATOMIC = 0;
pythonGenerator.ORDER_NONE = 0;

// 优先级定义（用于括号处理）
pythonGenerator.ORDER_MEMBER = 1;
pythonGenerator.ORDER_FUNCTION_CALL = 2;
pythonGenerator.ORDER_EXPONENTIATION = 3;
// ... 其他优先级
```

---

## 3. 代码模板设计

### 3.1 完整代码模板

```python
# ===== 自动生成的代码 - 请勿手动修改 =====
# 导入必要的模块
from backend.hal.motion_controller import MotionController
from backend.hal.sensor_controller import SensorController
from backend.hal.vision_controller import VisionController
import time

# 初始化控制器
motion = MotionController()
sensor = SensorController()
vision = VisionController()

# 全局标志位（用于停止控制）
_running = True

# ===== 用户代码开始 =====
{{USER_CODE}}

# ===== 用户代码结束 =====

# 清理资源
motion.stop()
```

### 3.2 积木块代码模板

每个积木块对应一个代码生成函数：

```javascript
// 运动积木示例
pythonGenerator.forBlock['motion_forward'] = function(block, generator) {
    // 获取参数
    const speed = block.getFieldValue('SPEED') || '50';

    // 生成代码
    const code = `motion.qianjin(${speed})\n`;

    return code;
};

// 传感器积木示例（返回值）
pythonGenerator.forBlock['sensor_ultrasonic'] = function(block, generator) {
    const code = 'sensor.heshengbo()';
    return [code, pythonGenerator.ORDER_MEMBER];
};

// 循环积木示例
pythonGenerator.forBlock['controls_repeat_ext'] = function(block, generator) {
    const repeats = String(
        generator.valueToCode(block, 'TIMES', pythonGenerator.ORDER_NONE) || '0'
    );
    const branch = generator.statementToCode(block, 'DO');
    branch = pythonGenerator.addLoopTrap(branch, block);

    return `for _ in range(${repeats}):\n${branch}\n`;
};
```

---

## 4. 作用域管理

### 4.1 变量声明

```javascript
// 变量积木
pythonGenerator.forBlock['variables_get'] = function(block, generator) {
    const varName = generator.getVariableName(block.getFieldValue('VAR'));
    return [varName, pythonGenerator.ORDER_ATOMIC];
};

pythonGenerator.forBlock['variables_set'] = function(block, generator) {
    const varName = generator.getVariableName(block.getFieldValue('VAR'));
    const value = generator.valueToCode(block, 'VALUE', pythonGenerator.ORDER_NONE) || '0';
    return `${varName} = ${value}\n`;
};
```

### 4.2 循环变量

```javascript
// 自动生成唯一的循环变量名
pythonGenerator.variableDB_ = new Blockly.Names('');

// 在循环中使用
const loopVar = pythonGenerator.variableDB_.getDistinctName(
    'count',
    Blockly.Variables.NAME_TYPE
);
```

---

## 5. 优先级与括号处理

### 5.1 优先级定义

```javascript
pythonGenerator.ORDER_ATOMIC = 0;           // 0 = ""
pythonGenerator.ORDER_NONE = 0;             // 0 = "..."
pythonGenerator.ORDER_MEMBER = 1;           // . []
pythonGenerator.ORDER_FUNCTION_CALL = 2;    // ()
pythonGenerator.ORDER_EXPONENTIATION = 3;   // **
pythonGenerator.ORDER_UNARY_SIGN = 4;       // + -
pythonGenerator.ORDER_BITWISE_NOT = 5;      // ~
pythonGenerator.ORDER_MULTIPLICATIVE = 6;   // * / // %
pythonGenerator.ORDER_ADDITIVE = 7;         // + -
pythonGenerator.ORDER_BITWISE_SHIFT = 8;    // << >>
pythonGenerator.ORDER_BITWISE_AND = 9;      // &
pythonGenerator.ORDER_BITWISE_XOR = 10;     // ^
pythonGenerator.ORDER_BITWISE_OR = 11;      // |
pythonGenerator.ORDER_COMPARISON = 12;      // == != > < >= <=
pythonGenerator.ORDER_LOGICAL_NOT = 13;     // not
pythonGenerator.ORDER_LOGICAL_AND = 14;     // and
pythonGenerator.ORDER_LOGICAL_OR = 15;      // or
pythonGenerator.ORDER_CONDITIONAL = 16;     // if else
pythonGenerator.ORDER_ASSIGNMENT = 17;      // = += -=
pythonGenerator.ORDER_LAMBDA = 18;          // lambda
pythonGenerator.ORDER_COMMA = 19;           // ,
pythonGenerator.ORDER_AT = 20;              // @
```

### 5.2 括号自动添加

```javascript
// 根据优先级自动添加括号
const value = generator.valueToCode(
    block,
    'VALUE',
    pythonGenerator.ORDER_MULTIPLICATIVE
);
```

---

## 6. 注释与文档

### 6.1 自动注释

```javascript
// 为生成的代码添加注释
pythonGenerator.addComment = function(code, comment) {
    return `# ${comment}\n${code}`;
};

// 为循环添加注释
pythonGenerator.forBlock['controls_repeat_ext'] = function(block, generator) {
    // ...
    const comment = Blockly.Msg.CONTROLS_REPEAT_TITLE_REPEAT +
                    ' ' + repeats + ' 次';
    return `# ${comment}\n${code}`;
};
```

### 6.2 代码说明

```python
# 在生成的代码中自动添加说明
# [运动控制] 前进 - 速度: 70
motion.qianjin(70)

# [传感器] 获取超声波距离
distance = sensor.heshengbo()

# [逻辑判断] 如果距离小于200mm
if distance < 200:
    # [运动控制] 停止
    motion.tingzhi()
```

---

## 7. 错误处理

### 7.1 参数验证

```javascript
// 生成时进行参数验证
pythonGenerator.forBlock['motion_forward'] = function(block, generator) {
    let speed = block.getFieldValue('SPEED');

    // 参数范围检查
    if (speed < 0 || speed > 100) {
        throw new Error('速度必须在 0-100 之间');
    }

    return `motion.qianjin(${speed})\n`;
};
```

### 7.2 运行时错误处理

```python
# 在生成的代码中添加错误处理
try:
    motion.qianjin(80)
except ParameterError as e:
    print(f"参数错误: {e}")
except HardwareError as e:
    print(f"硬件错误: {e}")
finally:
    motion.stop()
```

---

## 8. 实时代码预览

### 8.1 监听工作区变化

```javascript
// 监听工作区变化，实时更新代码预览
function updateCodePreview() {
    const code = pythonGenerator.workspaceToCode(workspace);
    document.getElementById('code-preview').textContent = code;
}

// 添加监听器
workspace.addChangeListener(updateCodePreview);
```

### 8.2 防抖处理

```javascript
// 防抖处理，避免频繁生成代码
let updateTimeout;
function debouncedUpdate() {
    clearTimeout(updateTimeout);
    updateTimeout = setTimeout(updateCodePreview, 300);
}

workspace.addChangeListener(debouncedUpdate);
```

---

## 9. 扩展机制

### 9.1 添加新积木的代码生成

```javascript
// 1. 定义积木块
Blockly.Blocks['my_custom_block'] = {
    init: function() {
        this.appendValueInput('PARAM')
            .setCheck('Number')
            .appendField('自定义积木');
        this.setPreviousStatement(true, null);
        this.setNextStatement(true, null);
        this.setColour(230);
    }
};

// 2. 定义代码生成器
pythonGenerator.forBlock['my_custom_block'] = function(block, generator) {
    const param = generator.valueToCode(block, 'PARAM', pythonGenerator.ORDER_NONE);
    return `my_function(${param})\n`;
};

// 3. 添加中文提示
Blockly.Msg['MY_CUSTOM_BLOCK'] = '自定义积木';
```

### 9.2 自定义代码片段

```javascript
// 添加自定义初始化代码
pythonGenerator.init = function(workspace) {
    return `# 自定义初始化\nimport custom_module\n`;
};

// 添加自定义清理代码
pythonGenerator.finish = function(code) {
    return code + '\n# 自定义清理\ncustom_module.cleanup()';
};
```

---

## 10. 代码格式化

### 10.1 缩进处理

```javascript
// Python使用4空格缩进
pythonGenerator.INDENT = '    ';

// 块语句自动缩进
function indentLines(code, indent) {
    return code.split('\n').map(line => {
        return line ? indent + line : '';
    }).join('\n');
}
```

### 10.2 空行处理

```javascript
// 在不同积木块之间添加空行
pythonGenerator.snippetLines_ = function(code) {
    return code.split('\n').map(line => line.trim()).filter(Boolean);
};
```

---

## 11. 性能优化

### 11.1 缓存机制

```javascript
// 缓存已生成的代码
const codeCache = new Map();

function getCachedCode(blockId) {
    if (codeCache.has(blockId)) {
        return codeCache.get(blockId);
    }
    const code = generateCode(blockId);
    codeCache.set(blockId, code);
    return code;
}

// 工作区变化时清除缓存
workspace.addChangeListener(() => {
    codeCache.clear();
});
```

### 11.2 增量更新

```javascript
// 只更新变化的积木块
function updateChangedBlocks(changedBlocks) {
    changedBlocks.forEach(block => {
        const code = generateCode(block);
        updateCodeDisplay(block.id, code);
    });
}
```

---

## 12. 测试支持

### 12.1 单元测试

```javascript
// 测试代码生成器
describe('Python Generator', () => {
    it('should generate forward motion code', () => {
        const xml = '<block type="motion_forward"><field name="SPEED">50</field></block>';
        workspace.clear();
        Blockly.Xml.domToWorkspace(Blockly.utils.xml.textToDom(xml), workspace);

        const code = pythonGenerator.workspaceToCode(workspace);
        expect(code).toContain('motion.qianjin(50)');
    });
});
```

### 12.2 快照测试

```javascript
// 快照测试，确保代码生成一致
describe('Code Snapshots', () => {
    it('matches snapshot for forward block', () => {
        const code = generateCodeFromXml('motion_forward');
        expect(code).toMatchSnapshot();
    });
});
```

---

## 13. 调试支持

### 13.1 生成时调试

```javascript
// 启用调试模式
const DEBUG = true;

pythonGenerator.forBlock['motion_forward'] = function(block, generator) {
    const speed = block.getFieldValue('SPEED');
    const code = `motion.qianjin(${speed})\n`;

    if (DEBUG) {
        console.log(`[DEBUG] Generated: ${code}`);
    }

    return code;
};
```

### 13.2 错误位置映射

```javascript
// 映射代码行号到积木块
const sourceMap = new Map();

function addSourceMap(code, blockId) {
    const lines = code.split('\n');
    lines.forEach((line, index) => {
        sourceMap.set(index, blockId);
    });
}
```

---

## 14. 积木块到代码映射表

| 积木块类型 | 生成代码示例 |
|-----------|-------------|
| `motion_forward` | `motion.qianjin(speed)` |
| `sensor_ultrasonic` | `sensor.heshengbo()` |
| `logic_if` | `if condition:\n    ...` |
| `controls_repeat` | `for _ in range(times):\n    ...` |
| `color_detect` | `vision.shibie_yanse()` |

---

*文档版本: v1.0*
*创建日期: 2026-02-19*
