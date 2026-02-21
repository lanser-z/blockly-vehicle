// main blockly-gateway云端网关服务
package main

import (
	"context"
	"fmt"
	stdhttp "net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/sirupsen/logrus"

	"blockly-gateway/internal/config"
	gatewayhttp "blockly-gateway/api/http"
	"blockly-gateway/internal/handler"
	"blockly-gateway/internal/message"
	"blockly-gateway/internal/pool"
)

var (
	Version   = "dev"
	BuildTime = "unknown"
	logger    = logrus.StandardLogger()
)

func main() {
	// 加载配置文件
	configPath := "configs/config.yaml"
	if envPath := os.Getenv("GATEWAY_CONFIG"); envPath != "" {
		configPath = envPath
	}

	cfg, err := config.Load(configPath)
	if err != nil {
		logger.Fatalf("加载配置失败: %v", err)
	}

	// 设置日志
	logger.SetFormatter(&logrus.JSONFormatter{})
	if cfg.Log.Format == "text" {
		logger.SetFormatter(&logrus.TextFormatter{})
	}

	// 设置日志级别
	switch cfg.Log.Level {
	case "debug":
		logger.SetLevel(logrus.DebugLevel)
	case "info":
		logger.SetLevel(logrus.InfoLevel)
	case "warn":
		logger.SetLevel(logrus.WarnLevel)
	case "error":
		logger.SetLevel(logrus.ErrorLevel)
	default:
		logger.SetLevel(logrus.InfoLevel)
	}

	// 设置连接池日志
	pool.SetLogger(logger)

	logger.Infof("Blockly云端网关服务启动中... version=%s build_time=%s", Version, BuildTime)
	logger.Infof("配置加载成功: %s", configPath)

	// 创建连接池
	connectionPool := pool.NewPool(cfg.GetHeartbeatInterval(), cfg.GetHeartbeatTimeout())

	// 设置车辆列表变化回调
	connectionPool.SetVehicleListCallback(func(vehicles []message.VehicleInfo) {
		data, err := message.EncodeVehicleList(vehicles)
		if err != nil {
			logger.Errorf("编码车辆列表失败: %v", err)
			return
		}

		// 广播到所有前端客户端
		if err := connectionPool.BroadcastToClients(data); err != nil {
			logger.Warnf("广播车辆列表失败: %v", err)
		} else {
			logger.Infof("车辆列表已广播，当前在线: %d辆", len(vehicles))
		}
	})

	// 启动心跳监控
	connectionPool.StartHeartbeatMonitor()
	defer connectionPool.Stop()

	// 创建HTTP路由
	router := gin.New()
	router.Use(gin.Recovery())
	router.Use(corsMiddleware())
	router.Use(loggerMiddleware())

	// 注册HTTP API
	httpHandlers := gatewayhttp.NewHandlers(connectionPool)
	router.GET("/health", httpHandlers.HealthCheck)
	router.GET("/api/vehicles", httpHandlers.GetVehicles)
	router.NoRoute(httpHandlers.NotFound)

	// 注册WebSocket端点
	wsHandler := handler.NewWebSocketHandler(connectionPool)
	router.GET("/ws/gateway", wsHandler.HandleWebSocket)

	// 创建HTTP服务器
	addr := cfg.GetAddr()
	srv := &stdhttp.Server{
		Addr:    addr,
		Handler: router,
	}

	// 启动HTTP服务器（非阻塞）
	go func() {
		logger.Infof("网关服务启动于 %s", addr)
		if err := srv.ListenAndServe(); err != nil && err != stdhttp.ErrServerClosed {
			logger.Fatalf("服务启动失败: %v", err)
		}
	}()

	// 等待中断信号
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	logger.Info("正在关闭服务...")

	// 优雅关闭
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := srv.Shutdown(ctx); err != nil {
		logger.Errorf("服务关闭失败: %v", err)
	}

	logger.Info("服务已退出")
}

// corsMiddleware CORS中间件
func corsMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		c.Writer.Header().Set("Access-Control-Allow-Origin", "*")
		c.Writer.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
		c.Writer.Header().Set("Access-Control-Allow-Headers", "Content-Type, X-Vehicle-ID")

		if c.Request.Method == "OPTIONS" {
			c.AbortWithStatus(stdhttp.StatusNoContent)
			return
		}

		c.Next()
	}
}

// loggerMiddleware 日志中间件
func loggerMiddleware() gin.HandlerFunc {
	return func(c *gin.Context) {
		start := time.Now()
		path := c.Request.URL.Path
		query := c.Request.URL.RawQuery

		c.Next()

		latency := time.Since(start)
		statusCode := c.Writer.Status()

		entry := logger.WithFields(logrus.Fields{
			"method":     c.Request.Method,
			"path":       path,
			"query":      query,
			"status":     statusCode,
			"latency":    latency,
			"ip":         c.ClientIP(),
			"user_agent": c.Request.UserAgent(),
		})

		if len(c.Errors) > 0 {
			entry.Error(c.Errors.String())
		} else {
			entry.Info("HTTP请求")
		}
	}
}

func init() {
	// 设置版本信息
	if Version == "dev" {
		if buildTime, err := time.Parse("2006-01-02_15:04:05", BuildTime); err == nil {
			Version = fmt.Sprintf("dev-%s", buildTime.Format("20060102"))
		}
	}
}
