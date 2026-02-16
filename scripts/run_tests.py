#!/usr/bin/env python
"""运行测试的便捷脚本"""

import subprocess
import sys


def main():
    """主函数"""
    args = sys.argv[1:] if len(sys.argv) > 1 else []
    cmd = ["pytest"] + args
    print(f"运行命令: {' '.join(cmd)}")
    print("-" * 60)
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
