# -*- coding: utf-8 -*-

# @Date    : 2019-06-25
# @Author  : Peng Shiyu
import sys

import os
from flask import Blueprint, jsonify, request

from spideradmin.api_app import scrapyd_utils

from spideradmin.api_app.scrapyd_api import ScrapydAPI
from spideradmin.api_app.scrapyd_utils import get_server_status, cancel_all_spider
from spideradmin.version import VERSION
from puremysql import PureMysql

from tinydb import TinyDB, Query

sys.path.insert(0, os.getcwd())

try:
    import config
except Exception as e:
    from spideradmin import default_config as config

api_app = Blueprint(name="api", import_name=__name__)
db = TinyDB("server.db")
user_server_table = db.table("user_servers")
query = Query()


def get_servers():
    user_servers = user_server_table.all()

    defualt_servers = [
        {
            "server_name": server_name,
            "server_host": server_host
        }
        for server_name, server_host in config.SCRAPYD_SERVERS
    ]

    user_servers.extend(defualt_servers)
    return user_servers


@api_app.route("/servers")
def servers():
    return jsonify(get_servers())


@api_app.route("/addServer", methods=["POST"])
def add_server():
    server_host = request.json.get("server_host", "")
    server_name = request.json.get("server_name", "")

    server_name = server_name.strip()
    server_host = server_host.strip()

    if not all([server_name, server_host]):
        message = "添加失败"
        message_type = "warning"

    else:
        user_server_table.insert(
            {
                "server_name": server_name,
                "server_host": server_host
            }
        )
        message = "添加成功"
        message_type = "success"

    data = {
        "message": message,
        "message_type": message_type
    }

    return jsonify(data)


@api_app.route("/removeServer", methods=["POST"])
def remove_server():
    server_host = request.json.get("server_host")
    server_name = request.json.get("server_name")
    server = {
        "server_name": server_name,
        "server_host": server_host
    }
    print(server)

    result = user_server_table.remove(
        (query.server_name == server_name) &
        (query.server_host == server_host)
    )
    if result:
        message = "移除成功"
        message_type = "success"
    else:
        message = "移除失败"
        message_type = "warning"
    return jsonify({
        "message": message,
        "message_type": message_type
    })


@api_app.route("/ServerStatus")
def servers_status():
    return jsonify(get_server_status(get_servers()))


@api_app.route("/listProjects")
def list_projects():
    """
    显示项目
    """
    server_host = request.args.get("server_host")
    server_name = request.args.get("server_name")

    scrapyd = ScrapydAPI(server_host)
    projects = scrapyd.list_projects()

    lst = []
    for project in projects:
        versions = scrapyd.list_versions(project)
        for version in versions:
            item = {
                "project_name": project,
                "human_version": scrapyd_utils.format_version(version),
                "version": version
            }
            lst.append(item)

    data = {
        "server_name": server_name,
        "server_host": server_host,
        "projects": lst

    }

    return jsonify(data)


@api_app.route("/listSpiders")
def list_spiders():
    """
    查看爬虫列表
    """
    server_host = request.args.get("server_host")
    server_name = request.args.get("server_name")
    project_name = request.args.get("project_name")

    scrapyd = ScrapydAPI(server_host)
    spiders = scrapyd.list_spiders(project_name)

    data = {
        "server_name": server_name,
        "server_host": server_host,
        "project_name": project_name,
        "spiders": [{"spider_name": spider} for spider in spiders]
    }
    return jsonify(data)


@api_app.route("/schedule")
def schedule():
    """
    调度运行爬虫
    """
    server_host = request.args.get("server_host")
    server_name = request.args.get("server_name")
    project_name = request.args.get("project_name")
    spider_name = request.args.get("spider_name")

    scrapyd = ScrapydAPI(server_host)
    result = scrapyd.schedule(project_name, spider_name)

    return jsonify({"message": result})


@api_app.route("/listJobs")
def list_jobs():
    """
    查看任务
    """
    server_host = request.args.get("server_host")
    server_name = request.args.get("server_name")
    project_name = request.args.get("project_name")

    scrapyd = ScrapydAPI(server_host)
    jobs = scrapyd.list_jobs(project_name)
    lst = []
    for job_status, job_list in jobs.items():
        for job in job_list:
            item = {
                "status": job_status,
                "spider": job["spider"],
                "start_time": scrapyd_utils.format_time(job.get("start_time", "")),
                "end_time": scrapyd_utils.format_time(job.get("end_time", "")),
                "timestamp": scrapyd_utils.get_timestamp(job.get("end_time"), job.get("start_time")),
                "job_id": job["id"]
            }
            lst.append(item)

    data = {
        "server_host": server_host,
        "server_name": server_name,
        "project_name": project_name,
        "jobs": lst,
    }

    return jsonify(data)


