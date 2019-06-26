# -*- coding: utf-8 -*-

# @Date    : 2019-06-26
# @Author  : Peng Shiyu


import os

import requests
from setuptools import setup, find_packages
import io

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

VERSION = '0.0.5'


# 将markdown格式转换为rst格式
def md_to_rst(from_file, to_file):
    r = requests.post(
        url='http://c.docverter.com/convert',
        data={'to': 'rst', 'from': 'markdown'},
        files={'input_files[]': open(from_file, 'rb')}
    )
    if not r.ok:
        return

    with open(to_file, "wb") as f:
        f.write(r.content)


if os.path.exists("README.md"):
    md_to_rst("README.md", "README.rst")

long_description = 'a spider admin based scrapyd api and APScheduler'
if os.path.exists('README.rst'):
    long_description = io.open('README.rst', encoding="utf-8").read()

setup(
    name='spideradmin',
    version=VERSION,
    description="a spider admin based scrapyd api and APScheduler",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    classifiers=[],  # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords='spider admin',
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
        "tinydb>=3.13.0",
        "Flask-BasicAuth>=0.2.0"
    ],
    entry_points={
        'console_scripts': [
            'spideradmin = spideradmin.run:main'
        ]
    }
)
