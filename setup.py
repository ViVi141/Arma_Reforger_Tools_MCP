"""安装脚本"""

from setuptools import setup, find_packages
from pathlib import Path

# 读取 README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# 读取 requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    requirements = [
        line.strip()
        for line in requirements_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]

setup(
    name="arma-reforger-api-mcp",
    version="0.1.0",
    description="MCP server for Arma Reforger API documentation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="ViVi141",
    author_email="747384120@qq.com",
    url="https://github.com/ViVi141/Arma_Reforger_Tools_MCP",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "arma-reforger-mcp=src.mcp_server.server:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
