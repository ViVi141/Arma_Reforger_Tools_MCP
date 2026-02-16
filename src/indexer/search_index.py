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
        # 注意：name 使用 TEXT 而不是 ID，以支持通配符和部分匹配搜索
        self.schema = Schema(
            name=TEXT(stored=True),  # 改为 TEXT 以支持通配符搜索
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

    def build_index(
        self,
        api_data: Dict[str, Any],
        overwrite: bool = False,
        procs: int = 0,
        multisegment: bool = True,
    ) -> None:
        """
        构建搜索索引

        Args:
            api_data: API 数据字典
            overwrite: 如果为 True，则覆盖现有索引；如果为 False，则追加到现有索引
            procs: Whoosh 并行索引进程数，0 表示单进程
            multisegment: 是否使用多段索引（批量构建时更快）
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

        writer_kwargs = {}
        if procs > 0:
            writer_kwargs["procs"] = procs
            writer_kwargs["multisegment"] = True  # 并行时启用多段以加速
            writer_kwargs["limitmb"] = 256  # 每进程内存，提升大批量索引速度
        elif multisegment:
            writer_kwargs["multisegment"] = True
        writer = self._index.writer(**writer_kwargs)
        
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
            # 使用通配符支持部分匹配（如果查询是单个词且没有通配符）
            processed_query = query.strip()
            # 如果查询是单个词且不包含通配符，尝试在多个字段中使用通配符搜索
            if " " not in processed_query and "*" not in processed_query and "?" not in processed_query:
                # 构建多查询：正常搜索 + 多个字段通配符搜索
                query_parser = MultifieldParser(
                    ["content", "name", "description", "signature", "full_name", "class_name"],
                    schema=self.schema
                )
                
                # 正常查询
                normal_query = query_parser.parse(query)
                
                # 在支持通配符的字段中使用通配符查询（full_name 和 class_name 是 TEXT 类型）
                full_name_parser = QueryParser("full_name", schema=self.schema)
                class_name_parser = QueryParser("class_name", schema=self.schema)
                content_parser = QueryParser("content", schema=self.schema)
                
                # 多个通配符查询
                wildcard_queries = [
                    full_name_parser.parse(f"*{query}*"),
                    class_name_parser.parse(f"*{query}*"),
                    content_parser.parse(f"*{query}*")
                ]
                
                # 组合所有查询（OR 关系）
                all_queries = [normal_query] + wildcard_queries
                
                # 组合查询（OR 关系）
                if result_type:
                    type_query = Term("type", result_type)
                    final_query = And([
                        Or(all_queries),
                        type_query
                    ])
                else:
                    final_query = Or(all_queries)
            else:
                # 多词查询或已包含通配符，使用原始逻辑
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

    def load_from_json(
        self,
        json_file: str,
        overwrite: bool = True,
        procs: int = 0,
    ) -> None:
        """
        从 JSON 文件加载数据并构建索引

        Args:
            json_file: JSON 文件名
            overwrite: 如果为 True，则覆盖现有索引；如果为 False，则追加到现有索引
            procs: Whoosh 并行索引进程数，0 表示单进程
        """
        api_data = load_json(json_file)
        if api_data:
            self.build_index(api_data, overwrite=overwrite, procs=procs)
        else:
            raise FileNotFoundError(f"无法加载 JSON 文件: {json_file}")

    def close(self) -> None:
        """关闭底层 Whoosh 索引/存储并释放文件句柄（在 Windows 上必须）。"""
        try:
            if self._index:
                try:
                    # 关闭 Index（会关闭相关资源）
                    self._index.close()
                except Exception:
                    pass
                # 有些 Whoosh Storage 仍然持有文件句柄，尝试调用 storage.close()
                try:
                    storage = getattr(self._index, "storage", None)
                    if storage and hasattr(storage, "close"):
                        storage.close()
                except Exception:
                    pass
        finally:
            # 删除引用并触发垃圾回收以尽快释放 Windows 文件句柄
            try:
                self._index = None
                import gc
                gc.collect()
            except Exception:
                pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def __del__(self):
        # 最后的兜底清理
        try:
            self.close()
        except Exception:
            pass
