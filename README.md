# Arma Reforger API MCP 服务器

这是一个 MCP（Model Context Protocol）服务器，将 Arma Reforger 和 Enfusion 脚本 API 文档集成到 Cursor 等 AI 代码编辑器中。

## 功能特性

- 🔍 **全文搜索**: 快速搜索 API（类、方法、属性、枚举）
- 📚 **详细信息**: 获取完整的 API 文档和代码示例
- 🔗 **关系查找**: 查找相关 API 和继承关系
- ⚡ **高性能**: 索引预加载和响应缓存
- 🛡️ **错误处理**: 完善的错误处理和验证机制

## 安装

### 0. 准备原始文档（可选）

**重要说明**：原始 HTML 文档（`ArmaReforgerScriptAPIPublic/` 和 `EnfusionScriptAPIPublic/`）位于：
```
\Steam\steamapps\common\Arma Reforger Tools\Workbench\docs
```

由于可能的版权原因，本仓库不包含这些文档文件。如果你需要构建索引，请将这些目录复制到项目根目录。

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 解析文档并构建索引

```bash
python -m src.parser.build_index
```

### 3. 配置 Cursor

在 Cursor 的 MCP 配置文件中添加：

```json
{
  "mcpServers": {
    "arma-reforger-api": {
      "command": "python",
      "args": ["-m", "src.mcp_server.server"],
      "cwd": "项目路径",
      "env": {
        "API_DATA_PATH": "项目路径/data"
      }
    }
  }
}
```

## 使用方法

在 Cursor 中，LLM 会自动使用以下工具：

- `search_api`: 搜索 API
- `get_class_info`: 获取类信息
- `get_function_info`: 获取方法信息
- `find_related_apis`: 查找相关 API
- `get_code_examples`: 获取代码示例

## 项目结构

```
├── src/
│   ├── parser/          # 文档解析器
│   ├── indexer/         # 索引系统
│   ├── mcp_server/      # MCP 服务器
│   └── utils/           # 工具函数
├── data/                # 处理后的数据
├── config/              # 配置文件
└── docs/                # 原始文档
```

## 测试

### 运行测试

```bash
# 运行所有测试
pytest

# 运行单元测试
pytest tests/unit/

# 运行集成测试
pytest tests/integration/ -m integration

# 运行特定测试文件
pytest tests/unit/utils/test_helpers.py

# 查看测试覆盖率
pytest --cov=src --cov-report=html
```

### 测试结构

```
tests/
├── unit/              # 单元测试
│   ├── parser/       # 解析器测试
│   ├── indexer/      # 索引系统测试
│   ├── mcp_server/   # MCP服务器测试
│   └── utils/        # 工具函数测试
└── integration/       # 集成测试
```

详细测试说明请查看 [tests/README.md](tests/README.md)

## 开发状态

### ✅ 已完成功能

- [x] HTML 文档解析器
- [x] 类、方法、属性信息提取
- [x] 搜索索引系统（Whoosh）
- [x] 关系索引系统
- [x] MCP 服务器框架
- [x] 5 个核心工具实现
- [x] 错误处理和日志系统
- [x] 单元测试框架

### 📋 待实现功能

- [x] ~~代码示例提取优化~~ ✅ **已完成** - 已实现代码示例提取功能（`_extract_examples` 方法和 `get_code_examples` 工具）
- [ ] 性能测试 - 需要添加性能基准测试和性能监控
- [x] ~~端到端测试~~ ✅ **部分完成** - 已实现集成测试（`test_parser_integration.py`），但缺少完整的 MCP 服务器端到端测试
- [ ] API 版本管理 - 需要实现多版本支持、版本比较和版本查询功能
- [ ] **SSE/HTTP 远程调用支持** ⚠️ **可选功能** - 当前使用 stdio 传输（适合本地使用）。SSE/HTTP 传输可用于远程访问场景（如远程服务器、云部署），但对大多数本地用户不必要

## 开发

安装和使用说明请查看 [INSTALLATION.md](INSTALLATION.md)

Cursor 集成指南请查看 [CURSOR_SETUP.md](CURSOR_SETUP.md)

## 许可证

MIT

## 作者

- **ViVi141** - [GitHub](https://github.com/ViVi141)
  - 邮箱: 747384120@qq.com
  - 仓库: [https://github.com/ViVi141/Arma_Reforger_Tools_MCP](https://github.com/ViVi141/Arma_Reforger_Tools_MCP)
