import json
import logging
import os
import time
from bs4 import BeautifulSoup
import requests

from urllib import request

import io 
import sys 
sys.stdout = io.TextIOWrapper(sys.stdout.buffer,encoding='gb18030')

_LOGGER = logging.getLogger(__file__)

#https://www.zhihu.com/api/v4/questions/60908883/answers?sort_by=default&limit=20&offset=23
#https://www.zhihu.com/question/60908883/answer/183125520

QUESTION_API = 'https://www.zhihu.com/api/v4/questions/{0}'
ANSWERS_OFFSET = '/answers?sort_by=default&limit=20&offset={0}'
ANSWER_URL = 'https://www.zhihu.com/question/{0}/answer/{1}'

ANSWER_LIMIT = 20

class ZhiHuSpider():
    def __init__(self, question_id, root):
        self.question_id = question_id
        self.question_url = QUESTION_API.format(self.question_id)
        self.root = root
        self.directory = os.path.join(self.root, self.question_id)
        if not os.path.exists(self.directory):
            os.makedirs(self.directory)
        self._session = requests.session()
        self._headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6',
            'Connection':'keep-alive',
            'Cache-Control':'max-age=0',
            'Host':'www.zhihu.com',
            'Upgrade-Insecure-Requests':'1',
            'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36'
        }

    def set_cookie(self, cookie):
        self._headers['Cookie'] = cookie

    def download_imgs(self, answer_count=100):
        self._print('Start to download images under question %s...' % self.question_id)
        offset = 0
        url = self.question_url + ANSWERS_OFFSET.format(offset)
        has_more, total_count, answer_list = self._get_answers(url)
        self._print('Start to download answers from %s to %s (total: %s)...' % (offset, offset + ANSWER_LIMIT, total_count))
        self._download_imgs_by_answer_group(answer_list)
        while has_more:
            offset = offset + ANSWER_LIMIT
            self._print('Start to download answers from %s to %s (total: %s)...' % (offset, offset + ANSWER_LIMIT, total_count))
            url = self.question_url + ANSWERS_OFFSET.format(offset)
            has_more, total_count, answer_list = self._get_answers(url)
            self._download_imgs_by_answer_group(answer_list)
            time.sleep(3)

    def _download_imgs_by_answer_group(self, answer_list):
        for answer_id, author_name, author_url in answer_list:
            self._print('Answer %s' % answer_id)
            self._download_imgs_by_answer(answer_id, author_name, author_url)
            self._print('-' * 24)

    def _download_imgs_by_answer(self, answer_id, author_name, author_url):
        answer_url = ANSWER_URL.format(self.question_id, answer_id)
        rep = self._session.get(answer_url, headers=self._headers, verify=True)
        soup = BeautifulSoup(rep.text, 'html.parser')
        tag_list = soup.find_all('noscript')
        index = 1
        if len(tag_list) == 0:
            self._print('No image in answer %s' % answer_id)
            return
        for tag in tag_list:
            img = tag.find('img')
            if 'data-original' in img:
                img_url = img['data-original']
            else:
                img_url = img['src']
            fmt = img_url[-4:]
            img_name = '{0}_{1}{2}'.format(answer_id, index, fmt)
            index = index + 1
            self.download_img(img_url, img_name)

    def _get_answers(self, offset_url):
        rep = self._session.get(offset_url, headers=self._headers, verify=True)
        if rep.status_code != 200:
            _LOGGER.error(rep.text)
            return
        answer_json = json.loads(rep.text)
        total_count = answer_json['paging']['totals']
        has_more = not answer_json['paging']['is_end']
        data = answer_json['data']
        answer_list = []
        if len(data) > 0:
            
            for item in data:
                author_name = item['author']['name']
                author_url = item['author']['url'].replace('/api/v4', '')
                answer_id = item['url'].replace('http://www.zhihu.com/api/v4/answers/', '')
                answer_list.append((answer_id, author_name, author_url))
        return has_more, total_count, answer_list

    def download_img(self, url, name):
        try:
            f = open(os.path.join(self.directory, name), 'wb')
            rep = self._session.get(url)
            f.write(rep.content)
            self._print('%s saved' % name)
        except:
            _LOGGER.error('Failed to download img: %s', url)
            pass    

    def _record(self, msg):
        pass #fp = open("test.txt",w)

    def _print(self, msg):
        print(msg, flush=True)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Requestion ID is required.')
    else:
        request_id = sys.argv[1]
        spider = ZhiHuSpider(request_id, r'/samba/zhihu')
        spider.set_cookie('d_c0="AJDCS--zEwyPTvyxJKnCZ2X2o_Waf99sjYE=|1500260667"; _zap=5367fc7a-055c-432f-b5d6-8b07b7203565; q_c1=2979b7f3e756448cbbaff523dd6bc382|1506307958000|1496998492000; q_c1=2979b7f3e756448cbbaff523dd6bc382|1506321963000|1496998492000; capsion_ticket="2|1:0|10:1506322340|14:capsion_ticket|44:MmNkZjczZmE5ODA2NDZhNzgzZGU1YWY0Zjk1Zjg1NDE=|358289c363a386fc8b08c2cfb88587a798435f57ad67493f083aa8234db6d0a7"; _ga=GA1.2.89326784.1503368122; _gid=GA1.2.1126089039.1506592707; r_cap_id="MjYyODE4YzY4NGYxNDk5Y2IwNzI5OGE2MDA0M2IxMzU=|1506658206|7244c0622bc3a3c8d52d3e564d1f4931f5c997e0"; cap_id="NmU5ZWQwNzEwOGI5NDI4MWEyMTc0Yzc2Njg1N2IzNjA=|1506658206|d261b6a8b092034ca83f4aec5eeb5661bd525992"; z_c0=Mi4xRFdNc0FBQUFBQUFBa01KTDc3TVREQmNBQUFCaEFsVk53VlQxV1FCX2xvVXhKTlVOZkpoZGJjRzlhN2xHM1lUa0xR|1506658241|82b6a3486fe20de0e904389a586cab6c1e775d9f; s-q=nba; s-i=1; sid=4fg7gsp8; __utma=155987696.89326784.1503368122.1506667724.1506667724.1; __utmb=155987696.0.10.1506667724; __utmc=155987696; __utmz=155987696.1506667724.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); _xsrf=6a7b0738-5a1d-438d-aaed-c7e5480c6a55')
        spider.download_imgs()
