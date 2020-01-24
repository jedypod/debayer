import os

from codecs import open
from setuptools import setup

name = 'debayer'
dirname = os.path.dirname(os.path.abspath(__file__))

# Get the long description from the README file
with open(os.path.join(dirname, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name=name,
    version='0.1.0',
    description=r'Command line tool to process camera raw image formats into scene-linear exr and other formats.',
    long_description=long_description,
    url='https://github.com/jedypod/{}.git'.format(name),
    download_url='https://github.com/jedypod/{}/archive/master.zip'.format(name),
    license='Proprietary',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Operating System :: OS Independent',
        'License :: Other/Proprietary License',
        'Private :: Do Not Upload',
    ],
    packages=[name],
    keywords=name,
    include_package_data=True,
    author='Jedediah Smith',
    install_requires=[
        'pyseq==0.5.1',
    ],
    entry_points={
        'console_scripts': [
            'debayer = debayer:Debayer',
        ],
    }
)
