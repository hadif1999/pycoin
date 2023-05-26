import setuptools

with open("README.md", "r", encoding = "utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name = "pycoin",
    version = "0.0.1",
    author = "hadi fathipour",
    author_email = "hadifathi13781378@gmail.com",
    description = "this python package includes tools specialized for financial markets.",
    long_description = "this python package includes tools specialized for financial markets, including visulizing, data gathering, and trend analysis,... tools. in future versions ML alghorithms will be added. it uses plotly for visulizing, kucoin api for gathering data, ta for calculating indicators.",
    long_description_content_type = "",
    url = "https://github.com/hadif1999/pykucoin",
    project_urls = {
        "Bug Tracker": "package issues URL",
    },
    classifiers = [
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires = ["plotly","kucoin-python","ta"],
    package_dir = {"": "src"},
    packages = setuptools.find_packages(where="src"),
    python_requires = ">=3.6"
)
