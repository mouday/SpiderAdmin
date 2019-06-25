# -*- coding: utf-8 -*-

# @Date    : 2019-06-25
# @Author  : Peng Shiyu

from flask import Blueprint, send_file, url_for, redirect

html_app = Blueprint(name="html_app", import_name=__name__)


@html_app.route("/")
def admin_vue():
    return send_file("templates/admin-vue.html")


@html_app.route("/server-vue")
def server_vue():
    return send_file("templates/server-vue.html")


@html_app.route("/server-status-vue")
def server_status_vue():
    return send_file("templates/server-status-vue.html")


@html_app.route("/project-vue")
def project_vue():
    return send_file("templates/project-vue.html")


@html_app.route("/spider-vue")
def spider_vue():
    return send_file("templates/spider-vue.html")


@html_app.route("/job-vue")
def job_vue():
    return send_file("templates/job-vue.html")


@html_app.route("/scheduler-vue")
def scheduler_vue():
    return send_file("templates/scheduler-vue.html")


@html_app.route("/scheduler-modify-vue")
def scheduler_modify_vue():
    return send_file("templates/scheduler-modify-vue.html")


