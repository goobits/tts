from setuptools import setup, find_packages

setup(
    name="tts-cli",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "click>=8.0.0",
    ],
    entry_points={
        "console_scripts": [
            "tts-cli=tts_cli.tts:cli",
        ],
    },
)