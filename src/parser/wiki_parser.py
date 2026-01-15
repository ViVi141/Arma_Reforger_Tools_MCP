"""Wiki 页面解析器 - 解析 MediaWiki HTML 页面"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup, Tag

from src.utils.helpers import clean_text


class WikiParser:
    """Wiki 页面解析器"""

    def __init__(self, wiki_pages_path: Optional[Path] = None):
        """
        初始化解析器
        
        Args:
            wiki_pages_path: Wiki 页面目录路径，如果为 None 则使用默认路径
        """
        if wiki_pages_path is None:
            # 默认使用项目根目录下的 wiki_pages
            base_path = Path(__file__).parent.parent.parent
            self.wiki_pages_path = base_path / "wiki_pages"
        else:
            self.wiki_pages_path = Path(wiki_pages_path)

    def parse_file(self, html_file: Path, json_file: Optional[Path] = None) -> Optional[Dict[str, Any]]:
        """
        解析单个 Wiki HTML 文件
        
        Args:
            html_file: HTML 文件路径
            json_file: 对应的 JSON 元数据文件路径（可选）
            
        Returns:
            解析后的数据字典，如果解析失败返回 None
        """
        if not html_file.exists():
            return None

        try:
            # 读取 HTML 文件
            encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
            content = None
            
            for encoding in encodings:
                try:
                    with open(html_file, "r", encoding=encoding, errors="replace") as f:
                        content = f.read()
                    break
                except (UnicodeDecodeError, UnicodeError):
                    continue
            
            if content is None:
                with open(html_file, "rb") as f:
                    raw_content = f.read()
                content = raw_content.decode("utf-8", errors="replace")
            
            soup = BeautifulSoup(content, "lxml")
            
            # 读取 JSON 元数据（如果存在）
            metadata = {}
            if json_file and json_file.exists():
                try:
                    with open(json_file, "r", encoding="utf-8") as f:
                        loaded_metadata = json.load(f)
                        if isinstance(loaded_metadata, dict):
                            metadata = loaded_metadata
                except Exception:
                    metadata = {}
            
            # 解析页面
            return self._parse_wiki_page(soup, html_file, metadata)
                
        except Exception as e:
            print(f"Error parsing wiki file {html_file}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _parse_wiki_page(self, soup: BeautifulSoup, file_path: Path, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """解析 Wiki 页面内容"""
        # 提取标题
        title_elem = soup.find("h1", class_="firstHeading")
        title = ""
        if title_elem:
            # 移除命名空间部分（如果有）
            title_text = title_elem.get_text(strip=True)
            if " – " in title_text:
                title = title_text.split(" – ")[0]
            else:
                title = title_text
        
        # 如果没有找到标题，使用文件名
        if not title:
            title = file_path.stem.replace("_", " ").replace("Arma Reforger", "").strip()
        
        # 提取主要内容
        content_elem = soup.find("div", id="mw-content-text")
        if not content_elem:
            content_elem = soup.find("div", class_="mw-body-content")
        
        # 提取文本内容
        description = ""
        full_text = ""
        sections = []
        
        if content_elem:
            # 移除不需要的元素
            for elem in content_elem.find_all(["script", "style", "nav", "div", "aside"]):
                if elem is None:
                    continue
                try:
                    elem_id = elem.get("id")
                    elem_class = elem.get("class")
                    # 处理 class 属性可能是 None 或字符串的情况
                    if elem_class is None:
                        elem_class = []
                    elif isinstance(elem_class, str):
                        elem_class = [elem_class]
                    elif not isinstance(elem_class, list):
                        elem_class = []
                    
                    if elem_id in ["toc", "mw-navigation", "siteSub", "contentSub"]:
                        elem.decompose()
                    elif isinstance(elem_class, list) and "toc" in elem_class:
                        elem.decompose()
                except (AttributeError, TypeError):
                    # 如果元素有问题，跳过
                    continue
            
            # 提取第一段作为描述
            first_p = content_elem.find("p")
            if first_p:
                description = clean_text(first_p.get_text())
            
            # 提取所有文本内容
            full_text = clean_text(content_elem.get_text())
            
            # 提取章节
            sections = self._extract_sections(content_elem)
        
        # 提取分类
        categories = []
        try:
            category_elem = soup.find("div", id="biki-top-categories")
            if category_elem:
                for link in category_elem.find_all("a"):
                    if link:
                        cat_text = link.get_text(strip=True)
                        if cat_text:
                            categories.append(cat_text)
        except (AttributeError, TypeError):
            # 如果提取分类失败，继续处理
            pass
        
        # 构建数据字典
        # 确保 metadata 是字典类型
        if not isinstance(metadata, dict):
            metadata = {}
        
        wiki_data = {
            "title": title,
            "api_source": "arma_reforger_wiki",
            "type": "wiki",
            "description": description,
            "full_text": full_text,
            "sections": sections,
            "categories": categories,
            "url": metadata.get("url", "") if isinstance(metadata, dict) else "",
            "saved_at": metadata.get("saved_at", "") if isinstance(metadata, dict) else "",
            "file_name": file_path.name
        }
        
        return wiki_data

    def _extract_sections(self, content_elem: Tag) -> List[Dict[str, Any]]:
        """提取页面章节"""
        sections = []
        
        # 查找所有标题
        headings = content_elem.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
        
        for heading in headings:
            heading_id = heading.get("id", "")
            heading_text = heading.get_text(strip=True)
            
            if not heading_text:
                continue
            
            # 提取该章节的内容
            section_content = []
            current = heading.next_sibling
            
            while current:
                # 如果遇到下一个同级或更高级的标题，停止
                if isinstance(current, Tag):
                    if current.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                        heading_level = int(current.name[1])
                        current_level = int(heading.name[1])
                        if heading_level <= current_level:
                            break
                    
                    # 收集段落内容
                    if current.name == "p":
                        text = clean_text(current.get_text())
                        if text:
                            section_content.append(text)
                
                current = current.next_sibling
            
            if heading_text or section_content:
                sections.append({
                    "id": heading_id,
                    "title": heading_text,
                    "level": int(heading.name[1]) if heading.name.startswith("h") else 1,
                    "content": "\n".join(section_content)
                })
        
        return sections

    def find_wiki_files(self) -> List[tuple[Path, Optional[Path]]]:
        """
        查找所有 Wiki 文件
        
        Returns:
            (HTML 文件路径, JSON 元数据文件路径) 的元组列表
        """
        wiki_files = []
        
        if not self.wiki_pages_path.exists():
            return wiki_files
        
        # 查找所有 HTML 文件
        for html_file in self.wiki_pages_path.glob("*.html"):
            # 跳过 Category 页面（可选）
            if html_file.stem.startswith("Category_"):
                continue
            
            # 查找对应的 JSON 文件
            json_file = html_file.with_suffix(".json")
            if not json_file.exists():
                json_file = None
            
            wiki_files.append((html_file, json_file))
        
        return sorted(wiki_files)