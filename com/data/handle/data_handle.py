# 亚马逊数据处理工具

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import requests
from lxml import etree
import threading
import os
import json

class handle(object):
    name = 'amazon'
    driver_path = '/Users/lsy/Downloads/chromedriver';
    url_one = 'https://xp.sellermotor.com/selection/index/market-insight'
    url_two = 'https://www.amz123.com/tools-wordcounter'
    url_three = 'https://www.sellersprite.com/v2/keyword-miner/dynamic'

    url_three_country_dict = {0: 'US', 1: 'JP', 2: 'UK', 3: 'DE', 4: 'FR', 5: 'IT', 6: 'ES', 7: 'CA'}

    # 爬取亚马逊信息
    goods_data_map = {}

    def run(self, key, country):
        # 打开第一个网页
        driver_one = webdriver.Chrome(self.driver_path)
        driver_one.get(self.url_one)
        # 判断是否未登录
        # 等待扫码
        while not self.check_login_one_url(driver_one):
            print("等待登陆")
            # 隔1s检查一次
            time.sleep(1)
        print("登陆完成")
        # 输入关键字
        input_element = driver_one.find_element_by_id("search-keyword")
        input_element.send_keys(key)
        input_element.send_keys(Keys.ENTER)
        # 循环n次取出url
        url_list = []
        cycle_num = 1
        for i in range(cycle_num):
            table_element = self.get_element_retry(driver_one, "top100-list")
            tbody_element = self.get_element_by_tag_name_retry(table_element, "tbody")
            tr_element = self.get_elements_by_tag_name_retry(tbody_element, "tr")
            for tr in tr_element:
                url = tr.find_element_by_class_name("text-left").find_element_by_tag_name("a").get_attribute("href")
                url_list.append(url)
            # 点击下一页
            if i < 9:
                next_page_element = driver_one.find_element_by_class_name("page-next")
                a_element = next_page_element.find_element_by_tag_name("a")
                a_element.click()
        # 关闭第一个网页
        driver_one.close()
        # 抓起商品信息
        print('共' + str(len(url_list)) + '个页面')
        self.get_amazon_good_info_async(url_list)
        # 打开第二个网页
        driver_two = webdriver.Chrome(self.driver_path)
        driver_two.get(self.url_two)
        # 遍历map 查询关键词
        goods_data_key_map = {}
        index = 0
        for key in self.goods_data_map:
            print('共' + str(len(self.goods_data_map)) + '个关键词列表 正在查询第' + str(index) + '个')
            goods_data = self.goods_data_map[key]
            title = goods_data[0]
            detail = goods_data[1]
            five_detail = goods_data[2]
            goods_data_key_map[key] = [self.getKeyWord(driver_two, title), self.getKeyWord(driver_two, detail), self.getKeyWord(driver_two, five_detail)]
            index += 1
        # 关闭第二个网页
        driver_two.close()
        # 打开第三个网页
        driver_three = webdriver.Chrome(self.driver_path)
        driver_three.get(self.url_three)
        # 检查登陆
        while not self.check_login_three_url(driver_three):
            print("等待登陆")
            # 隔1s检查一次
            time.sleep(1)
        # 获取cookie
        url_three_cookie = driver_three.get_cookies()
        for url in goods_data_key_map:
            # 每个url 三个关键文本
            for url_data in goods_data_key_map[key]:
                # 下载excel
                path = os.getcwd()[:-4] + str(time.time())
                self.download_excel(url, path, ';'.join([item['name'] + '=' + item['value'] for item in url_three_cookie]), url_data, country)
        # 关闭第三个网页
        driver_three.close()

    # 下载最终excel
    def download_excel(self, goods_url, path, cookie, keys, country):
        url = 'https://www.sellersprite.com/v2/keyword/list-export-dynamic'
        folder = os.path.exists(path)
        if not folder:  # 判断是否存在文件夹如果不存在则创建为文件夹
            os.makedirs(path)
        # 下载
        for key_list in keys:
            for key in key_list:
                # 处理空格
                key = key.replace(' ', '+')
                # 构造请求参数
                headers = {
                    'cookie': cookie
                }
                params = {
                    'station': self.url_three_country_dict[country],
                    'order.field': 'weight',
                    'order.desc': 'true',
                    'usestatic':'M',
                    'limitUserStatic': 'true',
                    'adminDes': 'N',
                    'keywords': key
                }
                file_path = path + '/' + goods_url.replace('/', '_') + '/'
                os.makedirs(path)
                down_res = requests.get(url=url, headers=headers, params=params)
                with open(file_path + key + '.xlsx', 'wb') as file:
                    file.write(down_res.content)

    # 查询关键词
    def getKeyWord(self, driver, str):
        data = []
        if str is None or len(str) == 0:
            return data
        # 一个词
        data.append(self.getKeyWordByNum(driver, str, 1))
        # 二个词
        data.append(self.getKeyWordByNum(driver, str, 2))
        # 三个词
        data.append(self.getKeyWordByNum(driver, str, 3))
        return data

    # 查询关键词
    def getKeyWordByNum(self, driver, find_str, num):
        data = []
        textarea_element = self.get_element_retry(driver, "textbox")
        # 清空文本
        textarea_element.clear()
        # 输入文本
        find_str = find_str.replace('\'', '\\\'').replace('"', '\\"')
        js = 'document.getElementById(\'textbox\').value=\'' + find_str + '\''
        print(js)
        driver.execute_script(js)
        textarea_element.click()
        # textarea_element.send_keys(find_str)
        # 切换关键字个数
        click_element = driver.find_element_by_xpath('//*[@id="ui-id-' + str(num) + '"]')
        click_element.click()
        # 获取结果
        table_element = driver.find_element_by_xpath('//*[@id="keyword_density-tab-' + str(num) + '-table"]/tbody')
        if table_element is not None:
            tr_elements = table_element.find_elements_by_tag_name('tr')
            for tr in tr_elements:
                td_elements = tr.find_elements_by_tag_name('td')
                if len(td_elements) == 2:
                    td_text = td_elements[0].text
                    if td_text is not None and len(td_text.split('. ')) == 2:
                        data.append(td_text.split('. ')[1])
        return data

    # 检查第一个页面登陆
    def check_login_one_url(self, driver):
        try:
            driver.find_element_by_id("qrcode-img")
            return False
        except:
            return True

    # 检查第三个页面登陆
    def check_login_three_url(self, driver):
        try:
            driver.find_element_by_xpath('//*[@id="form-condition-search"]/div[2]/input')
            return True
        except:
            return False

    # 不断尝试获取元素 阻塞
    def get_element_retry(self, driver, id):
        for i in range(1000000):
            try:
                element = driver.find_element_by_id(id)
                return element
            except:
                print("页面未加载完成 等待")
                time.sleep(0.1)

    # 不断尝试获取元素 阻塞
    def get_elements_by_tag_name_retry(self, element, id, ):
        for i in range(1000000):
            try:
                el = element.find_elements_by_tag_name(id)
                if len(el) == 0:
                    time.sleep(0.1)
                    continue
                return el
            except:
                print("页面未加载完成 等待")
                time.sleep(0.1)

    # 不断尝试获取元素 阻塞
    def get_element_by_tag_name_retry(self, element, id):
        for i in range(1000000):
            try:
                el = element.find_element_by_tag_name(id)
                return el
            except:
                print("页面未加载完成 等待")
                time.sleep(0.1)

    # 获取亚马逊商品信息 异步执行
    def get_amazon_good_info_async(self, urls):
        thread_list = []
        index = 0
        for url in urls:
            a_thread = amazon_goods_thread('正在解析第' + str(index) + '个页面', url, self)
            a_thread.start()
            thread_list.append(a_thread)
            time.sleep(0.5)
            index += 1
            # 控制并发度 5个线程同时执行
            if len(thread_list) >= 5:
                while thread_list:
                    thread_list.pop().join()
        while thread_list:
            thread_list.pop().join()

    # 获取亚马逊商品信息
    def get_amazon_good_info(self, url):
        headers = {
            'authority': 'www.amazon.com',
            'cache-control': 'max-age=0',
            'rtt': '100',
            'downlink': '8.8',
            'ect': '4g',
            'sec-ch-ua': '" Not;A Brand";v="99", "Google Chrome";v="91", "Chromium";v="91"',
            'sec-ch-ua-mobile': '?0',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'sec-fetch-site': 'none',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-user': '?1',
            'sec-fetch-dest': 'document',
            'accept-language': 'zh-CN,zh;q=0.9',
            'cookie': 'session-id=141-0198602-5971905; session-id-time=2082787201l; sp-cdn="L5Z9:HK"; skin=noskin; ubid-main=135-4979259-9456307; lc-main=en_US; i18n-prefs=USD'
        }
        resp = requests.get(url, headers=headers)
        html = etree.HTML(resp.text)
        # 获取标题
        title_data = ''
        title_data_html = html.xpath('//*[@id="productTitle"]')
        if len(title_data_html) > 0 and title_data_html[0] is not None and title_data_html[0].text is not None:
            title_data = title_data_html[0].text.replace('\n', '')
        # 获取描述
        detail_data = ''
        detail_data_html = html.xpath('//*[@id="productDescription"]/p')
        if len(detail_data_html) > 0 and detail_data_html[0] is not None and detail_data_html[0].text is not None:
            detail_data = detail_data_html[0].text.replace('\n', '')
        # 获取五点
        five_detail_data = []
        i = 3
        li_data = html.xpath('//*[@id="feature-bullets"]/ul/li[2]/span')
        while len(li_data) > 0 and li_data[0] is not None and li_data[0].text is not None:
            five_detail_data.append(li_data[0].text.replace('\n', ''))
            li_data = html.xpath('//*[@id="feature-bullets"]/ul/li['+ str(i) +']/span')
            i += 1
        data = [title_data, detail_data, ','.join(five_detail_data)]
        self.goods_data_map[url] = data

class amazon_goods_thread(threading.Thread):
    def __init__(self, thread_name, url, thread_object):
        threading.Thread.__init__(self)
        self.thread_name = thread_name
        self.url = url
        self.thread_object = thread_object
    def run(self):
        print ("开始线程: " + self.thread_name)
        self.thread_object.get_amazon_good_info(self.url)
        print ("结束线程: " + self.thread_name)

s = handle()
s.run("chairs", 0)
# s.get_amazon_good_info('https://www.amazon.com/dp/B07S1N5R59')