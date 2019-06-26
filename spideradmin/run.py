# -*- coding: utf-8 -*-

# @Date    : 2018-11-28
# @Author  : Peng Shiyu


import os
import sys

from flask import Flask

from spideradmin.api_app.controller import api_app

from spideradmin.html_app.controller import html_app
from spideradmin.scheduler_app.controller import scheduler_app

# 把当前目录加入执行路径，不然找不到用户自定义config.py文件
sys.path.insert(0, os.getcwd())

try:
    from config import host, port
except Exception as e:
    print(e)
    from spideradmin.default_config import host, port


app = Flask(__name__)

app.register_blueprint(blueprint=html_app, url_prefix="/")
app.register_blueprint(blueprint=api_app, url_prefix="/api")
app.register_blueprint(blueprint=scheduler_app, url_prefix="/scheduler")


def main():
    # 初始化解析器
    if len(sys.argv) == 2:
        init = sys.argv[1]

        if init == "init":
            import shutil
            import os
            base_dir = os.path.dirname(os.path.abspath(__file__))
            default_config = os.path.join(base_dir, "default_config.py")
            shutil.copy(default_config, "./config.py")
            print("spideradmin init successful!")
        else:
            print("you may need: spideradmin init ?")
    else:
        app.run(host, port)


if __name__ == '__main__':
    # app.run(debug=True)
    app.run(host, port)