@api_app.route("/log")
def log():
    """
    查看日志
    """
    server_host = request.args.get("server_host")
    project_name = request.args.get("project_name")
    spider_name = request.args.get("spider_name")
    job_id = request.args.get("job_id")

    url = scrapyd_utils.get_log_url(server_host, project_name, spider_name, job_id)
    return scrapyd_utils.get_log(url)


@api_app.route("/cancelAll")
def cancel_all():
    server_host = request.args.get("server_host")
    cancel_all_spider(server_host)
    return jsonify({
        "message": "删除成功!",
        "status": 200
    })


@api_app.route("/cancel")
def cancel():
    """
    取消爬虫运行
    """
    server_host = request.args.get("server_host")
    server_name = request.args.get("server_name")
    project_name = request.args.get("project_name")
    job_id = request.args.get("job_id")

    scrapyd = ScrapydAPI(server_host)
    result = scrapyd.cancel(project_name, job_id)

    return jsonify({"message": result})


@api_app.route("/deleteVersion")
def delete_version():
    """
    删除项目
    """
    server_host = request.args.get("server_host")
    server_name = request.args.get("server_name")
    project_name = request.args.get("project_name")
    version = request.args.get("version")
    scrapyd = ScrapydAPI(server_host)
    result = scrapyd.delete_version(project_name, version)
    return jsonify(
        {
            "message": result
        }
    )


@api_app.route("/currentVersion")
def current_version():
    return jsonify({
        "version": VERSION
    })


@api_app.route("/itemCount")
def item_count():
    """执行结果统计列表"""
    if config.ITEM_LOG_DATABASE_URL is None:
        return jsonify([])

    mysql = PureMysql(db_url=config.ITEM_LOG_DATABASE_URL)
    # sql = ""select * from {table} order by create_time desc limit 20".format(table=config.ITEM_LOG_TABLE))"
    sql = """
    select spider_name, 
    count(*) as total,
    sum(item_count) as item_count, 
    sum(duration) as duration, 
    sum(log_error) as log_error, 
    max(create_time) as create_time 
    from  {table} 
    GROUP BY spider_name
    """.format(
        table=config.ITEM_LOG_TABLE)

    cursor = mysql.execute(sql)

    data = []
    count = 0
    for row in cursor.fetchall():
        count += 1
        item = {
            "id": count,
            "create_time": row["create_time"].strftime("%Y-%m-%d %H:%M:%S"),
            "duration": int(row["duration"])/row['total'],
            "item_count": int(row["item_count"]),
            "log_error": int(row["log_error"]),
            "spider_name": row["spider_name"]
        }
        data.append(item)

    mysql.close()

    return jsonify(data)


@api_app.route("/truncateItem")
def truncate_item():
    """清空统计列表"""
    if config.ITEM_LOG_DATABASE_URL is None:
        return jsonify({"code": -1})

    mysql = PureMysql(db_url=config.ITEM_LOG_DATABASE_URL)

    sql = "TRUNCATE table {table}".format(table=config.ITEM_LOG_TABLE)

    cursor = mysql.execute(sql)

    mysql.close()

    return jsonify({"code": 0})


@api_app.route("/itemCountDetail")
def item_count_detail():
    """执行结果统计详细"""
    spider_name = request.args.get("spider_name")

    mysql = PureMysql(db_url=config.ITEM_LOG_DATABASE_URL)

    cursor = mysql.execute(
        "select * from {table} where spider_name=%(spider_name)s order by create_time desc limit 20".format(
            table=config.ITEM_LOG_TABLE),
        data={
            "spider_name": spider_name
        })

    create_times = []
    durations = []
    item_counts = []
    log_errors = []

    for row in cursor.fetchall():
        create_times.insert(0, row["create_time"].strftime("%H:%M"))
        durations.insert(0, row["duration"])
        item_counts.insert(0, row["item_count"])
        log_errors.insert(0, row["log_error"])

    data = {
        "spider_name": spider_name,
        "create_times": create_times,
        "durations": durations,
        "item_counts": item_counts,
        "log_errors": log_errors
    }

    mysql.close()

    return jsonify(data)
