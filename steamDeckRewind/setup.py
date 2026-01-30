#!/usr/bin/env python3
"""Setup script for Deck Rewind."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README
readme_path = Path(__file__).parent / "README.md"
long_description = readme_path.read_text() if readme_path.exists() else ""

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_path.exists():
    with open(requirements_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                requirements.append(line)

setup(
    name="deck-rewind",
    version="1.0.0",
    author="Deck Rewind Team",
    author_email="",
    description="Save-state functionality for Steam Deck games",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/[USER]/deck-rewind",
    project_urls={
        "Bug Tracker": "https://github.com/[USER]/deck-rewind/issues",
        "Documentation": "https://github.com/[USER]/deck-rewind#readme",
    },
    packages=find_packages(exclude=["tests", "tests.*"]),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Games/Entertainment",
        "Topic :: System :: Recovery Tools",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "deck-rewind=deck_rewind.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "deck_rewind": ["py.typed"],
    },
    zip_safe=False,
)
