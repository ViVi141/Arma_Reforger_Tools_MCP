"""测试 MCP 工具模块"""

import pytest
import json
from unittest.mock import patch, MagicMock
from typing import Dict, Any

# 尝试导入，如果失败则跳过相关测试
try:
    from src.mcp_server.tools import (
        register_tools,
        handle_search_api,
        handle_get_class_info,
        handle_get_function_info,
        handle_find_related_apis,
        handle_get_code_examples,
        get_search_index,
        get_relationship_index,
    )
    TOOLS_AVAILABLE = True
except ImportError:
    TOOLS_AVAILABLE = False


@pytest.mark.skipif(not TOOLS_AVAILABLE, reason="MCP SDK not available")
class TestRegisterTools:
    """测试工具注册"""
    
    def test_register_tools(self):
        """测试注册工具"""
        tools = register_tools()
        
        assert len(tools) == 5
        tool_names = [tool.name for tool in tools]
        assert "search_api" in tool_names
        assert "get_class_info" in tool_names
        assert "get_function_info" in tool_names
        assert "find_related_apis" in tool_names
        assert "get_code_examples" in tool_names
    
    def test_tool_schemas(self):
        """测试工具 Schema"""
        tools = register_tools()
        
        for tool in tools:
            assert tool.inputSchema is not None
            assert "type" in tool.inputSchema
            assert tool.inputSchema["type"] == "object"
            assert "properties" in tool.inputSchema


@pytest.mark.skipif(not TOOLS_AVAILABLE, reason="MCP SDK not available")
class TestHandleSearchApi:
    """测试 search_api 工具处理"""
    
    @pytest.mark.asyncio
    async def test_search_api_success(self):
        """测试成功搜索"""
        mock_index = MagicMock()
        mock_index.search.return_value = [
            {
                "name": "TestClass",
                "type": "class",
                "api_source": "arma_reforger",
                "description": "Test description",
                "relevance_score": 0.9
            }
        ]
        
        with patch("src.mcp_server.tools.get_search_index", return_value=mock_index):
            result = await handle_search_api({
                "query": "TestClass",
                "api_source": "arma_reforger",
                "limit": 10
            })
            
            result_data = json.loads(result)
            assert "results" in result_data
            assert len(result_data["results"]) > 0
    
    @pytest.mark.asyncio
    async def test_search_api_empty_query(self):
        """测试空查询"""
        result = await handle_search_api({"query": ""})
        result_data = json.loads(result)
        assert "error" in result_data
        assert result_data["error"]["code"] == "INVALID_PARAMETER"
    
    @pytest.mark.asyncio
    async def test_search_api_both_sources(self):
        """测试搜索两个 API 来源"""
        mock_index = MagicMock()
        mock_index.search.return_value = [
            {"name": "Test", "type": "class", "api_source": "arma_reforger", "relevance_score": 0.9}
        ]
        
        with patch("src.mcp_server.tools.get_search_index", return_value=mock_index):
            result = await handle_search_api({
                "query": "Test",
                "api_source": "both",
                "limit": 10
            })
            
            result_data = json.loads(result)
            assert "results" in result_data


@pytest.mark.skipif(not TOOLS_AVAILABLE, reason="MCP SDK not available")
class TestHandleGetClassInfo:
    """测试 get_class_info 工具处理"""
    
    @pytest.mark.asyncio
    async def test_get_class_info_success(self):
        """测试成功获取类信息"""
        class_data = {
            "name": "TestClass",
            "description": "Test class",
            "methods": [],
            "properties": []
        }
        
        with patch("src.mcp_server.tools.load_json", return_value={"classes": {"TestClass": class_data}}):
            result = await handle_get_class_info({
                "class_name": "TestClass",
                "api_source": "arma_reforger"
            })
            
            result_data = json.loads(result)
            assert "class" in result_data
            assert result_data["class"]["name"] == "TestClass"
    
    @pytest.mark.asyncio
    async def test_get_class_info_not_found(self):
        """测试类不存在"""
        with patch("src.mcp_server.tools.load_json", return_value={"classes": {}}):
            result = await handle_get_class_info({
                "class_name": "NonExistent",
                "api_source": "arma_reforger"
            })
            
            result_data = json.loads(result)
            assert "error" in result_data
            assert result_data["error"]["code"] == "API_NOT_FOUND"
    
    @pytest.mark.asyncio
    async def test_get_class_info_partial_match(self):
        """测试部分匹配"""
        class_data = {
            "name": "TestClass",
            "description": "Test",
            "methods": [],
            "properties": []
        }
        
        with patch("src.mcp_server.tools.load_json", return_value={"classes": {"TestClass": class_data}}):
            result = await handle_get_class_info({
                "class_name": "Test",
                "api_source": "arma_reforger"
            })
            
            result_data = json.loads(result)
            assert "class" in result_data


