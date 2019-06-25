# -*- coding: utf-8 -*-

# @Date    : 2019-05-26
# @Author  : Peng Shiyu

from setuptools import setup, find_packages

"""
安装测试
python setup.py install 

卸载
pip uninstall SpiderAdmin -y


打包
python setup.py sdist bdist_wheel

上传pypi
twine upload dist/*

打包的用的setup必须引入，
"""

VERSION = '0.0.1'

setup(
      name='SpiderAdmin',
      version=VERSION,
      description="a spider view and scheduler tool base scrapyd and apscheduler",
      long_description='a spider view and scheduler tool base scrapyd and apscheduler',
      keywords='SpiderAdmin',
      author='Peng Shiyu',
      author_email='pengshiyuyx@gmail.com',
      license='MIT',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
            "Flask>=1.0.3",
            "APScheduler>=3.6.0",
            "tinydb>=3.13.0"
      ],
      entry_points={
          'console_scripts': [
              'SpiderAdmin = SpiderAdmin.run:main'
          ]
      },
      classifiers=(
              "Programming Language :: Python :: 3",
              "License :: OSI Approved :: MIT License",
              "Operating System :: OS Independent",
          )
)
