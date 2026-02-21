// Package http HTTP API处理器
package http

import (
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
