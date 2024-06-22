from setuptools import setup, find_packages

def parse_requirements(filename: str):
    """
    Utility function to read the requirements.txt file  
    @param filename the requirements file name
    """
    with open(filename, 'r') as file:
        return file.read().splitlines()

setup(
    name='la-common',
    version='0.1',
    packages=find_packages(),
    install_requires=parse_requirements('requirements.txt'),  # Include dependencies
    author='Anderson Gomes',
    author_email='andersonmg@gmail.com',
    description='A shared package for common modules and constants',
    url='https://github.com/LearnAnything-Organization/la-common',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
     ],
     python_requires='>=3.11',
 )
