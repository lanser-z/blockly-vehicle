// Package handler 消息路由处理器
package handler

import (
	"github.com/sirupsen/logrus"

	"blockly-gateway/internal/message"
	"blockly-gateway/internal/pool"
)

var msgLogger = logrus.WithField("module", "router")

// MessageRouter 消息路由器
type MessageRouter struct {
	pool *pool.Pool
}

// NewMessageRouter 创建消息路由器
func NewMessageRouter(p *pool.Pool) *MessageRouter {
	return &MessageRouter{
		pool: p,
	}
}

// RouteMessage 路由消息
func (r *MessageRouter) RouteMessage(msg *message.Message, sourceConn *pool.Connection) error {
	switch msg.Type {
	case "execute_code":
		return r.handleExecuteCode(msg)

	case "stop_execution":
		return r.handleStopExecution(msg)

	case "emergency_stop":
		return r.handleEmergencyStop(msg)

	case "get_vehicle_list":
		return r.handleGetVehicleList(sourceConn)

	// 车辆发来的事件，需要转发给所有前端客户端
	case "execution_started":
		return r.forwardToClients(msg)

	case "execution_finished":
		return r.forwardToClientsWithVehicle(sourceConn, msg)

	case "execution_error":
		return r.forwardToClientsWithVehicle(sourceConn, msg)

	case "sensor_update":
		return r.forwardSensorUpdate(sourceConn, msg)

	case "status_update":
		return r.forwardStatusUpdate(sourceConn, msg)

	case "camera_snapshot_response":
		return r.handleCameraSnapshotResponse(sourceConn, msg)

	default:
		msgLogger.Warnf("未知消息类型: %s", msg.Type)
		return nil
	}
}

// handleExecuteCode 处理代码执行请求
func (r *MessageRouter) handleExecuteCode(msg *message.Message) error {
	if msg.VehicleID == "" {
		return r.sendErrorToSource("MISSING_VEHICLE_ID", "缺少车辆ID")
	}

	data, err := message.Encode(msg)
	if err != nil {
		return err
	}

	if err := r.pool.RouteToVehicle(msg.VehicleID, data); err != nil {
		msgLogger.Warnf("路由代码执行请求失败: %v", err)
		return r.sendErrorToSource("VEHICLE_OFFLINE", "车辆未连接")
	}

	msgLogger.Infof("代码执行请求已路由到车辆: %s", msg.VehicleID)
	return nil
}

// handleStopExecution 处理停止执行请求
func (r *MessageRouter) handleStopExecution(msg *message.Message) error {
	if msg.VehicleID == "" {
		return r.sendErrorToSource("MISSING_VEHICLE_ID", "缺少车辆ID")
	}

	data, err := message.Encode(msg)
	if err != nil {
		return err
	}

	if err := r.pool.RouteToVehicle(msg.VehicleID, data); err != nil {
		msgLogger.Warnf("路由停止执行请求失败: %v", err)
		return r.sendErrorToSource("VEHICLE_OFFLINE", "车辆未连接")
	}

	msgLogger.Infof("停止执行请求已路由到车辆: %s", msg.VehicleID)
	return nil
}

// handleEmergencyStop 处理紧急停止
func (r *MessageRouter) handleEmergencyStop(msg *message.Message) error {
	if msg.VehicleID == "" {
		// 如果没有指定车辆，向所有车辆发送紧急停止
		vehicles := r.pool.GetVehicleList()
		for _, v := range vehicles {
			if v.Online {
				emergencyMsg := message.NewMessage("emergency_stop")
				emergencyMsg.VehicleID = v.VehicleID
				data, _ := message.Encode(emergencyMsg)
				r.pool.RouteToVehicle(v.VehicleID, data)
			}
		}
		msgLogger.Warnf("紧急停止已发送到所有在线车辆")
		return nil
	}

	data, err := message.Encode(msg)
	if err != nil {
		return err
	}

	if err := r.pool.RouteToVehicle(msg.VehicleID, data); err != nil {
		msgLogger.Warnf("路由紧急停止失败: %v", err)
		return r.sendErrorToSource("VEHICLE_OFFLINE", "车辆未连接")
	}

	msgLogger.Warnf("紧急停止已发送到车辆: %s", msg.VehicleID)
	return nil
}

