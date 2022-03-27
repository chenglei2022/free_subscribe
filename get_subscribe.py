#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@author: Stone
@license: (C) Copyright 2017-2022, Node Supply Chain Manager Corporation Limited.
@contact: leicheng2013@outlook.com
@software: ChinaSoft
@file: get_subscribe.py
@time: 2022/3/27 18:01
@desc:
"""
import requests
import feedparser
import re
import os
import time
from datetime import datetime


class GetSubscribe:

    def __init__(self):
        self.url = 'https://www.cfmem.com/feeds/posts/default?alt=rss'
        self.profiles_dir = './profiles'
        self.log_dir = './log'
        self.subscribe_url = []
        self.ok_status_code = [200, 201, 202, 203, 204, 205, 206]
        self.update_history = []
        self.headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.74 Safari/537.36 Edg/99.0.1150.52"
        }

    def write_log(self, content, level='INFO'):
        date_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
        # update_log = f"[{date_str}] [{level}] {content}\n"
        update_log = '[{}] [{}] {}'.format(date_str, level, content)
        log_filename = time.strftime("%Y-%m", time.localtime(time.time())) + '-update.log'
        print(update_log)
        with open(file='./log/' + log_filename, mode='a',
                  encoding="utf-8") as f:
            f.write(update_log)

    def phrase_rss(self, url):
        print('开始解析rss')
        res = feedparser.parse(url)  # 解析rss
        entries = res.get('entries')
        if not entries:
            self.write_log(content='更新失败，无法拉取原网站内容，请稍后再试！', level='ERROR')
            return
        summary = entries[0].get('summary')  # 第一个是最新的订阅地址
        if not summary:
            # self.write_log('暂时没有可用的订阅更新，请稍后再试！', 'WARN')
            return
        v2ray_list = re.findall(r"v2ray订阅链接：(.+?)</span>", summary)
        clash_list = re.findall(r"clash订阅链接：(.+?)</span>", summary)
        self.subscribe_url.append(v2ray_list[0])
        self.subscribe_url.append(clash_list[0])
        print('解析完成，开始下载配置文件')
        return self.download_conf(self.subscribe_url)

    def download_conf(self, urls: list):
        # 解析配置文件，将其下载到本地
        for url in urls:
            if url.endswith('yaml'):
                clash_res = requests.request('get', url=url, verify=False, headers=self.headers)
                clash_status_code = clash_res.status_code
                if clash_status_code not in self.ok_status_code:
                    self.write_log(content='获取clash订阅失败：{url}--{clash_status_code}', level='WARN')
                else:
                    self.update_history.append(f'clash更新成功：{clash_status_code}')
                    with open(file=self.profiles_dir + '/clash.yaml', mode='w',
                              encoding='utf-8') as f:
                        f.write(clash_res.content.decode('utf-8'))
            else:
                v2ray_res = requests.request('get', url=url, verify=False, headers=self.headers)
                v2ray_status_code = v2ray_res.status_code
                if v2ray_status_code not in self.ok_status_code:
                    self.write_log(content='获取v2ray订阅失败：{url}--{v2ray_status_code}', level='WARN')
                else:
                    self.update_history.append(f'v2ray: {v2ray_status_code}')
                    with open(file=self.profiles_dir + '/v2ray.txt', mode='w',
                              encoding='utf-8') as f:
                        f.write(v2ray_res.text)
        print('配置文件下载完成，记录本次更新时间')
        if self.update_history:
            file_pat = re.compile(r'v2ray\.txt|clash\.yml')
            if file_pat.search(os.popen("git status").read()):
                self.write_log(content='更新成功：{}'.format(self.update_history), level='INFO')
            else:
                self.write_log(content='订阅暂未更新', level='WARN')
        else:
            self.write_log(content='未能获取新的更新内容', level='WARN')

    def get_subscribe(self):
        if not os.path.exists(self.profiles_dir):
            os.makedirs(self.profiles_dir)
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        self.phrase_rss(self.url)


if __name__ == '__main__':
    start_time = datetime.now().timestamp()
    gs = GetSubscribe()
    gs.get_subscribe()
    end_time = datetime.now().timestamp()
    print('任务完成，本次共耗时{time:.3f}秒'.format(time=end_time - start_time))
