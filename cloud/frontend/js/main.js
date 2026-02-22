// ===== 导入课程数据 =====
import { COURSES, CourseManager } from './courses.js';
// ===== 导入语言管理器 =====
import { languageManager, refreshTranslations, t } from './pinyin.js';

// ===== 全局配置 =====
const CONFIG = {
    // WebSocket连接URL - 连接到公网网关（使用原生WebSocket协议）
    wsUrl: 'wss://lanser.fun/block/ws/gateway',
    reconnectInterval: 5000,
};

// ===== 全局状态 =====
const state = {
    ws: null,
    connected: false,
    vehicleId: null,
    vehicles: [],
    executionId: null,
    workspace: null,
    codeGenerator: null,
    // 课程相关状态
    courseManager: new CourseManager(),
    currentCourse: null,
};

// ===== 积木分类翻译 =====
const CATEGORY_TRANSLATIONS = {
    chinese: {
        motion: '运动',
        gimbal: '云台',
        sensor: '传感',
        vision: '视觉',
        variables: '变量',
        math: '数学',
        logic: '逻辑',
        text: '文本',
        lists: '列表',
        functions: '函数',
    },
    pinyin: {
        motion: 'yùn dòng',
        gimbal: 'yún tái',
        sensor: 'chuán gǎn',
        vision: 'shì jué',
        variables: 'biàn liàng',
        math: 'shù xué',
        logic: 'luó ji',
        text: 'wén běn',
        lists: 'liè biǎo',
        functions: 'hán shù',
    }
};

// ===== 积木块文字翻译 =====
const BLOCK_TEXT_TRANSLATIONS = {
    chinese: {
        // 运动积木
        forward: '前进',
        backward: '后退',
        left: '左平移',
        right: '右平移',
        stop: '停止',
        turn_left: '左转',
        turn_right: '右转',
        slow: '慢速',
        medium: '中速',
        fast: '快速',
        // 云台积木
        gimbal_up: '云台向上',
        gimbal_down: '云台向下',
        gimbal_left: '云台向左',
        gimbal_right: '云台向右',
        gimbal_reset: '云台复位',
        // 传感积木
        ultrasonic: '超声波距离',
        line_sensor: '巡线传感器',
        // 视觉积木
        detect_color: '检测颜色',
        // 逻辑积木
        if_do: '如果',
        then_do: '就',
        repeat_times: '重复执行',
        times: '次',
        wait: '等待',
        seconds: '秒',
        // 颜色
        red: '红色',
        green: '绿色',
        blue: '蓝色',
        yellow: '黄色',
        orange: '橙色',
        // 巡线通道
        channel_1: '第1路',
        channel_2: '第2路',
        channel_3: '第3路',
        channel_4: '第4路',
    },
    pinyin: {
        // 运动积木
        forward: 'qián jìn',
        backward: 'hòu tuì',
        left: 'zuǒ píng yí',
        right: 'yòu píng yí',
        stop: 'tíng zhǐ',
        turn_left: 'xiǎo zuǒ zhuǎn',
        turn_right: 'xiǎo yòu zhuǎn',
        slow: 'màn sù',
        medium: 'zhōng sù',
        fast: 'kuài sù',
        // 云台积木
        gimbal_up: 'yún tái xiàng shàng',
        gimbal_down: 'yún tái xiàng xià',
        gimbal_left: 'yún tái xiàng zuǒ',
        gimbal_right: 'yún tái xiàng yòu',
        gimbal_reset: 'yún tái fù wèi',
        // 传感积木
        ultrasonic: 'chāo shēng bō jù lí',
        line_sensor: 'xún xiàn chuán gǎn qì',
        // 视觉积木
        detect_color: 'jiǎn cè yán sè',
        // 逻辑积木
        if_do: 'rú guǒ',
        then_do: 'jiù',
        repeat_times: 'chóng fù zhí xíng',
        times: 'cì',
        wait: 'děng dài',
        seconds: 'miǎo',
        // 颜色
        red: 'hóng sè',
        green: 'lǜ sè',
        blue: 'lán sè',
        yellow: 'huáng sè',
        orange: 'chéng sè',
        // 巡线通道
        channel_1: 'dì 1 lù',
        channel_2: 'dì 2 lù',
        channel_3: 'dì 3 lù',
        channel_4: 'dì 4 lù',
    }
};

// 获取积木块文字翻译
function getBlockText(key) {
    const lang = languageManager.isPinyinMode ? 'pinyin' : 'chinese';
    return BLOCK_TEXT_TRANSLATIONS[lang][key] || BLOCK_TEXT_TRANSLATIONS.chinese[key] || key;
}

