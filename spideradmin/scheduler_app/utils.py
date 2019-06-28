# -*- coding: utf-8 -*-
# @Date    : 2019-05-09
# @Author  : Peng Shiyu

import os
from datetime import datetime

# 时间格式化
DATE_FORMAT = "%Y-%m-%d"
DATE_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_log_path(log_dir, job_id):
    totay = datetime.today().strftime(DATE_FORMAT)
    today_log_dir = os.path.join(log_dir, totay)

    if not os.path.exists(today_log_dir):
        os.makedirs(today_log_dir)

    log_name = "{}.log".format(job_id)

    log_path = os.path.join(today_log_dir, log_name)
    return log_path


def parse_crontab(crontab):
    try:
        crontabs = crontab.split(" ")
    except Exception:
        return None

    if len(crontabs) == 5:
        return crontabs
    else:
        return None


def get_crontab(job):
    item = {}
    for field in job.trigger.fields:
        item[field.name] = str(field)

    crontab = "{} {} {} {} {}".format(
        item["minute"], item["hour"], item["day"], item["month"], item["day_of_week"]
    )
    return crontab


def get_job_info(job):
    if job is None:
        return {}

    if hasattr(job, "next_run_time"):
        next_run_time = job.next_run_time
    else:
        next_run_time = None

    if isinstance(next_run_time, datetime):
        next_run_time = next_run_time.strftime("%Y-%m-%d %H:%M:%S")

    if hasattr(job, "kwargs"):
        kwargs = job.kwargs
        if not kwargs:
            kwargs = {}
    else:
        kwargs = {}

    row = {
        "server_host": kwargs.get("server_host"),
        "server_name": kwargs.get("server_name"),
        "project_name": kwargs.get("project_name"),
        "spider_name": kwargs.get("spider_name"),

        "job_manage": "暂停" if next_run_time else "继续",
        "job_function": "pauseJob" if next_run_time else "resumeJob",
        "job_color": "warning" if next_run_time else "success",

        "next_run_time": next_run_time,
        # "timezone": job.trigger.timezone,
        "job_id": job.id,
        "pending": job.pending,

        "modify_time": kwargs.get("modify_time"),
        "last_run_time": kwargs.get("last_run_time"),

        "trigger": kwargs.get("trigger"),
        "cron": kwargs.get("cron"),
        "interval": kwargs.get("interval"),
        "random": kwargs.get("random"),
        "run_datetime": kwargs.get("run_datetime"),
        "times": kwargs.get("times"),
        "spider_job_id": kwargs.get("spider_job_id"),
        "spider_status": "success" if kwargs.get("spider_job_id") else "error",

    }

    return row


def tail(filename, n=10):
    with open(filename, "r") as f:
        lines = f.readlines()[-n:]

    return "".join(lines)
