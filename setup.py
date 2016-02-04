from setuptools import setup, find_packages
from os import path
here = path.abspath(path.dirname(__file__))
# Get the long description from the relevant file
setup(
    name='connect4',
    version='0.0.3',
    description='connect 4',
    long_description='Simple implementation for the connect 4 (originally 4-in-a-row)'
                     ' classic logic using tkinter GUI',
    url='https://github.com/reutsharabani/N-in-a-row',
    # Author details
    author='Reut Sharabani',
    author_email='reut.sharabani@gmail.com',
    # Choose your license
    license='MIT',
    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: End Users/Desktop',
        'Topic :: Games/Entertainment :: Board Games',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7'
    ],
    # What does your project relate to?
    # keywords='Simple and fun board logic to play with younger members of family.',
    keywords = ['games', 'board games'],
    # You can just specify the packages manually here if your project is
    #  simple. Or you can use find_packages().
    packages=find_packages(exclude=['contrib', 'docs', 'tests*']),
    install_requires=['']
)
