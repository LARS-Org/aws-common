from setuptools import setup, find_packages

def parse_requirements(filename: str):
    """
    Utility function to read the requirements.txt file
    @param filename the requirements file name
    """
    with open(filename, 'r') as file:
        return file.read().splitlines()

setup(
    name='aws-common',
    version='0.1',
    packages=find_packages(),
    install_requires=parse_requirements('requirements.txt'),  # Include dependencies
    author='LARS AI',
    author_email='lars-ai@lars-ai.com',
    description='A shared package for common modules and constants for AWS Lambda applications',
    url='https://github.com/LARS-Org/aws-common.git',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
     ],
     python_requires='>=3.11',
 )
