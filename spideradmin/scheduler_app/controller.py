# -*- coding: utf-8 -*-

# @Date    : 2019-06-25
# @Author  : Peng Shiyu

import logging
import random
import uuid
from datetime import datetime, timedelta
from collections import defaultdict
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.schedulers import SchedulerNotRunningError
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Blueprint, jsonify, request

from spideradmin.api_app.scrapyd_api import ScrapydAPI
from spideradmin.scheduler_app.utils import parse_crontab, DATE_TIME_FORMAT, get_job_info
from spideradmin.scheduler_app import scheduler_history

# ==============================================
# 调度情况日志配置
# ==============================================

scheduler_logging = logging.getLogger(__name__)
scheduler_logging.setLevel(logging.DEBUG)

log_fmt = "%(asctime)s - %(levelname)s: %(message)s"
formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")

scheduler_logging_filename = "scheduler_logging.log"
file_handler = logging.FileHandler(scheduler_logging_filename)
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

scheduler_logging.addHandler(stream_handler)
scheduler_logging.addHandler(file_handler)

# ==============================================
# 调度器服务配置
# ==============================================

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

scheduler = None


def start_scheduler():
    global scheduler
    global is_pause
    global is_start

    # 重启之后要初始化状态
    is_pause = False
    is_start = True

    scheduler = BackgroundScheduler(jobstores=jobstores, job_defaults=job_defaults)
    scheduler.start()


# 默认启动调度器
start_scheduler()
history = scheduler_history.SchedulerHistory()

# ==============================================
# 调度器接口服务
# ==============================================

scheduler_app = Blueprint(name="scheduler", import_name=__name__)

# 启动
is_start = True

# 暂停
is_pause = False


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
    job_id = kwargs["job_id"]
    times = kwargs.get("times")
    times += 1

    scheduler_logging.info("运行爬虫：[{}][{}] {}-{} => {}".format(
        times, server_host, server_name, project_name, spider_name))

    scrapyd = ScrapydAPI(server_host)
    result = scrapyd.schedule(project_name, spider_name)

    # 调度历史
    with scheduler_history.lock:
        history.insert(
            job_id=job_id,
            server_host=server_host,
            server_name=server_name,
            project_name=project_name,
            spider_name=spider_name,
            spider_job_id=result
        )

    scheduler_logging.info("结束爬虫：[{}] {}-{} => {} {}".format(
        server_host, server_name, project_name, spider_name, result))

    kwargs["times"] = times
    kwargs["spider_job_id"] = result
    kwargs["last_run_time"] = datetime.now().strftime(DATE_TIME_FORMAT)

    set_schedule(kwargs)


def set_schedule(data):
    """
    添加和修改任务计划的统一入口
    :param data:
    :return:
    """
    global scheduler

    server_host = data.get("server_host")
    server_name = data.get("server_name")
    project_name = data.get("project_name")
    spider_name = data.get("spider_name")
    job_id = data.get("job_id")
    last_run_time = data.get("last_run_time")
    modify_time = data.get("modify_time")
    is_modify = data.get("is_modify")
    times = data.get("times", 0)

    trigger = data.get("trigger")
    cron = data.get("cron")
    interval = data.get("interval")
    random_time = data.get("random")
    run_datetime = data.get("run_datetime")
    spider_job_id = data.get("spider_job_id")

    if all([server_host, server_name, project_name, spider_name]
           ) and any([cron, interval, random_time, run_datetime]):
        # 新增：如果没有任务id就设置一个
        # 修改：如果是修改就使用之前的任务id
        if not job_id:
            job_id = uuid.uuid4().hex

        # 如果是主动修改则更新 修改时间
        if is_modify:
            modify_time = datetime.now().strftime(DATE_TIME_FORMAT)

        kwargs = {
            "server_host": server_host,
            "server_name": server_name,
            "project_name": project_name,
            "spider_name": spider_name,
            "job_id": job_id,

            "last_run_time": last_run_time,
            "modify_time": modify_time,
            "trigger": trigger,
            "cron": cron,
            "interval": interval,
            "random": random_time,
            "run_datetime": run_datetime,
            "times": times,
            "spider_job_id": spider_job_id
        }

        # 以crontab 方式执行
        if trigger == "cron":
            crontabs = parse_crontab(cron)
            if not crontabs:
                return None

            minute, hour, day, month, day_of_week = crontabs

            scheduler.add_job(
                run_spider, kwargs=kwargs, id=job_id, replace_existing=True,
                trigger="cron",
                minute=minute, hour=hour, day=day, month=month, day_of_week=day_of_week

            )

        # 时间间隔方式执行
        elif trigger == "interval":
            try:
                interval = int(interval)
            except Exception:
                return None

            scheduler.add_job(
                run_spider, kwargs=kwargs, id=job_id, replace_existing=True,
                trigger="interval", minutes=interval
            )

        # 执行一次
        elif trigger == "date":
            try:
                run_datetime = datetime.strptime(run_datetime, "%Y-%m-%d %H:%M:%S")
            except Exception:
                return None

            scheduler.add_job(
                run_spider, kwargs=kwargs, id=job_id, replace_existing=True,
                trigger="date", run_date=run_datetime
            )

        # 随机时间间隔执行 用于拟人操作
        elif trigger == "random":
            try:
                randoms = random_time.split("-")
                random_start, random_end = [int(rand.strip()) for rand in randoms]

            except Exception:
                return None

            random_delay = random.randint(random_start, random_end)
            scheduler.add_job(
                run_spider, kwargs=kwargs, id=job_id, replace_existing=True,
                trigger="interval", minutes=random_delay
            )
        else:
            return None

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
    global scheduler

    if scheduler:
        jobs = scheduler.get_jobs()
        rows = []

        for job in jobs:
            try:
                row = get_job_info(job)
                if row:
                    rows.append(row)
            except AttributeError:
                continue
    else:
        rows = []

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
    global scheduler

    if not scheduler:
        message_type = "error"
        message = "调度器没启动"
        new_job_id = ""

    else:
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
    result = {
        "message_type": message_type,
        "message": message,
        "job_id": new_job_id
    }

    return jsonify(result)


