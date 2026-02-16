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
