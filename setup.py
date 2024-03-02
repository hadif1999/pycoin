#!/usr/bin/python3
# -*- coding:utf-8 -*-

from setuptools import setup, find_packages

from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()
short_description = "a lovable data analysis and algorithmic trading library for cryptocurrencies,including tools for deploying and analyzing any strategy"

plot = ['plotly>=4.0']

ai = ["tensorflow",
      'catboost; platform_machine != "aarch64"',
      'xgboost',
      'tensorboard']

develop = [
    'coveralls',
    'mypy',
    'ruff',
    'pre-commit',
    'pytest',
    'pytest-asyncio',
    'pytest-cov',
    'pytest-mock',
    'pytest-random-order',
    'isort',
    'time-machine',
    'types-cachetools',
    'types-filelock',
    'types-requests',
    'types-tabulate',
    'types-python-dateutil'
]

jupyter = [
    'jupyter',
    'nbstripout',
    'ipykernel',
    'nbconvert',
]

test = [
        'pytest',
        'pytest-asyncio',
        'pytest-cov',
        'pytest-mock',
        ]

hdf5 = [
    'tables',
    'blosc',
]


all_extra = plot + develop + jupyter + ai

base_requirements = [
    "celery>=5.3.6",
    "requests",
    "typeguard",
    "asyncer",
    "pandas",
    "numpy",
    "scipy",
    "ta",
    "ccxt",
    "freqtrade",
    "python-telegram-bot",
    "fastapi",
    "wheel",
    "setuptools >= 64.0.0"
    ]
    

setup(
    name='pythoncoin',
    version='v2.0.3',
    packages=find_packages(),
    license="MIT",
    author='Hadi Fathipour',
    author_email="hadi9628983@gmail.com",
    url='https://github.com/hadif1999/pycoin',
    description=short_description,
    long_description=long_description,
    long_description_content_type='text/markdown',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    tests_require=test, 
    install_requires=base_requirements,
    extras_require={
        "plot":plot,
        "ai":ai,
        "jupyter":jupyter,
        "hdf5":hdf5,
        "all":all_extra},
    python_requires='>=3.10',
    
)
