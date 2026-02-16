# Cursor 集成快速指南

## 快速步骤

### 1. 前置条件检查

确保已完成：
- ✅ 索引已构建（运行 `python -m src.parser.build_index --skip-parse`）
- ✅ 依赖已安装（`pip install -r requirements.txt`）
- ✅ 数据文件存在（`data/arma_reforger_api.json` 和 `data/search_index/arma_reforger/`）

### 2. 生成配置文件

运行以下命令生成配置（会自动使用当前项目路径）：

```bash
python -c "import json; from pathlib import Path; p = Path.cwd(); venv = p / '.venv' / 'Scripts' / 'python.exe'; cmd = str(venv) if venv.exists() else 'python'; config = {'mcpServers': {'arma-reforger-api': {'command': cmd, 'args': ['-m', 'src.mcp_server.server'], 'cwd': str(p), 'env': {'API_DATA_PATH': str(p / 'data'), 'LOG_LEVEL': 'INFO', 'PYTHONPATH': str(p)}}}}; print(json.dumps(config, indent=2, ensure_ascii=False))"
```

**复制输出的 JSON 配置**

### 3. 配置 Cursor

1. **打开配置文件**：
   - 路径：`%APPDATA%\Cursor\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json`
   - 或者：`C:\Users\74738\AppData\Roaming\Cursor\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json`

2. **添加配置**：
   - 如果文件不存在，创建它
   - 如果文件已存在，在 `mcpServers` 对象中添加配置
   - 粘贴步骤 2 中生成的 JSON 配置

3. **保存文件**

### 4. 重启 Cursor

**重要**：完全关闭并重新打开 Cursor 使配置生效！

### 5. 测试连接

在 Cursor 的聊天界面中尝试：

- "如何搜索 BaseWeaponComponent API？"
- "查找与武器相关的类"
- "获取 CharacterControllerComponent 的详细信息"

## 配置文件示例

**推荐：使用自动生成脚本**（在项目根目录运行）：
```bash
python -c "import json; from pathlib import Path; p = Path.cwd(); venv = p / '.venv' / 'Scripts' / 'python.exe'; cmd = str(venv) if venv.exists() else 'python'; config = {'mcpServers': {'arma-reforger-api': {'command': cmd, 'args': ['-m', 'src.mcp_server.server'], 'cwd': str(p), 'env': {'API_DATA_PATH': str(p / 'data'), 'LOG_LEVEL': 'INFO', 'PYTHONPATH': str(p)}}}}; print(json.dumps(config, indent=2, ensure_ascii=False))"
```

**手动配置示例**：
```json
{
  "mcpServers": {
    "arma-reforger-api": {
      "command": "python",
      "args": [
        "-m",
        "src.mcp_server.server"
      ],
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

**注意**：请将路径替换为你的实际项目路径！

## 故障排除

### 服务器无法启动

检查：
1. Python 路径是否正确（使用完整路径）
2. 虚拟环境是否存在（如果使用虚拟环境）
3. 所有依赖是否已安装

测试：
```bash
python -m src.mcp_server.server
```

### Cursor 无法连接

检查：
1. 配置文件格式是否正确（JSON 语法）
2. 路径是否正确（使用完整路径，反斜杠转义）
3. 是否已重启 Cursor

### 工具不可用

检查：
1. 数据文件是否存在
2. 索引是否已构建
3. 查看 Cursor 的开发者工具（帮助 > 切换开发者工具）

## 使用示例

配置成功后，在 Cursor 中可以这样使用：

**用户**：如何获取玩家的当前武器？

**AI**：[自动调用 search_api 工具] 让我搜索相关的 API...

**用户**：BaseWeaponComponent 有哪些方法？

**AI**：[自动调用 get_class_info 工具] BaseWeaponComponent 包含以下方法...

## 更多信息

- 详细安装说明：`INSTALLATION.md`
- 项目文档：`README.md`
