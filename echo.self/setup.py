#!/usr/bin/env python3
"""
Setup script for NanoCog
"""

from setuptools import setup, find_packages

# Read requirements from requirements.txt
with open("requirements.txt") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="nanocog",
    version="0.1.0",
    description="NanoCog - A CogPrime-trained nanoGPT model with Echo Self representation",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="NanoCog Team",
    packages=find_packages(),
    install_requires=requirements,
    python_requires=">=3.10",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)