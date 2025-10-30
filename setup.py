from setuptools import setup, find_packages

setup(
    name="minilang",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "llvmlite",
    ],
    entry_points={
        "console_scripts": [
            "minilang = cli:main",
        ],
    },
    python_requires=">=3.8",
)
