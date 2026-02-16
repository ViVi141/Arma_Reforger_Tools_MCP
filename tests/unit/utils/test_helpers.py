"""测试工具函数模块"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, mock_open

from src.utils.helpers import (
    get_cached_api_data,
    get_data_path,
    ensure_data_dir,
    invalidate_api_cache,
    load_json,
    save_json,
    clean_text,
    get_docs_path,
)


class TestGetDataPath:
    """测试 get_data_path 函数"""

    def test_default_path(self):
        """测试默认路径"""
        with patch.dict(os.environ, {}, clear=True):
            path = get_data_path()
            assert isinstance(path, Path)
            assert "data" in str(path)

    def test_custom_path_from_env(self):
        """测试从环境变量获取路径"""
        import platform
        custom_path = "/custom/data/path" if platform.system() != "Windows" else "C:\\custom\\data\\path"
        with patch.dict(os.environ, {"API_DATA_PATH": custom_path}):
            path = get_data_path()
            # Windows 路径会自动转换，所以比较路径对象而不是字符串
            assert Path(custom_path) == path or str(path).replace("\\", "/") == custom_path.replace("\\", "/")


class TestEnsureDataDir:
    """测试 ensure_data_dir 函数"""

    def test_creates_directory(self):
        """测试创建目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.utils.helpers.get_data_path", return_value=Path(tmpdir) / "test_data"):
                path = ensure_data_dir()
                assert path.exists()
                assert path.is_dir()


class TestSaveJson:
    """测试 save_json 函数"""

    def test_save_json_file(self):
        """测试保存 JSON 文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_data = {"key": "value", "number": 123}
            test_file = Path(tmpdir) / "test.json"
            
            with patch("src.utils.helpers.ensure_data_dir", return_value=Path(tmpdir)):
                save_json(test_data, "test.json")
            
            assert test_file.exists()
            with open(test_file, "r", encoding="utf-8") as f:
                loaded_data = json.load(f)
            assert loaded_data == test_data

    def test_save_json_creates_directory(self):
        """测试保存时创建目录"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_data = {"key": "value"}
            data_dir = Path(tmpdir) / "new_data"
            
            with patch("src.utils.helpers.get_data_path", return_value=data_dir):
                save_json(test_data, "test.json")
            
            assert data_dir.exists()
            assert (data_dir / "test.json").exists()


class TestLoadJson:
    """测试 load_json 函数"""

    def test_load_existing_json(self):
        """测试加载存在的 JSON 文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_data = {"key": "value", "number": 123}
            test_file = Path(tmpdir) / "test.json"
            
            with open(test_file, "w", encoding="utf-8") as f:
                json.dump(test_data, f)
            
            with patch("src.utils.helpers.get_data_path", return_value=Path(tmpdir)):
                loaded_data = load_json("test.json")
            
            assert loaded_data == test_data

    def test_load_nonexistent_json(self):
        """测试加载不存在的 JSON 文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("src.utils.helpers.get_data_path", return_value=Path(tmpdir)):
                result = load_json("nonexistent.json")
                assert result is None


class TestCleanText:
    """测试 clean_text 函数"""

    def test_clean_normal_text(self):
        """测试清理普通文本"""
        text = "  hello   world  "
        result = clean_text(text)
        assert result == "hello world"

    def test_clean_multiline_text(self):
        """测试清理多行文本"""
        text = "  hello\n\n  world  \n  test  "
        result = clean_text(text)
        assert result == "hello world test"

    def test_clean_empty_string(self):
        """测试清理空字符串"""
        assert clean_text("") == ""
        assert clean_text("   ") == ""

    def test_clean_none(self):
        """测试清理 None"""
        assert clean_text(None) == ""


class TestGetDocsPath:
    """测试 get_docs_path 函数"""

    def test_get_arma_reforger_path(self):
        """测试获取 Arma Reforger 文档路径"""
        path = get_docs_path("arma_reforger")
        assert isinstance(path, Path)
        assert "ArmaReforgerScriptAPIPublic" in str(path)

    def test_get_enfusion_path(self):
        """测试获取 Enfusion 文档路径"""
        path = get_docs_path("enfusion")
        assert isinstance(path, Path)
        assert "EnfusionScriptAPIPublic" in str(path)

    def test_get_invalid_path(self):
        """测试获取无效路径"""
        with pytest.raises(ValueError):
            get_docs_path("invalid_source")


class TestGetCachedApiData:
    """测试 get_cached_api_data 函数"""

    def setup_method(self):
        """每个测试前清除缓存"""
        invalidate_api_cache()

    def test_caches_arma_reforger_data(self):
        """测试缓存 arma_reforger 数据"""
        api_data = {"classes": {"TestClass": {}}, "api_source": "arma_reforger"}
        with patch("src.utils.helpers.load_json", return_value=api_data) as mock_load:
            result1 = get_cached_api_data("arma_reforger")
            result2 = get_cached_api_data("arma_reforger")
            assert result1 == api_data
            assert result2 == api_data
            assert result1 is result2
            mock_load.assert_called_once()

    def test_caches_enfusion_data(self):
        """测试缓存 enfusion 数据"""
        api_data = {"classes": {}, "api_source": "enfusion"}
        with patch("src.utils.helpers.load_json", return_value=api_data):
            result = get_cached_api_data("enfusion")
            assert result == api_data

    def test_returns_none_for_missing_file(self):
        """测试文件不存在时返回 None"""
        with patch("src.utils.helpers.load_json", return_value=None):
            result = get_cached_api_data("arma_reforger")
            assert result is None


class TestInvalidateApiCache:
    """测试 invalidate_api_cache 函数"""

    def setup_method(self):
        invalidate_api_cache()

    def test_invalidate_all_clears_cache(self):
        """测试清除全部缓存"""
        api_data = {"classes": {}}
        with patch("src.utils.helpers.load_json", return_value=api_data):
            get_cached_api_data("arma_reforger")
        invalidate_api_cache()
        with patch("src.utils.helpers.load_json", return_value=api_data) as mock_load:
            get_cached_api_data("arma_reforger")
            mock_load.assert_called_once()

    def test_invalidate_single_source(self):
        """测试清除单个来源缓存"""
        api_data = {"classes": {}}
        with patch("src.utils.helpers.load_json", return_value=api_data):
            get_cached_api_data("arma_reforger")
            get_cached_api_data("enfusion")
        invalidate_api_cache("arma_reforger")
        with patch("src.utils.helpers.load_json", return_value=api_data) as mock_load:
            get_cached_api_data("arma_reforger")
            mock_load.assert_called_once()
