"""扩展的 HTML 解析器测试"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.parser.html_parser import HTMLParser
from src.utils.helpers import get_docs_path


class TestHTMLParserExtended:
    """扩展的 HTML 解析器测试"""
    
    @pytest.fixture
    def parser(self):
        """创建解析器实例"""
        return HTMLParser(api_source="arma_reforger")
    
    @pytest.fixture
    def sample_functions_html(self):
        """示例函数页面 HTML"""
        return """
        <!DOCTYPE html>
        <html>
        <head><title>Functions</title></head>
        <body>
            <div class="headertitle">
                <div class="title">Global Functions</div>
            </div>
            <div class="contents">
                <h2>Functions</h2>
                <table class="memberdecls">
                    <tr>
                        <td class="memItemLeft">void</td>
                        <td class="memItemRight">
                            <a class="el" href="#SomeFunction">SomeFunction</a> (int param)
                        </td>
                    </tr>
                </table>
            </div>
        </body>
        </html>
        """
    
    @pytest.fixture
    def sample_class_with_properties_html(self):
        """包含属性的类页面"""
        return """
        <!DOCTYPE html>
        <html>
        <head><title>TestClass</title></head>
        <body>
            <div class="headertitle">
                <div class="title">TestClass Interface Reference</div>
            </div>
            <div class="contents">
                <div class="textblock">
                    This is a test class description.
                </div>
                <h2>Public Attributes</h2>
                <table class="memberdecls">
                    <tr>
                        <td class="memItemLeft">string</td>
                        <td class="memItemRight">
                            <a class="el" href="#mProperty">mProperty</a>
                            <div class="memdoc">
                                Property description
                            </div>
                        </td>
                    </tr>
                </table>
                <h2>Public Member Functions</h2>
                <table class="memberdecls">
                    <tr>
                        <td class="memItemLeft">proto external void</td>
                        <td class="memItemRight">
                            <a class="el" href="#TestMethod">TestMethod</a> (int param1, string param2)
                            <div class="memdoc">
                                Method description
                            </div>
                        </td>
                    </tr>
                </table>
            </div>
        </body>
        </html>
        """
    
    def test_parse_functions_page(self, parser, sample_functions_html):
        """测试解析函数页面"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(sample_functions_html)
            temp_path = Path(f.name)
        
        try:
            result = parser.parse_file(temp_path)
            
            assert result is not None
            assert "functions" in result.get("name", "").lower() or "global" in result.get("name", "").lower()
        finally:
            if temp_path.exists():
                temp_path.unlink()
    
    def test_extract_properties(self, parser, sample_class_with_properties_html):
        """测试提取属性"""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(sample_class_with_properties_html, "lxml")
        properties = parser._extract_properties(soup)
        
        assert isinstance(properties, list)
        if len(properties) > 0:
            assert "name" in properties[0]
            assert "type" in properties[0]
    
    def test_extract_inheritance(self, parser):
        """测试提取继承关系"""
        html_with_inheritance = """
        <html>
        <body>
            <div class="contents">
                <h2>Inheritance diagram</h2>
                <map id="TestClass_map">
                    <area href="BaseClass.html" alt="BaseClass"/>
                </map>
                <p>Inherits <a href="BaseClass.html">BaseClass</a></p>
            </div>
        </body>
        </html>
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(html_with_inheritance)
            temp_path = Path(f.name)
        
        try:
            result = parser.parse_file(temp_path)
            if result:
                assert "inheritance" in result
                assert isinstance(result["inheritance"], dict)
        finally:
            if temp_path.exists():
                temp_path.unlink()
    
    def test_extract_code_examples(self, parser):
        """测试提取代码示例"""
        html_with_example = """
        <html>
        <body>
            <div class="contents">
                <h2>Example</h2>
                <div class="fragment">
                    <pre class="fragment">
