# 前端开发规范 - Blockly Vehicle Frontend

## 📋 核心：必须按 API 设计文档开发

**最重要的规则**：在实现任何与后端通信的功能前，**必须先查看并遵循** API 设计文档。

### 📁 相关文档

| 文档 | 路径 | 用途 |
|------|------|------|
| 系统架构 | `../../docs/01-system-architecture.md` | 了解整体架构和消息格式 |
| 积木 API | `../../docs/02-block-api.md` | ⚠️ **积木块 API 定义 - 必须严格遵循** |
| 通信协议 | `../../docs/04-communication.md` | 消息协议定义（如果存在） |

---

## 🚨 黄金法则：文档先行，代码跟随

### 原则
**任何API变动必须先修改文档，然后再实现代码**

### 变更流程
```
1. 修改设计文档 (docs/02-block-api.md)
   ↓
2. 更新后端HAL实现以符合文档
   ↓
3. 更新沙箱导入新函数
   ↓
4. 更新前端代码生成器
   ↓
5. 测试验证
```

### 错误示例 ❌
```javascript
// 直接写代码，没有查看文档
state.codeGenerator.forBlock['gimbal_reset'] = function(block) {
    return 'yuntai_fuwei()\n';  // 后端实现的是 fuwei()，不匹配！
};
```

### 正确示例 ✅
```javascript
// 1. 先查看 docs/02-block-api.md 确认函数名是 yuntai_fuwei()
// 2. 确认后端已实现该函数（如果没有，先添加到后端）
// 3. 再写前端代码
state.codeGenerator.forBlock['gimbal_reset'] = function(block) {
    return 'yuntai_fuwei()\n';  // 与文档一致
};
```

### 变动检查清单
任何API相关修改前，必须：
- [ ] 已查看 `docs/02-block-api.md` 确认API定义
- [ ] 如需改动API，**先修改文档**
- [ ] 后端实现已更新以符合新文档
- [ ] 前端代码生成器已更新
- [ ] 已测试验证

---

---

## 🔴 本次问题的教训（2024-02-22）

### 问题
前端发送的 `execute_code` 消息格式不符合 Gateway 的设计：

```javascript
// ❌ 错误格式（前端之前的实现）
{
  "type": "execute_code",
  "data": {
    "vehicle_id": "vehicle-001",  // 错误：放在 data 里面
    "code": "gimbal.fuwei()",
    "timeout": 60,
    "execution_id": "exec_123"
  }
}

// ✅ 正确格式（Gateway 期望的）
{
  "type": "execute_code",
  "vehicle_id": "vehicle-001",     // 正确：在顶层
  "data": {
    "code": "gimbal.fuwei()",
    "timeout": 60,
    "execution_id": "exec_123"
  }
}
```

### 根本原因
1. **没有先查看 Gateway 的消息结构定义** (`cloud/gateway-go/internal/message/types.go`)
2. **没有参考系统架构文档** 中的消息示例
3. 直接凭直觉实现，导致字段位置错误

### 解决方案
**开发任何通信功能前，必须：**
1. 先查看后端的消息结构定义
2. 确认每个字段的位置（顶层 vs data 内部）
3. 编写代码前先用工具（如 Postman、浏览器控制台）验证格式

---

## ✅ WebSocket 消息格式规范

### 通用消息结构

所有通过 WebSocket 发送的 JSON 消息必须遵循以下结构：

```javascript
{
  "type": "消息类型",
  "vehicle_id": "车辆ID",      // 对于需要指定车辆的消息
  "data": {
    // 消息具体数据
  },
  "timestamp": 1737520638      // 可选：时间戳
}
```

### 常用消息类型

#### 1. 代码执行（execute_code）
```javascript
{
  "type": "execute_code",
  "vehicle_id": "vehicle-001",     // ⚠️ 必须在顶层
  "data": {
    "code": "yuntai_fuwei()",
    "timeout": 60,
    "execution_id": "exec_xxx"
  }
}
```

#### 2. 停止执行（stop_execution）
```javascript
{
  "type": "stop_execution",
  "vehicle_id": "vehicle-001",     // ⚠️ 必须在顶层
  "data": {
    "execution_id": "exec_xxx"
  }
}
```

#### 3. 紧急停止（emergency_stop）
```javascript
{
  "type": "emergency_stop",
  // vehicle_id 可选：不指定则发送给所有车辆
  "vehicle_id": "vehicle-001",
  "data": {}
}
```

#### 4. 心跳（heartbeat）
```javascript
{
  "type": "heartbeat",
  "data": {}
}
```

#### 5. 客户端注册（client_register）
```javascript
{
  "type": "client_register",
  "data": {
    "client_id": "client-xxx"
  }
}
```

---

## 🛠️ 开发工作流

### 新增消息类型的流程

1. **查看后端定义**
   ```bash
   # 查看 Gateway 的消息类型定义
   cat cloud/gateway-go/internal/message/types.go
   ```

2. **确认消息结构**
   ```bash
   # 查看消息处理器
   cat cloud/gateway-go/internal/handler/message.go
   ```

3. **编写前端代码**
   ```javascript
   // 严格按照后端定义编写
   function sendMessage(params) {
     const message = {
       type: params.type,
       vehicle_id: params.vehicleId,  // 在顶层
       data: params.data
     };
     send(message);
   }
   ```

4. **测试验证**
   - 打开浏览器控制台
   - 发送消息
   - 检查发送的 JSON 格式
   - 查看 Gateway 日志确认接收正确

### 调试技巧

```javascript
// 在 send 函数中添加日志
function send(message) {
  const jsonStr = JSON.stringify(message);
  console.log('WebSocket发送:', jsonStr);  // 调试日志
  // ... 发送逻辑
}

// 使用浏览器 Network 标签查看 WebSocket 帧
// 1. 打开 DevTools → Network → WS 标签
// 2. 选择 WebSocket 连接
// 3. 查看发送和接收的帧
```

---

## 📝 代码审查 Checklist

提交任何与 WebSocket 通信相关的代码前，必须确认：

- [ ] 已查看 Gateway 的消息结构定义
- [ ] `vehicle_id` 等路由字段在消息**顶层**，不在 `data` 内部
- [ ] 消息 `type` 字段与后端定义一致
- [ ] 已在浏览器控制台验证发送的 JSON 格式
- [ ] 已在 Gateway 日志中确认消息被正确接收和解析

---

## 🚫 常见错误

### 错误 1：字段位置错误
```javascript
// ❌ 错误
{
  "type": "execute_code",
  "data": {
    "vehicle_id": "vehicle-001",  // 错误位置
    "code": "..."
  }
}
```

### 错误 2：缺少必要字段
```javascript
// ❌ 错误 - 缺少 vehicle_id
{
  "type": "execute_code",
  "data": {
    "code": "..."
  }
}
```

### 错误 3：类型不匹配
```javascript
// ❌ 错误 - vehicle_id 应该是字符串
{
  "type": "execute_code",
  "vehicle_id": 123,  // 错误类型
  "data": {...}
}
```

---

## 📚 参考资源

- **系统架构**: `docs/01-system-architecture.md`
- **Gateway 消息定义**: `cloud/gateway-go/internal/message/types.go`
- **消息路由器**: `cloud/gateway-go/internal/handler/message.go`
- **车载服务**: `vehicle/connection/manager.py`

---

*最后更新: 2024-02-22*
*维护者: 前端开发团队*
