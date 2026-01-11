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
            class_data["methods"] = self._extract_methods(methods_table)

        # 提取属性（如果有）
        # 查找属性相关的表格或部分
        # 注意：Doxygen 可能将属性放在不同的表格中
        attrs_section = soup.find("h2", string=re.compile(".*Attributes.*|.*Properties.*", re.I))
        if attrs_section:
            attrs_table = attrs_section.find_next("table", class_="memberdecls")
            if attrs_table:
                class_data["properties"] = self._extract_properties(attrs_table)

        # 提取示例代码
        examples_section = soup.find("div", class_="fragment")
        if examples_section:
            class_data["examples"] = self._extract_examples(soup)

        return class_data

    def _extract_properties(self, table: Tag) -> List[Dict[str, Any]]:
        """从属性表中提取属性信息"""
        properties = []
        
        rows = table.find_all("tr", class_="memitem")
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
            # 属性类型
            type_elem = mem_item_left.find(text=True, recursive=False)
            if type_elem:
                property_data["type"] = clean_text(str(type_elem))
            
            # 属性名
            prop_link = mem_item_right.find("a", class_="el")
            if prop_link:
                property_data["name"] = clean_text(prop_link.get_text())

        # 提取描述
        mem_desc = row.find_next_sibling("tr", class_="memdesc")
        if mem_desc:
            desc_elem = mem_desc.find("td", class_="mdescRight")
            if desc_elem:
                property_data["description"] = clean_text(desc_elem.get_text())

        if property_data["name"]:
            return property_data
        return None

    def _extract_examples(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """提取代码示例"""
        examples = []
        
        # 查找代码片段
        code_fragments = soup.find_all("div", class_="fragment")
        for fragment in code_fragments:
            code_text = fragment.get_text()
            if code_text.strip():
                examples.append({
                    "code": clean_text(code_text),
                    "language": "enforce",  # Arma Reforger 使用 Enforce 脚本
                    "description": ""
                })
        
        return examples

    def _extract_methods(self, table: Tag) -> List[Dict[str, Any]]:
        """从方法表中提取方法信息"""
        methods = []
        
        rows = table.find_all("tr", class_="memitem")
        for row in rows:
            method = self._parse_method_row(row)
            if method:
                methods.append(method)
        
        return methods

    def _parse_method_row(self, row: Tag) -> Optional[Dict[str, Any]]:
        """解析单个方法行"""
        method = {
            "name": "",
            "signature": "",
            "description": "",
            "return_type": "",
            "parameters": []
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

        # 提取描述
        mem_desc = row.find_next_sibling("tr", class_="memdesc")
        if mem_desc:
            desc_elem = mem_desc.find("td", class_="mdescRight")
            if desc_elem:
                method["description"] = clean_text(desc_elem.get_text())

        if method["name"]:
            return method
        return None

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
