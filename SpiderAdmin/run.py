# -*- coding: utf-8 -*-

# @Date    : 2018-11-28
# @Author  : Peng Shiyu


from flask import Flask

from api_app.controller import api_app
try:
    from config import host, port
except:
    from defualt_config import host, port

from html_app.controller import html_app
from scheduler_app.controller import scheduler_app
import argparse

app = Flask(__name__)

app.register_blueprint(blueprint=html_app, url_prefix="/")
app.register_blueprint(blueprint=api_app, url_prefix="/api")
app.register_blueprint(blueprint=scheduler_app, url_prefix="/scheduler")


def main():
    # 初始化解析器
    parser = argparse.ArgumentParser()

    # 定义参数
    parser.add_argument("-a", "--a", help="参数a")

    # 解析
    args = parser.parse_args()
    if args.a == "init":
        import shutil
        import os
        base_dir = os.path.basename(os.path.abspath(__file__))
        defualt_config = os.path.join(base_dir, "defualt_config.py")
        shutil.copy(defualt_config, "./config.py")
    else:
        app.run(host, port)


if __name__ == '__main__':
    app.run(debug=True)
