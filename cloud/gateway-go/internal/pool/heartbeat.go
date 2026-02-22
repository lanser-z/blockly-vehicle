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
// 修复：避免在持锁状态下调用可能阻塞或尝试获取锁的方法
func (p *Pool) checkTimeouts() {
	// 第一阶段：收集超时连接信息（持锁）
	p.mu.Lock()
	now := time.Now()
	timeoutConns := make([]*Connection, 0)

	for vehicleID, conn := range p.vehicles {
		if now.Sub(conn.LastHeartbeat) > p.heartbeatTimeout {
			logger.Warnf("车辆 %s 心跳超时，准备断开连接", vehicleID)
			// 从连接池移除
			delete(p.vehicles, vehicleID)
			delete(p.connections, conn.ID)
			// 收集需要关闭的连接
			timeoutConns = append(timeoutConns, conn)
		}
	}

	// 标记需要通知车辆列表变化
	needNotify := len(timeoutConns) > 0
	p.mu.Unlock()

	// 第二阶段：关闭连接（不持锁，避免死锁）
	for _, conn := range timeoutConns {
		if err := conn.Close(); err != nil {
			logger.Errorf("关闭连接失败: %v", err)
		}
	}

	// 第三阶段：通知车辆列表变化（不持锁，避免与GetVehicleList死锁）
	if needNotify {
		p.notifyVehicleListChanged()
		logger.Warnf("清理了 %d 个超时连接", len(timeoutConns))
	}
}

// SetLogger 设置日志器
func SetLogger(l *logrus.Logger) {
	logger = l
}
