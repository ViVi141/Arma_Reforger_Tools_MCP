"""检查 JSON 中的空字段，按字段路径汇总统计"""

import json
from pathlib import Path
from collections import defaultdict

# 已知的 schema 字段名（非类名）
SCHEMA_KEYS = frozenset({
    "api_source", "classes", "name", "full_name", "description", "inheritance",
    "parent", "ancestors", "methods", "properties", "examples", "url",
    "signature", "return_type", "parameters", "type", "code", "language",
    "title",
})


def is_class_key(part: str) -> bool:
    """判断路径部分是否为类名（应被过滤）"""
    if part in SCHEMA_KEYS:
        return False
    # 包含 Interface、Template、<> 等视为类名
    if "Interface" in part or "Template" in part or "<" in part or ">" in part:
        return True
    return False


def get_field_path(path_parts: list) -> str:
    """将路径部分转换为可聚合的字段路径（忽略数组索引和类名）"""
    result = []
    skip_next = False  # 跳过 classes 后的第一个部分（类名）
    for part in path_parts:
        if part.startswith("["):
            continue  # 忽略数组索引
        if part == "classes":
            skip_next = True
            continue
        if skip_next:
            skip_next = False
            continue  # 跳过类名
        if is_class_key(part):
            continue
        result.append(part)
    return ".".join(result) if result else "root"


def check_empty(obj, path_parts=None, stats=None):
    if path_parts is None:
        path_parts = []
    if stats is None:
        stats = defaultdict(int)

    if isinstance(obj, dict):
        for k, v in obj.items():
            parts = path_parts + [k]
            if v == "" or v == [] or v is None:
                field_path = get_field_path(parts)
                stats[field_path] += 1
            check_empty(v, parts, stats)
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            check_empty(item, path_parts + [f"[{i}]"], stats)

    return stats


def truncate(text: str, max_len: int = 80) -> str:
    """截断过长文本"""
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def main():
    data_dir = Path(__file__).parent.parent / "data"
    files = ["arma_reforger_api.json", "enfusion_api.json"]
    max_line_len = 76  # 避免终端换行截断

    for filename in files:
        filepath = data_dir / filename
        if not filepath.exists():
            print(f"跳过（不存在）: {filename}")
            continue

        print(f"\n=== {filename} ===")
        try:
            data = json.loads(filepath.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"  解析失败: {e}")
            continue

        stats = check_empty(data)
        total_empty = sum(stats.values())
        print(f"  空字段总出现次数: {total_empty}")

        # 按出现次数排序，仅保留 schema 字段路径
        sorted_stats = sorted(stats.items(), key=lambda x: -x[1])
        print("\n  按字段路径汇总（前 30）:")
        for path, count in sorted_stats[:30]:
            path_display = truncate(path, max_line_len - 15)  # 预留 "    : 100000"
            print(f"    {path_display}: {count}")


if __name__ == "__main__":
    main()
