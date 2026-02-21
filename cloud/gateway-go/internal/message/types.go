// Package message 消息类型定义
package message

import "time"

// ConnType 连接类型
type ConnType int

const (
	ConnTypeUnknown ConnType = iota
	ConnTypeVehicle          // 车载服务连接
	ConnTypeClient           // 前端客户端连接
)

// String 返回连接类型的字符串表示
func (c ConnType) String() string {
	switch c {
	case ConnTypeVehicle:
		return "vehicle"
	case ConnTypeClient:
		return "client"
	default:
		return "unknown"
	}
}

// Message WebSocket消息格式
type Message struct {
	Type      string                 `json:"type"`
	VehicleID string                 `json:"vehicle_id,omitempty"`
	Data      map[string]interface{} `json:"data,omitempty"`
	Timestamp int64                  `json:"timestamp,omitempty"`
}

// NewMessage 创建新消息
func NewMessage(msgType string) *Message {
	return &Message{
		Type:      msgType,
		Data:      make(map[string]interface{}),
		Timestamp: time.Now().Unix(),
	}
}

// VehicleInfo 车辆信息
type VehicleInfo struct {
	VehicleID string `json:"vehicle_id"`
	Name      string `json:"name"`
	Online    bool   `json:"online"`
}

// VehicleStatus 车辆状态
type VehicleStatus struct {
	VehicleID string `json:"vehicle_id"`
	Online    bool   `json:"online"`
	Busy      bool   `json:"busy"`
}

// ExecutionData 代码执行相关数据
type ExecutionData struct {
	Code        string `json:"code,omitempty"`
	Timeout     int    `json:"timeout,omitempty"`
	ExecutionID string `json:"execution_id,omitempty"`
	ProcessID   string `json:"process_id,omitempty"`
	Success     bool   `json:"success,omitempty"`
	Error       string `json:"error,omitempty"`
	Output      []string `json:"output,omitempty"`
}

// SensorData 传感器数据
type SensorData struct {
	Ultrasonic *int     `json:"ultrasonic,omitempty"`
	Infrared   []bool   `json:"infrared,omitempty"`
	Battery    *float64 `json:"battery,omitempty"`
}

// ClientRegisterData 前端客户端注册数据
type ClientRegisterData struct {
	ClientID string `json:"client_id"`
}

// VehicleRegisterData 车载服务注册数据
type VehicleRegisterData struct {
	VehicleID string `json:"vehicle_id"`
}

// HeartbeatData 心跳数据
type HeartbeatData struct {
	VehicleID string `json:"vehicle_id"`
}

// VehicleListData 车辆列表响应数据
type VehicleListData struct {
	Vehicles []VehicleInfo `json:"vehicles"`
}

// ErrorData 错误响应数据
type ErrorData struct {
	Code    string `json:"code"`
	Message string `json:"message"`
}