void ExampleFunction() {
    // Example code
}
                    </pre>
                </div>
            </div>
        </body>
        </html>
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(html_with_example)
            temp_path = Path(f.name)
        
        try:
            result = parser.parse_file(temp_path)
            if result:
                assert "examples" in result
                assert isinstance(result["examples"], list)
        finally:
            if temp_path.exists():
                temp_path.unlink()
    
    def test_parse_method_row_complex(self, parser):
        """测试解析复杂的方法行"""
        html_complex_method = """
        <tr>
            <td class="memItemLeft">proto external out notnull array&lt;BaseClass&gt;</td>
            <td class="memItemRight">
                <a class="el" href="#GetArray">GetArray</a> 
                (out notnull array&lt;int&gt; outArray, int defaultParam = 10)
                <div class="memdoc">
                    Returns an array of BaseClass objects.
                </div>
            </td>
        </tr>
        """
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_complex_method, "lxml")
        row = soup.find("tr")
        
        method = parser._parse_method_row(row, soup)
        
        assert method is not None
        assert "name" in method
        assert "signature" in method
        assert method["name"] == "GetArray"
        assert "parameters" in method
    
    def test_extract_method_parameters_complex(self, parser):
        """测试提取复杂参数"""
        html_complex_params = """
        <tr>
            <td class="memItemLeft">void</td>
            <td class="memItemRight">
                <a class="el" href="#TestMethod">TestMethod</a> 
                (out notnull array&lt;BaseClass&gt; outArray, int defaultParam = 10, string optionalParam)
            </td>
        </tr>
        """
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_complex_params, "lxml")
        row = soup.find("tr")
        mem_item_right = row.find("td", class_="memItemRight")
        
        parameters = parser._extract_parameters(mem_item_right)
        
        assert isinstance(parameters, list)
        if len(parameters) > 0:
            # 检查参数结构
            assert "type" in parameters[0] or "name" in parameters[0]
    
    def test_build_method_signature_complex(self, parser):
        """测试构建复杂方法签名"""
        return_type = "proto external out notnull array<BaseClass>"
        method_name = "GetComplexMethod"
        parameters = [
            {"type": "int", "name": "param1", "description": ""},
            {"type": "string", "name": "param2", "description": ""},
            {"type": "array<BaseClass>", "name": "param3", "description": ""}
        ]
        
        signature = parser._build_method_signature(return_type, method_name, parameters)
        
        assert method_name in signature
        assert "int param1" in signature
        assert "string param2" in signature
        assert "array<BaseClass> param3" in signature
    
    def test_clean_text_various_formats(self, parser):
        """测试清理各种格式的文本"""
        from src.utils.helpers import clean_text
        
        # 测试包含换行符的文本
        text_with_newlines = "Line 1\nLine 2\nLine 3"
        cleaned = clean_text(text_with_newlines)
        assert "\n" not in cleaned or cleaned.count("\n") < text_with_newlines.count("\n")
        
        # 测试包含制表符的文本
        text_with_tabs = "Column1\tColumn2\tColumn3"
        cleaned = clean_text(text_with_tabs)
        assert isinstance(cleaned, str)
        
        # 测试空字符串
        assert clean_text("") == ""
        
        # 测试 None
        assert clean_text(None) == ""


