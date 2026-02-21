// Package message 消息编解码
package message

import (
	"encoding/json"
	"fmt"
)

// Encode 编码消息为JSON
func Encode(msg *Message) ([]byte, error) {
	return json.Marshal(msg)
}

// Decode 解码JSON消息
func Decode(data []byte) (*Message, error) {
	var msg Message
	if err := json.Unmarshal(data, &msg); err != nil {
		return nil, fmt.Errorf("消息解码失败: %w", err)
	}
	return &msg, nil
}

// EncodeVehicleList 编码车辆列表响应
func EncodeVehicleList(vehicles []VehicleInfo) ([]byte, error) {
	resp := map[string]interface{}{
		"type": "vehicle_list",
		"data": VehicleListData{
			Vehicles: vehicles,
		},
	}
	return json.Marshal(resp)
}

// EncodeError 编码错误响应
func EncodeError(code, message string) ([]byte, error) {
	resp := map[string]interface{}{
		"type": "error",
		"data": ErrorData{
			Code:    code,
			Message: message,
		},
	}
	return json.Marshal(resp)
}

// EncodePong 编码心跳响应
func EncodePong() ([]byte, error) {
	resp := map[string]interface{}{
		"type": "pong",
	}
	return json.Marshal(resp)
}

// MustEncode 编码消息，panic失败情况
func MustEncode(msg *Message) []byte {
	data, err := Encode(msg)
	if err != nil {
		panic(err)
	}
	return data
}
