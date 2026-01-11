"""MCP 服务器主文件"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any, Sequence

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Tool,
        TextContent,
        ImageContent,
        EmbeddedResource,
    )
except ImportError:
    # 如果 MCP SDK 未安装，提供友好的错误信息
    print("错误: 未安装 MCP SDK。请运行: pip install mcp")
    sys.exit(1)

from src.mcp_server.tools import (
    register_tools,
    handle_search_api,
    handle_get_class_info,
    handle_get_function_info,
    handle_find_related_apis,
    handle_get_code_examples,
)
from src.mcp_server.resources import register_resources
from src.utils.helpers import get_data_path, ensure_data_dir

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建 MCP 服务器实例
app = Server("arma-reforger-api")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """列出所有可用的工具"""
    return register_tools()


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> Sequence[TextContent | ImageContent | EmbeddedResource]:
    """处理工具调用"""
    try:
        logger.info(f"调用工具: {name}, 参数: {arguments}")
        
        if name == "search_api":
            result = await handle_search_api(arguments)
        elif name == "get_class_info":
            result = await handle_get_class_info(arguments)
        elif name == "get_function_info":
            result = await handle_get_function_info(arguments)
        elif name == "find_related_apis":
            result = await handle_find_related_apis(arguments)
        elif name == "get_code_examples":
            result = await handle_get_code_examples(arguments)
        else:
            raise ValueError(f"未知的工具: {name}")
        
        return [TextContent(type="text", text=result)]
        
    except Exception as e:
        logger.error(f"工具调用错误: {e}", exc_info=True)
        error_msg = {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": str(e)
            }
        }
        import json
        return [TextContent(type="text", text=json.dumps(error_msg, ensure_ascii=False, indent=2))]


@app.list_resources()
async def list_resources() -> list:
    """列出所有可用的资源"""
    return register_resources()


async def main():
    """主函数"""
    # 确保数据目录存在
    ensure_data_dir()
    
    logger.info("启动 Arma Reforger API MCP 服务器...")
    logger.info(f"数据路径: {get_data_path()}")
    
    # 使用 stdio 传输运行服务器
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