// ===== 获取当前语言的工具箱定义 =====
function getToolbox() {
    const lang = languageManager.isPinyinMode ? 'pinyin' : 'chinese';
    const cat = CATEGORY_TRANSLATIONS[lang];

    return {
        contents: [
            {
                kind: 'category',
                name: cat.motion,
                colour: '#4C97FF',
                contents: [
                    { kind: 'block', type: 'motion_forward' },
                    { kind: 'block', type: 'motion_backward' },
                    { kind: 'block', type: 'motion_left' },
                    { kind: 'block', type: 'motion_right' },
                    { kind: 'block', type: 'motion_turn_left' },
                    { kind: 'block', type: 'motion_turn_right' },
                    { kind: 'block', type: 'motion_stop' },
                ],
            },
            {
                kind: 'category',
                name: cat.gimbal,
                colour: '#A57C5B',
                contents: [
                    { kind: 'block', type: 'gimbal_up' },
                    { kind: 'block', type: 'gimbal_down' },
                    { kind: 'block', type: 'gimbal_left' },
                    { kind: 'block', type: 'gimbal_right' },
                    { kind: 'block', type: 'gimbal_reset' },
                ],
            },
            {
                kind: 'category',
                name: cat.sensor,
                colour: '#99CA49',
                contents: [
                    { kind: 'block', type: 'sensor_ultrasonic' },
                    { kind: 'block', type: 'sensor_line' },
                ],
            },
            {
                kind: 'category',
                name: cat.vision,
                colour: '#9E5BE9',
                contents: [
                    { kind: 'block', type: 'vision_detect_color' },
                ],
            },
            {
                kind: 'category',
                name: cat.variables,
                colour: '#A55B80',
                custom: 'VARIABLE',
            },
            {
                kind: 'category',
                name: cat.math,
                colour: '#59C059',
                contents: [
                    { kind: 'block', type: 'math_number' },
                    { kind: 'block', type: 'math_arithmetic' },
                    { kind: 'block', type: 'math_single' },
                    { kind: 'block', type: 'math_constant' },
                    { kind: 'block', type: 'math_modulo' },
                    { kind: 'block', type: 'math_round' },
                    { kind: 'block', type: 'math_random_int' },
                ],
            },
            {
                kind: 'category',
                name: cat.logic,
                colour: '#FFAB19',
                contents: [
                    { kind: 'block', type: 'controls_if' },
                    { kind: 'block', type: 'logic_compare' },
                    { kind: 'block', type: 'logic_operation' },
                    { kind: 'block', type: 'logic_boolean' },
                    { kind: 'block', type: 'controls_repeat_ext' },
                    { kind: 'block', type: 'controls_for' },
                    { kind: 'block', type: 'controls_whileUntil' },
                    { kind: 'block', type: 'delay_wait' },
                ],
            },
            {
                kind: 'category',
                name: cat.text,
                colour: '#9966FF',
                contents: [
                    { kind: 'block', type: 'text' },
                    { kind: 'block', type: 'text_join' },
                    { kind: 'block', type: 'text_length' },
                    { kind: 'block', type: 'text_print' },
                ],
            },
            {
                kind: 'category',
                name: cat.lists,
                colour: '#FF6680',
                contents: [
                    { kind: 'block', type: 'lists_create_with' },
                    { kind: 'block', type: 'lists_length' },
                ],
            },
            {
                kind: 'category',
                name: cat.functions,
                colour: '#FF9966',
                custom: 'PROCEDURE',
            },
        ],
    };
}

// ===== 初始化Blockly =====
function initBlockly() {
    // 创建Python代码生成器
    state.codeGenerator = new Blockly.Generator('Python');
    state.codeGenerator.ORDER_ATOMIC = 0;
    state.codeGenerator.ORDER_NONE = 0;

    // 定义缩进
    state.codeGenerator.INDENT = '    ';

    // ===== 关键：scrub_ 方法处理序列积木 =====
    // 这个方法负责将串联的积木块生成的代码连接起来
    // 如果没有这个方法，只能生成第一个积木的代码
    state.codeGenerator.scrub_ = function(block, code, opt_thisOnly) {
        const nextBlock = block.nextConnection && block.nextConnection.targetBlock();
        if (nextBlock && !opt_thisOnly) {
            // 递归生成下一个积木的代码并拼接
            const nextCode = this.blockToCode(nextBlock);
            return code + nextCode;
        }
        return code;
    };

    // 初始化工作区 - 使用动态工具箱
    const workspace = Blockly.inject('blockly-div', {
        toolbox: getToolbox(),
        scrollbars: true,
        trashcan: true,
        zoom: {
            controls: true,
            wheel: true,
            startScale: 1.0,
            maxScale: 3,
            minScale: 0.3,
            scaleSpeed: 1.2,
        },
        grid: {
            spacing: 20,
            length: 3,
            colour: '#ccc',
            snap: true,
        },
    });
    state.workspace = workspace;

    // 监听工作区变化，更新代码预览
    workspace.addChangeListener(updateCodePreview);

    console.log('Blockly初始化完成');
}

// ===== 更新代码预览 =====
function updateCodePreview() {
    if (!state.workspace || !state.codeGenerator) return;

    try {
        const code = state.codeGenerator.workspaceToCode(state.workspace);
        document.getElementById('code-preview').textContent = code || '# 生成的代码将显示在这里';
    } catch (e) {
        console.error('代码生成失败:', e);
    }
}

