"""错误处理模块"""

from enum import Enum
from typing import Dict, Any
import json


class ErrorCode(Enum):
    """错误代码枚举"""
    INVALID_PARAMETER = "INVALID_PARAMETER"
    API_NOT_FOUND = "API_NOT_FOUND"
    SEARCH_FAILED = "SEARCH_FAILED"
    DATA_LOAD_ERROR = "DATA_LOAD_ERROR"
    INDEX_NOT_FOUND = "INDEX_NOT_FOUND"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class APIError(Exception):
    """API 错误基类"""
    
    def __init__(self, code: ErrorCode, message: str, details: Dict[str, Any] = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "error": {
                "code": self.code.value,
                "message": self.message,
                "details": self.details
            }
        }
    
    def to_json(self) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class InvalidParameterError(APIError):
    """参数无效错误"""
    
    def __init__(self, parameter: str, reason: str = ""):
        message = f"参数无效: {parameter}"
        if reason:
            message += f" - {reason}"
        super().__init__(ErrorCode.INVALID_PARAMETER, message, {"parameter": parameter})


class APINotFoundError(APIError):
    """API 未找到错误"""
    
    def __init__(self, api_name: str, api_type: str = "API"):
        message = f"未找到{api_type}: {api_name}"
        super().__init__(ErrorCode.API_NOT_FOUND, message, {"api_name": api_name})


class SearchFailedError(APIError):
    """搜索失败错误"""
    
    def __init__(self, query: str, reason: str = ""):
        message = f"搜索失败: {query}"
        if reason:
            message += f" - {reason}"
        super().__init__(ErrorCode.SEARCH_FAILED, message, {"query": query})


class DataLoadError(APIError):
    """数据加载错误"""
    
    def __init__(self, file_path: str, reason: str = ""):
        message = f"数据加载失败: {file_path}"
        if reason:
            message += f" - {reason}"
        super().__init__(ErrorCode.DATA_LOAD_ERROR, message, {"file_path": file_path})


class IndexNotFoundError(APIError):
    """索引未找到错误"""
    
    def __init__(self, index_type: str, api_source: str):
        message = f"索引未找到: {index_type} ({api_source})"
        super().__init__(
            ErrorCode.INDEX_NOT_FOUND,
            message,
            {"index_type": index_type, "api_source": api_source}
        )
