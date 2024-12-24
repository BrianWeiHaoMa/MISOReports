from setuptools import setup, find_packages
from MISOReports import __version__

setup(
    name='MISOReports',
    version=__version__,    

    description='A comprehensive Python library for downloading Midcontinent Independent System Operator (MISO) public reports into pandas dataframes.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',

    author='Brian Wei Hao Ma, Ryan B. Green, William Sun',
    author_email='brianmaytc@gmail.com',
    license='MIT',
    url='https://github.com/BrianWeiHaoMa/MISOReports',
    
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License', 
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Information Technology',
        'Operating System :: OS Independent',  
        'Topic :: Software Development :: Libraries',      
        'Topic :: Utilities',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
    ],
    keywords=[
        'python',
        'data-science',
        'scraper',
        'download',
        'pandas',
        'reports',
        'electricity',
        'tables',
        'data-tables',
        'data-scraping',
        'miso',
        'energy-markets',
        'electricity-markets',
    ],

    python_requires='>=3.10',
    packages=find_packages(exclude=("tests", "helper_scripts",)),
    install_requires=[
        'pandas>=2.2.0, <3.0.0',
        'requests>=2.32.0, <3.0.0',
    ],
)