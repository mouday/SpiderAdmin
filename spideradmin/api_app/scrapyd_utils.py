# -*- coding: utf-8 -*-

# @Date    : 2018-11-28
# @Author  : Peng Shiyu

from datetime import datetime, timedelta
from urllib.parse import urljoin

from collections import defaultdict
from dateutil import parser
import requests


from spideradmin.api_app.scrapyd_api import ScrapydAPI


def format_time(date_time):
    """
    格式化时间
    :param date_time: str 各种时间格式
    :return: str eg:2019-03-03 20:09:43
    """
    try:
        dt = parser.parse(date_time)
        time_str = dt.strftime("%Y-%m-%d %H:%M:%S")
    except (TypeError, ValueError):
        time_str = date_time

    return time_str


def parse_time(date_time):
    try:
        dt = parser.parse(date_time)
    except TypeError:
        dt = date_time

    return dt


def format_delta(delta_time):
    if not isinstance(delta_time, timedelta):
        return ""

    delta_time = delta_time.seconds

    hour, second = divmod(delta_time, 60 * 60)
    minute, second = divmod(second, 60)

    if hour > 0:
        delta = "{}h:{}m:{}s".format(hour, minute, second)
    elif minute > 0:
        delta = "{}m:{}s".format(minute, second)
    else:
        delta = "{}s".format(second)

    return delta


def get_timestamp(end_time, start_time):
    """
    获取时间间隔的字符串格式
    """
    start_time = parse_time(start_time)
    end_time = parse_time(end_time)

    is_start_time = isinstance(start_time, datetime)
    is_end_time = isinstance(end_time, datetime)

    if all([is_start_time, is_end_time]):
        delta_time = end_time - start_time

    elif is_start_time:
        delta_time = datetime.now() - start_time
    else:
        delta_time = ""

    return format_delta(delta_time)


def get_log_url(server, project, spider, job_id):
    """
    获取日志url
    :param server: str 服务器地址
    :param project: str 项目名称
    :param spider: str 爬虫名称
    :param job_id: str 任务id
    :return: str url
    """
    # http://localserver:6801/logs/scrapy_demo/baidu/aabc0f10fb8e11e8b925f45c89bc23a1.log
    params = "logs/{}/{}/{}.log".format(project, spider, job_id)
    return urljoin(server, params)


def get_log(url):
    """
    获取日志内容
    :param url: str
    :return:
    """
    try:
        response = requests.get(url)
        response.encoding = response.apparent_encoding
        text = response.text
    except Exception as e:
        text = "<h2>{}</h2>".format(e)
    return "<pre>{}</pre>".format(text)


def format_version(version):
    try:
        date_time = datetime.fromtimestamp(int(version))
        version = date_time.strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        pass
    return version


def get_server_status(server_list):
    """
    获取服务器状态  版本不一致
    scrapyd=1.2.0
    服务器使用 scrapyd=1.1.0 没有接口 daemon_status

    :param server_list:
    :return:
    """
    servers = []
    count = 0

    for item in server_list:

        server_name = item["server_name"]
        server_host = item["server_host"]

        count += 1
        scrapyd = ScrapydAPI(server_host)
        server_status = scrapyd.daemon_status()

        # 兼容老版本
        if server_status.get("status") == "error":

            projects = scrapyd.list_projects()
            print("{}: {}".format(server_host, projects))

            if len(projects) == 0:
                status = "error"
            else:
                status = "ok"

            server_status = {
                "status": status,
            }

            status = defaultdict(int)
            for project in set(projects):
                jobs = scrapyd.list_jobs(project)

                for key, value in jobs.items():
                    status[key] += len(value)

            server_status.update(status)

        item = {
            "index": count,
            "server_name": server_name,
            "server_host": server_host,
            "server_status": server_status,
        }
        servers.append(item)
    return servers


def cancel_all_spider(server):
    """
    取消服务器上所有的爬虫任务
    :param server:
    :return:
    """
    scrapyd = ScrapydAPI(server)
    projects = scrapyd.list_projects()
    for project in projects:
        jobs = scrapyd.list_jobs(project)
        for job, value in jobs.items():
            print(job, value)
            for status in value:
                uid = status.get("id")
                print("{}: {}".format(project, uid))

                scrapyd.cancel(project, uid)
