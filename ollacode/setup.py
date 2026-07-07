from setuptools import setup, find_packages

setup(
    name="ollacode",
    version="0.1.0",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "ollacode=ollacode.__main__:main",
        ],
    },
    install_requires=[
        "rich>=13.0.0",
        "httpx>=0.27.0",
    ],
    python_requires=">=3.10",
)
