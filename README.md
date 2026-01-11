# Arma Reforger API MCP 服务器

> 一个强大的 MCP 服务器，为 Cursor 等 AI 代码编辑器提供 Arma Reforger 和 Enfusion 脚本 API 文档支持。

## ✨ 功能特性

- 🔍 **智能搜索** - 快速搜索 API 类、方法、属性，支持自然语言查询
- 📚 **完整文档** - 获取详细的 API 文档和代码示例
- 🔗 **关系图谱** - 查看 API 之间的继承和使用关系
- ⚡ **快速响应** - 基于全文索引的高性能搜索
- 🛡️ **稳定可靠** - 完善的错误处理和验证机制

## 🚀 快速开始

### 前置准备

> **注意**：原始 HTML 文档需要从 Steam 安装目录获取（由于版权原因，本仓库不包含原始文档）

文档位置：`\Steam\steamapps\common\Arma Reforger Tools\Workbench\docs`

将 `ArmaReforgerScriptAPIPublic` 和 `EnfusionScriptAPIPublic` 目录复制到项目根目录。

### 安装步骤

1. **克隆仓库**
   ```bash
   git clone https://github.com/ViVi141/Arma_Reforger_Tools_MCP.git
   cd Arma_Reforger_Tools_MCP
   ```

2. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

3. **构建索引**
   ```bash
   python -m src.parser.build_index
   ```
   > 这个过程可能需要几分钟时间

4. **配置 Cursor**

   在 Cursor 的 MCP 配置文件中添加（配置文件位置：`%APPDATA%\Cursor\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json`）：

   ```json
   {
     "mcpServers": {
       "arma-reforger-api": {
         "command": "python",
         "args": ["-m", "src.mcp_server.server"],
         "cwd": "你的项目路径",
         "env": {
           "API_DATA_PATH": "你的项目路径/data"
         }
       }
     }
   }
   ```

5. **重启 Cursor**

   完全关闭并重新打开 Cursor，使配置生效。

## 💡 使用示例

配置完成后，在 Cursor 中可以直接问 AI：

- **"如何获取玩家的当前武器？"**
- **"BaseWeaponComponent 有哪些方法？"**
- **"查找与武器相关的 API"**
- **"获取 CharacterControllerComponent 的详细信息"**
- **"ShowCodeExample 的使用示例"**

AI 会自动调用相应的工具为你提供准确的 API 信息。

## 📖 可用工具

| 工具名称 | 功能描述 |
|---------|---------|
| `search_api` | 搜索 API（类、方法、属性） |
| `get_class_info` | 获取类的详细信息 |
| `get_function_info` | 获取方法的详细信息 |
| `find_related_apis` | 查找相关的 API |
| `get_code_examples` | 获取代码示例 |

## 📚 文档

- 📘 [安装和使用指南](INSTALLATION.md) - 详细的安装和配置说明
- 🔧 [Cursor 集成指南](CURSOR_SETUP.md) - Cursor 集成步骤详解
- 🧪 [测试文档](TESTING.md) - 测试说明和开发指南

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

MIT License

## 👤 作者

- **ViVi141** - [GitHub](https://github.com/ViVi141)
  - 邮箱: 747384120@qq.com
  - 仓库: [https://github.com/ViVi141/Arma_Reforger_Tools_MCP](https://github.com/ViVi141/Arma_Reforger_Tools_MCP)

---

**提示**：如果遇到问题，请查看 [安装指南](INSTALLATION.md) 或提交 Issue。