// handleGetVehicleList 处理获取车辆列表
func (r *MessageRouter) handleGetVehicleList(sourceConn *pool.Connection) error {
	vehicles := r.pool.GetVehicleList()
	data, err := message.EncodeVehicleList(vehicles)
	if err != nil {
		return err
	}

	return sourceConn.Send(data)
}

// forwardToClients 转发消息到所有前端客户端
func (r *MessageRouter) forwardToClients(msg *message.Message) error {
	data, err := message.Encode(msg)
	if err != nil {
		return err
	}

	if err := r.pool.BroadcastToClients(data); err != nil {
		msgLogger.Warnf("广播消息失败: %v", err)
		return err
	}

	return nil
}

// forwardToClientsWithVehicle 转发消息到所有前端客户端（添加vehicle_id）
func (r *MessageRouter) forwardToClientsWithVehicle(sourceConn *pool.Connection, originalMsg *message.Message) error {
	// 创建新消息，添加vehicle_id
	msg := message.NewMessage(originalMsg.Type)
	msg.Data = originalMsg.Data
	msg.VehicleID = sourceConn.VehicleID

	data, err := message.Encode(msg)
	if err != nil {
		return err
	}

	if err := r.pool.BroadcastToClients(data); err != nil {
		msgLogger.Warnf("广播消息失败: %v", err)
		return err
	}

	return nil
}

// forwardSensorUpdate 转发传感器更新
func (r *MessageRouter) forwardSensorUpdate(sourceConn *pool.Connection, originalMsg *message.Message) error {
	msg := message.NewMessage("sensor_update")
	msg.VehicleID = sourceConn.VehicleID
	msg.Data = originalMsg.Data

	data, err := message.Encode(msg)
	if err != nil {
		return err
	}

	return r.pool.BroadcastToClients(data)
}

// forwardStatusUpdate 转发状态更新
func (r *MessageRouter) forwardStatusUpdate(sourceConn *pool.Connection, originalMsg *message.Message) error {
	busy := false
	if busyVal, ok := originalMsg.Data["busy"].(bool); ok {
		busy = busyVal
	}

	msg := message.NewMessage("vehicle_status")
	msg.VehicleID = sourceConn.VehicleID
	msg.Data = map[string]interface{}{
		"online": true,
		"busy":   busy,
	}

	data, err := message.Encode(msg)
	if err != nil {
		return err
	}

	return r.pool.BroadcastToClients(data)
}

// handleCameraSnapshotResponse 处理摄像头快照响应
// 从车载系统接收响应并传递给等待的HTTP请求
func (r *MessageRouter) handleCameraSnapshotResponse(sourceConn *pool.Connection, originalMsg *message.Message) error {
	// 提取request_id
	requestID, ok := originalMsg.Data["request_id"].(string)
	if !ok || requestID == "" {
		msgLogger.Warn("camera_snapshot_response缺少request_id")
		return nil
	}

	// 将响应传递给等待的请求
	msgLogger.Infof("传递摄像头响应: request_id=%s", requestID)

	// 编码响应消息
	respData, err := message.Encode(originalMsg)
	if err != nil {
		msgLogger.Errorf("编码摄像头响应失败: %v", err)
		return err
	}

	// 传递给连接中的pending请求
	sourceConn.DeliverResponse(requestID, respData)
	return nil
}

// sendErrorToSource 发送错误响应（暂未实现，需要记录来源连接）
func (r *MessageRouter) sendErrorToSource(code, message string) error {
	// TODO: 需要在路由器中记录消息来源连接
	msgLogger.Warnf("错误响应: %s - %s", code, message)
	return nil
}