// ===== 定义积木块 =====
function defineBlocks() {
    // 前进积木
    Blockly.Blocks['motion_forward'] = {
        init: function() {
            this.appendDummyInput()
                .appendField('⬆️ ' + getBlockText('forward'))
                .appendField(new Blockly.FieldDropdown([
                    ['🐢 ' + getBlockText('slow'), '30'],
                    ['🚶 ' + getBlockText('medium'), '50'],
                    ['🏃 ' + getBlockText('fast'), '70'],
                ]), 'SPEED');
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(230);
        }
    };

    // 后退积木
    Blockly.Blocks['motion_backward'] = {
        init: function() {
            this.appendDummyInput()
                .appendField('⬇️ ' + getBlockText('backward'))
                .appendField(new Blockly.FieldDropdown([
                    ['🐢 ' + getBlockText('slow'), '30'],
                    ['🚶 ' + getBlockText('medium'), '50'],
                    ['🏃 ' + getBlockText('fast'), '70'],
                ]), 'SPEED');
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(230);
        }
    };

    // 左平移积木
    Blockly.Blocks['motion_left'] = {
        init: function() {
            this.appendDummyInput()
                .appendField('⬅️ ' + getBlockText('left'))
                .appendField(new Blockly.FieldDropdown([
                    ['🐢 ' + getBlockText('slow'), '30'],
                    ['🚶 ' + getBlockText('medium'), '50'],
                    ['🏃 ' + getBlockText('fast'), '70'],
                ]), 'SPEED');
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(230);
        }
    };

    // 右平移积木
    Blockly.Blocks['motion_right'] = {
        init: function() {
            this.appendDummyInput()
                .appendField('➡️ ' + getBlockText('right'))
                .appendField(new Blockly.FieldDropdown([
                    ['🐢 ' + getBlockText('slow'), '30'],
                    ['🚶 ' + getBlockText('medium'), '50'],
                    ['🏃 ' + getBlockText('fast'), '70'],
                ]), 'SPEED');
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(230);
        }
    };

    // 停止积木
    Blockly.Blocks['motion_stop'] = {
        init: function() {
            this.appendDummyInput().appendField('🛑 ' + getBlockText('stop'));
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(230);
        }
    };

    // 左转积木
    Blockly.Blocks['motion_turn_left'] = {
        init: function() {
            this.appendDummyInput()
                .appendField('↪️ ' + getBlockText('turn_left'))
                .appendField(new Blockly.FieldDropdown([
                    ['🐢 ' + getBlockText('slow'), '30'],
                    ['🚶 ' + getBlockText('medium'), '50'],
                    ['🏃 ' + getBlockText('fast'), '70'],
                ]), 'SPEED');
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(230);
        }
    };

    // 右转积木
    Blockly.Blocks['motion_turn_right'] = {
        init: function() {
            this.appendDummyInput()
                .appendField('↩️ ' + getBlockText('turn_right'))
                .appendField(new Blockly.FieldDropdown([
                    ['🐢 ' + getBlockText('slow'), '30'],
                    ['🚶 ' + getBlockText('medium'), '50'],
                    ['🏃 ' + getBlockText('fast'), '70'],
                ]), 'SPEED');
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(230);
        }
    };

    // 云台向上积木
    Blockly.Blocks['gimbal_up'] = {
        init: function() {
            this.appendDummyInput().appendField('⬆️ ' + getBlockText('gimbal_up'));
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(330);
        }
    };

    // 云台向下积木
    Blockly.Blocks['gimbal_down'] = {
        init: function() {
            this.appendDummyInput().appendField('⬇️ ' + getBlockText('gimbal_down'));
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(330);
        }
    };

    // 云台向左积木
    Blockly.Blocks['gimbal_left'] = {
        init: function() {
            this.appendDummyInput().appendField('⬅️ ' + getBlockText('gimbal_left'));
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(330);
        }
    };

    // 云台向右积木
    Blockly.Blocks['gimbal_right'] = {
        init: function() {
            this.appendDummyInput().appendField('➡️ ' + getBlockText('gimbal_right'));
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(330);
        }
    };

    // 云台复位积木
    Blockly.Blocks['gimbal_reset'] = {
        init: function() {
            this.appendDummyInput().appendField('🔄 ' + getBlockText('gimbal_reset'));
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(330);
        }
    };

    // 超声波传感器积木
    Blockly.Blocks['sensor_ultrasonic'] = {
        init: function() {
            this.appendDummyInput().appendField('📡 ' + getBlockText('ultrasonic'));
            this.setOutput(true, 'Number');
            this.setColour(120);
        }
    };

    // 巡线传感器积木
    Blockly.Blocks['sensor_line'] = {
        init: function() {
            this.appendDummyInput()
                .appendField('🔍 ' + getBlockText('line_sensor'))
                .appendField(new Blockly.FieldDropdown([
                    [getBlockText('channel_1'), '0'],
                    [getBlockText('channel_2'), '1'],
                    [getBlockText('channel_3'), '2'],
                    [getBlockText('channel_4'), '3'],
                ]), 'CHANNEL');
            this.setOutput(true, 'Boolean');
            this.setColour(120);
        }
    };

    // 颜色识别积木
    Blockly.Blocks['vision_detect_color'] = {
        init: function() {
            this.appendDummyInput()
                .appendField('🎨 ' + getBlockText('detect_color'))
                .appendField(new Blockly.FieldDropdown([
                    [getBlockText('red'), 'red'],
                    [getBlockText('green'), 'green'],
                    [getBlockText('blue'), 'blue'],
                    [getBlockText('yellow'), 'yellow'],
                    [getBlockText('orange'), 'orange'],
                ]), 'COLOR');
            this.setOutput(true, 'Boolean');
            this.setColour(210);
        }
    };

    // 如果积木
    Blockly.Blocks['controls_if'] = {
        init: function() {
            this.appendValueInput('CONDITION')
                .setCheck('Boolean')
                .appendField(getBlockText('if_do'));
            this.appendStatementInput('DO')
                .appendField(getBlockText('then_do'));
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(330);
        }
    };

    // 重复执行积木
    Blockly.Blocks['controls_repeat_ext'] = {
        init: function() {
            this.appendValueInput('TIMES')
                .setCheck('Number')
                .appendField(getBlockText('repeat_times'));
            this.appendStatementInput('DO')
                .appendField(getBlockText('times'));
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(330);
        }
    };

    // 等待积木
    Blockly.Blocks['delay_wait'] = {
        init: function() {
            this.appendValueInput('SECONDS')
                .setCheck('Number')
                .appendField(getBlockText('wait'));
            this.appendDummyInput().appendField(getBlockText('seconds'));
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(330);
        }
    };

    console.log('积木块定义完成');
}

