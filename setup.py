from setuptools import setup, find_packages

setup(
    name="bolt-hub",
    version="0.1.0",
    author="Jacob Reedijk",
    author_email="jacobreedijk@gmail.com",
    description="A brief description of your project",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/your_username/your_project_repo",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "pandas",
        "matplotlib",
        "seaborn",
        "panel",
        "holoviews",
        "yfinance",
        "scipy",
        "financepy",
        "hvplot",

    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)