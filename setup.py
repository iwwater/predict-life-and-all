from setuptools import setup, find_packages
setup(
    name="divination",
    version="1.0.0",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "lunar-python>=1.4.8",
        "py-iztro>=0.1.5",
        "kinqimen",
        "bidict",
        "pendulum",
        "ephem>=4.2",
        "skyfield>=1.54",
        "skyfield-data>=7.0.0",
    ],
)
