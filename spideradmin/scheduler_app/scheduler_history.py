# -*- coding: utf-8 -*-

# @Date    : 2019-07-02
# @Author  : Peng Shiyu

from datetime import datetime
from threading import RLock

from sqlalchemy import Table, Column, Integer, String, MetaData
from sqlalchemy import create_engine, sql
from sqlalchemy.dialects.sqlite import DATETIME

lock = RLock()


class SchedulerHistory(object):
    def __init__(self, db_url=None):
        """
        允许sqlite被多个线程同时访问
        参考：Python SQLite3的问题sqlite3.ProgrammingError:
            SQLite objects created in a thread can only be used in th
        https://blog.csdn.net/blueheart20/article/details/70218102
        :param db_url:
        """
        self.con = None

        if db_url is None:
            db_url = 'sqlite:///history.db'

        self.engine = create_engine(
            db_url,
            connect_args={'check_same_thread': False}
            # echo=True,
        )

        metadata = MetaData()
        self.table = Table(
            'history', metadata,
            Column('id', Integer, autoincrement=True, primary_key=True),
            Column('job_id', String),
            Column('server_host', String),
            Column('server_name', String),
            Column('project_name', String),
            Column('spider_name', String),
            Column('spider_job_id', String),
            Column('schedule_time', DATETIME(truncate_microseconds=True)),
        )

    def get_con(self):
        if self.con is None:
            if not self.table.exists(self.engine):
                self.table.create(self.engine, True)

            self.con = self.engine.connect()

        return self.con

    def con_close(self):
        self.con.close()
        self.con = None

    def insert(self, job_id, server_host, server_name, project_name, spider_name, spider_job_id):
        schedule_time = datetime.now()
        insert = self.table.insert().values(
            job_id=job_id,
            server_host=server_host,
            server_name=server_name,
            project_name=project_name,
            spider_name=spider_name,
            spider_job_id=spider_job_id,
            schedule_time=schedule_time,
        )

        cursor = self.get_con().execute(insert)
        cursor.close()
        self.con_close()

    def select(self, job_id, limit):
        select = sql.select(
            [self.table]
        ).where(
            self.table.c.job_id == job_id
        ).order_by(
            self.table.c.schedule_time.desc()
        ).limit(limit)

        cursor = self.get_con().execute(select)
        rows = cursor.fetchall()
        keys = cursor.keys()

        cursor.close()
        self.con_close()

        lst = []
        for row in rows:
            lst.append(dict(zip(keys, row)))

        return lst
