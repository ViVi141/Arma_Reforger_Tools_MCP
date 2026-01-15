# Wiki 集成说明

## 概述

本项目现已支持将 Arma Reforger Wiki 页面集成到 MCP 服务器中，使得 AI 助手能够搜索和查询 Wiki 文档内容。

## ⚠️ 版权说明

**重要**：Wiki 页面来自 [Bohemia Interactive Community Wiki](https://community.bistudio.com/wiki)，属于 Bohemia Interactive 的版权内容。

- 本仓库**不包含**原始 Wiki HTML 和 JSON 文件
- 用户需要自行从 Wiki 网站获取或使用爬虫工具下载
- 下载的 Wiki 文件应放置在 `wiki_pages/` 目录中
- 本工具仅提供索引和搜索功能，不存储原始 Wiki 内容
- 使用 Wiki 内容时请遵守 Bohemia Interactive 的版权和使用条款

## 功能特性

- ✅ 解析 MediaWiki HTML 页面
- ✅ 提取页面标题、描述、章节内容
- ✅ 构建全文搜索索引
- ✅ 支持在 MCP 工具中搜索 Wiki 内容
- ✅ 保留 Wiki 页面的 URL 和分类信息

## 使用方法

### 1. 构建 Wiki 索引

#### 方法 1：只构建 Wiki 索引

```bash
python -m src.parser.build_index --wiki-only
```

#### 方法 2：在构建 API 索引时同时构建 Wiki 索引

```bash
python -m src.parser.build_index --api-source arma_reforger --include-wiki
```

#### 方法 3：只构建 Wiki 搜索索引（如果 JSON 数据已存在）

```bash
python -m src.parser.build_index --wiki-only --skip-parse
```

### 2. 在 MCP 工具中使用

#### 搜索 Wiki 页面

在 Cursor 中，你可以这样查询：

- **"搜索 Wiki 中关于脚本的内容"**
- **"查找 Wiki 中关于动画编辑器的页面"**
- **"Wiki 中有哪些关于游戏主控的文档？"**

#### 使用 search_api 工具

`search_api` 工具现在支持以下新参数：

- `type`: 可以设置为 `"wiki"` 来只搜索 Wiki 页面
- `api_source`: 可以设置为 `"arma_reforger_wiki"` 来只搜索 Wiki，或 `"all"` 来搜索所有来源（API + Wiki）

**示例查询**：

```json
{
  "query": "脚本最佳实践",
  "type": "wiki",
  "api_source": "arma_reforger_wiki",
  "limit": 10
}
```

或者搜索所有来源：

```json
{
  "query": "武器组件",
  "type": "all",
  "api_source": "all",
  "limit": 20
}
```

## 数据结构

### Wiki 页面数据结构

每个 Wiki 页面包含以下信息：

```json
{
  "title": "页面标题",
  "api_source": "arma_reforger_wiki",
  "type": "wiki",
  "description": "页面描述（第一段）",
  "full_text": "完整页面文本",
  "sections": [
    {
      "id": "section_id",
      "title": "章节标题",
      "level": 2,
      "content": "章节内容"
    }
  ],
  "categories": ["分类1", "分类2"],
  "url": "https://community.bistudio.com/wiki/...",
  "saved_at": "2026-01-15 14:42:22",
  "file_name": "Arma_Reforger_Getting_Started.html"
}
```

### 搜索结果格式

Wiki 搜索结果包含以下字段：

```json
{
  "name": "页面标题",
  "full_name": "页面标题",
  "type": "wiki",
  "api_source": "arma_reforger_wiki",
  "description": "页面描述",
  "url": "Wiki 页面 URL",
  "categories": "分类1 分类2",
  "relevance_score": 0.95
}
```

## 文件结构

### 新增文件

- `src/parser/wiki_parser.py` - Wiki 页面解析器
- `data/arma_reforger_wiki.json` - Wiki 数据文件（构建后生成）
- `data/search_index/arma_reforger_wiki/` - Wiki 搜索索引目录（构建后生成）

### 修改的文件

- `src/parser/build_index.py` - 添加了 Wiki 索引构建功能
- `src/indexer/search_index.py` - 添加了 Wiki 内容索引支持
- `src/mcp_server/tools.py` - 更新了搜索工具以支持 Wiki
- `src/utils/helpers.py` - 添加了 `get_wiki_pages_path()` 函数

## 命令行参数

### build_index.py 新增参数

- `--include-wiki`: 在构建 API 索引时同时构建 Wiki 索引
- `--wiki-only`: 只构建 Wiki 索引，跳过 API 索引

**示例**：

```bash
# 只构建 Wiki 索引
python -m src.parser.build_index --wiki-only

# 构建 API 索引并包含 Wiki
python -m src.parser.build_index --api-source arma_reforger --include-wiki

# 只构建 Wiki 搜索索引（跳过解析）
python -m src.parser.build_index --wiki-only --skip-parse
```

## 注意事项

1. **版权和获取**：
   - Wiki 页面来自 Bohemia Interactive Community Wiki
   - 由于版权原因，本仓库不包含原始 Wiki 文件
   - 用户需要自行从 Wiki 网站获取或使用爬虫工具下载
   - 请遵守 Bohemia Interactive 的版权和使用条款

2. **Wiki 文件位置**：Wiki HTML 和 JSON 文件应位于项目根目录的 `wiki_pages/` 目录中

3. **文件命名**：Wiki 文件应成对出现：
   - `Arma_Reforger_*.html` - HTML 文件
   - `Arma_Reforger_*.json` - JSON 元数据文件（可选）

3. **索引构建时间**：根据 Wiki 页面数量，索引构建可能需要几分钟时间

4. **搜索性能**：Wiki 搜索使用与 API 搜索相同的 Whoosh 全文搜索引擎，性能优异

## 故障排除

### 问题：找不到 Wiki 文件

**解决方案**：
- 确保 `wiki_pages/` 目录存在于项目根目录
- 检查文件命名是否正确

### 问题：Wiki 搜索结果为空

**解决方案**：
- 确保已运行索引构建命令
- 检查 `data/arma_reforger_wiki.json` 文件是否存在
- 检查 `data/search_index/arma_reforger_wiki/` 目录是否存在

### 问题：解析错误

**解决方案**：
- 检查 HTML 文件格式是否正确
- 查看控制台输出的错误信息
- 确保文件编码为 UTF-8

## 更新索引

当 Wiki 页面更新时，需要重新构建索引：

```bash
# 重新构建所有 Wiki 索引
python -m src.parser.build_index --wiki-only

# 只重新构建搜索索引（如果 JSON 数据已存在）
python -m src.parser.build_index --wiki-only --skip-parse
```

## 未来改进

- [ ] 支持 Wiki 页面的代码示例提取
- [ ] 支持 Wiki 页面之间的关系索引
- [ ] 支持 Wiki 页面的版本历史
- [ ] 支持多语言 Wiki 页面

---

**最后更新**: 2024年