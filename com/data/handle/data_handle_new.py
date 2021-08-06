# 亚马逊数据处理工具

from selenium import webdriver
import time
import requests
from lxml import etree
import threading
import os
import csv
import random
import json

class handle(object):
    name = 'amazon'
    code_path = os.path.abspath(os.path.dirname(__file__))
    driver_path = code_path + '/chromedriver.exe'
    url_one = 'https://xp.sellermotor.com/selection/index/market-insight'

    url_three = 'https://www.sellersprite.com/v2/keyword-miner/dynamic'

    amazon_url = 'https://www.amazon{0}'
    amazon_search_url = 'https://www.amazon{0}/s?k={1}&language=en_US'
    amazon_participle_url = 'https://www.amz123.com/tools-wordcounter'

    url_three_country_dict = {0: 'US', 1: 'JP', 2: 'UK', 3: 'DE', 4: 'FR', 5: 'IT', 6: 'ES', 7: 'CA'}

    country_name_dict = {0: '美国', 1: '德国', 2: '法国', 3: '西班牙', 4: '意大利'}
    country_post_code_dict = {0: '10010', 1: '10115', 2: '75000', 3: '66030', 4: '04810'}
    country_url_dict = {0: '.com', 1: '.de', 2: '.fr', 3: '.es', 4: '.it'}

    amazon_header = {}
    header_max_power = 100

    # 首次查询商品数目
    first_good_top_n = 500
    # 查询商品类目阈值
    find_category_num = 20

    # 介词表
    preposition_word_list = ['at', 'in', 'on', 'to', 'above', 'over', 'below', 'under', 'beside', 'behind', 'between',
                             'in', 'on', 'at', 'after', 'from', 'behind', 'across', 'through', 'past', 'to',
                             'towards', 'onto', 'into', 'up', 'down', 'at', 'under', 'on', 'about', 'by', 'with', 'in']
    # 介表词组表
    preposition_word_group_list = ['since for', 'according to', 'irrespective of', 'ahead of', 'owing to', 'but for', 'together with', 'prior to',
                                   'as forsave for', 'what with', 'in line with', 'in place of', 'for lack of', 'in return for', 'by way of',
                                   'on account of', 'by force of', 'with respect to', 'for the purpose of', 'at the mercy of', 'for the sake of',
                                   'in the care of', 'in the teeth of', 'on the eve of', 'on the ground of', 'on the part of', 'to the exclusion of',
                                   'with an eye to', 'under the auspices of', 'under the guise of']
    # 数字表
    number_list = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    # 符号表
    symbol_list = ['&', '+', '-', '#', '%', '@', '!', '*', '(', ')', '/', '\\']
    # 自定义过滤关键字
    var_word_list = []
    # 自定义过滤关键词组
    var_word_group_list = ['and a']

    # 需要查询的类目链接
    goods_category_url_num_map = {}
    # 亚马逊标题关键词
    goods_data_key_map = {}
    # 亚马逊商品信息 根据关键字分类
    category_goods_data_map = {}

    # csv文件夹路径
    path = ''

    def __init__(self, package_name):
        # 创建一个文件夹用于存放csv
        self.path = self.code_path + '/' + package_name
        # 创建文件夹
        folder = os.path.exists(self.path)
        if not folder:
            os.makedirs(self.path)
        # 初始化header池
        with open(self.code_path + '/amazon_request_header.txt') as fp:
            content = fp.read();
        amazon_header_list = json.loads(content)
        for header in amazon_header_list:
            self.amazon_header[json.JSONEncoder().encode(header)] = self.header_max_power

    # 爬取亚马逊信息
    def get_amazon_info(self, key, country):
        # 亚马逊地址
        amazon_search_url = self.amazon_search_url.format(self.country_url_dict[country], key)
        # 国家邮编
        country_post_code = self.country_post_code_dict[country]
        # 打开亚马逊页面
        driver = webdriver.Chrome(self.driver_path)
        driver.get(amazon_search_url)
        # 切换邮编
        post_code_div_element = self.get_element_by_xpath_retry(driver, '//*[@id="nav-global-location-popover-link"]')
        post_code_div_element.click()
        # 先判断一下是否需要点击后才能输入邮编
        self.click_element_by_xpath_retry(driver, '//*[@id="GLUXChangePostalCodeLink"]', 5)
        # 写入邮编
        post_code_input_element = self.get_element_by_xpath_retry(driver, '//*[@id="GLUXZipUpdateInput"]')
        post_code_input_element.send_keys(country_post_code)
        post_code_button_element = self.get_element_by_xpath_retry(driver, '//*[@id="GLUXZipUpdate"]/span/input')
        post_code_button_element.click()
        # 关闭可能出现的弹框
        self.click_element_by_xpath_retry(driver, '//*[@id="nav-main"]/div[1]/div/div/div[3]/span[2]/span', 5)
        self.click_element_by_xpath_retry(driver, '//*[@id="a-popover-4"]/div/div[2]/span/span', 5)
        time.sleep(5)
        # 获取top n商品 尽量晒出具有代表性的商品类目

        goods_url_set = set()
        goods_elements = self.get_elements_by_tag_class_retry(driver, 's-no-outline', 100)
        page = 2
        while len(goods_elements) > 0 and len(goods_url_set) < self.first_good_top_n:
            for goods_element in goods_elements:
                goods_url_set.add(goods_element.get_attribute('href') + '&language=en_US')
                if len(goods_url_set) == self.first_good_top_n:
                    break
            # 如果商品不足n个 则点击下一页
            if len(goods_url_set) < self.first_good_top_n:
                driver.execute_script('window.location.href="' + amazon_search_url + '&page=' + str(page) + '"')
                goods_elements = self.get_elements_by_tag_class_retry(driver, 's-no-outline', 100)
                page += 1
        # 关闭页面
        driver.close()
        # 爬取商品信息
        self.get_amazon_good_info_async(country, goods_url_set)
        # 根据类目获取各个类目下的top100商品
        category_goods_url_map = self.get_goods_url_by_category()
        # 爬取商品信息
        index = 0
        for category_url in category_goods_url_map:
            print('共' + str(len(category_goods_url_map)) + '个商品类目 正在查询第' + str(index) + '个')
            goods_data_map = self.get_amazon_good_info_async(country, category_goods_url_map[category_url])
            self.category_goods_data_map[category_url] = goods_data_map
            index += 1

    # 根据商品标题&五点获取关键字
    def get_amazon_key_word(self):
        # 打开分词网页
        driver = webdriver.Chrome(self.driver_path)
        driver.get(self.amazon_participle_url)
        # 同一个类目合并标题&五点
        index = 0
        for category_url in self.category_goods_data_map:
            print('共' + str(len(self.category_goods_data_map)) + '个关键词列表 正在查询第' + str(index) + '个')
            title_list = []
            five_detail_data_list = []
            goods_data_map = self.category_goods_data_map[category_url]
            for data_key in goods_data_map:
                if len(goods_data_map[data_key]) > 2:
                    title_list.append(goods_data_map[data_key][0])
                    five_detail_data_list.append(goods_data_map[data_key][2])
            # 查询关键字
            title_key_word_list = []
            five_detail_data_key_word_list = []
            if len(title_list) > 0:
                title_key_word_list = self.get_key_word(driver, ' '.join(title_list))
            if len(five_detail_data_list) > 0:
                five_detail_data_key_word_list = self.get_key_word(driver, ' '.join(five_detail_data_list))
            self.goods_data_key_map[category_url] = [title_key_word_list, five_detail_data_key_word_list]
            index += 1
        # 关闭网页
        driver.close()

    # 创建文件夹
    def create_package(self, file_name):
        path = self.code_path + '/' + str(time.time())
        # 创建文件夹
        folder = os.path.exists(path)
        if not folder:
            os.makedirs(path)
        return path

    # header 降权
    def header_power_down(self, header):
        header_json = json.JSONEncoder().encode(header)
        if header_json in self.amazon_header:
            power = self.amazon_header[header_json]
            if power > 0:
                self.amazon_header[header_json] = power - 1

    # header 升权
    def header_power_up(self, header):
        header_json = json.JSONEncoder().encode(header)
        if header_json in self.amazon_header:
            power = self.amazon_header[header_json]
            if power < self.header_max_power:
                self.amazon_header[header_json] = power + 1

    # 根据权重获取一个header
    def get_header(self):
        print(self.amazon_header.values())
        header_index_list = [[] for _ in range(self.header_max_power)]
        for header in self.amazon_header:
            header_index_list[self.amazon_header[header] - 1].append(header)
        choice_header_list = []
        for i in range(99, -1, -1):
            if (len(choice_header_list) > 0 and i < 80) or len(choice_header_list) > 2:
                break
            if len(header_index_list[i]) > 0:
                choice_header_list += header_index_list[i]
        return json.loads(random.choice(choice_header_list))

    # 导出商品信息csv文件
    def export_goods_csv(self, file_name):
        # 写入csv文件
        with open(self.path + '/' + file_name + '.csv', 'w', encoding='utf_8_sig') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['商品title', '商品链接', '商品描述', '商品五点', '商品类目'])
            for category_url in self.category_goods_data_map:
                goods_data_map = self.category_goods_data_map[category_url]
                for url in goods_data_map:
                    goods_data = goods_data_map[url]
                    if len(goods_data) == 4:
                        writer.writerow([goods_data[0], url, goods_data[1], goods_data[2], goods_data[3]])

    # 导出关键字csv文件
    def export_keyword_csv(self, file_name):
        # 写入csv文件
        with open(self.path + '/' + file_name + '.csv', 'w', encoding='utf_8_sig') as csvfile:
            writer = csv.writer(csvfile)
            # 根据分类链接写入
            for url in self.goods_data_key_map:
                writer.writerow(['商品类目链接', url, '', '', '', '', ''])
                writer.writerow(['标题关键字列表(1个单词)', '标题关键字列表(2个单词)', '标题关键字列表(3个单词)',
                                 '五点关键字列表(1个单词)', '五点关键字列表(2个单词)', '五点关键字列表(3个单词)', ''])
                title_key_word_list = self.goods_data_key_map[url][0]
                five_detail_data_key_word_list = self.goods_data_key_map[url][1]
                title_key_word_one_list = title_key_word_list[0]
                title_key_word_two_list = title_key_word_list[1]
                title_key_word_three_list = title_key_word_list[2]
                five_detail_data_key_word_one_list = five_detail_data_key_word_list[0]
                five_detail_data_key_word_two_list = five_detail_data_key_word_list[1]
                five_detail_data_key_word_three_list = five_detail_data_key_word_list[2]
                index = 0
                while 1:
                    need_break = True
                    key_word_rows = []
                    if index < len(title_key_word_one_list):
                        key_word_rows.append(title_key_word_one_list[index])
                        need_break = False
                    else:
                        key_word_rows.append('')
                    if index < len(title_key_word_two_list):
                        key_word_rows.append(title_key_word_two_list[index])
                        need_break = False
                    else:
                        key_word_rows.append('')
                    if index < len(title_key_word_three_list):
                        key_word_rows.append(title_key_word_three_list[index])
                        need_break = False
                    else:
                        key_word_rows.append('')
                    if index < len(five_detail_data_key_word_one_list):
                        key_word_rows.append(five_detail_data_key_word_one_list[index])
                        need_break = False
                    else:
                        key_word_rows.append('')
                    if index < len(five_detail_data_key_word_two_list):
                        key_word_rows.append(five_detail_data_key_word_two_list[index])
                        need_break = False
                    else:
                        key_word_rows.append('')
                    if index < len(five_detail_data_key_word_three_list):
                        key_word_rows.append(five_detail_data_key_word_three_list[index])
                        need_break = False
                    else:
                        key_word_rows.append('')
                    key_word_rows.append('')
                    if len(key_word_rows) > 0:
                        writer.writerow(key_word_rows)
                    index += 1
                    if need_break:
                        break

    # 下载最终excel 异步执行
    def download_excel_async(self, goods_data_key_map, url_three_cookie, country):
        path = self.code_path + str(time.time())
        # 创建文件夹
        folder = os.path.exists(path)
        if not folder:
            os.makedirs(path)
        print('共' + str(len(goods_data_key_map)) + '个url')
        index = 0
        for url in goods_data_key_map:
            # 创建文件具体目录
            file_path = path + '/' + url.replace('/', '_').replace(':', '') + '/'
            folder = os.path.exists(file_path)
            if not folder:
                os.makedirs(file_path)
            # 每个url 三个关键文本
            data_index = 0
            for url_data in goods_data_key_map[url]:
                # 下载excel
                thread_name = '正在下载第' + str(index) + '个url 第' + str(data_index) + '个关键文本'
                excel_thread = amazon_excel_thread(thread_name, file_path, ';'.join([item['name'] + '=' + item['value'] for item in url_three_cookie]), url_data, country, self)
                excel_thread.run()
                time.sleep(1)
                data_index += 1
            index += 1

    # 不断尝试获取元素 阻塞
    def get_elements_by_tag_class_retry_block(self, driver, class_name):
        for i in range(1000000):
            try:
                el = driver.find_elements_by_class_name(class_name)
                if len(el) == 0:
                    time.sleep(0.1)
                    continue
                return el
            except:
                print("页面未加载完成 等待")
                time.sleep(0.1)
            if (i + 1) % 150 == 0:
                driver.refresh()

    # 不断尝试获取元素 阻塞
    def get_elements_by_tag_class_retry(self, driver, class_name, retry):
        for i in range(retry):
            try:
                el = driver.find_elements_by_class_name(class_name)
                if len(el) == 0:
                    time.sleep(0.1)
                    continue
                return el
            except:
                print("页面未加载完成 等待")
                time.sleep(0.1)
            if (i + 1) % 150 == 0:
                driver.refresh()
        return []

    # 根据xpath不断尝试获取元素 阻塞
    def get_element_by_xpath_retry(self, driver, xpath):
        for i in range(1000000):
            try:
                element = driver.find_element_by_xpath(xpath)
                return element
            except:
                print('页面未加载完成 等待')
                time.sleep(0.1)
            if (i + 1) % 150 == 0:
                driver.refresh()

    # 根据xpath不断尝试获取元素 阻塞
    def get_elements_by_xpath_retry(self, driver, xpath):
        for i in range(1000000):
            try:
                elements = driver.find_elements_by_xpath(xpath)
                return elements
            except:
                print('页面未加载完成 等待')
                time.sleep(0.1)
            if (i + 1) % 150 == 0:
                driver.refresh()

    # 根据xpath判断元素是否存在 重试
    def element_exist_by_xpath_retry(self, driver, xpath, retry_num):
        for i in range(retry_num):
            try:
                driver.find_element_by_xpath(xpath)
                return True
            except:
                print('未获取到元素 重试第' + str(i) + '次')
                time.sleep(0.5)
        return False

    # 根据xpath不断尝试点击元素 重试
    def click_element_by_xpath_retry(self, driver, xpath, retry_num):
        for i in range(retry_num):
            try:
                element = driver.find_element_by_xpath(xpath)
                element.click()
                return
            except:
                print('未获取到元素 重试第' + str(i) + '次')
                time.sleep(0.5)

    # 下载最终excel
    def download_excel(self, file_path, cookie, keys, country):
        url = 'https://www.sellersprite.com/v2/keyword/list-export-dynamic'
        # 下载
        for key_list in keys:
            for key in key_list:
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
                    'keywords': key.replace(' ', '+')
                }
                down_res = requests.get(url=url, headers=headers, params=params)
                try:
                    with open(file_path + key + '.xlsx', 'wb') as file:
                        file.write(down_res.content)
                except:
                    print(key + " 此数据下载失败")

    # 查询关键词
    def get_key_word(self, driver, str):
        data = []
        if str is None or len(str) == 0:
            return data
        # 一个词
        data.append(self.get_key_word_by_num(driver, str, 1))
        # 二个词
        data.append(self.get_key_word_by_num(driver, str, 2))
        # 三个词
        data.append(self.get_key_word_by_num(driver, str, 3))
        return data

    # 查询关键词
    def get_key_word_by_num(self, driver, find_str, num):
        data = []
        textarea_element = self.get_element_retry(driver, "textbox")
        # 清空文本
        textarea_element.clear()
        # 输入文本
        # 处理特殊字符
        find_str = find_str.replace('\'', '\\\'').replace('"', '\\"').replace('&', '\\&')\
            .replace('\\n', '\\\\n').replace('\\r', '\\\\r').replace('\\t', '\\\\t').replace('\\b', '\\\\b').replace('\\f', '\\\\f')
        js = 'document.getElementById(\'textbox\').value=\'' + find_str + '\''
        print(js)
        try:
            driver.execute_script(js)
        except:
            textarea_element.send_keys(find_str)
        textarea_element.click()
        # 切换关键字个数
        click_element = driver.find_element_by_xpath('//*[@id="ui-id-' + str(num) + '"]')
        click_element.click()
        # 获取结果
        try:
            table_element = driver.find_element_by_xpath('//*[@id="keyword_density-tab-' + str(num) + '-table"]/tbody')
        except:
            print('获取关键字结果失败')
            return data
        if table_element is not None:
            tr_elements = table_element.find_elements_by_tag_name('tr')
            for tr in tr_elements:
                td_elements = tr.find_elements_by_tag_name('td')
                if len(td_elements) == 2:
                    td_text = td_elements[0].text
                    td_number_text = td_elements[1].text
                    # td_percentage_text = td_elements[1].find_element_by_tag_name('span').text
                    if td_text is not None and len(td_text.split('. ')) == 2:
                        # 判断是否为数字或单个字母或介词
                        td_str = td_text.split('. ')[1]
                        if self.check_key_word(td_str):
                            data.append(td_str + ' | ' + td_number_text)
                        else:
                            print('过滤关键字 ' + td_str)
        return data

    # 检查关键字是否可用
    def check_key_word(self, word):
        # 如果是数字
        if word.isdigit():
            return False
        # 如果只有一个字符
        if len(word) == 1:
            return False
        # 如果包含数字
        for w in self.number_list:
            if w in word:
                return False
        # 如果包含符号
        for w in self.symbol_list:
            if w in word:
                return False
        # 如果包含介词词组
        for w in self.preposition_word_group_list:
            if w in word:
                return False
        # 如果包含自定义过滤关键字词组
        for w in self.var_word_group_list:
            if w in word:
                return False
        # 关键字按空格分隔
        word_list = word.split(' ')
        # 如果包含介词
        for w in self.preposition_word_list:
            if w in word_list:
                return False
        # 如果包含自定义过滤关键字
        for w in self.var_word_list:
            if w in word_list:
                return False
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
    def get_elements_by_tag_name_retry(self, element, id):
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

    # 获取亚马逊商品类目信息
    def get_goods_url_by_category(self):
        category_goods_url_map = {}
        index = 0
        # 筛选需要查询的类目
        goods_category_url_set = set()
        for category_url in self.goods_category_url_num_map:
            num = self.goods_category_url_num_map[category_url]
            # 若类目出现次数大于阈值 则需要查询
            if num >= self.find_category_num:
                goods_category_url_set.add(category_url)
        for category_url in goods_category_url_set:
            print('共' + str(len(goods_category_url_set)) + '个类目 当前第' + str(index) + '个')
            category_goods_url_set = set()
            # 打开类目页面
            driver = webdriver.Chrome(self.driver_path)
            driver.get(category_url)
            goods_elements = self.get_elements_by_tag_class_retry(driver, 'a-text-normal', 300)
            last_size = -1
            while len(goods_elements) > 0 and len(category_goods_url_set) < 100 and last_size != len(category_goods_url_set):
                last_size = len(category_goods_url_set)
                for goods_element in goods_elements:
                    category_goods_url_set.add(goods_element.get_attribute('href') + '&language=en_US')
                    if len(category_goods_url_set) == 100:
                        break
                # 如果商品不足100个 则点击下一页
                if len(category_goods_url_set) < 100:
                    self.click_element_by_xpath_retry(driver, '//*[@id="zg-center-div"]/div[2]/div/ul/li[4]', 3)
                    goods_elements = self.get_elements_by_tag_class_retry(driver, 'a-text-normal', 300)
            category_goods_url_map[category_url] = category_goods_url_set
            index += 1
            # 关闭页面
            driver.close()
        return category_goods_url_map

    # 获取亚马逊商品信息 异步执行
    def get_amazon_good_info_async(self, country, urls):
        # 商品信息
        goods_data_map = {}
        thread_map = {}
        thread_key_list = []
        fail_url_list = []
        index = 0
        for url in urls:
            a_thread = amazon_goods_thread('共' + str(len(urls)) + '个页面 正在解析第' + str(index) + '个页面', country, url, self)
            a_thread.start()
            thread_map[url] = a_thread
            thread_key_list.append(url)
            time.sleep(1)
            index += 1
            # 控制并发度 3个线程同时执行
            if len(thread_key_list) >= 3:
                for key in thread_key_list:
                    t = thread_map[key]
                    t.join()
                    res_data = t.get_result()
                    if len(res_data) == 2:
                        goods_data_map[res_data[0]] = res_data[1]
                    else:
                        fail_url_list.append(key)
                thread_key_list = []
        for key in thread_key_list:
            t = thread_map[key]
            t.join()
            res_data = t.get_result()
            if len(res_data) == 2:
                goods_data_map[res_data[0]] = res_data[1]
            else:
                fail_url_list.append(key)
        print('共' + str(len(fail_url_list)) + '个失败页面')
        for fail_url in fail_url_list:
            print(fail_url)
        # 尽最大可能成功 失败url使用selenium重试
        fail_thread_map = {}
        fail_thread_key_list = []
        index = 0
        for fail_url in fail_url_list:
            fail_thread = amazon_goods_thread_selenium('共' + str(len(fail_url_list)) + '个失败重试页面 正在解析第' + str(index) + '个页面', fail_url, self)
            fail_thread.start()
            fail_thread_map[fail_url] = fail_thread
            fail_thread_key_list.append(fail_url)
            time.sleep(0.5)
            index += 1
            # 控制并发度 5个线程同时执行
            if len(fail_thread_key_list) >= 5:
                for key in fail_thread_key_list:
                    t = fail_thread_map[key]
                    t.join()
                    res_data = t.get_result()
                    if len(res_data) == 2:
                        goods_data_map[res_data[0]] = res_data[1]
                    else:
                        print('获取商品信息失败 ' + key)
                fail_thread_key_list = []
        for key in fail_thread_key_list:
            t = fail_thread_map[key]
            t.join()
            res_data = t.get_result()
            if len(res_data) == 2:
                goods_data_map[res_data[0]] = res_data[1]
            else:
                print('获取商品信息失败 ' + key)
        return goods_data_map

    # 获取亚马逊商品信息
    def get_amazon_good_info(self, country, url):
        url += '&language=en_US'
        # 获取标题
        title_data = ''
        # 为了防止验证码 重试3次
        retry = 3
        while (title_data == '' or len(title_data) == 0) and retry > 0:
            # 获取header
            headers = self.get_header()
            try:
                resp = requests.get(url, headers=headers, timeout=10)
            except:
                print('失败 ' + url)
                # 降权
                self.header_power_down(headers)
                continue
            html_text = resp.text
            html = etree.HTML(html_text)
            title_data_html = html.xpath('//*[@id="productTitle"]')
            if len(title_data_html) > 0 and title_data_html[0] is not None and title_data_html[0].text is not None:
                title_data = title_data_html[0].text.replace('\n', '')
            else:
                # 降权
                self.header_power_down(headers)
            retry -= 1
        if title_data == '':
            # 降权
            self.header_power_down(headers)
            print('访问被拦截 ' + url)
            return []
        # 尝试升权
        self.header_power_up(headers)
        # 获取描述
        detail_data = ''
        detail_data_html = html.xpath('//*[@id="productDescription"]/p')
        if len(detail_data_html) > 0:
            for detail in detail_data_html:
                if detail.text is not None:
                    detail_data += detail.text.replace('\n', '')
        # 获取五点
        five_detail_data = []
        i = 3
        li_data = html.xpath('//*[@id="feature-bullets"]/ul/li[2]/span')
        while len(li_data) > 0 and li_data[0] is not None and li_data[0].text is not None:
            five_detail_data.append(li_data[0].text.replace('\n', ''))
            li_data = html.xpath('//*[@id="feature-bullets"]/ul/li['+ str(i) +']/span')
            i += 1
        # 查询商品类目链接
        category_url = ''
        url_span_index = 1
        category_url_html = html.xpath('//*[@class="a-color-secondary a-size-base prodDetSectionEntry"]/../td/span/span[' + str(url_span_index) + ']/a/@href')
        while len(category_url_html) > 0 and category_url_html[0] is not None:
            url_span_index += 1
            category_url_html = html.xpath('//*[@class="a-color-secondary a-size-base prodDetSectionEntry"]/../td/span/span[' + str(url_span_index) + ']/a/@href')
        category_url_html = html.xpath('//*[@class="a-color-secondary a-size-base prodDetSectionEntry"]/../td/span/span[' + str(url_span_index - 1) + ']/a/@href')
        if len(category_url_html) > 0 and category_url_html[0] is not None:
            category_url = self.amazon_url.format(self.country_url_dict[country]) + category_url_html[0] + '?language=en_US'
            # 去除中文
            category_url = category_url.replace('-/zh/', '')
            if category_url in self.goods_category_url_num_map:
                self.goods_category_url_num_map[category_url] = self.goods_category_url_num_map[category_url] + 1
            else:
                self.goods_category_url_num_map[category_url] = 1
        data = [title_data, detail_data, ','.join(five_detail_data), category_url]
        return [url, data]

    # 获取亚马逊商品信息
    def get_amazon_good_info_selenium(self, url):
        # 打开亚马逊商品页面
        driver = webdriver.Chrome(self.driver_path)
        driver.get(url)
        # 获取标题
        title_element = self.get_element_by_xpath_retry(driver, '//*[@id="productTitle"]')
        title_data = title_element.text
        # 获取五点
        five_detail_data = []
        i = 3
        five_detail_data_xpath = '//*[@id="feature-bullets"]/ul/li[2]/span'
        while self.element_exist_by_xpath_retry(driver, five_detail_data_xpath, 10):
            five_detail_data_element = self.get_element_by_xpath_retry(driver, five_detail_data_xpath)
            five_detail_data.append(five_detail_data_element.text.replace('\n', ''))
            five_detail_data_xpath = '//*[@id="feature-bullets"]/ul/li[' + str(i) + ']/span'
            i += 1
        # 获取描述
        detail_data = ''
        if self.element_exist_by_xpath_retry(driver, '//*[@id="productDescription"]/p', 5):
            detail_data_elements = self.get_elements_by_xpath_retry(driver, '//*[@id="productDescription"]/p')
            for detail_data_element in detail_data_elements:
                if detail_data_element.text is not None:
                    detail_data += detail_data_element.text.replace('\n', '')
        # 查询商品类目链接
        category_url = ''
        url_span_index = 1
        category_url_xpath = '//*[@class="a-color-secondary a-size-base prodDetSectionEntry"]/../td/span/span[' + str(url_span_index) + ']/a'
        category_url_xpath_last = ''
        while self.element_exist_by_xpath_retry(driver, category_url_xpath, 5):
            category_url_xpath_last = category_url_xpath
            url_span_index += 1
            category_url_xpath = '//*[@class="a-color-secondary a-size-base prodDetSectionEntry"]/../td/span/span[' + str( url_span_index) + ']/a'
        if self.element_exist_by_xpath_retry(driver, category_url_xpath_last, 1):
            category_url_element = self.get_element_by_xpath_retry(driver, category_url_xpath_last)
            category_url = category_url_element.get_attribute('href') + '?language=en_US'
            # 去除中文
            category_url = category_url.replace('-/zh/', '')
            if category_url in self.goods_category_url_num_map:
                self.goods_category_url_num_map[category_url] = self.goods_category_url_num_map[category_url] + 1
            else:
                self.goods_category_url_num_map[category_url] = 1
        driver.close()
        data = [title_data, detail_data, ','.join(five_detail_data), category_url]
        return [url, data]

