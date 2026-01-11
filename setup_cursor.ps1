# Cursor MCP 服务器配置脚本
# 自动生成 Cursor 的 MCP 配置文件

$ErrorActionPreference = "Stop"

Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "Cursor MCP 服务器配置脚本" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

# 获取项目路径
$projectPath = (Get-Location).Path
Write-Host "项目路径: $projectPath" -ForegroundColor Green

# 检查虚拟环境
$venvPython = Join-Path $projectPath ".venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    Write-Host "使用虚拟环境: $venvPython" -ForegroundColor Green
    $pythonCommand = $venvPython
} else {
    Write-Host "警告: 未找到虚拟环境，将使用系统 Python" -ForegroundColor Yellow
    $pythonCommand = "python"
}

# 检查数据目录
$dataPath = Join-Path $projectPath "data"
if (-not (Test-Path $dataPath)) {
    Write-Host "警告: 数据目录不存在: $dataPath" -ForegroundColor Yellow
    Write-Host "请先运行: python -m src.parser.build_index" -ForegroundColor Yellow
}

# 配置文件路径
$configDir = "$env:APPDATA\Cursor\User\globalStorage\saoudrizwan.claude-dev\settings"
$configPath = Join-Path $configDir "cline_mcp_settings.json"

Write-Host ""
Write-Host "配置文件路径: $configPath" -ForegroundColor Green

# 创建配置对象
$mcpConfig = [PSCustomObject]@{
    command = $pythonCommand
    args = @("-m", "src.mcp_server.server")
    cwd = $projectPath
    env = @{
        API_DATA_PATH = $dataPath
        LOG_LEVEL = "INFO"
        PYTHONPATH = $projectPath
    }
}

# 读取现有配置（如果存在）
$existingConfig = $null
if (Test-Path $configPath) {
    Write-Host "读取现有配置..." -ForegroundColor Yellow
    try {
        $existingConfig = Get-Content $configPath -Raw -Encoding UTF8 | ConvertFrom-Json
    } catch {
        Write-Host "警告: 无法读取现有配置，将创建新配置" -ForegroundColor Yellow
        $existingConfig = $null
    }
}

# 合并配置
if ($existingConfig -and $existingConfig.mcpServers) {
    $existingConfig.mcpServers | Add-Member -MemberType NoteProperty -Name "arma-reforger-api" -Value $mcpConfig -Force
    $finalConfig = $existingConfig
} else {
    $finalConfig = [PSCustomObject]@{
        mcpServers = [PSCustomObject]@{
            "arma-reforger-api" = $mcpConfig
        }
    }
}

# 确保目录存在
if (-not (Test-Path $configDir)) {
    Write-Host "创建配置目录..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $configDir -Force | Out-Null
}

# 保存配置
Write-Host ""
Write-Host "保存配置..." -ForegroundColor Yellow
$finalConfig | ConvertTo-Json -Depth 10 | Set-Content $configPath -Encoding UTF8

Write-Host ""
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "配置完成！" -ForegroundColor Green
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "配置详情:" -ForegroundColor Cyan
Write-Host "  服务器名称: arma-reforger-api" -ForegroundColor White
Write-Host "  Python 路径: $pythonCommand" -ForegroundColor White
Write-Host "  工作目录: $projectPath" -ForegroundColor White
Write-Host "  数据路径: $dataPath" -ForegroundColor White
Write-Host ""
Write-Host "下一步:" -ForegroundColor Yellow
Write-Host "  1. 完全关闭 Cursor" -ForegroundColor White
Write-Host "  2. 重新打开 Cursor" -ForegroundColor White
Write-Host "  3. 在聊天中测试 API 查询" -ForegroundColor White
Write-Host ""
Write-Host "测试命令示例:" -ForegroundColor Cyan
Write-Host "  - 如何搜索 BaseWeaponComponent API？" -ForegroundColor White
Write-Host "  - 查找与武器相关的类" -ForegroundColor White
Write-Host "  - 获取 CharacterControllerComponent 的详细信息" -ForegroundColor White
Write-Host ""
