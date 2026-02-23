// Package http HTTP API处理器
package http

import (
	"encoding/base64"
	"encoding/json"
	"fmt"
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/sirupsen/logrus"

	"blockly-gateway/internal/pool"
)

var httpLogger = logrus.WithField("module", "http")

// Handlers HTTP处理器
type Handlers struct {
	pool *pool.Pool
}

// NewHandlers 创建HTTP处理器
func NewHandlers(p *pool.Pool) *Handlers {
	return &Handlers{
		pool: p,
	}
}

// HealthCheckResponse 健康检查响应
type HealthCheckResponse struct {
	Status         string    `json:"status"`
	Timestamp      time.Time `json:"timestamp"`
	VehiclesOnline int       `json:"vehicles_online"`
	Stats          pool.PoolStats `json:"stats"`
}

// VehicleListResponse 车辆列表响应
type VehicleListResponse struct {
	Success bool                       `json:"success"`
	Data    VehicleListData            `json:"data"`
}

// VehicleListData 车辆列表数据
type VehicleListData struct {
	Vehicles []VehicleInfo `json:"vehicles"`
}

// VehicleInfo 车辆信息
type VehicleInfo struct {
	VehicleID string `json:"vehicle_id"`
	Name      string `json:"name"`
	Online    bool   `json:"online"`
}

// HealthCheck 健康检查
func (h *Handlers) HealthCheck(c *gin.Context) {
	stats := h.pool.GetStats()

	c.JSON(http.StatusOK, HealthCheckResponse{
		Status:         "healthy",
		Timestamp:      time.Now(),
		VehiclesOnline: stats.VehicleCount,
		Stats:          stats,
	})
}

// GetVehicles 获取在线车辆列表
func (h *Handlers) GetVehicles(c *gin.Context) {
	vehicles := h.pool.GetVehicleList()

	// 转换为API响应格式
	vehicleInfos := make([]VehicleInfo, 0, len(vehicles))
	for _, v := range vehicles {
		vehicleInfos = append(vehicleInfos, VehicleInfo{
			VehicleID: v.VehicleID,
			Name:      v.Name,
			Online:    v.Online,
		})
	}

	c.JSON(http.StatusOK, VehicleListResponse{
		Success: true,
		Data: VehicleListData{
			Vehicles: vehicleInfos,
		},
	})
}

// NotFound 404处理
func (h *Handlers) NotFound(c *gin.Context) {
	c.JSON(http.StatusNotFound, gin.H{
		"error": "未找到请求的资源",
	})
}