# 亚马逊获取商品信息线程
class amazon_goods_thread(threading.Thread):
    def __init__(self, thread_name, country, url, thread_object):
        threading.Thread.__init__(self)
        self.thread_name = thread_name
        self.country = country
        self.url = url
        self.thread_object = thread_object
    def run(self):
        print ("开始线程: " + self.thread_name)
        self.result = self.thread_object.get_amazon_good_info(self.country, self.url)
        print ("结束线程: " + self.thread_name)
    def get_result(self):
        try:
            return self.result
        except Exception:
            print('线程未正常返回')
            return []

# 亚马逊获取商品信息线程
class amazon_goods_thread_selenium(threading.Thread):
    def __init__(self, thread_name, url, thread_object):
        threading.Thread.__init__(self)
        self.thread_name = thread_name
        self.url = url
        self.thread_object = thread_object
    def run(self):
        print ("开始线程: " + self.thread_name)
        self.result = self.thread_object.get_amazon_good_info_selenium(self.url)
        print ("结束线程: " + self.thread_name)
    def get_result(self):
        try:
            return self.result
        except Exception:
            print('线程未正常返回')
            return []

# 卖家精灵下载excel线程
class amazon_excel_thread(threading.Thread):
    def __init__(self, thread_name, file_path, cookie, keys, country, thread_object):
        threading.Thread.__init__(self)
        self.thread_name = thread_name
        self.file_path = file_path
        self.cookie = cookie
        self.keys = keys
        self.country = country
        self.thread_object = thread_object
    def run(self):
        print ("开始线程: " + self.thread_name)
        self.thread_object.download_excel(self.file_path, self.cookie, self.keys, self.country)
        print ("结束线程: " + self.thread_name)

# 生成csv文件夹名称
package_name = 'record weight'
# 关键字
key = 'record weight'
# 国家
country = 0
s = handle(package_name)
s.get_amazon_info(key, country)
s.get_amazon_key_word()
s.export_goods_csv(key + '_商品信息')
s.export_keyword_csv(key + '_关键字信息')

# s.get_amazon_good_info(country, 'https://www.amazon.com/Retekess-Cassette-Walkman-Reverse-Recording/dp/B0897Q3CPV/ref=zg_bs_172628_48/141-6156923-0779644?_encoding=UTF8&psc=1&refRID=3SPWVYS0W6MSZ16ZBE4J&language=en_US')