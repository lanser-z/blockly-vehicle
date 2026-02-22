// Package pool 连接池管理
package pool

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/gorilla/websocket"
	"blockly-gateway/internal/message"
)

// Connection WebSocket连接
type Connection struct {
	ID            string
	VehicleID     string
	Type          message.ConnType
	WS            *websocket.Conn
	LastHeartbeat time.Time
	ConnectedAt   time.Time
	mu            sync.RWMutex
	closed        bool
}

// Send 发送消息到连接
func (c *Connection) Send(data []byte) error {
	c.mu.RLock()
	defer c.mu.RUnlock()

	if c.closed {
		return fmt.Errorf("连接已关闭: %s", c.ID)
	}

	return c.WS.WriteMessage(websocket.TextMessage, data)
}

// Close 关闭连接
func (c *Connection) Close() error {
	c.mu.Lock()
	defer c.mu.Unlock()

	if c.closed {
		return nil
	}

	c.closed = true
	return c.WS.Close()
}

// IsClosed 检查连接是否已关闭
func (c *Connection) IsClosed() bool {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.closed
}

// Pool 连接池
type Pool struct {
	// vehicle_id -> Connection
	vehicles map[string]*Connection
	// conn_id -> Connection (所有连接)
	connections map[string]*Connection
	// 前端客户端集合
	clients map[string]*Connection

	mu sync.RWMutex

	// 心跳检测配置
	heartbeatCheckInterval time.Duration
	heartbeatTimeout       time.Duration

	// 上下文
	ctx    context.Context
	cancel context.CancelFunc

	// 事件回调
	onVehicleListChanged func([]message.VehicleInfo)
}

// NewPool 创建新连接池
func NewPool(checkInterval, timeout time.Duration) *Pool {
	ctx, cancel := context.WithCancel(context.Background())
	return &Pool{
		vehicles:               make(map[string]*Connection),
		connections:            make(map[string]*Connection),
		clients:                make(map[string]*Connection),
		heartbeatCheckInterval: checkInterval,
		heartbeatTimeout:       timeout,
		ctx:                    ctx,
		cancel:                 cancel,
	}
}

// SetVehicleListCallback 设置车辆列表变化回调
func (p *Pool) SetVehicleListCallback(fn func([]message.VehicleInfo)) {
	p.mu.Lock()
	defer p.mu.Unlock()
	p.onVehicleListChanged = fn
}

// AddConnection 添加连接
func (p *Pool) AddConnection(conn *Connection) error {
	p.mu.Lock()
	defer p.mu.Unlock()

	if _, exists := p.connections[conn.ID]; exists {
		return fmt.Errorf("连接已存在: %s", conn.ID)
	}

	p.connections[conn.ID] = conn

	if conn.Type == message.ConnTypeVehicle && conn.VehicleID != "" {
		p.vehicles[conn.VehicleID] = conn
		// 注意：不在持锁状态调用 notifyVehicleListChanged，避免死锁
		// 使用 goroutine 异步通知
		go p.notifyVehicleListChanged()
	} else if conn.Type == message.ConnTypeClient {
		p.clients[conn.ID] = conn
	}

	return nil
}

// RemoveConnection 移除连接
func (p *Pool) RemoveConnection(connID string) {
	// 先收集信息（持锁）
	var isVehicle bool
	var vehicleID string

	p.mu.Lock()
	conn, exists := p.connections[connID]
	if exists {
		isVehicle = conn.Type == message.ConnTypeVehicle && conn.VehicleID != ""
		vehicleID = conn.VehicleID
		delete(p.connections, connID)

		if isVehicle {
			delete(p.vehicles, vehicleID)
		} else {
			delete(p.clients, connID)
		}
	}
	p.mu.Unlock()

	// 释放锁后再通知（避免死锁）
	if isVehicle {
		p.notifyVehicleListChanged()
	}
}

// RegisterVehicle 将连接注册为车辆（用于后注册场景）
// 当车辆连接时未发送X-Vehicle-ID头，而是在后续消息中注册时使用
func (p *Pool) RegisterVehicle(conn *Connection) {
	p.mu.Lock()
	defer p.mu.Unlock()

	// 如果连接已经在 vehicles 中，跳过
	if _, exists := p.vehicles[conn.VehicleID]; exists {
		return
	}

	// 如果该连接在 clients 中，先移除
	delete(p.clients, conn.ID)

	// 添加到 vehicles
	p.vehicles[conn.VehicleID] = conn

	// 通知车辆列表变化（使用 goroutine 异步执行，避免在持锁状态阻塞）
	go p.notifyVehicleListChanged()
}

