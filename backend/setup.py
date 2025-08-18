from setuptools import find_packages, setup

setup(
    name="ai-character-backend",
    version="0.1.0",
    description="FastAPI backend for AI Character Conversation Platform",
    packages=find_packages(include=["backend", "backend.*"]),
    install_requires=[],  # rely on pyproject or external requirements
    python_requires=">=3.10",
)
