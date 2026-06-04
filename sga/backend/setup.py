"""
setup.py – allows the backend app to be installed as an editable package.
This lets pytest and other tools import 'app.*' without path manipulation.
"""
from setuptools import setup, find_packages

setup(
    name="sga-backend",
    version="1.0.0",
    packages=find_packages(),
)
