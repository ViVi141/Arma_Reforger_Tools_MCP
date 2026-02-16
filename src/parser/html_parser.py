"""HTML 文档解析器"""

import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup, Tag, NavigableString

from src.utils.helpers import clean_text, get_docs_path


class HTMLParser:
    """HTML 文档解析器"""

    def __init__(self, api_source: str = "arma_reforger"):
        """
        初始化解析器
        
        Args:
            api_source: API 来源 ("arma_reforger" 或 "enfusion")
        """
        self.api_source = api_source
        self.docs_path = get_docs_path(api_source)

    def parse_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        解析单个 HTML 文件
        
        Args:
            file_path: HTML 文件路径
            
        Returns:
            解析后的数据字典，如果解析失败返回 None
        """
        if not file_path.exists():
            return None

        try:
            # 尝试多种编码方式读取文件
            content = None
            encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252", "gbk", "gb2312"]
            
            for encoding in encodings:
                try:
                    with open(file_path, "r", encoding=encoding, errors="replace") as f:
                        content = f.read()
                    break
                except (UnicodeDecodeError, UnicodeError):
                    continue
            
            if content is None:
                # 如果所有编码都失败，使用二进制模式读取并使用错误替换
                with open(file_path, "rb") as f:
                    raw_content = f.read()
                content = raw_content.decode("utf-8", errors="replace")
            
            soup = BeautifulSoup(content, "lxml")
            
            # 检查是否是类接口页面
            # 通过文件名或页面内容判断
            if ("interface" in file_path.stem and file_path.stem.startswith("interface")) or \
               soup.find("div", class_="headertitle") is not None:
                return self._parse_class_page(soup, file_path)
            # 检查是否是函数页面
            elif "functions" in file_path.stem:
                return self._parse_functions_page(soup, file_path)
            else:
                return None
                
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return None

    def _parse_class_page(self, soup: BeautifulSoup, file_path: Path) -> Dict[str, Any]:
        """解析类接口页面"""
        # 计算相对路径，如果文件不在文档目录中则使用文件名
        try:
            url = str(file_path.relative_to(self.docs_path))
        except ValueError:
            # 文件不在文档目录中（例如测试文件）
            url = file_path.name
        
        class_data = {
            "name": "",
            "full_name": "",
            "api_source": self.api_source,
            "description": "",
            "inheritance": {
                "parent": None,
                "ancestors": []
            },
            "methods": [],
            "properties": [],
            "examples": [],
            "url": url
        }

        # 提取类名
        title_elem = soup.find("div", class_="headertitle")
        if title_elem:
            title_text = title_elem.find("div", class_="title")
            if title_text:
                class_data["name"] = clean_text(title_text.get_text())
                class_data["full_name"] = class_data["name"]

        # 提取描述
        desc_elem = soup.find("div", class_="textblock")
        if desc_elem:
            class_data["description"] = clean_text(desc_elem.get_text())

        # 提取继承关系
        inheritance_map = soup.find("map", id=re.compile(r".*_map$"))
        if inheritance_map:
            areas = inheritance_map.find_all("area")
            for area in areas:
                href = area.get("href", "")
                alt = area.get("alt", "")
                if href and alt:
                    if not class_data["inheritance"]["parent"]:
                        class_data["inheritance"]["parent"] = alt
                    class_data["inheritance"]["ancestors"].append(alt)

        # 提取方法
        methods_table = soup.find("table", class_="memberdecls")
        if methods_table:
            class_data["methods"] = self._extract_methods(methods_table, soup)

        # 提取属性（如果有）
        # Doxygen 的 h2 在 table 内部作为行标题，需用 find_parent 获取所在表格
        for h2 in soup.find_all("h2", class_="groupheader"):
            if re.search(r"Attributes|Properties", h2.get_text(), re.I):
                attrs_table = h2.find_parent("table", class_="memberdecls")
                if attrs_table:
                    class_data["properties"] = self._extract_properties(attrs_table)
                break

        # 提取示例代码
        examples_section = soup.find("div", class_="fragment")
        if examples_section:
            class_data["examples"] = self._extract_examples(soup)

        return class_data

    def _extract_properties(self, table: Tag) -> List[Dict[str, Any]]:
        """从属性表中提取属性信息"""
        properties = []
        # Doxygen 使用 memitem:hash 格式，需用正则匹配
        rows = table.find_all("tr", class_=re.compile(r"^memitem"))
        for row in rows:
            prop = self._parse_property_row(row)
            if prop:
                properties.append(prop)
        
        return properties

    def _parse_property_row(self, row: Tag) -> Optional[Dict[str, Any]]:
        """解析单个属性行"""
        property_data = {
            "name": "",
            "type": "",
            "description": ""
        }

        mem_item_left = row.find("td", class_="memItemLeft")
        mem_item_right = row.find("td", class_="memItemRight")
        
        if mem_item_left and mem_item_right:
            # 属性类型（需用 get_text 以支持带链接的类型，如 <a>BaseUserAction</a>）
            type_text = mem_item_left.get_text()
            if type_text:
                property_data["type"] = clean_text(type_text)
            
            # 属性名
            prop_link = mem_item_right.find("a", class_="el")
            if prop_link:
                property_data["name"] = clean_text(prop_link.get_text())

        # 提取描述（Doxygen 使用 memdesc:hash 格式）
        mem_desc = row.find_next_sibling("tr", class_=re.compile(r"^memdesc"))
        if mem_desc:
            desc_elem = mem_desc.find("td", class_="mdescRight")
            if desc_elem:
                property_data["description"] = clean_text(desc_elem.get_text())

        if property_data["name"]:
            return property_data
        return None

    def _extract_examples(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """
        提取代码示例
        
        支持多种代码块格式：
        - div.fragment (Doxygen 标准格式)
        - pre.code (标准 HTML 代码块)
        - code 标签内的代码
        """
        examples = []
        
        # 方法1: 查找 Doxygen 格式的代码片段 (div.fragment)
        code_fragments = soup.find_all("div", class_="fragment")
        for fragment in code_fragments:
            example = self._parse_code_fragment(fragment)
            if example:
                examples.append(example)
        
        # 方法2: 查找标准 HTML 代码块 (pre.code)
        pre_blocks = soup.find_all("pre")
        for pre_block in pre_blocks:
            # 跳过已经在 fragment 中的代码块
            if pre_block.find_parent("div", class_="fragment"):
                continue
            
            code_elem = pre_block.find("code")
            if code_elem:
                code_text = code_elem.get_text()
            else:
                code_text = pre_block.get_text()
            
            if code_text.strip():
                # 尝试从上下文提取描述
                description = self._extract_example_description(pre_block)
                language = self._detect_language(code_text)
                
                examples.append({
                    "code": clean_text(code_text),
                    "language": language,
                    "description": description,
                    "title": ""
                })
        
        # 方法3: 查找带标题的示例部分
        example_sections = soup.find_all(
            ["h2", "h3", "h4"],
            string=re.compile(r".*[Ee]xample.*|.*[Cc]ode.*|.*[Uu]sage.*", re.I)
        )
        for section in example_sections:
            # 查找该标题下的代码块
            next_elem = section.find_next_sibling()
            while next_elem:
                if next_elem.name in ["h2", "h3", "h4"]:
                    break
                
                code_frag = next_elem.find("div", class_="fragment")
                if code_frag:
                    example = self._parse_code_fragment(code_frag)
                    if example:
                        example["title"] = clean_text(section.get_text())
                        examples.append(example)
                    break
                
                pre_block = next_elem.find("pre")
                if pre_block:
                    code_text = pre_block.get_text()
                    if code_text.strip():
                        examples.append({
                            "code": clean_text(code_text),
                            "language": self._detect_language(code_text),
                            "description": self._extract_example_description(next_elem),
                            "title": clean_text(section.get_text())
                        })
                    break
                
                next_elem = next_elem.find_next_sibling()
        
        return examples
    
    def _parse_code_fragment(self, fragment: Tag) -> Optional[Dict[str, str]]:
        """解析单个代码片段"""
        code_text = fragment.get_text()
        if not code_text.strip():
            return None
        
        # 尝试从父元素或前一个元素提取描述
        description = self._extract_example_description(fragment)
        
        # 检测语言
        language = self._detect_language(code_text)
        
        # 尝试提取标题
        title = ""
        prev_elem = fragment.find_previous_sibling()
        if prev_elem and prev_elem.name in ["h2", "h3", "h4", "p"]:
            title_text = prev_elem.get_text().strip()
            if title_text and len(title_text) < 100:  # 避免过长的文本作为标题
                title = clean_text(title_text)
        
        return {
            "code": clean_text(code_text),
            "language": language,
            "description": description,
            "title": title
        }
    
    def _extract_example_description(self, code_element: Tag) -> str:
        """从代码元素周围提取描述"""
        description = ""
        
        # 查找前一个段落或 div
        prev_elem = code_element.find_previous_sibling()
        if prev_elem:
            if prev_elem.name == "p":
                desc_text = prev_elem.get_text().strip()
                if desc_text and not desc_text.startswith("<"):
                    description = clean_text(desc_text)
            elif prev_elem.name == "div" and "textblock" in prev_elem.get("class", []):
                desc_text = prev_elem.get_text().strip()
                if desc_text:
                    description = clean_text(desc_text)
        
        # 如果没有找到，查找父元素中的描述
        if not description:
            parent = code_element.find_parent(["div", "section"])
            if parent:
                # 查找父元素中的文本块
                text_blocks = parent.find_all("div", class_="textblock")
                for text_block in text_blocks:
                    if text_block.find("div", class_="fragment") == code_element:
                        desc_text = text_block.get_text().strip()
                        if desc_text:
                            description = clean_text(desc_text)
                            break
        
        return description
    
    def _detect_language(self, code_text: str) -> str:
        """检测代码语言"""
        code_lower = code_text.lower().strip()
        
        # 检测 C++ 特征
        cpp_keywords = ["#include", "namespace", "class", "public:", "private:", "std::"]
        if any(keyword in code_lower for keyword in cpp_keywords):
            return "c++"
        
        # 检测 Enforce 特征
        enforce_keywords = [
            "proto", "external", "class", "void", "int", "float", "string",
            "bool", "array", "ref", "autoptr", "override"
        ]
        if any(keyword in code_lower for keyword in enforce_keywords):
            return "enforce"
        
        # 默认返回 enforce（Arma Reforger 主要使用 Enforce）
        return "enforce"

    def _extract_methods(self, table: Tag, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """从方法表中提取方法信息"""
        methods = []
        # Doxygen 使用 memitem:hash 格式，需用正则匹配
        rows = table.find_all("tr", class_=re.compile(r"^memitem"))
        for row in rows:
            method = self._parse_method_row(row, soup)
            if method:
                methods.append(method)
        
        return methods

    def _parse_method_row(self, row: Tag, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """解析单个方法行"""
        method = {
            "name": "",
            "signature": "",
            "description": "",
            "return_type": "",
            "parameters": [],
            "examples": []
        }

        # 提取方法名和签名
        mem_item_left = row.find("td", class_="memItemLeft")
        mem_item_right = row.find("td", class_="memItemRight")
        
        if mem_item_left and mem_item_right:
            # 返回类型
            return_type_elem = mem_item_left.find(string=True)
            if return_type_elem:
                method["return_type"] = clean_text(str(return_type_elem).strip())
            
            # 方法名和参数
            method_link = mem_item_right.find("a", class_="el")
            if method_link:
                method["name"] = clean_text(method_link.get_text())
                # 提取参数
                method["parameters"] = self._extract_parameters(mem_item_right)
                # 构建完整签名
                method["signature"] = self._build_method_signature(
                    method["return_type"],
                    method["name"],
                    method["parameters"]
                )

        # 提取描述（Doxygen 使用 memdesc:hash 格式）
        mem_desc = row.find_next_sibling("tr", class_=re.compile(r"^memdesc"))
        if mem_desc:
            desc_elem = mem_desc.find("td", class_="mdescRight")
            if desc_elem:
                method["description"] = clean_text(desc_elem.get_text())
                
                # 在描述区域查找代码示例
                method_examples = self._extract_method_examples(desc_elem)
                if method_examples:
                    method["examples"] = method_examples

        if method["name"]:
            return method
        return None
    
    def _extract_method_examples(self, desc_elem: Tag) -> List[Dict[str, str]]:
        """从方法描述区域提取代码示例"""
        examples = []
        
        # 查找描述中的代码片段
        code_fragments = desc_elem.find_all("div", class_="fragment")
        for fragment in code_fragments:
            example = self._parse_code_fragment(fragment)
            if example:
                examples.append(example)
        
        # 查找 pre 标签中的代码
        pre_blocks = desc_elem.find_all("pre")
        for pre_block in pre_blocks:
            code_elem = pre_block.find("code")
            if code_elem:
                code_text = code_elem.get_text()
            else:
                code_text = pre_block.get_text()
            
            if code_text.strip():
                examples.append({
                    "code": clean_text(code_text),
                    "language": self._detect_language(code_text),
                    "description": "",
                    "title": ""
                })
        
        return examples

    def _extract_parameters(self, mem_item_right: Tag) -> List[Dict[str, str]]:
        """从方法行中提取参数"""
        parameters = []
        param_text = mem_item_right.get_text()
        
        # 查找参数部分（在方法名后的括号中）
        import re
        # 匹配方法名后的括号内容
        match = re.search(r'\(([^)]*)\)', param_text)
        if match:
            params_str = match.group(1).strip()
            if params_str:
                # 简单分割参数（可以后续优化）
                # 参数格式通常是: type paramName 或 type paramName, type paramName
                param_parts = [p.strip() for p in params_str.split(',')]
                for param_part in param_parts:
                    if param_part:
                        # 尝试解析参数类型和名称
                        parts = param_part.split()
                        if len(parts) >= 2:
                            param_type = ' '.join(parts[:-1])
                            param_name = parts[-1]
                            parameters.append({
                                "type": clean_text(param_type),
                                "name": clean_text(param_name),
                                "description": ""
                            })
                        else:
                            # 只有类型，没有名称
                            parameters.append({
                                "type": clean_text(param_part),
                                "name": "",
                                "description": ""
                            })
        
        return parameters

    def _build_method_signature(
        self, 
        return_type: str, 
        method_name: str, 
        parameters: List[Dict[str, str]]
    ) -> str:
        """构建方法签名"""
        # 构建参数字符串
        if parameters:
            params_str = ", ".join([
                f"{p['type']} {p['name']}" if p['name'] else p['type']
                for p in parameters
            ])
        else:
            params_str = ""
        
        signature = f"{return_type} {method_name}({params_str})"
        return clean_text(signature)

    def _parse_functions_page(self, soup: BeautifulSoup, file_path: Path) -> Dict[str, Any]:
        """解析函数页面"""
        # TODO: 实现函数页面解析
        return {}
