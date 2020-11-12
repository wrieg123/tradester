from setuptools import setup, find_packages

setup (
    name= 'tradester',
    version= '0.9',
    author = 'Will Rieger',
    description= 'Python based futures and securities backtesting engine',
    packages = find_packages(),
    install_requires = ['numpy', 'pandas', 'matplotlib', 'sqlalchemy', 'mysql-connector', 'numba', 'tqdm', 'mysqlclient'],
)
