// ===== 全局配置 =====
const CONFIG = {
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
};

// ===== Blockly工具箱定义 =====
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
                { kind: 'block', type: 'motion_stop' },
            ],
        },
        {
            kind: 'category',
            name: '传感',
            colour: '#99CA49',
            contents: [
                { kind: 'block', type: 'sensor_ultrasonic' },
            ],
        },
        {
            kind: 'category',
            name: '逻辑',
            colour: '#FFAB19',
            contents: [
                { kind: 'block', type: 'controls_if' },
                { kind: 'block', type: 'controls_repeat_ext' },
                { kind: 'block', type: 'delay_wait' },
            ],
        },
    ],
};

// ===== 初始化Blockly =====
function initBlockly() {
    // 创建Python代码生成器
    state.codeGenerator = new Blockly.Generator('Python');
    state.codeGenerator.ORDER_ATOMIC = 0;
    state.codeGenerator.ORDER_NONE = 0;

    // 定义缩进
    state.codeGenerator.INDENT = '    ';

    // 初始化工作区
    const workspace = Blockly.inject('blockly-div', {
        toolbox: toolbox,
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
                .appendField('⬆️ 前进')
                .appendField(new Blockly.FieldDropdown([
                    ['🐢 慢速', '30'],
                    ['🚶 中速', '50'],
                    ['🏃 快速', '70'],
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
                .appendField('⬇️ 后退')
                .appendField(new Blockly.FieldDropdown([
                    ['🐢 慢速', '30'],
                    ['🚶 中速', '50'],
                    ['🏃 快速', '70'],
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
                .appendField('⬅️ 左平移')
                .appendField(new Blockly.FieldDropdown([
                    ['🐢 慢速', '30'],
                    ['🚶 中速', '50'],
                    ['🏃 快速', '70'],
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
                .appendField('➡️ 右平移')
                .appendField(new Blockly.FieldDropdown([
                    ['🐢 慢速', '30'],
                    ['🚶 中速', '50'],
                    ['🏃 快速', '70'],
                ]), 'SPEED');
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(230);
        }
    };

    // 停止积木
    Blockly.Blocks['motion_stop'] = {
        init: function() {
            this.appendDummyInput().appendField('🛑 停止');
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(230);
        }
    };

    // 超声波传感器积木
    Blockly.Blocks['sensor_ultrasonic'] = {
        init: function() {
            this.appendDummyInput().appendField('📡 超声波距离');
            this.setOutput(true, 'Number');
            this.setColour(120);
        }
    };

    // 如果积木
    Blockly.Blocks['controls_if'] = {
        init: function() {
            this.appendValueInput('CONDITION')
                .setCheck('Boolean')
                .appendField('如果');
            this.appendStatementInput('DO')
                .appendField('就');
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
                .appendField('重复执行');
            this.appendStatementInput('DO')
                .appendField('次');
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
                .appendField('等待');
            this.appendDummyInput().appendField('秒');
            this.setPreviousStatement(true, null);
            this.setNextStatement(true, null);
            this.setColour(330);
        }
    };

    console.log('积木块定义完成');
}

// ===== 定义代码生成器 =====
function defineCodeGenerator() {
    // 运动积木代码生成
    state.codeGenerator.forBlock['motion_forward'] = function(block) {
        const speed = block.getFieldValue('SPEED');
        return `motion.qianjin(${speed})\n`;
    };

    state.codeGenerator.forBlock['motion_backward'] = function(block) {
        const speed = block.getFieldValue('SPEED');
        return `motion.houtui(${speed})\n`;
    };

    state.codeGenerator.forBlock['motion_left'] = function(block) {
        const speed = block.getFieldValue('SPEED');
        return `motion.zuopingyi(${speed})\n`;
    };

    state.codeGenerator.forBlock['motion_right'] = function(block) {
        const speed = block.getFieldValue('SPEED');
        return `motion.youpingyi(${speed})\n`;
    };

    state.codeGenerator.forBlock['motion_stop'] = function(block) {
        return `motion.tingzhi()\n`;
    };

    // 传感器积木代码生成
    state.codeGenerator.forBlock['sensor_ultrasonic'] = function(block) {
        const code = 'sensor.heshengbo()';
        return [code, state.codeGenerator.ORDER_MEMBER];
    };

    // 逻辑积木代码生成
    state.codeGenerator.forBlock['controls_if'] = function(block) {
        const condition = state.codeGenerator.valueToCode(block, 'CONDITION', state.codeGenerator.ORDER_NONE) || 'False';
        const branch = state.codeGenerator.statementToCode(block, 'DO');
        branch = state.codeGenerator.addLoopTrap(branch, block);
        return `if ${condition}:\n${branch}\n`;
    };

    state.codeGenerator.forBlock['controls_repeat_ext'] = function(block) {
        const repeats = state.codeGenerator.valueToCode(block, 'TIMES', state.codeGenerator.ORDER_NONE) || '0';
        const branch = state.codeGenerator.statementToCode(block, 'DO');
        branch = state.codeGenerator.addLoopTrap(branch, block);
        return `for _ in range(${repeats}):\n${branch}\n`;
    };

    state.codeGenerator.forBlock['delay_wait'] = function(block) {
        const seconds = state.codeGenerator.valueToCode(block, 'SECONDS', state.codeGenerator.ORDER_NONE) || '0';
        return `dengdai(${seconds})\n`;
    };

    console.log('代码生成器定义完成');
}

// ===== WebSocket连接管理 =====
function connectWebSocket() {
    if (state.ws) {
        state.ws.close();
    }

    state.ws = new WebSocket(CONFIG.wsUrl);

    state.ws.onopen = () => {
        console.log('WebSocket已连接');
        state.connected = true;
        updateConnectionStatus(true);

        // 发送客户端注册消息
        send({
            type: 'client_register',
            data: { client_id: generateClientId() },
        });

        // 请求车辆列表
        send({
            type: 'get_vehicle_list',
            data: {},
        });
    };

    state.ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        handleMessage(message);
    };

    state.ws.onerror = (error) => {
        console.error('WebSocket错误:', error);
    };

    state.ws.onclose = () => {
        console.log('WebSocket已断开');
        state.connected = false;
        updateConnectionStatus(false);

        // 5秒后重连
        setTimeout(connectWebSocket, CONFIG.reconnectInterval);
    };
}

function send(message) {
    if (state.ws && state.ws.readyState === WebSocket.OPEN) {
        message.vehicle_id = state.vehicleId;
        message.timestamp = Date.now();
        state.ws.send(JSON.stringify(message));
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

// ===== UI更新函数 =====
function updateConnectionStatus(connected) {
    const statusEl = document.getElementById('connection-status');
    const statusText = statusEl.querySelector('.status-text');

    if (connected) {
        statusEl.className = 'status-indicator online';
        statusText.textContent = '已连接';
        enableControls(true);
    } else {
        statusEl.className = 'status-indicator offline';
        statusText.textContent = '未连接';
        enableControls(false);
    }
}

function updateVehicleList(vehicles) {
    state.vehicles = vehicles;
    const select = document.getElementById('vehicle-select');
    select.innerHTML = '<option value="">选择小车...</option>';

    vehicles.forEach((vehicle) => {
        const option = document.createElement('option');
        option.value = vehicle.vehicle_id;
        option.textContent = `${vehicle.name} (${vehicle.online ? '在线' : '离线'})`;
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
function generateClientId() {
    return 'client_' + Math.random().toString(36).substr(2, 9);
}

function generateExecutionId() {
    return 'exec_' + Date.now() + '_' + Math.random().toString(36).substr(2, 5);
}

// ===== 事件处理 =====
function setupEventListeners() {
    // 车辆选择
    document.getElementById('vehicle-select').addEventListener('change', (e) => {
        state.vehicleId = e.target.value;
        enableControls(state.connected && state.vehicleId);
        showStatus(state.vehicleId ? `已选择: ${state.vehicleId}` : '请选择小车');
    });

    // 运行按钮
    document.getElementById('btn-run').addEventListener('click', () => {
        const code = state.codeGenerator.workspaceToCode(state.workspace);
        if (!code || code.trim() === '') {
            showError('请先拖拽积木块');
            return;
        }

        const executionId = generateExecutionId();
        send({
            type: 'execute_code',
            data: {
                code: code,
                timeout: 60,
                execution_id: executionId,
            },
        });
    });

    // 停止按钮
    document.getElementById('btn-stop').addEventListener('click', () => {
        if (state.executionId) {
            send({
                type: 'stop_execution',
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

// ===== 初始化 =====
function init() {
    console.log('初始化Blockly小车编程...');

    // 定义积木块
    defineBlocks();

    // 定义代码生成器
    defineCodeGenerator();

    // 初始化Blockly工作区
    initBlockly();

    // 设置事件监听
    setupEventListeners();

    // 连接WebSocket
    connectWebSocket();

    console.log('初始化完成');
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', init);
