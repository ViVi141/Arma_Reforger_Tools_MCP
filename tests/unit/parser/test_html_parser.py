"""测试 HTML 解析器"""

import pytest
import tempfile
from pathlib import Path
from bs4 import BeautifulSoup
from unittest.mock import patch, mock_open, MagicMock

from src.parser.html_parser import HTMLParser


class TestHTMLParser:
    """测试 HTMLParser 类"""

    @pytest.fixture
    def parser(self):
        """创建解析器实例"""
        return HTMLParser(api_source="arma_reforger")

    @pytest.fixture
    def sample_class_html(self):
        """示例类 HTML 内容"""
        return """
        <!DOCTYPE html>
        <html>
        <head><title>BaseWeaponComponent</title></head>
        <body>
            <div class="headertitle">
                <div class="title">BaseWeaponComponent Interface Reference</div>
            </div>
            <div class="textblock">
                This is a test description of BaseWeaponComponent.
            </div>
            <map id="BaseWeaponComponent_map">
                <area href="interfaceGameComponent.html" alt="GameComponent"/>
                <area href="interfaceWeaponComponent.html" alt="WeaponComponent"/>
            </map>
            <table class="memberdecls">
                <tr class="memitem">
                    <td class="memItemLeft">proto external UIInfo</td>
                    <td class="memItemRight">
                        <a class="el" href="#GetUIInfo">GetUIInfo</a> ()
                    </td>
                </tr>
                <tr class="memdesc">
                    <td class="mdescLeft"></td>
                    <td class="mdescRight">Returns UI information for the weapon.</td>
                </tr>
                <tr class="memitem">
                    <td class="memItemLeft">proto external string</td>
                    <td class="memItemRight">
                        <a class="el" href="#GetWeaponSlotType">GetWeaponSlotType</a> ()
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """

    def test_init(self, parser):
        """测试初始化"""
        assert parser.api_source == "arma_reforger"
        assert parser.docs_path.exists() or parser.docs_path.parent.exists()

    def test_parse_file_nonexistent(self, parser):
        """测试解析不存在的文件"""
        result = parser.parse_file(Path("/nonexistent/file.html"))
        assert result is None

    def test_parse_class_page(self, parser, sample_class_html):
        """测试解析类页面"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            f.write(sample_class_html)
            temp_path = Path(f.name)
        
        try:
            result = parser.parse_file(temp_path)
            
            assert result is not None
            # 类名可能包含额外文本，所以使用 in 检查
            assert "BaseWeaponComponent" in result.get("name", "")
            assert "description" in result
            assert "methods" in result
            assert isinstance(result["methods"], list)
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_extract_methods(self, parser, sample_class_html):
        """测试提取方法"""
        soup = BeautifulSoup(sample_class_html, "lxml")
        table = soup.find("table", class_="memberdecls")
        
        methods = parser._extract_methods(table, soup)
        
        assert len(methods) > 0
        assert any(m["name"] == "GetUIInfo" for m in methods)

    def test_parse_method_row(self, parser, sample_class_html):
        """测试解析方法行"""
        soup = BeautifulSoup(sample_class_html, "lxml")
        table = soup.find("table", class_="memberdecls")
        row = table.find("tr", class_="memitem")
        
        method = parser._parse_method_row(row, soup)
        
        assert method is not None
        assert method["name"] == "GetUIInfo"
        assert "return_type" in method
        assert "signature" in method

    def test_build_method_signature(self, parser):
        """测试构建方法签名"""
        # 测试参数列表
        parameters = [
            {"type": "int", "name": "param1", "description": ""},
            {"type": "string", "name": "param2", "description": ""}
        ]
        
        signature = parser._build_method_signature(
            "proto external void",
            "TestMethod",
            parameters
        )
        
        assert "TestMethod" in signature
        assert "void" in signature or "proto" in signature
        assert "int param1" in signature
        assert "string param2" in signature

    def test_clean_text_integration(self, parser):
        """测试文本清理集成"""
        from src.utils.helpers import clean_text
        text = "  hello   world  "
        result = clean_text(text)
        assert result == "hello world"
