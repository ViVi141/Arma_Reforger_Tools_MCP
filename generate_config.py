#!/usr/bin/env python
"""动态生成 Cursor MCP 配置的脚本"""

import json
import sys
import os
from pathlib import Path


def detect_python_executable():
    """检测 Python 可执行文件"""
    current_exe = Path(sys.executable)

    # 方法1: 检查是否在虚拟环境中 (更准确的检查)
    # 比较 sys.prefix 和 sys.base_prefix
    in_venv = False
    if hasattr(sys, 'base_prefix'):
        in_venv = sys.prefix != sys.base_prefix
    elif hasattr(sys, 'real_prefix'):  # 旧版 virtualenv
        in_venv = True

    if in_venv:
        # 在虚拟环境中，直接使用当前解释器
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
            # 使用 conda run 获取正确的 python 路径
            result = subprocess.run(["conda", "run", "-n", os.environ["CONDA_DEFAULT_ENV"], "python", "-c", "import sys; print(sys.executable)"],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
        except:
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

    # 方法5: 如果当前解释器看起来像是在虚拟环境中，使用它
    # 检查路径是否包含虚拟环境指示器
    exe_str = str(current_exe)
    venv_indicators = ["venv", "virtualenv", "conda", "miniconda", "anaconda"]
    if any(indicator in exe_str.lower() for indicator in venv_indicators):
        return str(current_exe)

    # 默认返回当前解释器
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
                    "PYTHONPATH": str(project_path)
                }
            }
        }
    }

    return config


def main():
    """主函数"""
    print("生成 Cursor MCP 配置")
    print("=" * 50)

    # 检测项目结构
    project_path = Path.cwd()
    setup_py = project_path / "setup.py"
    src_dir = project_path / "src"

    if not setup_py.exists() or not src_dir.exists():
        print("错误: 请在项目根目录运行此脚本")
        print(f"   当前目录: {project_path}")
        sys.exit(1)

    print(f"项目路径: {project_path}")

    # 生成配置
    config = generate_config()
    python_cmd = config["mcpServers"]["arma-reforger-api"]["command"]
    data_path = config["mcpServers"]["arma-reforger-api"]["env"]["API_DATA_PATH"]

    print(f"Python 命令: {python_cmd}")
    print(f"数据路径: {data_path}")

    # 检查数据目录
    data_path_obj = Path(data_path)
    if not data_path_obj.exists():
        print("警告: 数据目录不存在，请先运行构建索引")
        print("   运行: python -m src.parser.build_index")

    print("\n复制以下配置到 Cursor 的 MCP 配置文件:")
    print("   路径: %APPDATA%\\Cursor\\User\\globalStorage\\saoudrizwan.claude-dev\\settings\\cline_mcp_settings.json")
    print("\n" + "=" * 50)

    # 输出 JSON 配置
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