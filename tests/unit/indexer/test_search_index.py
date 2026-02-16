"""测试搜索索引模块"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

# 尝试导入，如果失败则跳过相关测试
try:
    from src.indexer.search_index import SearchIndex
    from src.indexer.relationship_index import RelationshipIndex
    from src.utils.helpers import save_json, get_data_path
    INDEXER_AVAILABLE = True
except ImportError as e:
    INDEXER_AVAILABLE = False
    print(f"索引模块导入失败: {e}")


@pytest.mark.skipif(not INDEXER_AVAILABLE, reason="索引模块不可用")
class TestSearchIndex:
    """测试搜索索引类"""
    
    @pytest.fixture
    def sample_api_data(self):
        """示例 API 数据"""
        return {
            "api_source": "arma_reforger",
            "classes": {
                "TestClass": {
                    "name": "TestClass",
                    "full_name": "TestClass",
                    "api_source": "arma_reforger",
                    "description": "A test class for testing",
                    "inheritance": {
                        "parent": "BaseClass",
                        "ancestors": ["BaseClass", "Object"]
                    },
                    "methods": [
                        {
                            "name": "TestMethod",
                            "signature": "void TestMethod(int param)",
                            "description": "A test method",
                            "return_type": "void",
                            "parameters": [
                                {"type": "int", "name": "param", "description": ""}
                            ]
                        }
                    ],
                    "properties": [
                        {
                            "name": "testProperty",
                            "type": "string",
                            "description": "A test property"
                        }
                    ],
                    "examples": [],
                    "url": "interfaceTestClass.html"
                }
            },
            "total_classes": 1,
            "total_methods": 1,
            "total_properties": 1
        }
    
    @pytest.fixture
    def search_index(self):
        """创建搜索索引实例"""
        with tempfile.TemporaryDirectory() as tmpdir:
            index_dir = Path(tmpdir) / "test_index"
            index = SearchIndex(api_source="arma_reforger", index_dir=index_dir)
            try:
                yield index
            finally:
                # 优先使用公开的 close()，并作为回退采取更强力的清理以确保 Windows 释放文件句柄
                if hasattr(index, "close"):
                    try:
                        index.close()
                    except Exception:
                        pass

                if hasattr(index, '_index') and index._index:
                    try:
                        index._index.close()
                    except Exception:
                        pass
                    try:
                        storage = getattr(index._index, 'storage', None)
                        if storage and hasattr(storage, 'close'):
                            storage.close()
                    except Exception:
                        pass

                # 删除引用并强制回收，增加短暂停顿以确保文件句柄释放
                try:
                    import gc
                    del index
                    gc.collect()
                except Exception:
                    pass

                import time
                time.sleep(0.2)
    
    def test_init(self, search_index):
        """测试初始化"""
        assert search_index.api_source == "arma_reforger"
        assert search_index.index_dir.exists()
        assert search_index.schema is not None
    
    def test_build_index(self, search_index, sample_api_data):
        """测试构建索引"""
        search_index.build_index(sample_api_data)
        
        # 验证索引已创建
        assert search_index._index is not None
    
    def test_index_class(self, search_index, sample_api_data):
        """测试索引类"""
        from whoosh.writing import IndexWriter
        
        # 创建临时索引
        if not search_index._index:
            from whoosh import index as whoosh_index
            search_index._index = whoosh_index.create_in(
                str(search_index.index_dir),
                search_index.schema
            )
        
        writer = search_index._index.writer()
        class_data = sample_api_data["classes"]["TestClass"]
        search_index._index_class(writer, class_data)
        writer.commit()
        
        # 验证可以搜索
        from whoosh.qparser import QueryParser
        searcher = search_index._index.searcher()
        try:
            query_parser = QueryParser("content", search_index.schema)
            query = query_parser.parse("TestClass")
            results = searcher.search(query)
            assert len(results) > 0
        finally:
            searcher.close()
    
    def test_index_method(self, search_index, sample_api_data):
        """测试索引方法"""
        from whoosh import index as whoosh_index
        
        if not search_index._index:
            search_index._index = whoosh_index.create_in(
                str(search_index.index_dir),
                search_index.schema
            )
        
        writer = search_index._index.writer()
        method = sample_api_data["classes"]["TestClass"]["methods"][0]
        search_index._index_method(writer, method, "TestClass")
        writer.commit()
        
        # 验证可以搜索方法
        from whoosh.qparser import QueryParser
        with search_index._index.searcher() as searcher:
            query_parser = QueryParser("content", search_index.schema)
            query = query_parser.parse("TestMethod")
            results = searcher.search(query)
            assert len(results) > 0
        
        # 关闭索引以释放文件句柄
        if search_index._index:
            try:
                search_index._index.close()
            except:
                pass
    
    def test_index_property(self, search_index, sample_api_data):
        """测试索引属性"""
        from whoosh import index as whoosh_index
        
        if not search_index._index:
            search_index._index = whoosh_index.create_in(
                str(search_index.index_dir),
                search_index.schema
            )
        
        writer = search_index._index.writer()
        prop = sample_api_data["classes"]["TestClass"]["properties"][0]
        search_index._index_property(writer, prop, "TestClass")
        writer.commit()
        
        # 验证可以搜索属性
        from whoosh.qparser import QueryParser
        searcher = search_index._index.searcher()
        try:
            query_parser = QueryParser("content", search_index.schema)
            query = query_parser.parse("testProperty")
            results = searcher.search(query)
            assert len(results) > 0
        finally:
            searcher.close()
    
    def test_search(self, search_index, sample_api_data):
        """测试搜索功能"""
        # 构建索引
        search_index.build_index(sample_api_data)
        
        # 执行搜索
        results = search_index.search("TestClass", limit=10)
        
        assert isinstance(results, list)
        assert len(results) > 0
        assert results[0]["name"] == "TestClass"
        assert results[0]["type"] == "class"
    
    def test_search_with_type_filter(self, search_index, sample_api_data):
        """测试带类型过滤的搜索"""
        search_index.build_index(sample_api_data)
        
        # 搜索类
        results = search_index.search("Test", result_type="class", limit=10)
        assert all(r["type"] == "class" for r in results)
        
        # 搜索方法
        results = search_index.search("Test", result_type="function", limit=10)
        assert all(r["type"] == "function" for r in results)
    
    def test_search_empty_query(self, search_index, sample_api_data):
        """测试空查询"""
        search_index.build_index(sample_api_data)
        
        results = search_index.search("", limit=10)
        # 空查询可能返回所有结果或空结果，取决于实现
        assert isinstance(results, list)
    
    def test_search_no_index(self, search_index):
        """测试没有索引时的搜索"""
        # 不构建索引，直接搜索
        results = search_index.search("test", limit=10)
        assert results == []
    
    def test_load_from_json(self, sample_api_data):
        """测试从 JSON 加载并构建索引"""
        with tempfile.TemporaryDirectory() as tmpdir:
            json_file = Path(tmpdir) / "arma_reforger_api.json"
            import json
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(sample_api_data, f)
            
            # 创建新的索引实例，使用临时目录
            index_dir = Path(tmpdir) / "test_index"
            search_index = SearchIndex(api_source="arma_reforger", index_dir=index_dir)
            
            # 修改索引的数据路径
            with patch("src.indexer.search_index.load_json") as mock_load:
                mock_load.return_value = sample_api_data
                search_index.data_path = Path(tmpdir)
                search_index.load_from_json("arma_reforger_api.json")
            
            # 验证索引已构建
            assert search_index._index is not None
            # 关闭索引
            if search_index._index:
                try:
                    search_index._index.close()
                except:
                    pass
    
    def test_load_from_json_nonexistent(self, search_index):
        """测试加载不存在的 JSON 文件"""
        with patch("src.indexer.search_index.load_json", return_value=None):
            with pytest.raises(FileNotFoundError):
                search_index.load_from_json("nonexistent.json")


@pytest.mark.skipif(not INDEXER_AVAILABLE, reason="索引模块不可用")
class TestRelationshipIndex:
    """测试关系索引类"""
    
    @pytest.fixture
    def sample_api_data(self):
        """示例 API 数据"""
        return {
            "api_source": "arma_reforger",
            "classes": {
                "BaseClass": {
                    "name": "BaseClass",
                    "methods": [
                        {
                            "name": "BaseMethod",
                            "return_type": "void",
                            "parameters": []
                        }
                    ]
                },
                "ChildClass": {
                    "name": "ChildClass",
                    "inheritance": {
                        "parent": "BaseClass",
                        "ancestors": ["BaseClass", "Object"]
                    },
                    "methods": [
                        {
                            "name": "ChildMethod",
                            "return_type": "BaseClass",
                            "parameters": [
                                {"type": "BaseClass", "name": "obj", "description": ""}
                            ]
                        }
                    ]
                }
            }
        }
    
    @pytest.fixture
    def relationship_index(self, sample_api_data):
        """创建关系索引实例"""
        index = RelationshipIndex(api_source="arma_reforger")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            json_file = Path(tmpdir) / "arma_reforger_api.json"
            import json
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(sample_api_data, f)
            
            # 使用 load_json 的 mock
            with patch("src.indexer.relationship_index.load_json") as mock_load:
                mock_load.return_value = sample_api_data
                with patch("src.indexer.relationship_index.get_data_path", return_value=Path(tmpdir)):
                    index.data_path = Path(tmpdir)
                    index.load_data("arma_reforger_api.json")
            
            yield index
    
    def test_init(self):
        """测试初始化"""
        index = RelationshipIndex(api_source="arma_reforger")
        assert index.api_source == "arma_reforger"
        assert index._inheritance_map == {}
        assert index._usage_map == {}
    
    def test_load_data(self, relationship_index):
        """测试加载数据"""
        assert relationship_index.api_data is not None
        assert "classes" in relationship_index.api_data
    
    def test_build_relationship_maps(self, relationship_index):
        """测试构建关系映射"""
        # load_data 会自动调用 _build_relationship_maps
        assert "BaseClass" in relationship_index._inheritance_map
        assert "ChildClass" in relationship_index._inheritance_map.get("BaseClass", [])
    
    def test_find_related_apis_inheritance(self, relationship_index):
        """测试查找继承关系"""
        related = relationship_index.find_related_apis("BaseClass", "inheritance")
        
        assert len(related) > 0
        # 应该找到子类
        child_relations = [r for r in related if r["relation"] == "child_class"]
        assert len(child_relations) > 0
        assert any(r["name"] == "ChildClass" for r in child_relations)
    
    def test_find_related_apis_usage(self, relationship_index):
        """测试查找使用关系"""
        related = relationship_index.find_related_apis("BaseClass", "usage")
        
        # BaseClass 被 ChildClass 使用（作为返回类型和参数类型）
        used_by = [r for r in related if r["relation"] == "used_by"]
        assert len(used_by) > 0
    
    def test_find_related_apis_all(self, relationship_index):
        """测试查找所有关系"""
        related = relationship_index.find_related_apis("BaseClass", "all")
        
        assert len(related) > 0
        # 应该包含继承和使用关系
        relations = set(r["relation"] for r in related)
        assert len(relations) > 1
    
    def test_find_related_apis_nonexistent(self, relationship_index):
        """测试查找不存在的 API"""
        related = relationship_index.find_related_apis("NonExistentClass", "all")
        # 应该返回空列表或包含一些结果
        assert isinstance(related, list)
    
    def test_add_usage_relationship(self, relationship_index):
        """测试添加使用关系"""
        relationship_index._add_usage_relationship("ClassA", "ClassB")
        
        assert "ClassB" in relationship_index._usage_map
        assert "ClassA" in relationship_index._usage_map["ClassB"]
    
    def test_load_data_nonexistent_file(self):
        """测试加载不存在的文件"""
        index = RelationshipIndex(api_source="arma_reforger")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.indexer.relationship_index.get_data_path", return_value=Path(tmpdir)):
                index.data_path = Path(tmpdir)
                with pytest.raises(FileNotFoundError):
                    index.load_data("nonexistent.json")
