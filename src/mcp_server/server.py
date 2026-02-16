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
from src.utils.helpers import get_data_path, ensure_data_dir, get_project_root

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建 MCP 服务器实例
app = Server("arma-reforger-api")


def validate_paths() -> bool:
    """验证关键路径是否存在"""
    logger.info("验证项目路径...")

    # 检查项目根目录
    project_root = get_project_root()
    logger.info(f"项目根目录: {project_root}")

    if not project_root.exists():
        logger.error(f"项目根目录不存在: {project_root}")
        return False

    # 检查数据目录
    data_path = get_data_path()
    logger.info(f"数据目录: {data_path}")

    if not data_path.exists():
        logger.warning(f"数据目录不存在，将自动创建: {data_path}")
        try:
            data_path.mkdir(parents=True, exist_ok=True)
            logger.info("数据目录创建成功")
        except Exception as e:
            logger.error(f"创建数据目录失败: {e}")
            return False

    # 检查搜索索引目录
    search_index_path = data_path / "search_index"
    if not search_index_path.exists():
        logger.warning(f"搜索索引目录不存在: {search_index_path}")
        logger.warning("请运行 'python -m src.parser.build_index' 来构建索引")

    # 检查 API 数据文件
    api_files = ["arma_reforger_api.json", "enfusion_api.json"]
    found_api_data = False
    for api_file in api_files:
        if (data_path / api_file).exists():
            found_api_data = True
            break

    if not found_api_data:
        logger.warning("未找到 API 数据文件")
        logger.warning("请运行 'python -m src.parser.build_index' 来构建索引")

    return True


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
    # 验证路径
    if not validate_paths():
        logger.error("路径验证失败，请检查项目配置")
        return

    # 确保数据目录存在
    ensure_data_dir()

    logger.info("启动 Arma Reforger API MCP 服务器...")
    logger.info(f"数据路径: {get_data_path()}")
    logger.info(f"项目根目录: {get_project_root()}")

    # 使用 stdio 传输运行服务器
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
