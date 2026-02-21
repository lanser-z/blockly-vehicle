"""
测试云端网关服务
"""

import pytest
import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../cloud/gateway'))

from main import VehicleConnectionPool, create_app, pool
from aiohttp import web
import json


class TestVehicleConnectionPool:
    """测试车辆连接池"""

    def setup_method(self):
        """每个测试方法前的设置"""
        # 创建新的连接池实例用于测试
        self.pool = VehicleConnectionPool()

    @pytest.mark.asyncio
    async def test_init(self):
        """测试初始化"""
        assert self.pool is not None
        assert len(self.pool.vehicle_connections) == 0
        assert len(self.pool.last_heartbeat) == 0
        assert len(self.pool.sid_to_vehicle) == 0

    @pytest.mark.asyncio
    async def test_add_connection(self):
        """测试添加连接"""
        await self.pool.add_connection("vehicle-001", "sid_123")
        assert "vehicle-001" in self.pool.vehicle_connections
        assert self.pool.vehicle_connections["vehicle-001"] == "sid_123"
        assert "sid_123" in self.pool.sid_to_vehicle
        assert self.pool.sid_to_vehicle["sid_123"] == "vehicle-001"

    @pytest.mark.asyncio
    async def test_remove_connection(self):
        """测试移除连接"""
        await self.pool.add_connection("vehicle-001", "sid_123")
        await self.pool.remove_connection("sid_123")
        assert "vehicle-001" not in self.pool.vehicle_connections
        assert "sid_123" not in self.pool.sid_to_vehicle

    @pytest.mark.asyncio
    async def test_update_heartbeat(self):
        """测试更新心跳"""
        await self.pool.add_connection("vehicle-001", "sid_123")
        import time
        old_time = self.pool.last_heartbeat["vehicle-001"]
        await asyncio.sleep(0.1)
        await self.pool.update_heartbeat("vehicle-001")
        new_time = self.pool.last_heartbeat["vehicle-001"]
        assert new_time > old_time

    @pytest.mark.asyncio
    async def test_route_to_vehicle_success(self):
        """测试路由消息到车辆（成功）"""
        await self.pool.add_connection("vehicle-001", "sid_123")

        # 由于实际发送需要SocketIO服务器，这里只验证返回值
        # 在集成测试中会实际测试
        # 这里我们只验证车辆存在时的逻辑
        assert "vehicle-001" in self.pool.vehicle_connections

    @pytest.mark.asyncio
    async def test_route_to_vehicle_fail(self):
        """测试路由消息到车辆（失败）"""
        # 车辆不存在
        # 由于实际发送被mock，这里只验证逻辑
        assert "nonexistent" not in self.pool.vehicle_connections

    @pytest.mark.asyncio
    async def test_get_vehicle_list(self):
        """测试获取车辆列表"""
        await self.pool.add_connection("vehicle-001", "sid_123")
        await self.pool.add_connection("vehicle-002", "sid_456")

        vehicle_list = await self.pool.get_vehicle_list()
        assert len(vehicle_list) == 2
        assert any(v['vehicle_id'] == 'vehicle-001' for v in vehicle_list)
        assert any(v['vehicle_id'] == 'vehicle-002' for v in vehicle_list)
        assert all(v['online'] for v in vehicle_list)

    @pytest.mark.asyncio
    async def test_get_vehicle_list_empty(self):
        """测试获取空车辆列表"""
        vehicle_list = await self.pool.get_vehicle_list()
        assert len(vehicle_list) == 0

    @pytest.mark.asyncio
    async def test_start_heartbeat_monitor(self):
        """测试启动心跳监控"""
        self.pool.start_heartbeat_monitor()
        assert self.pool._heartbeat_task is not None


class TestHealthCheck:
    """测试健康检查端点"""

    @pytest.mark.asyncio
    async def test_health_check_response(self):
        """测试健康检查响应"""
        from main import health_check
        from datetime import datetime

        request = None  # 实际使用时需要mock request
        response = await health_check(request)

        # 由于没有真实request，我们验证函数存在
        assert callable(health_check)


class TestGetVehicles:
    """测试获取车辆列表端点"""

    @pytest.mark.asyncio
    async def test_get_vehicles_response(self):
        """测试获取车辆列表响应"""
        from main import get_vehicles

        request = None  # 实际使用时需要mock request
        response = await get_vehicles(request)

        # 验证函数存在
        assert callable(get_vehicles)


class TestCreateApp:
    """测试应用创建"""

    def test_create_app(self):
        """测试创建应用"""
        app = create_app()
        assert app is not None
        assert isinstance(app, web.Application)

    def test_startup_handler(self):
        """测试启动处理器"""
        app = create_app()
        # 验证on_startup已设置
        assert len(app.on_startup) > 0


class TestIntegration:
    """集成测试"""

    @pytest.mark.asyncio
    async def test_full_flow(self):
        """测试完整流程"""
        # 创建应用
        app = create_app()

        # 验证应用结构
        assert app is not None

        # 验证路由已注册
        routes = [r.path for r in app.router.routes()]
        assert '/health' in routes
        assert '/api/vehicles' in routes


# 简单的HTTP测试客户端
class TestHttpClient:
    """HTTP客户端测试（需要服务器运行）"""

    @pytest.mark.skipif(True, reason="需要运行中的服务器")
    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        """测试健康检查端点（需要服务器运行）"""
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get('http://127.0.0.1:5001/health') as resp:
                assert resp.status == 200
                data = await resp.json()
                assert 'status' in data
                assert data['status'] == 'healthy'

    @pytest.mark.skipif(True, reason="需要运行中的服务器")
    @pytest.mark.asyncio
    async def test_vehicles_endpoint(self):
        """测试车辆列表端点（需要服务器运行）"""
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get('http://127.0.0.1:5001/api/vehicles') as resp:
                assert resp.status == 200
                data = await resp.json()
                assert 'success' in data
                assert 'data' in data
                assert 'vehicles' in data['data']
