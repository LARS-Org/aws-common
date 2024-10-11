from setuptools import find_packages, setup

# Read version from the VERSION file
with open("VERSION", "r") as version_file:
    version = version_file.read().strip()

setup(
    name="aws-common",
    version="0.1",
    packages=find_packages(),
    install_requires=[],  # Pipenv manages dependencies
    author="LARS AI",
    author_email="lars-ai@lars-ai.com",
    description="A shared package for common modules and constants for AWS Lambda applications",  # noqa:E501
    url="https://github.com/LARS-Org/aws-common.git",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.11",
)
