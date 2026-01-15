"""搜索索引系统"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from whoosh import index
from whoosh.fields import Schema, TEXT, ID, KEYWORD, STORED
from whoosh.qparser import QueryParser, MultifieldParser
from whoosh.query import And, Or, Term

from src.utils.helpers import get_data_path, load_json


class SearchIndex:
    """全文搜索索引"""

    def __init__(self, api_source: str = "arma_reforger", index_dir: Optional[Path] = None):
        """
        初始化搜索索引
        
        Args:
            api_source: API 来源
            index_dir: 索引目录，如果为 None 则使用默认目录
        """
        self.api_source = api_source
        self.data_path = get_data_path()
        
        if index_dir is None:
            self.index_dir = self.data_path / "search_index" / api_source
        else:
            self.index_dir = index_dir
        
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        # 定义索引 schema
        self.schema = Schema(
            name=ID(stored=True),
            full_name=TEXT(stored=True),
            type=TEXT(stored=True),  # class, function, variable, enum, wiki
            api_source=ID(stored=True),
            description=TEXT,
            signature=TEXT,
            return_type=TEXT,
            class_name=TEXT(stored=True),
            url=TEXT(stored=True),  # Wiki URL
            categories=KEYWORD(stored=True),  # Wiki categories
            content=TEXT  # 全文搜索内容
        )
        
        self._index = None

    def build_index(self, api_data: Dict[str, Any], overwrite: bool = False) -> None:
        """
        构建搜索索引
        
        Args:
            api_data: API 数据字典
            overwrite: 如果为 True，则覆盖现有索引；如果为 False，则追加到现有索引
        """
        # 如果需要覆盖，删除现有索引目录
        if overwrite and index.exists_in(str(self.index_dir)):
            import shutil
            shutil.rmtree(str(self.index_dir))
            self.index_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建或打开索引
        if index.exists_in(str(self.index_dir)):
            self._index = index.open_dir(str(self.index_dir))
        else:
            self._index = index.create_in(str(self.index_dir), self.schema)
        
        writer = self._index.writer()
        
        try:
            # 检查是否是 Wiki 数据
            if api_data.get("api_source") == "arma_reforger_wiki" or "pages" in api_data:
                # 索引 Wiki 页面
                pages = api_data.get("pages", {})
                for page_title, page_data in pages.items():
                    self._index_wiki_page(writer, page_data)
                
                writer.commit()
                print(f"索引构建完成: {len(pages)} 个 Wiki 页面已索引")
            else:
                # 索引 API 类
                classes = api_data.get("classes", {})
                for class_name, class_data in classes.items():
                    self._index_class(writer, class_data)
                    
                    # 索引类的方法
                    methods = class_data.get("methods", [])
                    for method in methods:
                        self._index_method(writer, method, class_name)
                    
                    # 索引类的属性
                    properties = class_data.get("properties", [])
                    for prop in properties:
                        self._index_property(writer, prop, class_name)
                
                writer.commit()
                print(f"索引构建完成: {len(classes)} 个类已索引")
            
        except Exception as e:
            writer.cancel()
            raise e

    def _index_class(self, writer, class_data: Dict[str, Any]) -> None:
        """索引类"""
        content_parts = [
            class_data.get("name", ""),
            class_data.get("description", ""),
            class_data.get("full_name", "")
        ]
        
        # 添加继承关系
        inheritance = class_data.get("inheritance", {})
        if inheritance.get("parent"):
            content_parts.append(inheritance["parent"])
        for ancestor in inheritance.get("ancestors", []):
            content_parts.append(ancestor)
        
        writer.add_document(
            name=class_data.get("name", ""),
            full_name=class_data.get("full_name", ""),
            type="class",
            api_source=self.api_source,
            description=class_data.get("description", ""),
            signature="",
            return_type="",
            class_name=class_data.get("name", ""),
            content=" ".join(content_parts)
        )

    def _index_method(self, writer, method: Dict[str, Any], class_name: str) -> None:
        """索引方法"""
        content_parts = [
            method.get("name", ""),
            method.get("description", ""),
            method.get("signature", ""),
            method.get("return_type", ""),
            class_name
        ]
        
        # 添加参数信息
        for param in method.get("parameters", []):
            content_parts.append(param.get("type", ""))
            content_parts.append(param.get("name", ""))
        
        writer.add_document(
            name=method.get("name", ""),
            full_name=f"{class_name}.{method.get('name', '')}",
            type="function",
            api_source=self.api_source,
            description=method.get("description", ""),
            signature=method.get("signature", ""),
            return_type=method.get("return_type", ""),
            class_name=class_name,
            content=" ".join(content_parts)
        )

    def _index_property(self, writer, prop: Dict[str, Any], class_name: str) -> None:
        """索引属性"""
        content_parts = [
            prop.get("name", ""),
            prop.get("description", ""),
            prop.get("type", ""),
            class_name
        ]
        
        writer.add_document(
            name=prop.get("name", ""),
            full_name=f"{class_name}.{prop.get('name', '')}",
            type="variable",
            api_source=self.api_source,
            description=prop.get("description", ""),
            signature="",
            return_type="",
            class_name=class_name,
            url="",
            categories="",
            content=" ".join(content_parts)
        )

    def _index_wiki_page(self, writer, page_data: Dict[str, Any]) -> None:
        """索引 Wiki 页面"""
        title = page_data.get("title", "")
        description = page_data.get("description", "")
        full_text = page_data.get("full_text", "")
        url = page_data.get("url", "")
        categories = " ".join(page_data.get("categories", []))
        
        # 构建搜索内容
        content_parts = [
            title,
            description,
            full_text
        ]
        
        # 添加章节标题
        for section in page_data.get("sections", []):
            content_parts.append(section.get("title", ""))
            content_parts.append(section.get("content", ""))
        
        writer.add_document(
            name=title,
            full_name=title,
            type="wiki",
            api_source=self.api_source,
            description=description,
            signature="",
            return_type="",
            class_name="",
            url=url,
            categories=categories,
            content=" ".join(content_parts)
        )

    def search(
        self,
        query: str,
        result_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        搜索 API
        
        Args:
            query: 搜索查询
            result_type: 结果类型过滤 (class/function/variable/enum)
            limit: 结果数量限制
            
        Returns:
            搜索结果列表
        """
        if not self._index:
            if index.exists_in(str(self.index_dir)):
                self._index = index.open_dir(str(self.index_dir))
            else:
                return []
        
        results = []
        
        with self._index.searcher() as searcher:
            # 构建查询
            if result_type:
                # 多字段查询，包含类型过滤
                query_parser = MultifieldParser(
                    ["content", "name", "description", "signature"],
                    schema=self.schema
                )
                parsed_query = query_parser.parse(query)
                # 添加类型过滤
                type_query = Term("type", result_type)
                final_query = And([parsed_query, type_query])
            else:
                # 普通多字段查询
                query_parser = MultifieldParser(
                    ["content", "name", "description", "signature"],
                    schema=self.schema
                )
                final_query = query_parser.parse(query)
            
            # 执行搜索
            search_results = searcher.search(final_query, limit=limit)
            
            for result in search_results:
                result_dict = {
                    "name": result.get("name", ""),
                    "full_name": result.get("full_name", ""),
                    "type": result.get("type", ""),
                    "api_source": result.get("api_source", ""),
                    "description": result.get("description", ""),
                    "signature": result.get("signature", ""),
                    "return_type": result.get("return_type", ""),
                    "class_name": result.get("class_name", ""),
                    "relevance_score": result.score
                }
                
                # 如果是 Wiki 页面，添加额外字段
                if result.get("type") == "wiki":
                    result_dict["url"] = result.get("url", "")
                    result_dict["categories"] = result.get("categories", "")
                
                results.append(result_dict)
        
        return results

    def load_from_json(self, json_file: str, overwrite: bool = True) -> None:
        """
        从 JSON 文件加载数据并构建索引
        
        Args:
            json_file: JSON 文件名
            overwrite: 如果为 True，则覆盖现有索引；如果为 False，则追加到现有索引
        """
        api_data = load_json(json_file)
        if api_data:
            self.build_index(api_data, overwrite=overwrite)
        else:
            raise FileNotFoundError(f"无法加载 JSON 文件: {json_file}")
