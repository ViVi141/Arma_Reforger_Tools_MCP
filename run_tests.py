#!/usr/bin/env python
"""运行测试的便捷脚本"""

import sys
import subprocess


def main():
    """主函数"""
    # 默认运行所有测试
    args = sys.argv[1:] if len(sys.argv) > 1 else []
    
    # 构建 pytest 命令
    cmd = ["pytest"] + args
    
    print(f"运行命令: {' '.join(cmd)}")
    print("-" * 60)
    
    # 运行测试
    result = subprocess.run(cmd)
    
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
