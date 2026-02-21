// Package handler WebSocket处理器
package handler

import (
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/gorilla/websocket"
	"github.com/sirupsen/logrus"

	"blockly-gateway/internal/message"
	"blockly-gateway/internal/pool"
)

var wsLogger = logrus.WithField("module", "websocket")

// WebSocketHandler WebSocket处理器
type WebSocketHandler struct {
	pool *pool.Pool
}

// NewWebSocketHandler 创建WebSocket处理器
func NewWebSocketHandler(p *pool.Pool) *WebSocketHandler {
	return &WebSocketHandler{
		pool: p,
	}
}

// upgrader WebSocket升级器
var upgrader = websocket.Upgrader{
	CheckOrigin: func(r *http.Request) bool {
		return true // 允许所有来源(CORS)
	},
	HandshakeTimeout: 10 * time.Second,
}

// HandleWebSocket 处理WebSocket升级请求
func (h *WebSocketHandler) HandleWebSocket(c *gin.Context) {
	// 升级HTTP到WebSocket
	ws, err := upgrader.Upgrade(c.Writer, c.Request, nil)
	if err != nil {
		wsLogger.Errorf("WebSocket升级失败: %v", err)
		c.JSON(http.StatusBadRequest, gin.H{"error": "WebSocket升级失败"})
		return
	}

	// 生成连接ID
	connID := generateConnID()

	// 检查是否为车载连接
	vehicleID, isVehicle := h.isVehicleConnection(c)

	// 创建连接对象
	conn := &pool.Connection{
		ID:            connID,
		VehicleID:     vehicleID,
		Type:          getConnType(isVehicle),
		WS:            ws,
		LastHeartbeat: time.Now(),
		ConnectedAt:   time.Now(),
	}

	// 添加到连接池
	if err := h.pool.AddConnection(conn); err != nil {
		wsLogger.Errorf("添加连接失败: %v", err)
		ws.Close()
		return
	}

	// 记录连接
	if isVehicle {
		wsLogger.Infof("车载服务已连接: vehicle_id=%s, conn_id=%s", vehicleID, connID)
	} else {
		wsLogger.Infof("客户端已连接: conn_id=%s", connID)
	}

	// 启动消息处理循环
	go h.handleConnection(conn)
}

// isVehicleConnection 检查是否为车载连接
func (h *WebSocketHandler) isVehicleConnection(c *gin.Context) (string, bool) {
	vehicleID := c.GetHeader("X-Vehicle-ID")
	if vehicleID != "" {
		return vehicleID, true
	}
	return "", false
}

// handleConnection 处理单个WebSocket连接
func (h *WebSocketHandler) handleConnection(conn *pool.Connection) {
	defer func() {
		// 连接关闭时清理
		h.pool.RemoveConnection(conn.ID)
		conn.Close()
		wsLogger.Infof("连接已关闭: conn_id=%s, vehicle_id=%s", conn.ID, conn.VehicleID)
	}()

	// 如果是前端客户端，发送当前车辆列表
	if conn.Type == message.ConnTypeClient {
		vehicles := h.pool.GetVehicleList()
		data, _ := message.EncodeVehicleList(vehicles)
		conn.Send(data)
	}

	// 消息读取循环
	for {
		_, data, err := conn.WS.ReadMessage()
		if err != nil {
			if websocket.IsUnexpectedCloseError(err, websocket.CloseGoingAway, websocket.CloseAbnormalClosure) {
				wsLogger.Warnf("读取消息错误: %v", err)
			}
			break
		}

		// 处理消息
		h.handleMessage(conn, data)
	}
}

// handleMessage 处理接收到的消息
func (h *WebSocketHandler) handleMessage(conn *pool.Connection, data []byte) {
	msg, err := message.Decode(data)
	if err != nil {
		wsLogger.Warnf("消息解码失败: %v", err)
		return
	}

	wsLogger.Debugf("收到消息: type=%s, from=%s, vehicle_id=%s",
		msg.Type, conn.Type, conn.VehicleID)

	switch msg.Type {
	case "heartbeat":
		h.handleHeartbeat(conn, msg)

	case "register":
		h.handleVehicleRegister(conn, msg)

	case "client_register":
		h.handleClientRegister(conn, msg)

	default:
		// 其他消息类型由消息路由器处理
		// 这里只做简单日志，实际路由在主程序中
		wsLogger.Debugf("消息类型 %s 需要路由处理", msg.Type)
	}
}

// handleHeartbeat 处理心跳消息
func (h *WebSocketHandler) handleHeartbeat(conn *pool.Connection, msg *message.Message) {
	if conn.Type == message.ConnTypeVehicle && conn.VehicleID != "" {
		h.pool.UpdateHeartbeat(conn.VehicleID)

		// 发送pong响应
		pong, _ := message.EncodePong()
		conn.Send(pong)
	}
}

// handleVehicleRegister 处理车载服务注册
func (h *WebSocketHandler) handleVehicleRegister(conn *pool.Connection, msg *message.Message) {
	// 如果连接时没有X-Vehicle-ID头，可以通过register事件设置
	dataBytes, _ := json.Marshal(msg.Data)
	var regData message.VehicleRegisterData
	if err := json.Unmarshal(dataBytes, &regData); err != nil {
		wsLogger.Warnf("车辆注册数据解析失败: %v", err)
		return
	}

	if regData.VehicleID == "" {
		wsLogger.Warn("车辆注册缺少vehicle_id")
		return
	}

	// 更新连接的vehicle_id
	conn.VehicleID = regData.VehicleID
	conn.Type = message.ConnTypeVehicle

	wsLogger.Infof("车辆注册成功: vehicle_id=%s, conn_id=%s", regData.VehicleID, conn.ID)
}

// handleClientRegister 处理前端客户端注册
func (h *WebSocketHandler) handleClientRegister(conn *pool.Connection, msg *message.Message) {
	dataBytes, _ := json.Marshal(msg.Data)
	var regData message.ClientRegisterData
	if err := json.Unmarshal(dataBytes, &regData); err != nil {
		wsLogger.Warnf("客户端注册数据解析失败: %v", err)
		return
	}

	wsLogger.Infof("客户端注册成功: client_id=%s, conn_id=%s", regData.ClientID, conn.ID)
}

// getConnType 获取连接类型
func getConnType(isVehicle bool) message.ConnType {
	if isVehicle {
		return message.ConnTypeVehicle
	}
	return message.ConnTypeClient
}

// generateConnID 生成唯一连接ID
func generateConnID() string {
	return fmt.Sprintf("conn_%d", time.Now().UnixNano())
}
