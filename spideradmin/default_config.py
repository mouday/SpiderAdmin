# -*- coding: utf-8 -*-

# 配置示例

# 批量配置scrapyd 服务器地址
SCRAPYD_SERVERS = [
    # 别名（唯一）， 服务器地址
    ("master", "http://127.0.0.1:6800/"),
]

SECRET_KEY = "2QDq4HSpT8U4W6iZ2xDzGW3CcY2WVsJXVEwYv0qludY="

# 配置端口号
HOST = None
PORT = None

# 登录账号密码
BASIC_AUTH_USERNAME = "admin"
BASIC_AUTH_PASSWORD = "123456"

# 如果为 True 整个站点都验证， 默认不验证
BASIC_AUTH_FORCE = False

# 执行结果数据库配置
ITEM_LOG_DATABASE_URL = None
ITEM_LOG_TABLE = None
