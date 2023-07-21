#!/usr/bin/python3
# -*- coding:utf-8 -*-

from setuptools import setup

from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()


setup(
    name='pythoncoin',
    version='v1.0.02',
    packages=['pycoin', 'pycoin/market_data_gathering', 'pycoin/market_data_kline_plots'],
    license="MIT",
    author='Hadi Fathipour',
    author_email="hadi9628983@gmail.com",
    url='https://github.com/hadif1999/pycoin',
    description="a packege to make some algorithmic trading analyses easy.",
    install_requires=['plotly', 'pandas', 'numpy', 'kucoin-python'],
    long_description=long_description,
    long_description_content_type='text/markdown',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