class TestHTMLParserErrorHandling:
    """HTML 解析器错误处理测试"""
    
    @pytest.fixture
    def parser(self):
        """创建解析器实例"""
        return HTMLParser(api_source="arma_reforger")
    
    def test_parse_file_with_invalid_html(self, parser):
        """测试解析无效 HTML"""
        invalid_html = "<html><body><div>Unclosed tags"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(invalid_html)
            temp_path = Path(f.name)
        
        try:
            # 应该不崩溃，返回 None 或空结果
            result = parser.parse_file(temp_path)
            # 结果可能是 None 或者是一个有效的结果
            assert result is None or isinstance(result, dict)
        finally:
            if temp_path.exists():
                temp_path.unlink()
    
    def test_parse_file_with_empty_file(self, parser):
        """测试解析空文件"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write("")
            temp_path = Path(f.name)
        
        try:
            result = parser.parse_file(temp_path)
            # 应该返回 None 或空结果
            assert result is None or isinstance(result, dict)
        finally:
            if temp_path.exists():
                temp_path.unlink()
    
    def test_extract_methods_with_no_table(self, parser):
        """测试在没有方法表格时提取方法"""
        html_no_methods = """
        <html>
        <body>
            <div class="contents">
                <h2>Public Member Functions</h2>
                <!-- 没有方法表格 -->
            </div>
        </body>
        </html>
        """
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_no_methods, "lxml")
        table = soup.find("table", class_="memberdecls")
        # 如果没有表格，创建一个空的 Tag 对象用于测试
        if table is None:
            from bs4 import Tag
            table = Tag(name="table", attrs={"class": "memberdecls"})
            soup.append(table)
        methods = parser._extract_methods(table, soup)
        
        assert isinstance(methods, list)
        assert len(methods) == 0  # 没有表格应该返回空列表
    
    def test_extract_properties_with_no_table(self, parser):
        """测试在没有属性表格时提取属性"""
        html_no_properties = """
        <html>
        <body>
            <div class="contents">
                <h2>Public Attributes</h2>
                <!-- 没有属性表格 -->
            </div>
        </body>
        </html>
        """
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_no_properties, "lxml")
        properties = parser._extract_properties(soup)
        
        assert isinstance(properties, list)


class TestHTMLParserEdgeCases:
    """HTML 解析器边缘情况测试"""
    
    @pytest.fixture
    def parser(self):
        """创建解析器实例"""
        return HTMLParser(api_source="arma_reforger")
    
    def test_parse_file_with_special_characters(self, parser):
        """测试包含特殊字符的文件"""
        html_special = """
        <html>
        <body>
            <div class="headertitle">
                <div class="title">TestClass &amp; Reference</div>
            </div>
            <div class="textblock">
                Description with &lt;angle&gt; brackets and &quot;quotes&quot;
            </div>
        </body>
        </html>
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(html_special)
            temp_path = Path(f.name)
        
        try:
            result = parser.parse_file(temp_path)
            assert result is not None
            # 特殊字符应该被正确解析
            assert "TestClass" in result.get("name", "")
        finally:
            if temp_path.exists():
                temp_path.unlink()
    
    def test_extract_method_parameters_edge_cases(self, parser):
        """测试参数提取的边缘情况"""
        from bs4 import BeautifulSoup, Tag
        
        # 空参数
        html_empty = """
        <tr>
            <td class="memItemRight">
                <a class="el" href="#NoParams">NoParams</a> ()
            </td>
        </tr>
        """
        soup = BeautifulSoup(html_empty, "lxml")
        mem_item_right = soup.find("td", class_="memItemRight")
        result = parser._extract_parameters(mem_item_right)
        assert isinstance(result, list)
        
        # 单个参数无类型
        html_no_type = """
        <tr>
            <td class="memItemRight">
                <a class="el" href="#OneParam">OneParam</a> (paramName)
            </td>
        </tr>
        """
        soup = BeautifulSoup(html_no_type, "lxml")
        mem_item_right = soup.find("td", class_="memItemRight")
        result = parser._extract_parameters(mem_item_right)
        assert isinstance(result, list)
        
        # 嵌套泛型
        html_nested = """
        <tr>
            <td class="memItemRight">
                <a class="el" href="#Nested">Nested</a> (array&lt;array&lt;int&gt;&gt; nestedArray)
            </td>
        </tr>
        """
        soup = BeautifulSoup(html_nested, "lxml")
        mem_item_right = soup.find("td", class_="memItemRight")
        result = parser._extract_parameters(mem_item_right)
        assert isinstance(result, list)
    
    def test_parse_method_row_without_description(self, parser):
        """测试没有描述的方法行"""
        html_no_desc = """
        <tr>
            <td class="memItemLeft">void</td>
            <td class="memItemRight">
                <a class="el" href="#NoDesc">NoDesc</a> ()
            </td>
        </tr>
        """
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_no_desc, "lxml")
        row = soup.find("tr")
        
        method = parser._parse_method_row(row, soup)
        
        assert method is not None
        assert method["name"] == "NoDesc"
        assert "description" in method
