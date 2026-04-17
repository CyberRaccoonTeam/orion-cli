from setuptools import setup, find_packages

setup(
    name="orion-cli",
    version="0.1.0",
    description="Orion CLI — Clone local de Gemini CLI propulsé par Ollama",
    author="Project Orion",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.10",
    install_requires=[
        "ollama>=0.4.0",
        "langchain>=0.3.0",
        "langchain-ollama>=0.2.0",
        "langchain-openai>=0.2.0",
        "langchain-anthropic>=0.1.0",
        "langchain-community>=0.3.0",
        "rich>=13.7.0",
        "prompt_toolkit>=3.0.43",
        "typer>=0.12.0",
        "pyperclip>=1.9.0",
        "PyYAML>=6.0.2",
        "tomli>=2.0.0",
        "httpx>=0.27.0",
        "ddgs>=0.1.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "black>=24.0.0",
            "ruff>=0.4.0",
            "mypy>=1.10.0",
            "pytest-cov>=5.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "orion=orion.main:app",
        ],
    },
)
