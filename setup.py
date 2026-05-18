"""Westlake Singularity — setup
Developer: Westlake Singularity Contributors
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="westlake-singularity",
    version="0.2.0",
    author="Jiaxiang Cong",
    author_email="singularity@westlake.edu.cn",
    description="AI-Native Quantum Laboratory Operating System — 西湖大学AI量子实验室",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/jiaxiang-cong/westlake-singularity",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Physics",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.11",
    install_requires=[
        "asyncio",
        "websockets>=12.0",
        "numpy>=1.26",
    ],
    extras_require={
        "full": [
            "vllm>=0.6.0",
            "torch>=2.4.0",
            "faiss-cpu>=1.8.0",
            "opencv-python>=4.9.0",
            "scipy>=1.12.0",
        ],
        "vision": ["opencv-python>=4.9.0", "pillow>=10.0"],
        "dft": ["ase>=3.22", "pymatgen>=2024.0"],
    },
    entry_points={
        "console_scripts": [
            "singularity=core.main:main",
            "wls=core.main:main",
        ],
    },
)