// ===== 定义代码生成器 =====
function defineCodeGenerator() {
    // 运动积木代码生成（使用全局函数，与沙箱一致）
    state.codeGenerator.forBlock['motion_forward'] = function(block) {
        const speed = block.getFieldValue('SPEED');
        return `qianjin(${speed})\n`;
    };

    state.codeGenerator.forBlock['motion_backward'] = function(block) {
        const speed = block.getFieldValue('SPEED');
        return `houtui(${speed})\n`;
    };

    state.codeGenerator.forBlock['motion_left'] = function(block) {
        const speed = block.getFieldValue('SPEED');
        return `zuopingyi(${speed})\n`;
    };

    state.codeGenerator.forBlock['motion_right'] = function(block) {
        const speed = block.getFieldValue('SPEED');
        return `youpingyi(${speed})\n`;
    };

    state.codeGenerator.forBlock['motion_stop'] = function(block) {
        return `tingzhi()\n`;
    };

    // 左右转积木代码生成
    state.codeGenerator.forBlock['motion_turn_left'] = function(block) {
        const speed = block.getFieldValue('SPEED');
        return `xiaozuozhuan(${speed})\n`;
    };

    state.codeGenerator.forBlock['motion_turn_right'] = function(block) {
        const speed = block.getFieldValue('SPEED');
        return `xiaoyouzhuan(${speed})\n`;
    };

    // 云台积木代码生成（按设计文档命名: yuntai_*）
    state.codeGenerator.forBlock['gimbal_up'] = function(block) {
        return `yuntai_shang(30)\n`;
    };

    state.codeGenerator.forBlock['gimbal_down'] = function(block) {
        return `yuntai_xia(30)\n`;
    };

    state.codeGenerator.forBlock['gimbal_left'] = function(block) {
        return `yuntai_zuo(30)\n`;
    };

    state.codeGenerator.forBlock['gimbal_right'] = function(block) {
        return `yuntai_you(30)\n`;
    };

    state.codeGenerator.forBlock['gimbal_reset'] = function(block) {
        return `yuntai_fuwei()\n`;
    };

    // 传感器积木代码生成（使用全局函数）
    state.codeGenerator.forBlock['sensor_ultrasonic'] = function(block) {
        const code = 'heshengbo()';
        return [code, state.codeGenerator.ORDER_FUNCTION_CALL];
    };

    state.codeGenerator.forBlock['sensor_line'] = function(block) {
        const channel = block.getFieldValue('CHANNEL');
        const code = `xunxian(${channel})`;
        return [code, state.codeGenerator.ORDER_FUNCTION_CALL];
    };

    // 视觉积木代码生成（使用全局函数）
    state.codeGenerator.forBlock['vision_detect_color'] = function(block) {
        const color = block.getFieldValue('COLOR');
        const colorMap = {
            'red': 'hong',
            'green': 'lv',
            'blue': 'lan',
            'yellow': 'huang',
            'orange': 'cheng',
        };
        const colorName = colorMap[color] || color;
        const code = `shibieyanse("${colorName}")`;
        return [code, state.codeGenerator.ORDER_FUNCTION_CALL];
    };

    // 逻辑积木代码生成
    state.codeGenerator.forBlock['controls_if'] = function(block) {
        const condition = state.codeGenerator.valueToCode(block, 'CONDITION', state.codeGenerator.ORDER_NONE) || 'False';
        let branch = state.codeGenerator.statementToCode(block, 'DO');
        branch = state.codeGenerator.addLoopTrap(branch, block);
        return `if ${condition}:\n${branch}\n`;
    };

    state.codeGenerator.forBlock['controls_repeat_ext'] = function(block) {
        const repeats = state.codeGenerator.valueToCode(block, 'TIMES', state.codeGenerator.ORDER_NONE) || '0';
        let branch = state.codeGenerator.statementToCode(block, 'DO');
        branch = state.codeGenerator.addLoopTrap(branch, block);
        return `for _ in range(${repeats}):\n${branch}\n`;
    };

    state.codeGenerator.forBlock['delay_wait'] = function(block) {
        const seconds = state.codeGenerator.valueToCode(block, 'SECONDS', state.codeGenerator.ORDER_NONE) || '0';
        return `dengdai(${seconds})\n`;
    };

    // ===== Blockly内置积木代码生成 =====

    // 数学积木
    state.codeGenerator.forBlock['math_number'] = function(block) {
        const code = String(block.getFieldValue('NUM'));
        return [code, state.codeGenerator.ORDER_ATOMIC];
    };

    state.codeGenerator.forBlock['math_arithmetic'] = function(block) {
        const operator = block.getFieldValue('OP');
        const argument0 = state.codeGenerator.valueToCode(block, 'A', state.codeGenerator.ORDER_NONE) || '0';
        const argument1 = state.codeGenerator.valueToCode(block, 'B', state.codeGenerator.ORDER_NONE) || '0';

        const operators = {
            'ADD': [' + ', state.codeGenerator.ORDER_ADDITIVE],
            'MINUS': [' - ', state.codeGenerator.ORDER_ADDITIVE],
            'MULTIPLY': [' * ', state.codeGenerator.ORDER_MULTIPLICATIVE],
            'DIVIDE': [' / ', state.codeGenerator.ORDER_MULTIPLICATIVE],
            'POWER': [' ** ', state.codeGenerator.ORDER_EXPONENTIATION],
        };

        const tuple = operators[operator] || operators['ADD'];
        const code = argument0 + tuple[0] + argument1;
        return [code, tuple[1]];
    };

    state.codeGenerator.forBlock['math_random_int'] = function(block) {
        const argument0 = state.codeGenerator.valueToCode(block, 'FROM', state.codeGenerator.ORDER_NONE) || '0';
        const argument1 = state.codeGenerator.valueToCode(block, 'TO', state.codeGenerator.ORDER_NONE) || '0';
        const code = `random.randint(${argument0}, ${argument1})`;
        return [code, state.codeGenerator.ORDER_FUNCTION_CALL];
    };

    state.codeGenerator.forBlock['math_single'] = function(block) {
        const operator = block.getFieldValue('OP');
        let code;
        let arg;

        if (operator === 'ABS') {
            arg = state.codeGenerator.valueToCode(block, 'NUM', state.codeGenerator.ORDER_NONE) || '0';
            code = `abs(${arg})`;
        } else if (operator === 'ROOT') {
            arg = state.codeGenerator.valueToCode(block, 'NUM', state.codeGenerator.ORDER_NONE) || '0';
            code = `math.sqrt(${arg})`;
        } else if (operator === 'NEG') {
            arg = state.codeGenerator.valueToCode(block, 'NUM', state.codeGenerator.ORDER_UNARY_SIGN) || '0';
            code = `-${arg}`;
        } else if (operator === 'SIN') {
            arg = state.codeGenerator.valueToCode(block, 'NUM', state.codeGenerator.ORDER_NONE) || '0';
            code = `math.sin(${arg})`;
        } else if (operator === 'COS') {
            arg = state.codeGenerator.valueToCode(block, 'NUM', state.codeGenerator.ORDER_NONE) || '0';
            code = `math.cos(${arg})`;
        } else if (operator === 'TAN') {
            arg = state.codeGenerator.valueToCode(block, 'NUM', state.codeGenerator.ORDER_NONE) || '0';
            code = `math.tan(${arg})`;
        } else {
            arg = state.codeGenerator.valueToCode(block, 'NUM', state.codeGenerator.ORDER_NONE) || '0';
            code = `(${arg})`;
        }

        return [code, state.codeGenerator.ORDER_FUNCTION_CALL];
    };

    // 逻辑比较积木
    state.codeGenerator.forBlock['logic_compare'] = function(block) {
        const operator = block.getFieldValue('OP');
        const argument0 = state.codeGenerator.valueToCode(block, 'A', state.codeGenerator.ORDER_NONE) || '0';
        const argument1 = state.codeGenerator.valueToCode(block, 'B', state.codeGenerator.ORDER_NONE) || '0';

        const operators = {
            'EQ': [' == ', state.codeGenerator.ORDER_EQUALITY],
            'NEQ': [' != ', state.codeGenerator.ORDER_EQUALITY],
            'LT': [' < ', state.codeGenerator.ORDER_RELATIONAL],
            'LTE': [' <= ', state.codeGenerator.ORDER_RELATIONAL],
            'GT': [' > ', state.codeGenerator.ORDER_RELATIONAL],
            'GTE': [' >= ', state.codeGenerator.ORDER_RELATIONAL],
        };

        const tuple = operators[operator] || operators['EQ'];
        const code = argument0 + tuple[0] + argument1;
        return [code, tuple[1]];
    };

    // 逻辑运算积木
    state.codeGenerator.forBlock['logic_operation'] = function(block) {
        const operator = block.getFieldValue('OP');
        const argument0 = state.codeGenerator.valueToCode(block, 'A', state.codeGenerator.ORDER_NONE) || 'False';
        const argument1 = state.codeGenerator.valueToCode(block, 'B', state.codeGenerator.ORDER_NONE) || 'False';

        if (operator === 'AND') {
            const code = argument0 + ' and ' + argument1;
            return [code, state.codeGenerator.ORDER_LOGICAL_AND];
        } else if (operator === 'OR') {
            const code = argument0 + ' or ' + argument1;
            return [code, state.codeGenerator.ORDER_LOGICAL_OR];
        }
        return ['False', state.codeGenerator.ORDER_ATOMIC];
    };

    // 布尔值积木
    state.codeGenerator.forBlock['logic_boolean'] = function(block) {
        const boolValue = block.getFieldValue('BOOL') === 'TRUE';
        return [boolValue ? 'True' : 'False', state.codeGenerator.ORDER_ATOMIC];
    };

    // 变量积木
    state.codeGenerator.forBlock['variables_get'] = function(block) {
        const code = state.codeGenerator.nameDB_.getName(block.getFieldValue('VAR'), Blockly.Variables.NAME_TYPE);
        return [code, state.codeGenerator.ORDER_ATOMIC];
    };

    state.codeGenerator.forBlock['variables_set'] = function(block) {
        const argument0 = state.codeGenerator.valueToCode(block, 'VALUE', state.codeGenerator.ORDER_NONE) || '0';
        const varName = state.codeGenerator.nameDB_.getName(block.getFieldValue('VAR'), Blockly.Variables.NAME_TYPE);
        return varName + ' = ' + argument0 + '\n';
    };

    // ===== 循环积木代码生成 =====

    // 计数循环
    state.codeGenerator.forBlock['controls_for'] = function(block) {
        const variable0 = state.codeGenerator.nameDB_.getName(block.getFieldValue('VAR'), Blockly.Variables.NAME_TYPE);
        const argument0 = state.codeGenerator.valueToCode(block, 'FROM', state.codeGenerator.ORDER_NONE) || '0';
        const argument1 = state.codeGenerator.valueToCode(block, 'TO', state.codeGenerator.ORDER_NONE) || '0';
        const argument2 = state.codeGenerator.valueToCode(block, 'BY', state.codeGenerator.ORDER_NONE) || '1';
        let branch = state.codeGenerator.statementToCode(block, 'DO');
        branch = state.codeGenerator.addLoopTrap(branch, block);

        let code = '';
        const range = function(left, right, inc) {
            if (inc === '1') {
                return `range(${left}, ${right} + 1)`;
            } else if (inc === '-1') {
                return `range(${left}, ${right} - 1, -1)`;
            } else {
                return `range(${left}, ${right} + (${inc > 0 ? 1 : -1}), ${inc})`;
            }
        };
        code = `for ${variable0} in ${range(argument0, argument1, argument2)}:\n${branch}\n`;
        return code;
    };

    // 当/直到循环
    state.codeGenerator.forBlock['controls_whileUntil'] = function(block) {
        const mode = block.getFieldValue('MODE');
        let condition = state.codeGenerator.valueToCode(block, 'BOOL', state.codeGenerator.ORDER_NONE) || 'False';
        let branch = state.codeGenerator.statementToCode(block, 'DO');
        branch = state.codeGenerator.addLoopTrap(branch, block);

        switch (mode) {
            case 'WHILE':
                return `while ${condition}:\n${branch}\n`;
            case 'UNTIL':
                // Python没有until，用while not实现
                return `while not (${condition}):\n${branch}\n`;
            default:
                break;
        }
        return '';
    };

    // ===== 数学积木代码生成 =====

    // 数学常数
    state.codeGenerator.forBlock['math_constant'] = function(block) {
        const constant = block.getFieldValue('CONSTANT');
        const constants = {
            'PI': 'math.pi',
            'E': 'math.e',
            'GOLDEN_RATIO': '(1 + math.sqrt(5)) / 2',
            'SQRT2': 'math.sqrt(2)',
            'SQRT1_2': 'math.sqrt(1 / 2)',
            'INFINITY': 'float("inf")',
        };
        const code = constants[constant] || '0';
        return [code, state.codeGenerator.ORDER_ATOMIC];
    };

    // 取模运算
    state.codeGenerator.forBlock['math_modulo'] = function(block) {
        const argument0 = state.codeGenerator.valueToCode(block, 'DIVIDEND', state.codeGenerator.ORDER_MULTIPLICATIVE) || '0';
        const argument1 = state.codeGenerator.valueToCode(block, 'DIVISOR', state.codeGenerator.ORDER_MULTIPLICATIVE) || '0';
        const code = `(${argument0} % ${argument1})`;
        return [code, state.codeGenerator.ORDER_MULTIPLICATIVE];
    };

    // 四舍五入
    state.codeGenerator.forBlock['math_round'] = function(block) {
        const operator = block.getFieldValue('OP');
        const argument0 = state.codeGenerator.valueToCode(block, 'NUM', state.codeGenerator.ORDER_NONE) || '0';
        let code;

        switch (operator) {
            case 'ROUND':
                code = `round(${argument0})`;
                break;
            case 'ROUNDUP':
                code = `math.ceil(${argument0})`;
                break;
            case 'ROUNDDOWN':
                code = `math.floor(${argument0})`;
                break;
            default:
                code = `round(${argument0})`;
        }
        return [code, state.codeGenerator.ORDER_FUNCTION_CALL];
    };

    // ===== 文本积木代码生成 =====

    // 文本值
    state.codeGenerator.forBlock['text'] = function(block) {
        const textValue = block.getFieldValue('TEXT');
        return [`'${textValue}'`, state.codeGenerator.ORDER_ATOMIC];
    };

    // 文本连接
    state.codeGenerator.forBlock['text_join'] = function(block) {
        const elements = [];
        for (let i = 0; i <= block.itemCount_; i++) {
            elements[i] = state.codeGenerator.valueToCode(block, 'ADD' + i, state.codeGenerator.ORDER_NONE) || "''";
        }
        const code = `(${elements.join(' + ')})`;
        return [code, state.codeGenerator.ORDER_NONE];
    };

    // 文本长度
    state.codeGenerator.forBlock['text_length'] = function(block) {
        const argument0 = state.codeGenerator.valueToCode(block, 'VALUE', state.codeGenerator.ORDER_NONE) || "''";
        return [`len(${argument0})`, state.codeGenerator.ORDER_FUNCTION_CALL];
    };

    // 打印文本
    state.codeGenerator.forBlock['text_print'] = function(block) {
        const argument0 = state.codeGenerator.valueToCode(block, 'TEXT', state.codeGenerator.ORDER_NONE) || "''";
        return `print(${argument0})\n`;
    };

    // ===== 列表积木代码生成 =====

    // 创建列表
    state.codeGenerator.forBlock['lists_create_with'] = function(block) {
        const elements = [];
        for (let i = 0; i <= block.itemCount_; i++) {
            elements[i] = state.codeGenerator.valueToCode(block, 'ADD' + i, state.codeGenerator.ORDER_NONE) || 'None';
        }
        const code = `[${elements.join(', ')}]`;
        return [code, state.codeGenerator.ORDER_ATOMIC];
    };

    // 列表长度
    state.codeGenerator.forBlock['lists_length'] = function(block) {
        const argument0 = state.codeGenerator.valueToCode(block, 'VALUE', state.codeGenerator.ORDER_NONE) || '[]';
        return [`len(${argument0})`, state.codeGenerator.ORDER_FUNCTION_CALL];
    };

    // ===== 函数积木代码生成 =====

    // 函数定义（无参数）
    state.codeGenerator.forBlock['procedures_defnoreturn'] = function(block) {
        const funcName = state.codeGenerator.nameDB_.getName(
            block.getFieldValue('NAME'),
            Blockly.Procedures.NAME_TYPE
        );
        let branch = state.codeGenerator.statementToCode(block, 'STACK');
        branch = state.codeGenerator.addLoopTrap(branch, block);
        return `def ${funcName}():\n${branch}\n`;
    };

    // 函数定义（有返回值）
    state.codeGenerator.forBlock['procedures_defreturn'] = function(block) {
        const funcName = state.codeGenerator.nameDB_.getName(
            block.getFieldValue('NAME'),
            Blockly.Procedures.NAME_TYPE
        );
        let branch = state.codeGenerator.statementToCode(block, 'STACK');
        const returnValue = state.codeGenerator.valueToCode(block, 'RETURN', state.codeGenerator.ORDER_NONE) || 'None';
        branch = state.codeGenerator.addLoopTrap(branch, block);
        return `def ${funcName}():\n${branch}    return ${returnValue}\n`;
    };

    // 函数调用（无返回值）
    state.codeGenerator.forBlock['procedures_callnoreturn'] = function(block) {
        const funcName = state.codeGenerator.nameDB_.getName(
            block.getFieldValue('NAME'),
            Blockly.Procedures.NAME_TYPE
        );
        return `${funcName}()\n`;
    };

    // 函数调用（有返回值）
    state.codeGenerator.forBlock['procedures_callreturn'] = function(block) {
        const funcName = state.codeGenerator.nameDB_.getName(
            block.getFieldValue('NAME'),
            Blockly.Procedures.NAME_TYPE
        );
        return [`${funcName}()`, state.codeGenerator.ORDER_FUNCTION_CALL];
    };

    // 如果-否则积木
    state.codeGenerator.forBlock['controls_ifelse'] = function(block) {
        const condition = state.codeGenerator.valueToCode(block, 'IF0', state.codeGenerator.ORDER_NONE) || 'False';
        let thenCode = state.codeGenerator.statementToCode(block, 'DO0');
        let elseCode = state.codeGenerator.statementToCode(block, 'ELSE');
        thenCode = state.codeGenerator.addLoopTrap(thenCode, block);
        elseCode = state.codeGenerator.addLoopTrap(elseCode, block);
        return `if ${condition}:\n${thenCode}else:\n${elseCode}\n`;
    };

    console.log('代码生成器定义完成');
}

