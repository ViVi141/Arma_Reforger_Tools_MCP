"""MCP 工具实现"""

import atexit
import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from mcp.types import Tool

from src.indexer.search_index import SearchIndex
from src.indexer.relationship_index import RelationshipIndex
from src.mcp_server.errors import APINotFoundError, InvalidParameterError
from src.utils.helpers import get_cached_api_data

logger = logging.getLogger(__name__)


def _json_response(data: Dict[str, Any]) -> str:
    """统一 JSON 响应格式"""
    return json.dumps(data, ensure_ascii=False, indent=2)


def _resolve_api_sources(api_source: str) -> List[str]:
    """解析 API 来源为列表（仅 arma_reforger、enfusion）"""
    if api_source == "both":
        return ["arma_reforger", "enfusion"]
    return [api_source]


def _resolve_search_sources(api_source: str) -> List[str]:
    """解析搜索来源为列表（含 Wiki）"""
    if api_source == "all":
        return ["arma_reforger", "enfusion", "arma_reforger_wiki"]
    if api_source == "both":
        return ["arma_reforger", "enfusion"]
    return [api_source]


def _find_class_in_sources(
    class_name: str,
    sources: List[str],
    include_examples: bool,
) -> Dict[str, Any]:
    """
    在多个来源中查找类，返回包含 class 键的字典。
    未找到时抛出 APINotFoundError。
    """
    for source in sources:
        api_data = get_cached_api_data(source)
        if not api_data:
            continue
        classes = api_data.get("classes", {})
        if class_name in classes:
            class_data = classes[class_name].copy()
            if not include_examples:
                class_data.pop("examples", None)
            return {"class": class_data}
        for name, data in classes.items():
            if class_name.lower() in name.lower():
                class_data = data.copy()
                if not include_examples:
                    class_data.pop("examples", None)
                return {"class": class_data}
    raise APINotFoundError(class_name, "类")


