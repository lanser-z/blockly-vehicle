// Package config 配置管理
package config

import (
	"fmt"
	"time"

	"github.com/spf13/viper"
)

// Config 应用配置
type Config struct {
	Server   ServerConfig   `mapstructure:"server"`
	Gateway  GatewayConfig  `mapstructure:"gateway"`
	Log      LogConfig      `mapstructure:"log"`
}

// ServerConfig 服务器配置
type ServerConfig struct {
	Host string `mapstructure:"host"`
	Port int    `mapstructure:"port"`
}

// GatewayConfig 网关配置
type GatewayConfig struct {
	HeartbeatCheckInterval int `mapstructure:"heartbeat_check_interval"`
	HeartbeatTimeout       int `mapstructure:"heartbeat_timeout"`
}

// LogConfig 日志配置
type LogConfig struct {
	Level  string `mapstructure:"level"`
	Format string `mapstructure:"format"`
}

// Load 加载配置文件
func Load(configPath string) (*Config, error) {
	v := viper.New()
	v.SetConfigFile(configPath)
	v.SetConfigType("yaml")

	// 设置默认值
	v.SetDefault("server.host", "127.0.0.1")
	v.SetDefault("server.port", 5001)
	v.SetDefault("gateway.heartbeat_check_interval", 30)
	v.SetDefault("gateway.heartbeat_timeout", 60)
	v.SetDefault("log.level", "info")
	v.SetDefault("log.format", "json")

	// 读取配置文件
	if err := v.ReadInConfig(); err != nil {
		return nil, fmt.Errorf("读取配置文件失败: %w", err)
	}

	var cfg Config
	if err := v.Unmarshal(&cfg); err != nil {
		return nil, fmt.Errorf("解析配置文件失败: %w", err)
	}

	return &cfg, nil
}

// GetAddr 获取服务器地址
func (c *Config) GetAddr() string {
	return fmt.Sprintf("%s:%d", c.Server.Host, c.Server.Port)
}

// GetHeartbeatInterval 获取心跳检测间隔
func (c *Config) GetHeartbeatInterval() time.Duration {
	return time.Duration(c.Gateway.HeartbeatCheckInterval) * time.Second
}

// GetHeartbeatTimeout 获取心跳超时时间
func (c *Config) GetHeartbeatTimeout() time.Duration {
	return time.Duration(c.Gateway.HeartbeatTimeout) * time.Second
}