// ===== WebSocket连接管理（原生WebSocket）=====
function connectWebSocket() {
    if (state.ws) {
        if (state.ws.readyState === WebSocket.OPEN || state.ws.readyState === WebSocket.CONNECTING) {
            state.ws.close();
        }
    }

    console.log('连接到网关:', CONFIG.wsUrl);

    // 创建原生WebSocket连接
    state.ws = new WebSocket(CONFIG.wsUrl);

    // 连接成功
    state.ws.onopen = () => {
        console.log('WebSocket已连接');
        state.connected = true;
        updateConnectionStatus(true);

        // 发送客户端注册消息
        send({
            type: 'client_register',
            data: { client_id: generateClientId() }
        });
    };

    // 收到消息
    state.ws.onmessage = (event) => {
        try {
            const message = JSON.parse(event.data);
            handleMessage(message);
        } catch (e) {
            console.error('解析消息失败:', e, event.data);
        }
    };

    // 连接关闭
    state.ws.onclose = (event) => {
        console.log('WebSocket已断开:', event.code, event.reason);
        state.connected = false;
        updateConnectionStatus(false);

        // 自动重连
        setTimeout(() => {
            if (!state.connected) {
                console.log('尝试重新连接...');
                connectWebSocket();
            }
        }, CONFIG.reconnectInterval);
    };

    // 连接错误
    state.ws.onerror = (error) => {
        console.error('WebSocket错误:', error);
    };
}

