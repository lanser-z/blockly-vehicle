// Package pool 连接池测试
package pool

import (
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"blockly-gateway/internal/message"
)

func TestNewPool(t *testing.T) {
	p := NewPool(30*time.Second, 60*time.Second)
	assert.NotNil(t, p)
	assert.Equal(t, 0, len(p.GetVehicleList()))
	assert.Equal(t, 30*time.Second, p.heartbeatCheckInterval)
	assert.Equal(t, 60*time.Second, p.heartbeatTimeout)
}

func TestPoolGetStats(t *testing.T) {
	p := NewPool(5*time.Second, 10*time.Second)

	stats := p.GetStats()
	assert.Equal(t, 0, stats.VehicleCount)
	assert.Equal(t, 0, stats.ClientCount)
	assert.Equal(t, 0, stats.TotalCount)
	assert.Equal(t, 5*time.Second, stats.CheckInterval)
	assert.Equal(t, 10*time.Second, stats.Timeout)
}

func TestPoolGetVehicleListEmpty(t *testing.T) {
	p := NewPool(30*time.Second, 60*time.Second)
	vehicles := p.GetVehicleList()
	assert.NotNil(t, vehicles)
	assert.Equal(t, 0, len(vehicles))
}

func TestPoolRemoveNonExistentConnection(t *testing.T) {
	p := NewPool(30*time.Second, 60*time.Second)
	// 移除不存在的连接不应panic
	p.RemoveConnection("non-existent")
}

func TestPoolGetNonExistentConnection(t *testing.T) {
	p := NewPool(30*time.Second, 60*time.Second)
	_, exists := p.GetConnection("non-existent")
	assert.False(t, exists)
}

func TestPoolGetNonExistentVehicle(t *testing.T) {
	p := NewPool(30*time.Second, 60*time.Second)
	_, exists := p.GetVehicle("non-existent")
	assert.False(t, exists)
}

func TestPoolUpdateHeartbeatNonExistent(t *testing.T) {
	p := NewPool(30*time.Second, 60*time.Second)
	// 更新不存在的车辆不应panic
	p.UpdateHeartbeat("non-existent")
}

func TestPoolRouteToVehicleNotFound(t *testing.T) {
	p := NewPool(30*time.Second, 60*time.Second)
	testData := []byte(`{"type":"test"}`)
	err := p.RouteToVehicle("non-existent", testData)
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "未连接")
}

func TestPoolBroadcastToEmptyClients(t *testing.T) {
	p := NewPool(30*time.Second, 60*time.Second)
	testData := []byte(`{"type":"test"}`)
	// 广播到空客户端列表不应报错
	err := p.BroadcastToClients(testData)
	assert.NoError(t, err)
}

func TestPoolVehicleListCallback(t *testing.T) {
	p := NewPool(30*time.Second, 60*time.Second)

	callbackCalled := false
	var callbackVehicles []message.VehicleInfo

	p.SetVehicleListCallback(func(vehicles []message.VehicleInfo) {
		callbackCalled = true
		callbackVehicles = vehicles
	})

	// 手动调用通知方法测试回调
	p.notifyVehicleListChanged()

	assert.True(t, callbackCalled)
	assert.NotNil(t, callbackVehicles)
}

func TestPoolStop(t *testing.T) {
	p := NewPool(30*time.Second, 60*time.Second)
	// 停止连接池不应panic
	p.Stop()
}

func TestConnTypeString(t *testing.T) {
	tests := []struct {
		name     string
		connType message.ConnType
		expected string
	}{
		{"Vehicle", message.ConnTypeVehicle, "vehicle"},
		{"Client", message.ConnTypeClient, "client"},
		{"Unknown", message.ConnTypeUnknown, "unknown"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			assert.Equal(t, tt.expected, tt.connType.String())
		})
	}
}

// TestPoolHeartbeatMonitorBasic 基本心跳测试
func TestPoolHeartbeatMonitorBasic(t *testing.T) {
	p := NewPool(100*time.Millisecond, 200*time.Millisecond)
	p.StartHeartbeatMonitor()
	defer p.Stop()

	// 让心跳监控运行一小段时间
	time.Sleep(150 * time.Millisecond)

	// 验证连接池仍然正常
	stats := p.GetStats()
	assert.NotNil(t, stats)
}
