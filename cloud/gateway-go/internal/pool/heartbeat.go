// Package pool 心跳检测
package pool

import (
	"time"

	"github.com/sirupsen/logrus"
)

var logger = logrus.StandardLogger()

// heartbeatMonitor 心跳监控goroutine
func (p *Pool) heartbeatMonitor() {
	ticker := time.NewTicker(p.heartbeatCheckInterval)
	defer ticker.Stop()

	logger.Infof("心跳检测已启动，间隔=%v，超时=%v", p.heartbeatCheckInterval, p.heartbeatTimeout)

	for {
		select {
		case <-ticker.C:
			p.checkTimeouts()
		case <-p.ctx.Done():
			logger.Info("心跳检测已停止")
			return
		}
	}
}

// checkTimeouts 检查超时连接
func (p *Pool) checkTimeouts() {
	p.mu.Lock()
	defer p.mu.Unlock()

	now := time.Now()
	timeoutVehicles := make([]string, 0)

	for vehicleID, conn := range p.vehicles {
		if now.Sub(conn.LastHeartbeat) > p.heartbeatTimeout {
			timeoutVehicles = append(timeoutVehicles, vehicleID)
		}
	}

	// 清理超时连接
	for _, vehicleID := range timeoutVehicles {
		conn := p.vehicles[vehicleID]
		logger.Warnf("车辆 %s 心跳超时，断开连接", vehicleID)

		// 关闭WebSocket连接
		conn.Close()

		// 从连接池移除
		delete(p.vehicles, vehicleID)
		delete(p.connections, conn.ID)

		// 通知车辆列表变化
		p.notifyVehicleListChanged()
	}

	if len(timeoutVehicles) > 0 {
		logger.Warnf("清理了 %d 个超时连接", len(timeoutVehicles))
	}
}

// SetLogger 设置日志器
func SetLogger(l *logrus.Logger) {
	logger = l
}
