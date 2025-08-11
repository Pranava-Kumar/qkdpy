import os

from setuptools import find_packages, setup

# Read README file
with open("README.md", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements file (optional to avoid errors if missing)
requirements = []
requirements_path = "requirements.txt"
if os.path.exists(requirements_path):
    with open(requirements_path, encoding="utf-8") as fh:
        requirements = [
            line.strip() for line in fh if line.strip() and not line.startswith("#")
        ]

setup(
    name="qkdpy",
    version="0.1.3",
    author="Pranava-Kumar",
    author_email="pranavakumar.it@gmail.com",
    description="A Python Package for Quantum Key Distribution",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Pranava-Kumar/qkdpy",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering :: Physics",
        "Topic :: Security :: Cryptography",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
            "pre-commit>=3.0.0",
            "sphinx>=6.0.0",
            "sphinx-rtd-theme>=1.2.0",
            "twine>=4.0.0",
            "build>=0.10.0",
        ],
        "docs": [
            "sphinx>=6.0.0",
            "sphinx-rtd-theme>=1.2.0",
            "myst-parser>=1.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "qkdpy=qkdpy.cli:main",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)
