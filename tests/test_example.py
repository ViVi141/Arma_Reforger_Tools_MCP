"""示例测试 - 用于验证测试框架是否正常工作"""

import pytest


def test_example():
    """示例测试"""
    assert 1 + 1 == 2


class TestExample:
    """示例测试类"""
    
    def test_string_concatenation(self):
        """测试字符串连接"""
        assert "hello" + " " + "world" == "hello world"
    
    def test_list_operations(self):
        """测试列表操作"""
        my_list = [1, 2, 3]
        my_list.append(4)
        assert len(my_list) == 4
        assert my_list[-1] == 4
    
    @pytest.mark.parametrize("input_value,expected", [
        (1, 2),
        (2, 4),
        (3, 6),
    ])
    def test_multiplication(self, input_value, expected):
        """参数化测试示例"""
        assert input_value * 2 == expected
