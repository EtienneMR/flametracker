from setuptools import find_packages, setup

setup(
    name="flametracker",
    version="0.0.1",
    author="Etienne_MR",
    author_email="etienne@etiennemr.fr",
    description="A script tracking utility to generate flamegraph",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/EtienneMR/flametracker",
    package_data={"flametracker": ["py.typed"]},
    packages=find_packages(),  # Automatically finds packages
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)
