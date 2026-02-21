# Makefile for blockly-gateway

APP_NAME=gateway
VERSION=$(shell git describe --tags --always --dirty 2>/dev/null || echo "dev")
BUILD_TIME=$(shell date -u '+%Y-%m-%d_%H:%M:%S')
LDFLAGS=-ldflags "-X main.Version=$(VERSION) -X main.BuildTime=$(BUILD_TIME)"

# Go编译参数
CGO_ENABLED=0
GOFLAGS=-trimpath

.PHONY: all build clean test run deps install deploy

all: build

## deps: 下载依赖
deps:
	go mod download
	go mod tidy

## build: 编译二进制文件
build:
	CGO_ENABLED=0 $(GOFLAGS) go build $(LDFLAGS) -o bin/$(APP_NAME) cmd/gateway/main.go

## build-linux: 交叉编译到Linux
build-linux:
	CGO_ENABLED=0 GOOS=linux GOARCH=amd64 $(GOFLAGS) go build $(LDFLAGS) -o bin/$(APP_NAME)-linux-amd64 cmd/gateway/main.go

## build-all: 编译所有平台
build-all: build-linux
	@echo "编译完成"

## clean: 清理编译产物
clean:
	rm -rf bin/

## test: 运行测试
test:
	go test -v -race -cover ./...

## run: 运行服务
run:
	go run cmd/gateway/main.go

## install: 安装到系统
install: build
	install -m 755 bin/$(APP_NAME) /usr/local/bin/

## deploy: 部署到服务器
deploy: build-linux
	@echo "部署到 /opt/blockly-gateway"
	sudo mkdir -p /opt/blockly-gateway/bin
	sudo mkdir -p /opt/blockly-gateway/configs
	sudo cp bin/$(APP_NAME)-linux-amd64 /opt/blockly-gateway/bin/gateway
	sudo cp -r configs/* /opt/blockly-gateway/configs/
	sudo chown -R www-data:www-data /opt/blockly-gateway
	sudo chmod +x /opt/blockly-gateway/bin/gateway
	@echo "部署完成"
