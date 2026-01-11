"""测试错误处理模块"""

import pytest
import json

from src.mcp_server.errors import (
    ErrorCode,
    APIError,
    InvalidParameterError,
    APINotFoundError,
    SearchFailedError,
    DataLoadError,
    IndexNotFoundError,
)


class TestErrorCode:
    """测试错误代码枚举"""
    
    def test_error_codes(self):
        """测试所有错误代码"""
        assert ErrorCode.INVALID_PARAMETER.value == "INVALID_PARAMETER"
        assert ErrorCode.API_NOT_FOUND.value == "API_NOT_FOUND"
        assert ErrorCode.SEARCH_FAILED.value == "SEARCH_FAILED"
        assert ErrorCode.DATA_LOAD_ERROR.value == "DATA_LOAD_ERROR"
        assert ErrorCode.INDEX_NOT_FOUND.value == "INDEX_NOT_FOUND"
        assert ErrorCode.INTERNAL_ERROR.value == "INTERNAL_ERROR"


class TestAPIError:
    """测试 API 错误基类"""
    
    def test_api_error_init(self):
        """测试初始化"""
        error = APIError(ErrorCode.INVALID_PARAMETER, "Test error", {"key": "value"})
        
        assert error.code == ErrorCode.INVALID_PARAMETER
        assert error.message == "Test error"
        assert error.details == {"key": "value"}
    
    def test_api_error_to_dict(self):
        """测试转换为字典"""
        error = APIError(ErrorCode.INVALID_PARAMETER, "Test error")
        error_dict = error.to_dict()
        
        assert "error" in error_dict
        assert error_dict["error"]["code"] == "INVALID_PARAMETER"
        assert error_dict["error"]["message"] == "Test error"
    
    def test_api_error_to_json(self):
        """测试转换为 JSON"""
        error = APIError(ErrorCode.INVALID_PARAMETER, "Test error")
        error_json = error.to_json()
        
        error_dict = json.loads(error_json)
        assert "error" in error_dict


class TestInvalidParameterError:
    """测试参数无效错误"""
    
    def test_invalid_parameter_error(self):
        """测试参数错误"""
        error = InvalidParameterError("param1", "reason")
        
        assert error.code == ErrorCode.INVALID_PARAMETER
        assert "param1" in error.message
        assert error.details["parameter"] == "param1"
    
    def test_invalid_parameter_error_no_reason(self):
        """测试无原因的参数错误"""
        error = InvalidParameterError("param1")
        assert error.code == ErrorCode.INVALID_PARAMETER


class TestAPINotFoundError:
    """测试 API 未找到错误"""
    
    def test_api_not_found_error(self):
        """测试 API 未找到"""
        error = APINotFoundError("TestClass", "类")
        
        assert error.code == ErrorCode.API_NOT_FOUND
        assert "TestClass" in error.message
        assert error.details["api_name"] == "TestClass"
    
    def test_api_not_found_error_default_type(self):
        """测试默认类型"""
        error = APINotFoundError("TestClass")
        assert "API" in error.message or "TestClass" in error.message


class TestSearchFailedError:
    """测试搜索失败错误"""
    
    def test_search_failed_error(self):
        """测试搜索失败"""
        error = SearchFailedError("test query", "reason")
        
        assert error.code == ErrorCode.SEARCH_FAILED
        assert "test query" in error.message
        assert error.details["query"] == "test query"


class TestDataLoadError:
    """测试数据加载错误"""
    
    def test_data_load_error(self):
        """测试数据加载失败"""
        error = DataLoadError("test.json", "file not found")
        
        assert error.code == ErrorCode.DATA_LOAD_ERROR
        assert "test.json" in error.message
        assert error.details["file_path"] == "test.json"


class TestIndexNotFoundError:
    """测试索引未找到错误"""
    
    def test_index_not_found_error(self):
        """测试索引未找到"""
        error = IndexNotFoundError("search", "arma_reforger")
        
        assert error.code == ErrorCode.INDEX_NOT_FOUND
        assert "search" in error.message
        assert error.details["index_type"] == "search"
        assert error.details["api_source"] == "arma_reforger"