function send(message) {
    if (state.ws && state.connected) {
        const jsonStr = JSON.stringify(message);
        console.log('WebSocket发送:', jsonStr);
        state.ws.send(jsonStr);
    } else {
        console.warn('WebSocket未连接，无法发送消息');
    }
}

function handleMessage(message) {
    const { type, data, vehicle_id } = message;

    switch (type) {
        case 'vehicle_list':
            updateVehicleList(data.vehicles);
            break;
        case 'vehicle_status':
            updateVehicleStatus(vehicle_id, data);
            break;
        case 'execution_started':
            handleExecutionStarted(data);
            break;
        case 'execution_finished':
            handleExecutionFinished(data);
            break;
        case 'execution_error':
            handleExecutionError(data);
            break;
        case 'sensor_update':
            updateSensorDisplay(data.sensors);
            break;
        case 'error':
            showError(data.message);
            break;
        default:
            console.log('未知消息类型:', type);
    }
}

// ===== 辅助函数 =====
function selectVehicle(vehicleId) {
    state.vehicleId = vehicleId;
    const select = document.getElementById('vehicle-select');
    select.value = vehicleId;
    enableControls(true);
    showStatus(`已连接到: ${vehicleId}`);
}

function generateClientId() {
    return 'client-' + Math.random().toString(36).substr(2, 9);
}

