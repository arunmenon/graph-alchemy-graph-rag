from setuptools import setup, find_packages

setup(
    name="graph_rag",
    version="0.2.0",
    description="Graph Retrieval-Augmented Generation System",
    author="Arun Menon",
    packages=find_packages(),
    install_requires=[
        "openai>=1.0.0",
        "neo4j>=5.0.0",
        "fastapi>=0.100.0",
        "uvicorn>=0.23.0",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0",
        "requests>=2.28.0",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)