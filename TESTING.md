# 测试文档

本文档说明项目的测试策略和测试覆盖情况。

## 测试框架

项目使用 **pytest** 作为测试框架，具有以下特性：

- 简洁的测试语法
- 丰富的断言支持
- 强大的 fixture 系统
- 参数化测试
- 测试覆盖率报告

## 测试分类

### 1. 单元测试 (`tests/unit/`)

单元测试针对单个模块或函数进行测试，不依赖外部资源。

**已实现的测试：**

- ✅ `tests/unit/utils/test_helpers.py` - 工具函数测试
  - `get_data_path()` - 路径获取
  - `ensure_data_dir()` - 目录创建
  - `save_json()` / `load_json()` - JSON 操作
  - `clean_text()` - 文本清理
  - `get_docs_path()` - 文档路径获取

- ✅ `tests/unit/parser/test_html_parser.py` - HTML 解析器测试
  - 类页面解析
  - 方法提取
  - 签名构建

- ✅ `tests/unit/parser/test_build_index.py` - 索引构建测试
  - 接口文件查找
  - API 索引构建
  - 错误处理

**待实现的测试：**

- ⏳ `tests/unit/indexer/test_search_index.py` - 搜索索引测试
- ⏳ `tests/unit/mcp_server/test_server.py` - MCP 服务器测试

### 2. 集成测试 (`tests/integration/`)

集成测试验证多个模块协同工作，可能使用真实文件。

**已实现的测试：**

- ✅ `tests/integration/test_parser_integration.py` - 解析器集成测试
  - 真实文件解析
  - BaseWeaponComponent 解析

## 运行测试

### 基本命令

```bash
# 运行所有测试
pytest

# 运行单元测试
pytest tests/unit/

# 运行集成测试
pytest tests/integration/ -m integration

# 运行特定测试文件
pytest tests/unit/utils/test_helpers.py

# 运行特定测试类
pytest tests/unit/utils/test_helpers.py::TestGetDataPath

# 运行特定测试方法
pytest tests/unit/utils/test_helpers.py::TestGetDataPath::test_default_path
```

### 使用便捷脚本

```bash
# 运行所有测试
python run_tests.py

# 运行特定测试
python run_tests.py tests/unit/utils/
```

### 测试覆盖率

```bash
# 生成覆盖率报告
pytest --cov=src --cov-report=html

# 查看报告
# 打开 htmlcov/index.html
```

## 测试标记

使用 pytest 标记来分类测试：

- `@pytest.mark.unit` - 单元测试
- `@pytest.mark.integration` - 集成测试
- `@pytest.mark.slow` - 慢速测试

运行特定标记的测试：

```bash
pytest -m unit          # 只运行单元测试
pytest -m integration   # 只运行集成测试
pytest -m "not slow"    # 排除慢速测试
```

## 编写测试

### 测试命名规范

- 测试文件：`test_*.py`
- 测试类：`Test*`
- 测试函数：`test_*`

### 测试结构示例

```python
import pytest
from src.module import function

class TestFunction:
    """测试 function 函数"""
    
    def test_normal_case(self):
        """测试正常情况"""
        result = function("input")
        assert result == "expected"
    
    def test_edge_case(self):
        """测试边界情况"""
        result = function("")
        assert result is None
    
    @pytest.mark.parametrize("input,expected", [
        ("a", "A"),
        ("b", "B"),
    ])
    def test_multiple_cases(self, input, expected):
        """参数化测试"""
        result = function(input)
        assert result == expected
```

### 使用 Fixtures

```python
@pytest.fixture
def sample_data():
    """提供测试数据"""
    return {"key": "value"}

def test_with_fixture(sample_data):
    """使用 fixture"""
    assert "key" in sample_data
```

### Mock 外部依赖

```python
from unittest.mock import patch, MagicMock

def test_with_mock():
    """使用 mock"""
    with patch("module.external_function") as mock_func:
        mock_func.return_value = "mocked"
        result = function_under_test()
        assert result == "mocked"
```

## 测试最佳实践

1. **独立性**: 每个测试应该独立运行，不依赖其他测试
2. **可重复性**: 测试结果应该一致，不依赖外部状态
3. **快速性**: 单元测试应该快速执行
4. **清晰性**: 测试名称和断言应该清晰表达意图
5. **覆盖率**: 尽量覆盖所有代码路径，包括错误情况

## 持续集成

建议在 CI/CD 流程中运行测试：

```yaml
# 示例 GitHub Actions 配置
- name: Run tests
  run: |
    pip install -r requirements.txt
    pytest --cov=src --cov-report=xml
```

## 当前测试状态

### 覆盖率统计

运行 `pytest --cov=src` 查看当前覆盖率。

### 测试通过率

所有已实现的测试应该通过：

```bash
pytest -v
```

## 待办事项

- [ ] 实现索引系统的单元测试
- [ ] 实现 MCP 服务器的单元测试
- [ ] 添加性能测试
- [ ] 添加端到端测试
- [ ] 提高测试覆盖率到 80%+
