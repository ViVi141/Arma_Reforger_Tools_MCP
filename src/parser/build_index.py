"""构建 API 索引的主脚本"""

import sys
from pathlib import Path
from typing import Dict, List, Any
import json

from src.parser.html_parser import HTMLParser
from src.indexer.search_index import SearchIndex
from src.indexer.relationship_index import RelationshipIndex
from src.utils.helpers import save_json, get_docs_path, ensure_data_dir


def find_interface_files(docs_path: Path) -> List[Path]:
    """查找所有接口文件"""
    interface_files = []
    
    # 查找所有 interface*.html 文件
    for html_file in docs_path.glob("interface*.html"):
        # 排除 -members.html 文件（成员列表页面）
        if "-members" not in html_file.stem:
            interface_files.append(html_file)
    
    return sorted(interface_files)


def build_api_index(api_source: str = "arma_reforger") -> Dict[str, Any]:
    """
    构建 API 索引
    
    Args:
        api_source: API 来源
        
    Returns:
        构建的索引数据
    """
    print(f"开始构建 {api_source} API 索引...")
    
    docs_path = get_docs_path(api_source)
    if not docs_path.exists():
        print(f"错误: 文档路径不存在: {docs_path}")
        return {}
    
    parser = HTMLParser(api_source)
    interface_files = find_interface_files(docs_path)
    
    print(f"找到 {len(interface_files)} 个接口文件")
    
    api_data = {
        "api_source": api_source,
        "classes": {},
        "total_classes": 0,
        "total_methods": 0,
        "total_properties": 0
    }
    
    processed = 0
    for interface_file in interface_files:
        processed += 1
        if processed % 100 == 0:
            print(f"已处理 {processed}/{len(interface_files)} 个文件...")
        
        class_data = parser.parse_file(interface_file)
        if class_data and class_data.get("name"):
            class_name = class_data["name"]
            api_data["classes"][class_name] = class_data
            api_data["total_methods"] += len(class_data.get("methods", []))
            api_data["total_properties"] += len(class_data.get("properties", []))
    
    api_data["total_classes"] = len(api_data["classes"])
    
    print(f"完成! 解析了 {api_data['total_classes']} 个类, "
          f"{api_data['total_methods']} 个方法, "
          f"{api_data['total_properties']} 个属性")
    
    return api_data


def build_search_index(api_source: str = "arma_reforger") -> None:
    """
    构建搜索索引
    
    Args:
        api_source: API 来源
    """
    print(f"开始构建 {api_source} 搜索索引...")
    
    json_file = f"{api_source}_api.json"
    search_index = SearchIndex(api_source)
    
    try:
        search_index.load_from_json(json_file)
        print(f"搜索索引构建完成!")
    except Exception as e:
        print(f"构建搜索索引时出错: {e}")


def build_relationship_index(api_source: str = "arma_reforger") -> None:
    """
    构建关系索引
    
    Args:
        api_source: API 来源
    """
    print(f"开始构建 {api_source} 关系索引...")
    
    json_file = f"{api_source}_api.json"
    rel_index = RelationshipIndex(api_source)
    
    try:
        rel_index.load_data(json_file)
        print(f"关系索引构建完成!")
    except Exception as e:
        print(f"构建关系索引时出错: {e}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="构建 Arma Reforger API 索引")
    parser.add_argument(
        "--api-source",
        choices=["arma_reforger", "enfusion", "both"],
        default="arma_reforger",
        help="要构建的 API 来源"
    )
    parser.add_argument(
        "--skip-parse",
        action="store_true",
        help="跳过文档解析，只构建索引"
    )
    parser.add_argument(
        "--skip-search-index",
        action="store_true",
        help="跳过搜索索引构建"
    )
    parser.add_argument(
        "--skip-relationship-index",
        action="store_true",
        help="跳过关系索引构建"
    )
    
    args = parser.parse_args()
    
    ensure_data_dir()
    
    if args.api_source in ["arma_reforger", "both"]:
        if not args.skip_parse:
            arma_data = build_api_index("arma_reforger")
            save_json(arma_data, "arma_reforger_api.json")
            print(f"已保存 Arma Reforger API 数据到 data/arma_reforger_api.json")
        
        if not args.skip_search_index:
            build_search_index("arma_reforger")
        
        if not args.skip_relationship_index:
            build_relationship_index("arma_reforger")
    
    if args.api_source in ["enfusion", "both"]:
        if not args.skip_parse:
            enfusion_data = build_api_index("enfusion")
            save_json(enfusion_data, "enfusion_api.json")
            print(f"已保存 Enfusion API 数据到 data/enfusion_api.json")
        
        if not args.skip_search_index:
            build_search_index("enfusion")
        
        if not args.skip_relationship_index:
            build_relationship_index("enfusion")
    
    print("索引构建完成!")


if __name__ == "__main__":
    main()
