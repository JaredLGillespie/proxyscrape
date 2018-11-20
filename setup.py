from setuptools import setup
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst')) as f:
    long_description = f.read()

setup(
    name='proxyscrape',
    version='0.1.0',
    description='A library for retrieving free proxies (HTTP, HTTPS, SOCKS4, SOCKS5).',
    long_description=long_description,
    url='https://github.com/jaredlgillespie/proxyscrape',
    author='Jared Gillespie',
    author_email='jaredlgillespie@hotmail.com',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities'
    ],
    keywords='proxyscrape proxy scrape scraper',
    packages=['proxyscrape'],
    test_suite='tests',
    install_requires=[
        'BeautifulSoup4',
        'requests',
    ]
)
