# -*- coding: utf-8 -*-

# @Date    : 2019-06-25
# @Author  : Peng Shiyu

import uuid
from datetime import datetime

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers import SchedulerAlreadyRunningError, SchedulerNotRunningError
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Blueprint, jsonify, request

from spideradmin.api_app.scrapyd_api import ScrapydAPI
from spideradmin.scheduler_app.utils import parse_crontab, DATE_TIME_FORMAT, get_job_info

scheduler_app = Blueprint(name="scheduler", import_name=__name__)

# 启动
is_start = True

# 暂停
is_pause = False

jobstores = {
    'default': SQLAlchemyJobStore(url='sqlite:///db.sqlite')
}

# executors = {
#     'default': ThreadPoolExecutor(THREAD_NUM),
#     'processpool': ProcessPoolExecutor(PROCESS_NUM)
# }

job_defaults = {
    'coalesce': True,
    'max_instances': 1
}

scheduler = BackgroundScheduler(jobstores=jobstores, job_defaults=job_defaults)
scheduler.start()


def run_spider(**kwargs):
    """
    运行爬虫函数
    :param kwargs:
    :return:
    """
    server_host = kwargs["server_host"]
    server_name = kwargs["server_name"]
    project_name = kwargs["project_name"]
    spider_name = kwargs["spider_name"]

    scrapyd = ScrapydAPI(server_host)
    result = scrapyd.schedule(project_name, spider_name)
    kwargs["last_run_time"] = datetime.now().strftime(DATE_TIME_FORMAT)
    set_schedule(kwargs)


def set_schedule(data):
    """
    添加和修改任务计划的统一入口
    :param data:
    :return:
    """
    crontab = data.get("crontab")
    server_host = data.get("server_host")
    server_name = data.get("server_name")
    project_name = data.get("project_name")
    spider_name = data.get("spider_name")
    job_id = data.get("job_id")
    last_run_time = data.get("last_run_time")
    modify_time = data.get("modify_time")
    is_modify = data.get("is_modify")

    crontabs = parse_crontab(crontab)
    if all([crontabs, server_host, server_name, project_name, spider_name]):
        # 新增：如果没有任务id就设置一个
        # 修改：如果是修改就使用之前的任务id
        if not job_id:
            job_id = uuid.uuid4().hex

        # 如果是修改则更新 修改时间
        if is_modify:
            modify_time = datetime.now().strftime(DATE_TIME_FORMAT)

        minute, hour, day, month, day_of_week = crontabs

        kwargs = {
            "crontab": crontab,
            "server_host": server_host,
            "server_name": server_name,
            "project_name": project_name,
            "spider_name": spider_name,
            "job_id": job_id,
            "last_run_time": last_run_time,
            "modify_time": modify_time
        }

        scheduler.add_job(
            run_spider, "cron", kwargs=kwargs, id=job_id,
            minute=minute, hour=hour, day=day, month=month, day_of_week=day_of_week,
            replace_existing=True
        )
        return job_id
    else:
        return None


#########################
#   任务管理
#########################
@scheduler_app.route("/getJobs")
def get_jobs():
    global is_start
    global is_pause

    jobs = scheduler.get_jobs()
    rows = []

    for job in jobs:
        row = get_job_info(job)
        rows.append(row)

    data = {
        "jobs": rows,
        "scheduler_data": {
            "is_start": is_start,
            "start_text": "关闭调度器" if is_start else "启动调度器",
            "start_type": "warning" if is_start else "success",
            "start_function": "shutdown" if is_start else "start",

            "is_pause": is_pause,
            "pause_text": "继续调度器" if is_pause else "暂停调度器",
            "pause_type": "success" if is_pause else "warning",
            "pause_function": "resume" if is_pause else "pause"
        }
    }

    return jsonify(data)


@scheduler_app.route("/addJob", methods=["POST"])
def add_job():
    data = request.json
    data["is_modify"] = True
    job_id = data.get("job_id")
    new_job_id = set_schedule(data)

    if new_job_id:
        message_type = "success"
        if job_id:
            message = "任务修改成功！"
        else:
            message = "任务添加成功！"

    else:
        message_type = "error"
        if job_id:
            message = "任务修改失败！"
        else:
            message = "任务添加失败！"

    return jsonify({
        "message_type": message_type,
        "message": message,
        "job_id": new_job_id
    })


@scheduler_app.route("/removeJob")
def remove_job():
    job_id = request.args.get("job_id")

    scheduler.remove_job(job_id)
    return jsonify({
        "message": "任务移除成功"
    })


@scheduler_app.route("/pauseJob")
def pause_job():
    job_id = request.args.get("job_id")
    scheduler.pause_job(job_id)
    return jsonify({
        "message": "暂停成功",
        "message_type": "warning"
    })


@scheduler_app.route("/resumeJob")
def resume_job():
    job_id = request.args.get("job_id")
    scheduler.resume_job(job_id)
    return jsonify({
        "message": "继续运行",
        "message_type": "success"
    })


@scheduler_app.route("/runJob")
def run_job():
    job_id = request.args.get("job_id")
    job = scheduler.get_job(job_id)
    job_info = get_job_info(job)

    scheduler.add_job(run_spider, kwargs=job_info)

    return jsonify({
        "message": "运行成功"
    })


@scheduler_app.route("/jobDetail")
def job_detail():
    job_id = request.args.get("job_id")
    job = scheduler.get_job(job_id)
    row = get_job_info(job)
    return jsonify(row)


#########################
#   调度器管理
#########################
@scheduler_app.route("/start")
def start():
    global is_start
    is_start = True

    try:
        scheduler.start()
        message = "启动调度"
        message_type = "success"
    except SchedulerAlreadyRunningError:
        message = "调度已经在运行了"
        message_type = "warning"
    return jsonify({
        "message": message,
        "message_type": message_type
    })


@scheduler_app.route("/shutdown")
def shutdown():
    global is_start
    is_start = False

    try:
        scheduler.shutdown()
        message = "关闭调度"
        message_type = "warning"
    except SchedulerNotRunningError:
        message = "调度器还没运行"
        message_type = "error"

    return jsonify({
        "message": message,
        "message_type": message_type
    })


@scheduler_app.route("/pause")
def pause():
    global is_pause

    try:
        scheduler.pause()
        message = "全部任务暂停"
        message_type = "warning"
        is_pause = True
    except SchedulerNotRunningError:
        message = "调度器没有启动"
        message_type = "error"

    return jsonify({
        "message": message,
        "message_type": message_type
    })


@scheduler_app.route("/resume")
def resume():
    global is_pause

    try:
        scheduler.resume()
        message = "全部任务继续"
        message_type = "success"
        is_pause = False
    except SchedulerNotRunningError:
        message = "调度器没有启动"
        message_type = "warning"

    return jsonify({
        "message": message,
        "message_type": message_type
    })


@scheduler_app.route("/removeAllJobs")
def remove_all_jobs():
    scheduler.remove_all_jobs()
    return jsonify({
        "message": "全部任务移除"
    })
