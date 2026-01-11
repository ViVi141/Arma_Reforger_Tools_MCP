"""测试资源模块"""

import pytest
import json
from unittest.mock import patch, MagicMock

# 尝试导入，如果失败则跳过相关测试
try:
    from src.mcp_server.resources import (
        register_resources,
        get_resource,
        get_api_index,
        get_class_resource,
    )
    RESOURCES_AVAILABLE = True
except ImportError:
    RESOURCES_AVAILABLE = False


@pytest.mark.skipif(not RESOURCES_AVAILABLE, reason="MCP SDK not available")
class TestRegisterResources:
    """测试资源注册"""
    
    def test_register_resources(self):
        """测试注册资源"""
        resources = register_resources()
        
        assert len(resources) >= 2
        # Resource 对象可能有不同的属性访问方式
        resource_uris = [r.uri if hasattr(r, 'uri') else str(r) for r in resources]
        # 检查是否包含索引资源
        assert any("index" in str(r) or "index" in (r.uri if hasattr(r, 'uri') else '') for r in resources)


@pytest.mark.skipif(not RESOURCES_AVAILABLE, reason="MCP SDK not available")
class TestGetApiIndex:
    """测试获取 API 索引"""
    
    def test_get_api_index(self):
        """测试获取索引"""
        api_data = {
            "classes": {
                "TestClass1": {},
                "TestClass2": {}
            }
        }
        
        with patch("src.mcp_server.resources.load_json", return_value=api_data):
            result = get_api_index()
            result_data = json.loads(result)
            
            assert "arma_reforger" in result_data or "enfusion" in result_data
    
    def test_get_api_index_no_data(self):
        """测试无数据时获取索引"""
        with patch("src.mcp_server.resources.load_json", return_value=None):
            result = get_api_index()
            result_data = json.loads(result)
            # 应该返回空索引或默认结构
            assert isinstance(result_data, dict)


@pytest.mark.skipif(not RESOURCES_AVAILABLE, reason="MCP SDK not available")
class TestGetClassResource:
    """测试获取类资源"""
    
    def test_get_class_resource_success(self):
        """测试成功获取类资源"""
        class_data = {
            "name": "TestClass",
            "description": "Test",
            "methods": []
        }
        
        api_data = {"classes": {"TestClass": class_data}}
        
        with patch("src.mcp_server.resources.load_json", return_value=api_data):
            result = get_class_resource("TestClass")
            result_data = json.loads(result)
            
            assert result_data["name"] == "TestClass"
    
    def test_get_class_resource_not_found(self):
        """测试类不存在"""
        with patch("src.mcp_server.resources.load_json", return_value={"classes": {}}):
            result = get_class_resource("NonExistent")
            result_data = json.loads(result)
            
            assert "error" in result_data
            assert result_data["error"]["code"] == "API_NOT_FOUND"
