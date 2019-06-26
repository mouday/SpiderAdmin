# -*- coding: utf-8 -*-

# @Date    : 2019-05-26
# @Author  : Peng Shiyu

from setuptools import setup, find_packages

"""
安装测试
python setup.py install 

卸载
pip uninstall spideradmin -y


打包
python setup.py sdist bdist_wheel

上传pypi
twine upload dist/*

打包的用的setup必须引入，
"""

VERSION = '0.0.4'

setup(
    name='spideradmin',
    version=VERSION,
    description="spider admin",
    long_description='a spider admin based scrapyd api and APScheduler',
    classifiers=[],  # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='spideradmin',
    author='Peng Shiyu',
    author_email='pengshiyuyx@gmail.com',
    license='MIT',
    url="https://github.com/mouday/SpiderAdmin",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=True,
    install_requires=[
        "requests>=2.22.0",
        "Flask>=1.0.3",
        "APScheduler>=3.6.0",
        "tinydb>=3.13.0"
    ],
    entry_points={
        'console_scripts': [
            'spideradmin = spideradmin.run:main'
        ]
    }
)
