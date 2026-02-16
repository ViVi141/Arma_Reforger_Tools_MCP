"""MCP 资源实现"""

from typing import List
from mcp.types import Resource

from src.utils.helpers import get_cached_api_data


def register_resources() -> List[Resource]:
    """注册所有资源"""
    return [
        Resource(
            uri="arma-reforger-api://index",
            name="API Index",
            description="所有 API 的索引列表",
            mimeType="application/json"
        ),
        Resource(
            uri="arma-reforger-api://class/{class_name}",
            name="Class Documentation",
            description="类的完整文档",
            mimeType="application/json"
        ),
    ]


async def get_resource(uri: str) -> str:
    """获取资源内容"""
    if uri == "arma-reforger-api://index":
        return get_api_index()
    elif uri.startswith("arma-reforger-api://class/"):
        class_name = uri.replace("arma-reforger-api://class/", "")
        return get_class_resource(class_name)
    else:
        return ""


def get_api_index() -> str:
    """获取 API 索引"""
    import json
    
    index_data = {
        "arma_reforger": {},
        "enfusion": {}
    }
    
    for source in ["arma_reforger", "enfusion"]:
        api_data = get_cached_api_data(source)
        if api_data:
            classes = api_data.get("classes", {})
            index_data[source] = {
                "total_classes": len(classes),
                "classes": list(classes.keys())[:100]  # 限制返回数量
            }
    
    return json.dumps(index_data, ensure_ascii=False, indent=2)


def get_class_resource(class_name: str) -> str:
    """获取类资源"""
    import json
    
    for source in ["arma_reforger", "enfusion"]:
        api_data = get_cached_api_data(source)
        if api_data:
            classes = api_data.get("classes", {})
            if class_name in classes:
                return json.dumps(classes[class_name], ensure_ascii=False, indent=2)
    
    return json.dumps({
        "error": {
            "code": "API_NOT_FOUND",
            "message": f"未找到类: {class_name}"
        }
    }, ensure_ascii=False, indent=2)