// CameraSnapshot 摄像头快照代理
// 通过 WebSocket 向车载系统请求摄像头快照，并等待响应
func (h *Handlers) CameraSnapshot(c *gin.Context) {
	vehicleID := c.Query("vehicle_id")
	if vehicleID == "" {
		vehicleID = "vehicle-001" // 默认车辆
	}

	// 从连接池获取车辆连接
	conn, exists := h.pool.GetVehicle(vehicleID)
	if !exists {
		c.JSON(http.StatusServiceUnavailable, gin.H{
			"error": fmt.Sprintf("车辆 %s 未连接", vehicleID),
		})
		return
	}

	if conn.IsClosed() {
		c.JSON(http.StatusServiceUnavailable, gin.H{
			"error": fmt.Sprintf("车辆 %s 连接已关闭", vehicleID),
		})
		return
	}

	// 初始化请求响应机制（如果尚未初始化）
	conn.InitPendingRequests(5 * time.Second)

	// 生成唯一的请求ID
	requestID := fmt.Sprintf("cam_%d", time.Now().UnixNano())

	// 创建请求消息
	requestMsg := map[string]interface{}{
		"type": "camera_snapshot_request",
		"data": map[string]interface{}{
			"request_id": requestID,
		},
	}

	msgBytes, err := json.Marshal(requestMsg)
	if err != nil {
		httpLogger.Errorf("编码摄像头请求失败: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "编码请求失败"})
		return
	}

	// 发送请求到车载系统
	if err := conn.Send(msgBytes); err != nil {
		httpLogger.Errorf("发送摄像头请求失败: %v", err)
		c.JSON(http.StatusBadGateway, gin.H{"error": "发送请求失败"})
		return
	}

	httpLogger.Infof("摄像头请求已发送: vehicle_id=%s, request_id=%s", vehicleID, requestID)

	// 等待响应（5秒超时）
	respData, ok := conn.WaitForResponse(requestID, 5*time.Second)
	if !ok {
		httpLogger.Warnf("摄像头响应超时: request_id=%s", requestID)
		// 返回占位图像
		h.sendPlaceholderImage(c)
		return
	}

	// 解析响应
	var resp struct {
		Type string `json:"type"`
		Data struct {
			RequestID string `json:"request_id"`
			Image     string `json:"image"`
		} `json:"data"`
	}
	if err := json.Unmarshal(respData, &resp); err != nil {
		httpLogger.Errorf("解析摄像头响应失败: %v", err)
		h.sendPlaceholderImage(c)
		return
	}

	// 解码Base64图像
	imageBytes, err := base64.StdEncoding.DecodeString(resp.Data.Image)
	if err != nil {
		httpLogger.Errorf("解码Base64图像失败: %v", err)
		h.sendPlaceholderImage(c)
		return
	}

	if len(imageBytes) == 0 {
		httpLogger.Warnf("摄像头图像为空: request_id=%s", requestID)
		h.sendPlaceholderImage(c)
		return
	}

	c.Data(http.StatusOK, "image/jpeg", imageBytes)
	httpLogger.Infof("摄像头图像已返回: request_id=%s, size=%d", requestID, len(imageBytes))
}

// sendPlaceholderImage 发送占位图像
func (h *Handlers) sendPlaceholderImage(c *gin.Context) {
	// 1x1像素透明JPEG
	transparentPixel := []byte{
		0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46, 0x00, 0x01, 0x01, 0x00, 0x00, 0x01,
		0x00, 0x01, 0x00, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43, 0x00, 0x03, 0x02, 0x02, 0x03, 0x02, 0x02,
		0x03, 0x03, 0x03, 0x03, 0x04, 0x03, 0x03, 0x04, 0x05, 0x05, 0x05, 0x05, 0x05, 0x05, 0x05, 0x05,
		0x05, 0x07, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08, 0x08,
		0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
		0xFF, 0xC4, 0x00, 0x01, 0x00, 0x00, 0x01, 0x05, 0x01, 0x00, 0x00, 0x00, 0x01, 0x02, 0x03,
		0x04, 0x05, 0xFF, 0xDA, 0x00, 0x03, 0x01, 0x02, 0x03, 0x00, 0x02, 0x03, 0xFF, 0xD9,
	}
	c.Data(http.StatusOK, "image/jpeg", transparentPixel)
}

// CameraSnapshotDirect 直接摄像头快照（用于测试）
// 这个方法假设车载系统在同一局域网或可通过本地端口访问
func (h *Handlers) CameraSnapshotDirect(c *gin.Context) {
	// 获取第一个在线车辆
	vehicles := h.pool.GetVehicleList()
	if len(vehicles) == 0 {
		c.JSON(http.StatusServiceUnavailable, gin.H{
			"error": "没有在线车辆",
		})
		return
	}

	vehicleID := vehicles[0].VehicleID

	// 检查车辆连接状态
	conn, exists := h.pool.GetVehicle(vehicleID)
	if !exists || conn.IsClosed() {
		c.JSON(http.StatusServiceUnavailable, gin.H{
			"error": fmt.Sprintf("车辆 %s 未连接", vehicleID),
		})
		return
	}

	// 通过 WebSocket 发送快照请求
	// 注意：这需要车载系统实现 camera_snapshot 消息类型的处理
	request := map[string]interface{}{
		"type": "camera_snapshot",
	}

	requestBytes, _ := json.Marshal(request)
	if err := conn.Send(requestBytes); err != nil {
		c.JSON(http.StatusBadGateway, gin.H{"error": "发送请求失败"})
		return
	}

	// 由于 WebSocket 是异步的，实际实现需要等待响应
	// 这里返回一个占位响应
	c.JSON(http.StatusOK, gin.H{
		"status": "requested",
		"vehicle_id": vehicleID,
		"message": "摄像头快照请求已发送，请通过 WebSocket 接收图像数据",
	})
}
