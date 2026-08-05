"""Setup for qcli web version — pip install -e . from this directory."""

from setuptools import setup, find_packages

setup(
    name="qcli",
    version="0.2.0",
    description="qubi Agentic Flows CLI — validate, save, and deploy workflows",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "click>=8.0.0",
        "requests>=2.28.0",
    ],
    entry_points={
        "console_scripts": [
            "qcli=qcli.cli:main",
        ],
    },
)