// GetConnection 获取连接
func (p *Pool) GetConnection(connID string) (*Connection, bool) {
	p.mu.RLock()
	defer p.mu.RUnlock()
	conn, exists := p.connections[connID]
	return conn, exists
}

// GetVehicle 获取车辆连接
func (p *Pool) GetVehicle(vehicleID string) (*Connection, bool) {
	p.mu.RLock()
	defer p.mu.RUnlock()
	conn, exists := p.vehicles[vehicleID]
	return conn, exists
}

// UpdateHeartbeat 更新心跳
func (p *Pool) UpdateHeartbeat(vehicleID string) {
	p.mu.Lock()
	defer p.mu.Unlock()

	if conn, exists := p.vehicles[vehicleID]; exists {
		conn.LastHeartbeat = time.Now()
	}
}

// GetVehicleList 获取在线车辆列表
func (p *Pool) GetVehicleList() []message.VehicleInfo {
	p.mu.RLock()
	defer p.mu.RUnlock()

	vehicles := make([]message.VehicleInfo, 0, len(p.vehicles))
	for vehicleID := range p.vehicles {
		// 提取车辆编号作为名称
		name := vehicleID
		vehicles = append(vehicles, message.VehicleInfo{
			VehicleID: vehicleID,
			Name:      name,
			Online:    true,
		})
	}

	return vehicles
}

// RouteToVehicle 路由消息到指定车辆
func (p *Pool) RouteToVehicle(vehicleID string, data []byte) error {
	conn, exists := p.GetVehicle(vehicleID)
	if !exists {
		return fmt.Errorf("车辆未连接: %s", vehicleID)
	}

	if conn.IsClosed() {
		return fmt.Errorf("车辆连接已关闭: %s", vehicleID)
	}

	return conn.Send(data)
}

// BroadcastToClients 广播消息到所有前端客户端
func (p *Pool) BroadcastToClients(data []byte) error {
	p.mu.RLock()
	defer p.mu.RUnlock()

	var errs []error
	for _, client := range p.clients {
		if err := client.Send(data); err != nil {
			errs = append(errs, err)
		}
	}

	if len(errs) > 0 {
		return fmt.Errorf("广播失败，%d个客户端发送错误", len(errs))
	}

	return nil
}

// BroadcastToAll 广播消息到所有连接
func (p *Pool) BroadcastToAll(data []byte) error {
	p.mu.RLock()
	defer p.mu.RUnlock()

	var errs []error
	for _, conn := range p.connections {
		if err := conn.Send(data); err != nil {
			errs = append(errs, err)
		}
	}

	if len(errs) > 0 {
		return fmt.Errorf("广播失败，%d个连接发送错误", len(errs))
	}

	return nil
}

// notifyVehicleListChanged 通知车辆列表变化
func (p *Pool) notifyVehicleListChanged() {
	if p.onVehicleListChanged != nil {
		vehicles := p.GetVehicleList()
		p.onVehicleListChanged(vehicles)
	}
}

// StartHeartbeatMonitor 启动心跳监控
func (p *Pool) StartHeartbeatMonitor() {
	go p.heartbeatMonitor()
}

// Stop 停止连接池
func (p *Pool) Stop() {
	p.cancel()
}

// GetStats 获取连接池统计信息
func (p *Pool) GetStats() PoolStats {
	p.mu.RLock()
	defer p.mu.RUnlock()

	return PoolStats{
		VehicleCount:  len(p.vehicles),
		ClientCount:   len(p.clients),
		TotalCount:    len(p.connections),
		CheckInterval: p.heartbeatCheckInterval,
		Timeout:       p.heartbeatTimeout,
	}
}

// PoolStats 连接池统计信息
type PoolStats struct {
	VehicleCount  int           `json:"vehicle_count"`
	ClientCount   int           `json:"client_count"`
	TotalCount    int           `json:"total_count"`
	CheckInterval time.Duration `json:"check_interval"`
	Timeout       time.Duration `json:"timeout"`
}
