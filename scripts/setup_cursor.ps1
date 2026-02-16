# Cursor MCP 服务器配置脚本
# 自动生成 Cursor 的 MCP 配置文件
# 用法: 在项目根目录执行 .\scripts\setup_cursor.ps1

$ErrorActionPreference = "Stop"

# 获取项目根目录（脚本所在目录的父目录）
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectPath = Split-Path -Parent $scriptDir

Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "Cursor MCP 服务器配置脚本" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "项目路径: $projectPath" -ForegroundColor Green

$venvPython = Join-Path $projectPath ".venv\Scripts\python.exe"
if (Test-Path $venvPython) {
    Write-Host "使用虚拟环境: $venvPython" -ForegroundColor Green
    $pythonCommand = $venvPython
} else {
    Write-Host "警告: 未找到虚拟环境，将使用系统 Python" -ForegroundColor Yellow
    $pythonCommand = "python"
}

$dataPath = Join-Path $projectPath "data"
if (-not (Test-Path $dataPath)) {
    Write-Host "警告: 数据目录不存在: $dataPath" -ForegroundColor Yellow
    Write-Host "请先运行: python -m src.parser.build_index" -ForegroundColor Yellow
}

$configDir = "$env:APPDATA\Cursor\User\globalStorage\saoudrizwan.claude-dev\settings"
$configPath = Join-Path $configDir "cline_mcp_settings.json"
Write-Host ""
Write-Host "配置文件路径: $configPath" -ForegroundColor Green

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

if (-not (Test-Path $configDir)) {
    Write-Host "创建配置目录..." -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $configDir -Force | Out-Null
}

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
