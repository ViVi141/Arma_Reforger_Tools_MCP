# Arma Reforger API MCP 服务器

> 一个强大的 MCP 服务器，为 Cursor 等 AI 代码编辑器提供 Arma Reforger 和 Enfusion 脚本 API 文档支持。

## ✨ 功能特性

- 🔍 **智能搜索** - 快速搜索 API 类、方法、属性，支持自然语言查询
- 📚 **完整文档** - 获取详细的 API 文档和代码示例
- 📖 **Wiki 支持** - 搜索和查询 Arma Reforger Wiki 页面内容
- 🔗 **关系图谱** - 查看 API 之间的继承和使用关系
- ⚡ **快速响应** - 基于全文索引的高性能搜索
- 🛡️ **稳定可靠** - 完善的错误处理和验证机制

## 📦 获取方式

本 MCP 服务已发布至 **ModelScope** 平台，你可以：

- 🌐 [在 ModelScope 上查看和安装](https://modelscope.cn/mcp/servers/ViVi141/Arma_Reforger_Tools_MCP)
- 📥 从 GitHub 克隆源码自行构建（见下方安装步骤）

## 🚀 快速开始

### 前置准备

> **注意**：原始 HTML 文档需要从 Steam 安装目录获取（由于版权原因，本仓库不包含原始文档）

**API 文档位置**：`\Steam\steamapps\common\Arma Reforger Tools\Workbench\docs`

将 `ArmaReforgerScriptAPIPublic` 和 `EnfusionScriptAPIPublic` 目录复制到项目根目录。

**Wiki 页面**（可选）：
- Wiki 页面来自 [Bohemia Interactive Community Wiki](https://community.bistudio.com/wiki)
- 由于可能的版权原因，本仓库不包含原始 Wiki HTML 和 JSON 文件
- 如果需要使用 Wiki 功能，请将 Wiki 页面文件放置在 `wiki_pages/` 目录中
- 可以使用爬虫工具从 Wiki 网站下载页面

### 安装步骤

1. **克隆仓库**
   ```bash
   git clone https://github.com/ViVi141/Arma_Reforger_Tools_MCP.git
   cd Arma_Reforger_Tools_MCP
   ```

2. **安装依赖**
   ```bash
   pip install -e .
   ```
   或使用 requirements.txt：`pip install -r requirements.txt`

3. **构建索引**
   ```bash
   # 构建 API 索引
   python -m src.parser.build_index
   
   # 构建 Wiki 索引（如果 wiki_pages 目录存在）
   python -m src.parser.build_index --wiki-only
   
   # 或者同时构建 API 和 Wiki 索引
   python -m src.parser.build_index --api-source arma_reforger --include-wiki
   ```
   > 这个过程可能需要几分钟时间

4. **配置 Cursor**

   在 Cursor 的 MCP 配置文件中添加（配置文件位置：`%APPDATA%\Cursor\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json`）：

   **自动生成配置**（推荐）：
   ```bash
   # 方法1: 使用专用脚本（推荐）
   python scripts/generate_config.py
   
   # 方法2: 安装后使用命令
   arma-reforger-mcp-config
   
   # 方法3: Windows PowerShell 自动写入配置
   .\scripts\setup_cursor.ps1
   ```

   > **虚拟环境说明**：脚本会自动检测并使用虚拟环境中的 Python 解释器。

   **手动配置**：
   ```json
   {
     "mcpServers": {
       "arma-reforger-api": {
         "command": "python",
         "args": ["-m", "src.mcp_server.server"],
         "cwd": "你的项目路径",
         "env": {
           "API_DATA_PATH": "你的项目路径/data",
           "LOG_LEVEL": "INFO",
           "PYTHONPATH": "你的项目路径"
         }
       }
     }
   }
   ```

5. **重启 Cursor**

   完全关闭并重新打开 Cursor，使配置生效。

## 💡 使用示例

配置完成后，在 Cursor 中可以直接问 AI：

### 基础查询
- **"如何获取玩家的当前武器？"**
- **"BaseWeaponComponent 有哪些方法？"**
- **"查找与武器相关的 API"**
- **"获取 CharacterControllerComponent 的详细信息"**

### Wiki 查询
- **"搜索 Wiki 中关于脚本的内容"**
- **"查找 Wiki 中关于动画编辑器的页面"**
- **"Wiki 中有哪些关于游戏主控的文档？"**

### 代码示例查询
- **"ShowCodeExample 的使用示例"**
- **"获取 BaseWeaponComponent 的代码示例"**
- **"如何创建武器组件？给我代码示例"**
- **"GetWeapon 方法的示例代码"**
- **"查找所有关于玩家控制的代码示例"**

AI 会自动调用相应的工具为你提供准确的 API 信息和代码示例。

### 代码示例功能说明

`get_code_examples` 工具支持：

1. **多来源查找**：从类级别和方法级别查找代码示例
2. **智能匹配**：支持精确匹配和部分匹配类名、方法名
3. **语言过滤**：支持按语言过滤（enforce、c++、all）
4. **上下文信息**：每个示例包含完整的上下文信息（所属类、方法等）
5. **丰富元数据**：示例包含标题、描述、语言类型等信息

**返回格式示例**：
```json
{
  "api_name": "BaseWeaponComponent",
  "examples": [
    {
      "code": "BaseWeaponComponent weapon = GetWeapon();\nif (weapon) {\n    // 使用武器组件\n}",
      "language": "enforce",
      "description": "获取武器组件的示例",
      "title": "使用示例",
      "context": {
        "type": "class",
        "class_name": "BaseWeaponComponent",
        "api_source": "arma_reforger"
      }
    }
  ],
  "total": 1,
  "matched_classes": [...],
  "matched_methods": [...]
}
```

## 📖 可用工具

| 工具名称 | 功能描述 | 主要参数 |
|---------|---------|---------|
| `search_api` | 搜索 API（类、方法、属性）和 Wiki 页面，支持自然语言查询 | `query`（必需）、`type`（支持 `wiki`）、`api_source`（支持 `arma_reforger_wiki`、`all`）、`limit` |
| `get_class_info` | 获取类的详细信息，包括方法、属性、继承关系、代码示例 | `class_name`（必需）、`api_source`、`include_examples` |
| `get_function_info` | 获取方法的详细信息，包括签名、参数、返回值、描述 | `function_name`（必需）、`class_name`、`api_source` |
| `find_related_apis` | 查找相关的 API，包括继承关系、使用关系等 | `api_name`（必需）、`api_source`、`relation_type` |
| `get_code_examples` | 获取代码示例，支持从类和方法中查找，包含完整的上下文信息 | `api_name`（必需）、`api_source`、`language` |

### 工具详细说明

#### `get_code_examples` - 代码示例工具

**功能**：
- 从类级别和方法级别查找代码示例
- 支持精确匹配和部分匹配
- 自动检测代码语言（enforce、c++）
- 提取示例的标题、描述和上下文信息

**参数**：
- `api_name`（必需）：要查找的 API 名称（类名或方法名）
- `api_source`（可选）：API 来源，可选值：`"arma_reforger"`、`"enfusion"`、`"both"`（默认）
- `language`（可选）：代码语言过滤，可选值：`"enforce"`（默认）、`"c++"`、`"all"`

**使用场景**：
- 查找特定类的使用示例
- 查找特定方法的调用示例
- 学习 API 的最佳实践
- 获取代码模板和参考实现

## 📚 文档

- 📘 [安装和使用指南](docs/INSTALLATION.md) - 详细的安装和配置说明
- 🔧 [Cursor 集成指南](docs/CURSOR_SETUP.md) - Cursor 集成步骤详解
- 📖 [Wiki 集成说明](docs/WIKI_INTEGRATION.md) - Wiki 页面集成和使用指南
- 🧪 [测试文档](docs/TESTING.md) - 测试说明和开发指南
- 📝 [更新日志](CHANGELOG.md) - 版本更新记录
- 🌐 [ModelScope 页面](https://modelscope.cn/mcp/servers/ViVi141/Arma_Reforger_Tools_MCP) - 在 ModelScope 平台上查看和使用

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

AGPL-3.0 license

## 👤 作者

- **ViVi141** - [GitHub](https://github.com/ViVi141)
  - 邮箱: 747384120@qq.com
  - 仓库: [https://github.com/ViVi141/Arma_Reforger_Tools_MCP](https://github.com/ViVi141/Arma_Reforger_Tools_MCP)
  - ModelScope: [https://modelscope.cn/mcp/servers/ViVi141/Arma_Reforger_Tools_MCP](https://modelscope.cn/mcp/servers/ViVi141/Arma_Reforger_Tools_MCP)

---

**提示**：如果遇到问题，请查看 [安装指南](docs/INSTALLATION.md) 或提交 Issue。