def _collect_code_examples(
    api_name: str,
    sources: List[str],
    language: str,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    从多个来源收集代码示例。
    返回 (examples, matched_classes, matched_methods)。
    """
    examples = []
    matched_classes = []
    matched_methods = []

    for source in sources:
        api_data = get_cached_api_data(source)
        if not api_data:
            continue
        classes = api_data.get("classes", {})

        # 精确匹配类名
        if api_name in classes:
            class_data = classes[api_name]
            matched_classes.append({"name": api_name, "api_source": source, "type": "class"})
            for example in class_data.get("examples", []):
                if language == "all" or example.get("language") == language:
                    ex = example.copy()
                    ex["context"] = {"type": "class", "class_name": api_name, "api_source": source}
                    examples.append(ex)

        # 部分匹配类名
        for cls_name, class_data in classes.items():
            if api_name.lower() in cls_name.lower() and cls_name != api_name:
                matched_classes.append({"name": cls_name, "api_source": source, "type": "class"})
                for example in class_data.get("examples", []):
                    if language == "all" or example.get("language") == language:
                        ex = example.copy()
                        ex["context"] = {"type": "class", "class_name": cls_name, "api_source": source}
                        examples.append(ex)

        # 查找方法中的示例
        for cls_name, class_data in classes.items():
            for method in class_data.get("methods", []):
                method_name = method.get("name", "")
                if method_name == api_name:
                    matched_methods.append({
                        "name": method_name,
                        "class_name": cls_name,
                        "api_source": source,
                        "type": "method",
                    })
                    for example in method.get("examples", []):
                        if language == "all" or example.get("language") == language:
                            ex = example.copy()
                            ex["context"] = {
                                "type": "method",
                                "method_name": method_name,
                                "class_name": cls_name,
                                "api_source": source,
                            }
                            examples.append(ex)
                elif api_name.lower() in method_name.lower():
                    matched_methods.append({
                        "name": method_name,
                        "class_name": cls_name,
                        "api_source": source,
                        "type": "method",
                    })
                    for example in method.get("examples", []):
                        if language == "all" or example.get("language") == language:
                            ex = example.copy()
                            ex["context"] = {
                                "type": "method",
                                "method_name": method_name,
                                "class_name": cls_name,
                                "api_source": source,
                            }
                            examples.append(ex)

    return examples, matched_classes, matched_methods


# 全局索引实例（延迟加载）
_search_indices: Dict[str, SearchIndex] = {}
_relationship_indices: Dict[str, RelationshipIndex] = {}


def _close_all_indices() -> None:
    """进程退出时关闭所有搜索索引，释放文件句柄"""
    global _search_indices
    for index in _search_indices.values():
        try:
            index.close()
        except Exception as e:
            logger.debug("关闭索引时出错: %s", e)
    _search_indices.clear()


atexit.register(_close_all_indices)


def get_search_index(api_source: str) -> Optional[SearchIndex]:
    """获取搜索索引实例（延迟加载）"""
    if api_source not in _search_indices:
        try:
            index = SearchIndex(api_source)
            if index._index is None:
                # 尝试打开现有索引
                if index.index_dir.exists() and any(index.index_dir.iterdir()):
                    from whoosh import index as whoosh_index
                    if whoosh_index.exists_in(str(index.index_dir)):
                        index._index = whoosh_index.open_dir(str(index.index_dir))
                    else:
                        logger.warning(f"搜索索引不存在: {api_source}")
                        return None
            _search_indices[api_source] = index
        except Exception as e:
            logger.error(f"加载搜索索引失败: {e}")
            return None
    return _search_indices.get(api_source)


def get_relationship_index(api_source: str) -> Optional[RelationshipIndex]:
    """获取关系索引实例（延迟加载）"""
    if api_source not in _relationship_indices:
        try:
            index = RelationshipIndex(api_source)
            json_file = f"{api_source}_api.json"
            index.load_data(json_file)
            _relationship_indices[api_source] = index
        except Exception as e:
            logger.error(f"加载关系索引失败: {e}")
            return None
    return _relationship_indices.get(api_source)


def register_tools() -> List[Tool]:
    """注册所有工具"""
    return [
        Tool(
            name="search_api",
            description="搜索 Arma Reforger 或 Enfusion API（类、方法、属性、枚举）以及 Wiki 页面。支持自然语言查询和类型过滤。",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词，支持自然语言查询"
                    },
                    "type": {
                        "type": "string",
                        "enum": ["class", "function", "variable", "enum", "wiki", "all"],
                        "default": "all",
                        "description": "API 类型过滤，默认为 'all'。支持 'wiki' 类型搜索 Wiki 页面"
                    },
                    "api_source": {
                        "type": "string",
                        "enum": ["arma_reforger", "enfusion", "arma_reforger_wiki", "both", "all"],
                        "default": "both",
                        "description": "API 来源，默认为 'both'。'all' 包含所有来源（API + Wiki），'arma_reforger_wiki' 只搜索 Wiki"
                    },
                    "limit": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 50,
                        "default": 10,
                        "description": "返回结果数量限制"
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_class_info",
            description="获取类的详细信息，包括方法、属性、继承关系、代码示例等。",
            inputSchema={
                "type": "object",
                "properties": {
                    "class_name": {
                        "type": "string",
                        "description": "类名（支持部分匹配）"
                    },
                    "api_source": {
                        "type": "string",
                        "enum": ["arma_reforger", "enfusion", "both"],
                        "default": "both",
                        "description": "API 来源"
                    },
                    "include_examples": {
                        "type": "boolean",
                        "default": True,
                        "description": "是否包含代码示例"
                    }
                },
                "required": ["class_name"]
            }
        ),
        Tool(
            name="get_function_info",
            description="获取方法的详细信息，包括签名、参数、返回值、描述、示例等。",
            inputSchema={
                "type": "object",
                "properties": {
                    "function_name": {
                        "type": "string",
                        "description": "方法名"
                    },
                    "class_name": {
                        "type": "string",
                        "description": "所属类名（可选，用于精确匹配）"
                    },
                    "api_source": {
                        "type": "string",
                        "enum": ["arma_reforger", "enfusion", "both"],
                        "default": "both",
                        "description": "API 来源"
                    }
                },
                "required": ["function_name"]
            }
        ),
        Tool(
            name="find_related_apis",
            description="查找相关的 API，包括继承关系、使用关系等。",
            inputSchema={
                "type": "object",
                "properties": {
                    "api_name": {
                        "type": "string",
                        "description": "API 名称"
                    },
                    "api_source": {
                        "type": "string",
                        "enum": ["arma_reforger", "enfusion", "both"],
                        "default": "both",
                        "description": "API 来源"
                    },
                    "relation_type": {
                        "type": "string",
                        "enum": ["inheritance", "usage", "similar", "all"],
                        "default": "all",
                        "description": "关系类型"
                    }
                },
                "required": ["api_name"]
            }
        ),
        Tool(
            name="get_code_examples",
            description="获取代码示例，帮助理解 API 的使用方式。",
            inputSchema={
                "type": "object",
                "properties": {
                    "api_name": {
                        "type": "string",
                        "description": "API 名称"
                    },
                    "api_source": {
                        "type": "string",
                        "enum": ["arma_reforger", "enfusion", "both"],
                        "default": "both",
                        "description": "API 来源"
                    },
                    "language": {
                        "type": "string",
                        "enum": ["enforce", "c++", "all"],
                        "default": "enforce",
                        "description": "代码语言"
                    }
                },
                "required": ["api_name"]
            }
        ),
    ]


async def handle_search_api(arguments: Dict[str, Any]) -> str:
    """处理 search_api 工具调用"""
    query = arguments.get("query", "")
    result_type = arguments.get("type", "all")
    api_source = arguments.get("api_source", "both")
    limit = arguments.get("limit", 10)
    
    if not query:
        raise InvalidParameterError("query", "查询参数不能为空")
    
    results = []
    sources = _resolve_search_sources(api_source)

    for source in sources:
        search_index = get_search_index(source)
        if search_index:
            # 如果指定了 wiki 类型，只在 wiki 索引中搜索
            if result_type == "wiki" and source != "arma_reforger_wiki":
                continue
            # 如果指定了非 wiki 类型，跳过 wiki 索引
            if result_type != "wiki" and result_type != "all" and source == "arma_reforger_wiki":
                continue
            
            search_results = search_index.search(
                query=query,
                result_type=result_type if result_type != "all" else None,
                limit=limit
            )
            results.extend(search_results)
        else:
            logger.warning(f"搜索索引不可用: {source}")
    
    # 按相关性排序
    results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
    results = results[:limit]
    
    response = {
        "results": results,
        "total": len(results),
        "query": query,
    }
    return _json_response(response)


async def handle_get_class_info(arguments: Dict[str, Any]) -> str:
    """处理 get_class_info 工具调用"""
    class_name = arguments.get("class_name", "")
    api_source = arguments.get("api_source", "both")
    include_examples = arguments.get("include_examples", True)

    if not class_name:
        raise InvalidParameterError("class_name", "类名不能为空")

    result = _find_class_in_sources(class_name, _resolve_api_sources(api_source), include_examples)
    return _json_response(result)


async def handle_get_function_info(arguments: Dict[str, Any]) -> str:
    """处理 get_function_info 工具调用"""
    function_name = arguments.get("function_name", "")
    class_name = arguments.get("class_name")
    api_source = arguments.get("api_source", "both")
    
    if not function_name:
        raise InvalidParameterError("function_name", "方法名不能为空")

    sources = _resolve_api_sources(api_source)
    
    for source in sources:
        api_data = get_cached_api_data(source)
        if not api_data:
            continue
        
        classes = api_data.get("classes", {})
        
        # 如果指定了类名，只在该类中查找
        if class_name:
            if class_name in classes:
                class_data = classes[class_name]
                for method in class_data.get("methods", []):
                    if method.get("name") == function_name:
                        return _json_response({"function": method})
        else:
            # 在所有类中查找
            for cls_name, class_data in classes.items():
                for method in class_data.get("methods", []):
                    if method.get("name") == function_name:
                        method_with_class = method.copy()
                        method_with_class["class_name"] = cls_name
                        return _json_response({"function": method_with_class})
    
    raise APINotFoundError(function_name, "方法")


async def handle_find_related_apis(arguments: Dict[str, Any]) -> str:
    """处理 find_related_apis 工具调用"""
    api_name = arguments.get("api_name", "")
    api_source = arguments.get("api_source", "both")
    relation_type = arguments.get("relation_type", "all")
    
    if not api_name:
        raise InvalidParameterError("api_name", "API 名称不能为空")

    sources = _resolve_api_sources(api_source)
    all_related = []
    
    for source in sources:
        rel_index = get_relationship_index(source)
        if rel_index:
            related = rel_index.find_related_apis(api_name, relation_type)
            all_related.extend(related)
        else:
            logger.warning(f"关系索引不可用: {source}")
    
    response = {
        "api_name": api_name,
        "related_apis": all_related,
        "total": len(all_related),
    }
    return _json_response(response)


async def handle_get_code_examples(arguments: Dict[str, Any]) -> str:
    """
    处理 get_code_examples 工具调用
    
    支持从以下位置查找代码示例：
    1. 类级别的示例
    2. 方法级别的示例
    3. 支持部分匹配类名和方法名
    """
    api_name = arguments.get("api_name", "")
    api_source = arguments.get("api_source", "both")
    language = arguments.get("language", "enforce")
    
    if not api_name:
        raise InvalidParameterError("api_name", "API 名称不能为空")

    sources = _resolve_api_sources(api_source)
    examples, matched_classes, matched_methods = _collect_code_examples(api_name, sources, language)

    response = {
        "api_name": api_name,
        "examples": examples,
        "total": len(examples),
        "matched_classes": matched_classes[:10],
        "matched_methods": matched_methods[:10],
    }
    return _json_response(response)
