"""构建 API 索引的主脚本"""

import os
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.parser.html_parser import HTMLParser
from src.parser.wiki_parser import WikiParser
from src.indexer.search_index import SearchIndex
from src.indexer.relationship_index import RelationshipIndex
from src.utils.helpers import save_json, get_docs_path, get_wiki_pages_path, ensure_data_dir

# 单文件解析超时（秒），超时则跳过该文件
_PARSE_TIMEOUT = 30


def get_cpu_count() -> int:
    """获取 CPU 核心数，兼容多平台"""
    return os.cpu_count() or 1


def _get_worker_count(workers: Optional[int] = None, for_parallel_sources: bool = False) -> int:
    """
    获取 HTML 解析工作线程/进程数（自动检测）

    Args:
        workers: 显式指定时使用该值
        for_parallel_sources: 当 api_source=both 时 True，会分配一半以避免过载

    Returns:
        工作线程/进程数
    """
    if workers is not None and workers > 0:
        n = workers
    else:
        cpu = get_cpu_count()
        # Windows 下 32 线程易卡死，限制为 8
        cap = 8 if os.name == "nt" else 32
        n = min(cap, max(cpu, cpu * 2))
    if for_parallel_sources and n > 1:
        return max(1, n // 2)
    return n


def _get_index_procs(procs: int) -> int:
    """
    获取 Whoosh 并行索引进程数（自动检测）

    Args:
        procs: 0 表示自动检测，>0 使用指定值

    Returns:
        进程数，0 表示单进程
    """
    if procs > 0:
        return procs
    cpu = get_cpu_count()
    # Whoosh procs 建议 2-4，过多收益递减
    return min(4, max(1, cpu))


def _get_chunksize(task_count: int, worker_count: int) -> int:
    """计算 executor.map 的 chunksize，平衡负载与开销"""
    return max(1, task_count // (worker_count * 8))


def _parse_single_file(args: Tuple[Path, str]) -> Optional[Dict[str, Any]]:
    """工作线程：解析单个 HTML 文件。每个线程使用独立的 parser 实例。"""
    file_path, api_source = args
    parser = HTMLParser(api_source)
    return parser.parse_file(file_path)


def find_interface_files(docs_path: Path) -> List[Path]:
    """查找所有接口文件"""
    interface_files = []
    
    # 查找所有 interface*.html 文件
    for html_file in docs_path.glob("interface*.html"):
        # 排除 -members.html 文件（成员列表页面）
        if "-members" not in html_file.stem:
            interface_files.append(html_file)
    
    return sorted(interface_files)


def build_api_index(
    api_source: str = "arma_reforger",
    workers: Optional[int] = None,
    for_parallel_sources: bool = False,
) -> Dict[str, Any]:
    """
    构建 API 索引

    Args:
        api_source: API 来源
        workers: 并行工作线程数，None 则自动检测

    Returns:
        构建的索引数据
    """
    print(f"开始构建 {api_source} API 索引...")

    docs_path = get_docs_path(api_source)
    if not docs_path.exists():
        print(f"错误: 文档路径不存在: {docs_path}")
        return {}

    interface_files = find_interface_files(docs_path)
    print(f"找到 {len(interface_files)} 个接口文件")

    api_data = {
        "api_source": api_source,
        "classes": {},
        "total_classes": 0,
        "total_methods": 0,
        "total_properties": 0,
    }

    max_workers = _get_worker_count(workers, for_parallel_sources=for_parallel_sources)
    tasks = [(f.resolve(), api_source) for f in interface_files]

    # 使用 as_completed + 超时，避免单文件卡死阻塞整体；Windows 用进程池更稳定
    use_processes = os.name == "nt"
    executor_cls = ProcessPoolExecutor if use_processes else ThreadPoolExecutor
    results = [None] * len(tasks)

    print(f"开始解析（{max_workers} 个{'进程' if use_processes else '线程'}，超时 {_PARSE_TIMEOUT}s/文件）...", flush=True)
    with executor_cls(max_workers=max_workers) as executor:
        future_to_idx = {executor.submit(_parse_single_file, t): i for i, t in enumerate(tasks)}
        done_count = 0
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            try:
                results[idx] = future.result(timeout=_PARSE_TIMEOUT)
            except Exception as e:
                file_path = tasks[idx][0]
                print(f"跳过 {file_path.name}: {e}", flush=True)
            done_count += 1
            if done_count % 100 == 0:
                print(f"已处理 {done_count}/{len(interface_files)} 个文件...", flush=True)

    for i, class_data in enumerate(results):
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


def build_search_index(
    api_source: str = "arma_reforger",
    procs: int = 0,
) -> None:
    """
    构建搜索索引

    Args:
        api_source: API 来源
        procs: Whoosh 并行索引进程数，0 表示单进程
    """
    print(f"开始构建 {api_source} 搜索索引...")

    json_file = f"{api_source}_api.json"
    search_index = SearchIndex(api_source)

    try:
        search_index.load_from_json(json_file, procs=procs)
        print("搜索索引构建完成!")
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
        print("关系索引构建完成!")
    except Exception as e:
        print(f"构建关系索引时出错: {e}")


def _parse_wiki_file(args: Tuple[Path, Path, Path]) -> Optional[Dict[str, Any]]:
    """工作线程：解析单个 Wiki 文件"""
    html_file, json_file, wiki_pages_path = args
    parser = WikiParser(wiki_pages_path)
    return parser.parse_file(html_file, json_file)


def build_wiki_index(workers: Optional[int] = None) -> Dict[str, Any]:
    """
    构建 Wiki 索引

    Args:
        workers: 并行工作线程数，None 则自动检测

    Returns:
        构建的 Wiki 索引数据
    """
    print("开始构建 Wiki 索引...")

    wiki_pages_path = get_wiki_pages_path()
    if not wiki_pages_path.exists():
        print(f"错误: Wiki 页面路径不存在: {wiki_pages_path}")
        return {}

    parser = WikiParser(wiki_pages_path)
    wiki_files = parser.find_wiki_files()
    print(f"找到 {len(wiki_files)} 个 Wiki 文件")

    wiki_data = {
        "api_source": "arma_reforger_wiki",
        "pages": {},
        "total_pages": 0,
        "total_sections": 0,
    }

    max_workers = _get_worker_count(workers)
    tasks = [(html_f, json_f, wiki_pages_path) for html_f, json_f in wiki_files]
    chunksize = _get_chunksize(len(tasks), max_workers)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(_parse_wiki_file, tasks, chunksize=chunksize))

    for i, page_data in enumerate(results):
        if i > 0 and i % 10 == 0:
            print(f"已处理 {i}/{len(wiki_files)} 个文件...")
        if page_data and page_data.get("title"):
            page_title = page_data["title"]
            wiki_data["pages"][page_title] = page_data
            wiki_data["total_sections"] += len(page_data.get("sections", []))

    wiki_data["total_pages"] = len(wiki_data["pages"])
    print(f"完成! 解析了 {wiki_data['total_pages']} 个 Wiki 页面, "
          f"{wiki_data['total_sections']} 个章节")

    return wiki_data


def build_wiki_search_index(procs: int = 0) -> None:
    """构建 Wiki 搜索索引"""
    print("开始构建 Wiki 搜索索引...")

    json_file = "arma_reforger_wiki.json"
    search_index = SearchIndex("arma_reforger_wiki")

    try:
        search_index.load_from_json(json_file, procs=procs)
        print("Wiki 搜索索引构建完成!")
    except Exception as e:
        print(f"构建 Wiki 搜索索引时出错: {e}")


def _build_single_source(
    api_source: str,
    skip_parse: bool,
    skip_search_index: bool,
    skip_relationship_index: bool,
    workers: Optional[int],
    index_procs: int,
    for_parallel_sources: bool = False,
) -> None:
    """构建单个 API 来源的索引"""
    # 并行构建时 Whoosh procs>1 在 Windows 上易与线程死锁，强制单进程
    search_procs = 1 if for_parallel_sources else index_procs

    if not skip_parse:
        data = build_api_index(
            api_source,
            workers=workers,
            for_parallel_sources=for_parallel_sources,
        )
        save_json(data, f"{api_source}_api.json")
        print(f"已保存 {api_source} API 数据到 data/{api_source}_api.json", flush=True)

    if not skip_search_index:
        build_search_index(api_source, procs=search_procs)

    if not skip_relationship_index:
        build_relationship_index(api_source)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="构建 Arma Reforger API 索引")
    parser.add_argument(
        "--api-source",
        choices=["arma_reforger", "enfusion", "both"],
        default="arma_reforger",
        help="要构建的 API 来源",
    )
    parser.add_argument(
        "--skip-parse",
        action="store_true",
        help="跳过文档解析，只构建索引",
    )
    parser.add_argument(
        "--skip-search-index",
        action="store_true",
        help="跳过搜索索引构建",
    )
    parser.add_argument(
        "--skip-relationship-index",
        action="store_true",
        help="跳过关系索引构建",
    )
    parser.add_argument(
        "--include-wiki",
        action="store_true",
        help="包含 Wiki 页面索引构建",
    )
    parser.add_argument(
        "--wiki-only",
        action="store_true",
        help="只构建 Wiki 索引",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=None,
        metavar="N",
        help="HTML 解析并行工作线程数，默认自动检测 (CPU*2)",
    )
    parser.add_argument(
        "--index-procs",
        type=int,
        default=0,
        metavar="N",
        help="Whoosh 搜索索引并行进程数，0 表示自动检测",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="最快索引：自动检测 CPU/线程并应用最优设置",
    )
    parser.add_argument(
        "--sequential",
        action="store_true",
        help="api-source=both 时顺序构建（避免 Windows 下并行死锁）",
    )

    args = parser.parse_args()

    ensure_data_dir()

    workers = args.workers
    index_procs = max(0, args.index_procs)
    if index_procs == 0:
        index_procs = _get_index_procs(0)
    if args.fast:
        workers = workers or _get_worker_count(None)
        cpu = get_cpu_count()
        # Windows 下并行构建易死锁，自动使用顺序模式
        if args.api_source == "both" and os.name == "nt" and not args.sequential:
            args.sequential = True
            print(f"[最快模式] 检测到 {cpu} 核 CPU，"
                  f"解析线程: {workers}，Whoosh 进程: {index_procs}")
            print("[最快模式] Windows 下 api-source=both 使用顺序构建以避免死锁", flush=True)
        else:
            print(f"[最快模式] 检测到 {cpu} 核 CPU，"
                  f"解析线程: {workers}，Whoosh 进程: {index_procs}")

    # 如果只构建 Wiki，跳过 API 构建
    if args.wiki_only:
        if not args.skip_parse:
            wiki_data = build_wiki_index(workers=workers)
            save_json(wiki_data, "arma_reforger_wiki.json")
            print("已保存 Wiki 数据到 data/arma_reforger_wiki.json")

        if not args.skip_search_index:
            build_wiki_search_index(procs=index_procs)

        print("Wiki 索引构建完成!")
        return

    # 构建 API 索引
    if args.api_source == "both":
        if args.sequential:
            # 顺序构建，避免 Windows 下线程+多进程死锁
            print("顺序构建 Arma Reforger 和 Enfusion 索引...", flush=True)
            _build_single_source(
                "arma_reforger",
                args.skip_parse,
                args.skip_search_index,
                args.skip_relationship_index,
                workers,
                index_procs,
                for_parallel_sources=False,
            )
            _build_single_source(
                "enfusion",
                args.skip_parse,
                args.skip_search_index,
                args.skip_relationship_index,
                workers,
                index_procs,
                for_parallel_sources=False,
            )
        else:
            # 并行构建 arma_reforger 和 enfusion，每个源分配一半线程
            print("并行构建 Arma Reforger 和 Enfusion 索引...", flush=True)
            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = [
                    executor.submit(
                        _build_single_source,
                        "arma_reforger",
                        args.skip_parse,
                        args.skip_search_index,
                        args.skip_relationship_index,
                        workers,
                        index_procs,
                        for_parallel_sources=True,
                    ),
                    executor.submit(
                        _build_single_source,
                        "enfusion",
                        args.skip_parse,
                        args.skip_search_index,
                        args.skip_relationship_index,
                        workers,
                        index_procs,
                        for_parallel_sources=True,
                    ),
                ]
                for f in as_completed(futures):
                    f.result()
    else:
        _build_single_source(
            args.api_source,
            args.skip_parse,
            args.skip_search_index,
            args.skip_relationship_index,
            workers,
            index_procs,
        )

    # 构建 Wiki 索引（如果启用）
    if args.include_wiki:
        if not args.skip_parse:
            wiki_data = build_wiki_index(workers=workers)
            save_json(wiki_data, "arma_reforger_wiki.json")
            print("已保存 Wiki 数据到 data/arma_reforger_wiki.json")

        if not args.skip_search_index:
            build_wiki_search_index(procs=index_procs)

    print("索引构建完成!")


if __name__ == "__main__":
    main()
