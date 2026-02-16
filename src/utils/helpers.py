"""工具函数"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional


def get_project_root() -> Path:
    """获取项目根目录（健壮的实现）"""
    # 方法1: 通过环境变量
    if "PROJECT_ROOT" in os.environ:
        return Path(os.environ["PROJECT_ROOT"])

    # 方法2: 通过当前文件位置向上查找项目标识文件
    current_file = Path(__file__)
    for parent in current_file.parents:
        if (parent / "setup.py").exists() or (parent / "pyproject.toml").exists():
            return parent

    # 方法3: 默认使用相对路径（向上3级目录）
    return current_file.parent.parent.parent


def get_data_path() -> Path:
    """获取数据目录路径"""
    data_path = os.environ.get("API_DATA_PATH")
    if data_path:
        return Path(data_path)
    # 默认使用项目根目录下的 data 文件夹
    return get_project_root() / "data"


def ensure_data_dir() -> Path:
    """确保数据目录存在"""
    data_path = get_data_path()
    data_path.mkdir(parents=True, exist_ok=True)
    return data_path


def save_json(data: Dict[str, Any], filename: str) -> None:
    """保存 JSON 数据"""
    data_path = ensure_data_dir()
    file_path = data_path / filename
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_json(filename: str) -> Optional[Dict[str, Any]]:
    """加载 JSON 数据"""
    data_path = get_data_path()
    file_path = data_path / filename
    if not file_path.exists():
        return None
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


# API 数据缓存（仅缓存 arma_reforger 和 enfusion，不含 Wiki）
_api_data_cache: Dict[str, Dict[str, Any]] = {}


def get_cached_api_data(source: str) -> Optional[Dict[str, Any]]:
    """
    获取缓存的 API 数据，减少重复 I/O。
    仅缓存 arma_reforger 和 enfusion，Wiki 数据结构不同需单独处理。
    """
    if source not in ("arma_reforger", "enfusion"):
        return load_json(f"{source}_api.json")
    if source not in _api_data_cache:
        data = load_json(f"{source}_api.json")
        if data is not None:
            _api_data_cache[source] = data
        return data
    return _api_data_cache[source]


def invalidate_api_cache(source: Optional[str] = None) -> None:
    """
    使 API 缓存失效。供测试或热重载使用。
    Args:
        source: 若指定则只清除该来源；若为 None 则清除全部。
    """
    global _api_data_cache
    if source is None:
        _api_data_cache.clear()
    elif source in _api_data_cache:
        del _api_data_cache[source]


def clean_text(text: str) -> str:
    """清理文本，移除多余的空白字符"""
    if not text:
        return ""
    return " ".join(text.split())


def get_docs_path(api_source: str = "arma_reforger") -> Path:
    """获取文档路径"""
    base_path = get_project_root()
    if api_source == "arma_reforger":
        return base_path / "ArmaReforgerScriptAPIPublic"
    elif api_source == "enfusion":
        return base_path / "EnfusionScriptAPIPublic"
    else:
        raise ValueError(f"Unknown API source: {api_source}")


def get_wiki_pages_path() -> Path:
    """获取 Wiki 页面目录路径"""
    base_path = get_project_root()
    return base_path / "wiki_pages"
