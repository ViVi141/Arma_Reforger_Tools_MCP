# 更新日志

本文件记录项目的所有重要更改。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [0.2.1] - 2026-02-16

### 新增
- `--fast` 选项：自动检测 CPU/线程并应用最优索引设置
- `--sequential` 选项：`api-source=both` 时顺序构建，避免 Windows 下卡死
- Windows 下解析使用 ProcessPoolExecutor，单文件超时 30 秒，避免卡死

### 改进
- 索引构建：Windows 下自动使用顺序构建（`--fast --api-source both`）
- 解析：使用 `as_completed` 替代 `map`，不按顺序等待结果
- 解析：Windows 下并行数限制为 8，避免资源竞争
- 属性解析：修复 `properties.type` 在类型含链接时解析为空的问题

### 修复
- 修复 Windows 下 `api-source=both` 并行构建时卡死问题
- 修复 Doxygen `memitem:hash` 格式导致方法/属性无法解析为空的问题

## [0.2.0] - 2025-01-21

### 新增
- 搜索功能支持单词自动通配符匹配，搜索 "Hint" 可以找到所有包含 Hint 的类
- 搜索索引 schema 中 `name` 字段改为 `TEXT` 类型，支持更灵活的搜索

### 改进
- 优化搜索逻辑，单词查询自动在 `full_name`、`class_name`、`content` 字段中使用通配符搜索
- 提升搜索准确度和召回率

### 修复
- 修复搜索单个关键词时结果不完整的问题（如搜索 "Hint" 只返回少量结果）

## [0.1.0] - 初始版本

### 新增
- MCP 服务器基础框架
- `search_api` - 搜索 API 和 Wiki 页面
- `get_class_info` - 获取类的详细信息
- `get_function_info` - 获取方法的详细信息
- `find_related_apis` - 查找相关 API
- `get_code_examples` - 获取代码示例
- HTML 文档解析器（支持 Arma Reforger 和 Enfusion API）
- Wiki 页面解析器
- 基于 Whoosh 的全文搜索索引
- API 关系索引（继承关系、使用关系）
- 完整的测试框架和文档
