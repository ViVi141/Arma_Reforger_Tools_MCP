# 安装和使用指南

## 安装步骤

### 0. 准备原始文档（可选）

**重要说明**：

#### API 文档

原始 HTML 文档文件（`ArmaReforgerScriptAPIPublic/` 和 `EnfusionScriptAPIPublic/`）位于 Steam 安装目录：
```
\Steam\steamapps\common\Arma Reforger Tools\Workbench\docs
```

由于可能的版权原因，本仓库不包含这些文档文件。如果你需要构建索引，请将这两个目录从上述路径复制到项目根目录。

**注意**：
- 这些文档由 Doxygen 生成，属于 Arma Reforger Tools 的一部分
- 本仓库只包含索引构建工具和生成的索引数据
- 用户需要自行从 Steam 安装目录获取原始文档

#### Wiki 页面（可选）

**版权说明**：
- Wiki 页面来自 [Bohemia Interactive Community Wiki](https://community.bistudio.com/wiki)
- 由于可能的版权原因，本仓库**不包含**原始 Wiki HTML 和 JSON 文件
- 如果需要使用 Wiki 功能，请将 Wiki 页面文件放置在 `wiki_pages/` 目录中
- 可以使用爬虫工具从 Wiki 网站下载页面
- 使用 Wiki 内容时请遵守 Bohemia Interactive 的版权和使用条款

**获取方式**：
- 从 Wiki 网站手动下载或使用爬虫工具
- 文件应包含 HTML 和对应的 JSON 元数据文件（可选）
- 文件命名格式：`Arma_Reforger_*.html` 和 `Arma_Reforger_*.json`

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 解析文档并构建索引

首先需要解析 HTML 文档并构建索引（需要先完成步骤 0）：

```bash
# 构建 Arma Reforger API 索引
python -m src.parser.build_index --api-source arma_reforger

# 或者同时构建两个 API 的索引
python -m src.parser.build_index --api-source both
```

这个过程可能需要几分钟，取决于文档数量。

### 3. 配置 Cursor

#### 方法 1：手动配置（推荐）

1. **找到配置文件路径**：
   ```
   %APPDATA%\Cursor\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json
   ```
   或者：
   ```
   C:\Users\74738\AppData\Roaming\Cursor\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json
   ```

2. **创建或编辑配置文件**，添加以下配置（**请将路径替换为你的实际项目路径**）：

   ```json
   {
     "mcpServers": {
       "arma-reforger-api": {
         "command": "C:\\Users\\74738\\Desktop\\Arma_Reforger_Tools_MCP\\.venv\\Scripts\\python.exe",
         "args": [
           "-m",
           "src.mcp_server.server"
         ],
         "cwd": "C:\\Users\\74738\\Desktop\\Arma_Reforger_Tools_MCP",
         "env": {
           "API_DATA_PATH": "C:\\Users\\74738\\Desktop\\Arma_Reforger_Tools_MCP\\data",
           "LOG_LEVEL": "INFO",
           "PYTHONPATH": "C:\\Users\\74738\\Desktop\\Arma_Reforger_Tools_MCP"
         }
       }
     }
   }
   ```

   **重要说明**：
   - 如果使用虚拟环境，`command` 应该是 `.venv\Scripts\python.exe` 的完整路径
   - 如果不使用虚拟环境，`command` 可以是 `python` 或 `python3`
   - `cwd` 必须是项目根目录的完整路径
   - 路径中的反斜杠需要转义（`\\`）

3. **保存配置文件**

#### 方法 2：使用 Python 生成配置

运行以下命令生成配置（会自动检测项目路径和虚拟环境）：

```bash
python -c "import json; from pathlib import Path; p = Path.cwd(); venv = p / '.venv' / 'Scripts' / 'python.exe'; cmd = str(venv) if venv.exists() else 'python'; config = {'mcpServers': {'arma-reforger-api': {'command': cmd, 'args': ['-m', 'src.mcp_server.server'], 'cwd': str(p), 'env': {'API_DATA_PATH': str(p / 'data'), 'LOG_LEVEL': 'INFO', 'PYTHONPATH': str(p)}}}}; print(json.dumps(config, indent=2, ensure_ascii=False))"
```

然后将输出复制到配置文件中。

### 4. 重启 Cursor

配置完成后，**完全关闭并重新打开 Cursor**，使配置生效。

### 5. 验证连接

在 Cursor 的聊天界面中测试：

- "如何搜索 BaseWeaponComponent API？"
- "查找与武器相关的类"
- "获取 CharacterControllerComponent 的详细信息"

如果 LLM 能够调用工具并返回结果，说明配置成功！

## 验证安装

### 检查数据文件

确保以下文件存在：
- `data/arma_reforger_api.json` (如果构建了 Arma Reforger 索引)
- `data/enfusion_api.json` (如果构建了 Enfusion 索引)
- `data/search_index/arma_reforger/` (搜索索引目录)
- `data/search_index/enfusion/` (搜索索引目录)

### 测试服务器

可以手动测试服务器是否正常工作：

```bash
python -m src.mcp_server.server
```

如果服务器正常启动，应该看到日志输出。

## 使用工具

在 Cursor 中，LLM 会自动使用以下工具：

### 1. search_api
搜索 API（类、方法、属性）

**示例查询**:
- "如何获取玩家的武器？"
- "BaseWeaponComponent"
- "武器组件"

### 2. get_class_info
获取类的详细信息

**示例查询**:
- "BaseWeaponComponent 有哪些方法？"
- "如何使用 CharacterControllerComponent？"

### 3. get_function_info
获取方法的详细信息

**示例查询**:
- "GetCurrentWeapon 方法的参数是什么？"
- "如何调用 GetOwner 方法？"

### 4. find_related_apis
查找相关的 API

**示例查询**:
- "BaseWeaponComponent 有哪些相关的类？"
- "哪些类使用了 WeaponComponent？"

### 5. get_code_examples
获取代码示例

**示例查询**:
- "BaseWeaponComponent 的使用示例"
- "如何创建武器组件？"

## 故障排除

### 问题：服务器无法启动

**解决方案**:
1. 检查 Python 版本（需要 3.8+）
2. 检查所有依赖是否已安装
3. 检查数据文件是否存在
4. 查看日志文件了解详细错误

### 问题：找不到 API

**解决方案**:
1. 确保已运行索引构建脚本
2. 检查 JSON 数据文件是否存在
3. 尝试重新构建索引

### 问题：搜索返回空结果

**解决方案**:
1. 检查搜索索引是否已构建
2. 尝试使用更通用的搜索词
3. 检查索引目录是否存在

## 更新索引

当 API 文档更新时，需要重新构建索引：

```bash
# 重新构建所有索引
python -m src.parser.build_index --api-source both

# 只重新构建搜索索引（如果 JSON 数据已存在）
python -m src.parser.build_index --skip-parse --api-source both
```

## 性能优化

### 索引预加载

索引会在首次使用时自动加载，后续查询会更快。

### 缓存

搜索结果可以缓存以提高性能（如果启用了缓存功能）。

## 支持

如果遇到问题，请检查：
1. 日志文件
2. 数据文件完整性
3. 配置文件格式