// ===== UI更新函数 =====
function updateConnectionStatus(connected) {
    const statusEl = document.getElementById('connection-status');
    const statusText = statusEl.querySelector('.status-text');

    if (connected) {
        statusEl.className = 'status-indicator online';
        statusText.textContent = t('已连接');
        enableControls(true);
    } else {
        statusEl.className = 'status-indicator offline';
        statusText.textContent = t('未连接');
        enableControls(false);
    }
}

function updateVehicleList(vehicles) {
    state.vehicles = vehicles;
    const select = document.getElementById('vehicle-select');
    select.innerHTML = `<option value="">${t('选择小车...')}</option>`;

    vehicles.forEach((vehicle) => {
        const option = document.createElement('option');
        option.value = vehicle.vehicle_id;
        const status = vehicle.online ? t('在线') : t('离线');
        option.textContent = `${vehicle.name} (${status})`;
        option.disabled = !vehicle.online;
        select.appendChild(option);
    });
}

function updateVehicleStatus(vehicleId, status) {
    if (vehicleId === state.vehicleId) {
        enableControls(status.online && !status.busy);
    }
}

function updateSensorDisplay(sensors) {
    if (sensors.ultrasonic !== undefined) {
        document.getElementById('sensor-ultrasonic').textContent = sensors.ultrasonic;
    }
    if (sensors.infrared) {
        document.getElementById('sensor-line').textContent =
            sensors.infrared.map((v) => v ? '●' : '○').join(' ');
    }
    if (sensors.battery !== undefined) {
        document.getElementById('sensor-battery').textContent = sensors.battery.toFixed(1);
    }
}

function enableControls(enabled) {
    document.getElementById('btn-run').disabled = !enabled || !state.vehicleId;
    document.getElementById('btn-stop').disabled = !enabled;
    document.getElementById('btn-emergency').disabled = !enabled;
}

function handleExecutionStarted(data) {
    state.executionId = data.execution_id;
    showStatus('代码正在执行...');
    document.getElementById('btn-run').disabled = true;
    document.getElementById('btn-stop').disabled = false;
}

function handleExecutionFinished(data) {
    state.executionId = null;
    showStatus('代码执行完成');
    document.getElementById('btn-run').disabled = false;
    document.getElementById('btn-stop').disabled = true;
}

function handleExecutionError(data) {
    state.executionId = null;
    showError('执行错误: ' + data.error);
    document.getElementById('btn-run').disabled = false;
    document.getElementById('btn-stop').disabled = true;
}

function showStatus(message) {
    document.getElementById('status-message').textContent = message;
}

function showError(message) {
    showStatus('❌ ' + message);
    console.error(message);
}

// ===== 工具函数 =====
function generateExecutionId() {
    return 'exec_' + Date.now() + '_' + Math.random().toString(36).substr(2, 5);
}

// ===== 课程系统功能 =====
function renderCourseList() {
    const courseListEl = document.getElementById('course-list');
    courseListEl.innerHTML = '';

    // 遍历每个难度级别
    Object.values(COURSES).forEach(level => {
        const levelEl = document.createElement('div');
        levelEl.className = 'course-level';
        levelEl.style.borderLeftColor = level.color;

        // 级别头部 - 应用翻译
        const levelHeader = document.createElement('div');
        levelHeader.className = 'course-level-header';
        levelHeader.innerHTML = `
            <span class="level-icon">${level.icon}</span>
            <span class="level-name">${t(level.name)}</span>
            <span class="level-description">${t(level.description)}</span>
            <span class="level-progress">
                ${state.courseManager.getCompletedCount(level.id)}/${state.courseManager.getTotalCount(level.id)}
            </span>
        `;
        levelEl.appendChild(levelHeader);

        // 课程列表容器
        const coursesContainer = document.createElement('div');
        coursesContainer.className = 'course-level-courses';

        // 该级别下的所有课程
        level.courses.forEach(course => {
            const courseEl = document.createElement('div');
            courseEl.className = 'course-item';
            const isCompleted = state.courseManager.isCompleted(course.id);

            courseEl.innerHTML = `
                <div class="course-item-header">
                    <span class="course-title">${t(course.title)}</span>
                    ${isCompleted ? '<span class="course-badge completed">✓</span>' : ''}
                </div>
                <div class="course-item-info">
                    <span class="course-duration">⏱️ ${course.duration}</span>
                    <span class="course-fun">${t(course.funText)}</span>
                </div>
            `;

            courseEl.addEventListener('click', () => selectCourse(course));
            coursesContainer.appendChild(courseEl);
        });

        levelEl.appendChild(coursesContainer);
        courseListEl.appendChild(levelEl);
    });
}

function selectCourse(course) {
    state.currentCourse = course;

    // 显示当前课程信息
    const currentCourseHint = document.getElementById('current-course-hint');
    currentCourseHint.classList.remove('hidden');
    document.getElementById('current-course-title').textContent = course.title;

    // 显示课程提示面板
    showCourseHint(course);

    // 关闭课程选择面板
    document.getElementById('course-panel').classList.add('hidden');

    showStatus(`已选择课程: ${course.title}`);
}

