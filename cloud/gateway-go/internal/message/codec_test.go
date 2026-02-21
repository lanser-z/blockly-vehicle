// Package message 消息编解码测试
package message

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestEncodeDecode(t *testing.T) {
	msg := NewMessage("test_type")
	msg.VehicleID = "vehicle-001"
	msg.Data = map[string]interface{}{
		"key": "value",
		"num": 123,
	}

	// 编码
	data, err := Encode(msg)
	assert.NoError(t, err)
	assert.NotNil(t, data)

	// 解码
	decoded, err := Decode(data)
	assert.NoError(t, err)
	assert.Equal(t, "test_type", decoded.Type)
	assert.Equal(t, "vehicle-001", decoded.VehicleID)
	assert.Equal(t, "value", decoded.Data["key"])
	assert.Equal(t, float64(123), decoded.Data["num"])
}

func TestEncodeVehicleList(t *testing.T) {
	vehicles := []VehicleInfo{
		{VehicleID: "vehicle-001", Name: "小车001", Online: true},
		{VehicleID: "vehicle-002", Name: "小车002", Online: false},
	}

	data, err := EncodeVehicleList(vehicles)
	assert.NoError(t, err)
	assert.NotNil(t, data)

	// 验证JSON格式
	assert.Contains(t, string(data), "vehicle_list")
	assert.Contains(t, string(data), "vehicle-001")
}

func TestEncodeError(t *testing.T) {
	data, err := EncodeError("TEST_CODE", "测试错误")
	assert.NoError(t, err)
	assert.NotNil(t, data)

	assert.Contains(t, string(data), "error")
	assert.Contains(t, string(data), "TEST_CODE")
}

func TestEncodePong(t *testing.T) {
	data, err := EncodePong()
	assert.NoError(t, err)
	assert.NotNil(t, data)

	assert.Contains(t, string(data), "pong")
}

func TestConnTypeString(t *testing.T) {
	assert.Equal(t, "vehicle", ConnTypeVehicle.String())
	assert.Equal(t, "client", ConnTypeClient.String())
	assert.Equal(t, "unknown", ConnTypeUnknown.String())
}

func TestNewMessage(t *testing.T) {
	msg := NewMessage("test")
	assert.Equal(t, "test", msg.Type)
	assert.NotNil(t, msg.Data)
	assert.Greater(t, msg.Timestamp, int64(0))
}

func TestMustEncode(t *testing.T) {
	msg := NewMessage("test")
	msg.VehicleID = "vehicle-001"

	// 正常情况不应panic
	data := MustEncode(msg)
	assert.NotNil(t, data)

	// 验证可以解码
	decoded, err := Decode(data)
	assert.NoError(t, err)
	assert.Equal(t, "test", decoded.Type)
}
