#!/usr/bin/env python
"""动态生成 Cursor MCP 配置的脚本"""

import json
import os
import sys
from pathlib import Path


def detect_python_executable():
    """检测 Python 可执行文件"""
    current_exe = Path(sys.executable)

    # 方法1: 检查是否在虚拟环境中 (更准确的检查)
    if hasattr(sys, "base_prefix"):
        in_venv = sys.prefix != sys.base_prefix
    elif hasattr(sys, "real_prefix"):
        in_venv = True
    else:
        in_venv = False

    if in_venv:
        return str(current_exe)

    # 方法2: 检查 VIRTUAL_ENV 环境变量
    if "VIRTUAL_ENV" in os.environ:
        venv_path = Path(os.environ["VIRTUAL_ENV"])
        if sys.platform == "win32":
            python_exe = venv_path / "Scripts" / "python.exe"
        else:
            python_exe = venv_path / "bin" / "python"
        if python_exe.exists():
            return str(python_exe)

    # 方法3: 检查 CONDA_DEFAULT_ENV 环境变量
    if "CONDA_DEFAULT_ENV" in os.environ:
        try:
            import subprocess
            result = subprocess.run(
                [
                    "conda", "run", "-n",
                    os.environ["CONDA_DEFAULT_ENV"],
                    "python", "-c", "import sys; print(sys.executable)"
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass

    # 方法4: 检查常见的虚拟环境目录
    project_root = Path.cwd()
    possible_venv_dirs = [".venv", "venv", "env", ".env"]
    for venv_dir in possible_venv_dirs:
        if sys.platform == "win32":
            python_exe = project_root / venv_dir / "Scripts" / "python.exe"
        else:
            python_exe = project_root / venv_dir / "bin" / "python"
        if python_exe.exists():
            return str(python_exe)

    # 方法5: 路径包含虚拟环境指示器
    exe_str = str(current_exe)
    venv_indicators = ["venv", "virtualenv", "conda", "miniconda", "anaconda"]
    if any(indicator in exe_str.lower() for indicator in venv_indicators):
        return str(current_exe)

    return str(current_exe)


def generate_config():
    """生成 MCP 配置"""
    project_path = Path.cwd()
    python_cmd = detect_python_executable()
    data_path = project_path / "data"
    config = {
        "mcpServers": {
            "arma-reforger-api": {
                "command": python_cmd,
                "args": ["-m", "src.mcp_server.server"],
                "cwd": str(project_path),
                "env": {
                    "API_DATA_PATH": str(data_path),
                    "LOG_LEVEL": "INFO",
                    "PYTHONPATH": str(project_path),
                },
            }
        }
    }
    return config


def main():
    """主函数"""
    print("生成 Cursor MCP 配置")
    print("=" * 50)

    project_path = Path.cwd()
    has_setup = (project_path / "setup.py").exists()
    has_pyproject = (project_path / "pyproject.toml").exists()
    src_dir = project_path / "src"

    if (not has_setup and not has_pyproject) or not src_dir.exists():
        print("错误: 请在项目根目录运行此脚本")
        print(f"   当前目录: {project_path}")
        sys.exit(1)

    print(f"项目路径: {project_path}")

    config = generate_config()
    python_cmd = config["mcpServers"]["arma-reforger-api"]["command"]
    data_path = config["mcpServers"]["arma-reforger-api"]["env"]["API_DATA_PATH"]

    print(f"Python 命令: {python_cmd}")
    print(f"数据路径: {data_path}")

    if not Path(data_path).exists():
        print("警告: 数据目录不存在，请先运行构建索引")
        print("   运行: python -m src.parser.build_index")

    print("\n复制以下配置到 Cursor 的 MCP 配置文件:")
    print("   路径: %APPDATA%\\Cursor\\User\\globalStorage\\saoudrizwan.claude-dev\\settings\\cline_mcp_settings.json")
    print("\n" + "=" * 50)
    print(json.dumps(config, indent=2, ensure_ascii=False))
    print("\n" + "=" * 50)
    print("配置生成完成")
    print("\n使用说明:")
    print("   1. 复制上面的 JSON 配置")
    print("   2. 打开 Cursor 的配置文件")
    print("   3. 在 mcpServers 对象中添加配置")
    print("   4. 重启 Cursor")


if __name__ == "__main__":
    main()