function showCourseHint(course) {
    document.getElementById('hint-title').textContent = `${t(course.title)}`;
    document.getElementById('hint-duration').textContent = `⏱️ ${course.duration}`;
    document.getElementById('hint-description').textContent = t(course.description);
    document.getElementById('hint-fun-text').textContent = `🎉 ${t(course.funText)}`;
    document.getElementById('hint-expected').textContent = t(course.expected);

    // 积木列表 - 应用翻译
    const blocksEl = document.getElementById('hint-blocks');
    blocksEl.innerHTML = '';
    course.blocks.forEach(block => {
        const blockTag = document.createElement('span');
        blockTag.className = 'block-tag';
        blockTag.textContent = t(block);
        blocksEl.appendChild(blockTag);
    });

    // 搭建步骤 - 应用翻译
    const stepsEl = document.getElementById('hint-steps');
    stepsEl.innerHTML = '';
    course.hints.forEach(hint => {
        const li = document.createElement('li');
        li.textContent = t(hint);
        stepsEl.appendChild(li);
    });

    // 显示面板
    document.getElementById('course-hint-panel').classList.remove('hidden');
}

function closeCourseHint() {
    document.getElementById('course-hint-panel').classList.add('hidden');
}

function markCourseCompleted() {
    if (state.currentCourse) {
        state.courseManager.markCompleted(state.currentCourse.id);
        showStatus(`🎉 恭喜完成课程: ${state.currentCourse.title}!`);
        closeCourseHint();
        renderCourseList(); // 更新列表显示完成状态
    }
}

function toggleCoursePanel() {
    const panel = document.getElementById('course-panel');
    panel.classList.toggle('hidden');
    if (!panel.classList.contains('hidden')) {
        renderCourseList();
    }
}

// ===== 语言切换功能 =====
function toggleLanguage() {
    languageManager.toggle();
    refreshTranslations();
    updateLanguageButton();

    // 重新定义积木块（使用新语言）
    defineBlocks();

    // 更新Blockly工具箱和刷新工作区
    if (state.workspace) {
        // 保存当前工作区的XML
        const xml = Blockly.Xml.workspaceToDom(state.workspace);
        const xmlText = Blockly.Xml.domToText(xml);

        // 更新工具箱
        state.workspace.updateToolbox(getToolbox());

        // 清除并重新加载工作区
        state.workspace.clear();
        // 使用Blockly.utils.xml.textToDom代替已废弃的Blockly.Xml.textToDom
        const newXml = Blockly.utils.xml.textToDom(xmlText);
        Blockly.Xml.domToWorkspace(newXml, state.workspace);
    }

    // 刷新课程列表以应用翻译
    const panel = document.getElementById('course-panel');
    if (!panel.classList.contains('hidden')) {
        renderCourseList();
    }
}

function updateLanguageButton() {
    const btn = document.getElementById('btn-language');
    if (languageManager.isPinyinMode) {
        btn.textContent = '🔄 拼';
        btn.title = '切换到汉字';
    } else {
        btn.textContent = '🔄 汉';
        btn.title = '切换到拼音';
    }
}

// ===== 事件处理 =====
function setupEventListeners() {
    // 语言切换按钮
    document.getElementById('btn-language').addEventListener('click', toggleLanguage);

    // 课程按钮
    document.getElementById('btn-courses').addEventListener('click', toggleCoursePanel);

    // 关闭课程面板
    document.getElementById('btn-close-courses').addEventListener('click', () => {
        document.getElementById('course-panel').classList.add('hidden');
    });

    // 关闭提示面板
    document.getElementById('btn-close-hint').addEventListener('click', closeCourseHint);
    document.getElementById('btn-close-hint-panel').addEventListener('click', closeCourseHint);

    // 查看提示按钮
    document.getElementById('btn-show-hint').addEventListener('click', () => {
        if (state.currentCourse) {
            showCourseHint(state.currentCourse);
        }
    });

    // 完成课程按钮
    document.getElementById('btn-mark-complete').addEventListener('click', markCourseCompleted);

    // 车辆选择
    document.getElementById('vehicle-select').addEventListener('change', (e) => {
        state.vehicleId = e.target.value;
        enableControls(state.connected && state.vehicleId);
        showStatus(state.vehicleId ? `已选择: ${state.vehicleId}` : '请选择小车');
    });

    // 运行按钮
    document.getElementById('btn-run').addEventListener('click', () => {
        console.log('点击运行按钮, state.vehicleId =', state.vehicleId);
        const code = state.codeGenerator.workspaceToCode(state.workspace);
        if (!code || code.trim() === '') {
            showError('请先拖拽积木块');
            return;
        }

        const executionId = generateExecutionId();
        const message = {
            type: 'execute_code',
            vehicle_id: state.vehicleId,  // vehicle_id 在顶层
            data: {
                code: code,
                timeout: 60,
                execution_id: executionId,
            },
        };
        console.log('发送消息:', message);
        send(message);
    });

    // 停止按钮
    document.getElementById('btn-stop').addEventListener('click', () => {
        if (state.executionId) {
            send({
                type: 'stop_execution',
                vehicle_id: state.vehicleId,  // vehicle_id 在顶层
                data: {
                    execution_id: state.executionId,
                },
            });
        }
    });

    // 紧急停止按钮
    document.getElementById('btn-emergency').addEventListener('click', () => {
        send({
            type: 'emergency_stop',
            data: {},
        });
    });
}

// ===== 等待 Blockly 加载完成 =====
function waitForBlockly() {
    return new Promise((resolve) => {
        if (typeof Blockly !== 'undefined') {
            resolve();
        } else {
            const checkInterval = setInterval(() => {
                if (typeof Blockly !== 'undefined') {
                    clearInterval(checkInterval);
                    resolve();
                }
            }, 50);
        }
    });
}

// ===== 初始化 =====
async function init() {
    console.log('初始化Blockly小车编程...');

    // 等待 Blockly 加载完成
    await waitForBlockly();
    console.log('Blockly 已加载');

    // 定义积木块
    defineBlocks();

    // 初始化Blockly工作区（创建 codeGenerator）
    initBlockly();

    // 定义代码生成器（需要在 codeGenerator 创建后）
    defineCodeGenerator();

    // 设置事件监听
    setupEventListeners();

    // 应用语言翻译
    refreshTranslations();
    updateLanguageButton();

    // 连接WebSocket
    connectWebSocket();

    console.log('初始化完成');
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', init);
// v2
