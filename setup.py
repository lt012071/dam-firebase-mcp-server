"""Setup script for Firebase MCP Server."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="mcp-server-firebase",
    version="0.1.0",
    author="Firebase MCP Server",
    description="MCP Server for Firebase Firestore and Storage access",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/mcp-server-firebase",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "firebase-mcp-server=main:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)