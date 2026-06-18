#!/usr/bin/env python3
"""Setup script for linux-tweaker."""

from setuptools import setup, find_packages
from pathlib import Path

README = Path(__file__).parent / "README.md"
long_description = README.read_text() if README.exists() else ""

setup(
    name="linux-tweaker",
    version="2.0.0",
    description="Robust Linux desktop configuration tool with zero-crash policy",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Peter",
    url="https://github.com/xxxxpeterxxxxxx-cloud/linux-tweaker",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    py_modules=["app"],
    scripts=["app.py"],
    entry_points={
        "console_scripts": [
            "linux-tweaker=app:main",
            "tweak=app:main",
        ],
    },
    install_requires=[
        "rich>=13.7.0",
    ],
    extras_require={
        "dev": ["pytest>=7.4.0", "black", "flake8"],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Desktop Environment",
        "Topic :: System :: Shells",
        "Topic :: Utilities",
    ],
    keywords="ricing theming linux hyprland configuration backup security",
    project_urls={
        "Bug Reports": "https://github.com/xxxxpeterxxxxxx-cloud/linux-tweaker/issues",
        "Source": "https://github.com/xxxxpeterxxxxxx-cloud/linux-tweaker",
        "Documentation": "https://github.com/xxxxpeterxxxxxx-cloud/linux-tweaker/blob/main/ARCHITECTURE.md",
    },
    include_package_data=True,
    package_data={
        "": ["*.json", "*.yaml", "*.yml", "*.rasi", "*.css", "*.conf"],
    },
)
