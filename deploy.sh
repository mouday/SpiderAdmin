# 打包部署
rm -rf dist build *.egg-info \
&& python setup.py install \
&& python setup.py sdist bdist_wheel \
&& twine check dist/* \
&& twine upload dist/* \
&& rm -rf dist build *.egg-info

# 安装升级
pip uninstall ggtool -y \
&& pip install -U ggtool -i https://pypi.org/simple
