# 测试说明

本目录包含项目的所有测试代码。

## 目录结构

```
tests/
├── unit/              # 单元测试
│   ├── parser/       # 解析器测试
│   ├── indexer/      # 索引系统测试
│   ├── mcp_server/   # MCP服务器测试
│   └── utils/        # 工具函数测试
├── integration/       # 集成测试
└── conftest.py        # pytest 配置
```

## 运行测试

### 运行所有测试

```bash
pytest
```

### 运行单元测试

```bash
pytest tests/unit/
```

### 运行集成测试

```bash
pytest tests/integration/ -m integration
```

### 运行特定测试文件

```bash
pytest tests/unit/utils/test_helpers.py
```

### 运行特定测试类

```bash
pytest tests/unit/utils/test_helpers.py::TestGetDataPath
```

### 运行特定测试方法

```bash
pytest tests/unit/utils/test_helpers.py::TestGetDataPath::test_default_path
```

## 测试覆盖率

生成测试覆盖率报告：

```bash
pytest --cov=src --cov-report=html
```

覆盖率报告将生成在 `htmlcov/index.html`

## 测试标记

- `@pytest.mark.unit`: 单元测试
- `@pytest.mark.integration`: 集成测试
- `@pytest.mark.slow`: 慢速测试

运行特定标记的测试：

```bash
pytest -m unit          # 只运行单元测试
pytest -m integration   # 只运行集成测试
pytest -m "not slow"    # 排除慢速测试
```

## 编写测试

### 单元测试示例

```python
import pytest
from src.utils.helpers import clean_text

class TestCleanText:
    def test_clean_normal_text(self):
        text = "  hello   world  "
        result = clean_text(text)
        assert result == "hello world"
```

### 集成测试示例

```python
import pytest

@pytest.mark.integration
class TestParserIntegration:
    def test_parse_real_file(self):
        # 测试真实文件解析
        pass
```

## 注意事项

1. 单元测试应该快速且独立
2. 集成测试可能需要访问实际文件
3. 使用 fixtures 来设置测试数据
4. 使用 mock 来隔离依赖