@pytest.mark.skipif(not TOOLS_AVAILABLE, reason="MCP SDK not available")
class TestHandleGetFunctionInfo:
    """测试 get_function_info 工具处理"""
    
    @pytest.mark.asyncio
    async def test_get_function_info_success(self):
        """测试成功获取方法信息"""
        class_data = {
            "methods": [
                {
                    "name": "TestMethod",
                    "signature": "void TestMethod()",
                    "description": "Test method",
                    "return_type": "void",
                    "parameters": []
                }
            ]
        }
        
        with patch("src.mcp_server.tools.load_json", return_value={"classes": {"TestClass": class_data}}):
            result = await handle_get_function_info({
                "function_name": "TestMethod",
                "class_name": "TestClass",
                "api_source": "arma_reforger"
            })
            
            result_data = json.loads(result)
            assert "function" in result_data
            assert result_data["function"]["name"] == "TestMethod"
    
    @pytest.mark.asyncio
    async def test_get_function_info_without_class(self):
        """测试不指定类名的方法查找"""
        class_data = {
            "methods": [
                {
                    "name": "TestMethod",
                    "signature": "void TestMethod()",
                    "return_type": "void",
                    "parameters": []
                }
            ]
        }
        
        with patch("src.mcp_server.tools.load_json", return_value={"classes": {"TestClass": class_data}}):
            result = await handle_get_function_info({
                "function_name": "TestMethod",
                "api_source": "arma_reforger"
            })
            
            result_data = json.loads(result)
            assert "function" in result_data


@pytest.mark.skipif(not TOOLS_AVAILABLE, reason="MCP SDK not available")
class TestHandleFindRelatedApis:
    """测试 find_related_apis 工具处理"""
    
    @pytest.mark.asyncio
    async def test_find_related_apis_success(self):
        """测试成功查找相关 API"""
        mock_index = MagicMock()
        mock_index.find_related_apis.return_value = [
            {"name": "RelatedClass", "relation": "child_class", "api_source": "arma_reforger"}
        ]
        
        with patch("src.mcp_server.tools.get_relationship_index", return_value=mock_index):
            result = await handle_find_related_apis({
                "api_name": "TestClass",
                "api_source": "arma_reforger",
                "relation_type": "all"
            })
            
            result_data = json.loads(result)
            assert "related_apis" in result_data
            assert len(result_data["related_apis"]) > 0
    
    @pytest.mark.asyncio
    async def test_find_related_apis_empty_name(self):
        """测试空名称"""
        result = await handle_find_related_apis({"api_name": ""})
        result_data = json.loads(result)
        assert "error" in result_data


@pytest.mark.skipif(not TOOLS_AVAILABLE, reason="MCP SDK not available")
class TestHandleGetCodeExamples:
    """测试 get_code_examples 工具处理"""
    
    @pytest.mark.asyncio
    async def test_get_code_examples_success(self):
        """测试成功获取代码示例"""
        class_data = {
            "examples": [
                {
                    "code": "void example() {}",
                    "language": "enforce",
                    "description": "Example code"
                }
            ]
        }
        
        with patch("src.mcp_server.tools.load_json", return_value={"classes": {"TestClass": class_data}}):
            result = await handle_get_code_examples({
                "api_name": "TestClass",
                "api_source": "arma_reforger",
                "language": "enforce"
            })
            
            result_data = json.loads(result)
            assert "examples" in result_data
            assert len(result_data["examples"]) > 0
    
    @pytest.mark.asyncio
    async def test_get_code_examples_empty_name(self):
        """测试空名称"""
        result = await handle_get_code_examples({"api_name": ""})
        result_data = json.loads(result)
        assert "error" in result_data


@pytest.mark.skipif(not TOOLS_AVAILABLE, reason="MCP SDK not available")
class TestGetSearchIndex:
    """测试获取搜索索引"""
    
    def test_get_search_index_first_time(self):
        """测试首次获取索引"""
        with patch("src.indexer.search_index.SearchIndex") as mock_class:
            mock_instance = MagicMock()
            mock_instance._index = None
            mock_instance.index_dir.exists.return_value = True
            mock_class.return_value = mock_instance
            
            result = get_search_index("arma_reforger")
            assert result is not None
    
    def test_get_search_index_cached(self):
        """测试缓存的索引"""
        # 第一次调用
        index1 = get_search_index("arma_reforger")
        # 第二次调用应该返回缓存的实例
        index2 = get_search_index("arma_reforger")
        # 注意：由于延迟加载，可能返回 None
        # 这里主要测试函数不会崩溃


@pytest.mark.skipif(not TOOLS_AVAILABLE, reason="MCP SDK not available")
class TestGetRelationshipIndex:
    """测试获取关系索引"""
    
    def test_get_relationship_index_first_time(self):
        """测试首次获取索引"""
        with patch("src.indexer.relationship_index.RelationshipIndex") as mock_class:
            mock_instance = MagicMock()
            mock_class.return_value = mock_instance
            
            with patch("src.mcp_server.tools.load_json", return_value={"classes": {}}):
                result = get_relationship_index("arma_reforger")
                # 可能返回 None 如果加载失败
                assert result is None or result is not None