@scheduler_app.route("/removeJob")
def remove_job():
    global scheduler

    job_id = request.args.get("job_id")

    scheduler.remove_job(job_id)
    return jsonify(
        {
            "message": "任务移除成功"
        }
    )


@scheduler_app.route("/pauseJob")
def pause_job():
    global scheduler

    job_id = request.args.get("job_id")
    scheduler.pause_job(job_id)
    return jsonify(
        {
            "message": "暂停成功",
            "message_type": "warning"
        }
    )


@scheduler_app.route("/resumeJob")
def resume_job():
    global scheduler

    job_id = request.args.get("job_id")
    scheduler.resume_job(job_id)
    return jsonify(
        {
            "message": "继续运行",
            "message_type": "success"
        }
    )


@scheduler_app.route("/runJob")
def run_job():
    global scheduler

    job_id = request.args.get("job_id")
    job = scheduler.get_job(job_id)
    job_info = get_job_info(job)

    if job_info:
        scheduler.add_job(run_spider, kwargs=job_info)
        message = "运行成功"
        message_type = "success"
    else:
        message = "运行失败"
        message_type = "warning"

    data = {
        "message": message,
        "message_type": message_type

    }

    return jsonify(data)


@scheduler_app.route("/jobDetail")
def job_detail():
    global scheduler
    if scheduler:
        job_id = request.args.get("job_id")
        job = scheduler.get_job(job_id)
        row = get_job_info(job)
    else:
        row = {}
    return jsonify(row)


#########################
#   调度器管理
#########################
@scheduler_app.route("/start")
def start():
    global is_start
    global is_pause
    global scheduler

    if scheduler:
        message = "调度已经在运行了"
        message_type = "warning"

    else:
        start_scheduler()

        message = "启动调度"
        message_type = "success"

    data = {
        "message": message,
        "message_type": message_type
    }

    return jsonify(data)


@scheduler_app.route("/shutdown")
def shutdown():
    global is_start
    global scheduler

    is_start = False

    try:
        scheduler.shutdown()
        scheduler = None
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
    global scheduler

    try:
        scheduler.pause()
        message = "全部任务暂停"
        message_type = "warning"
        is_pause = True
    except (SchedulerNotRunningError, AttributeError):
        message = "调度器没有启动"
        message_type = "error"

    return jsonify({
        "message": message,
        "message_type": message_type
    })


@scheduler_app.route("/resume")
def resume():
    global is_pause
    global scheduler

    try:
        scheduler.resume()
        message = "全部任务继续"
        message_type = "success"
        is_pause = False
    except (SchedulerNotRunningError, AttributeError):
        message = "调度器没有启动"
        message_type = "warning"

    return jsonify({
        "message": message,
        "message_type": message_type
    })


@scheduler_app.route("/removeAllJobs")
def remove_all_jobs():
    global scheduler

    if scheduler:
        scheduler.remove_all_jobs()
        message = "全部任务移除"
        message_type = "success"
    else:
        message = "任务移除失败, 调度器没有启动"
        message_type = "warning"

    return jsonify(
        {
            "message": message,
            "message_type": message_type
        }
    )


@scheduler_app.route("/history")
def get_schedule_history():
    job_id = request.args.get("job_id")
    count = request.args.get("count", "30")

    with scheduler_history.lock:
        result = history.select(job_id, count)

    fmt = "%H:%M"
    now = datetime.now()
    min_time = now
    spider_name = None

    schedule_list = defaultdict(int)

    for row in result:
        if spider_name is None:
            spider_name = row["spider_name"]

        schedule_time = row["schedule_time"]
        if schedule_time < min_time:
            min_time = schedule_time

        t = schedule_time.strftime(fmt)

        schedule_list[t] += 1

    time_list = []
    while min_time <= now:
        time_list.append(min_time.strftime(fmt))
        min_time += timedelta(minutes=1)

    data_list = []
    for time_item in time_list:
        data_list.append(schedule_list.get(time_item, 0))

    data = {
        "title": spider_name,
        "values": data_list,
        "keys": time_list
    }

    return jsonify(data)
