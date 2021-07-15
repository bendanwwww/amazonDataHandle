# 亚马逊数据处理工具

from selenium import webdriver
import time
import requests
from lxml import etree
import threading
import os
import csv
import random

class handle(object):
    name = 'amazon'
    code_path = os.path.abspath(os.path.dirname(__file__))
    driver_path = code_path + '/chromedriver_bak'
    url_one = 'https://xp.sellermotor.com/selection/index/market-insight'

    url_three = 'https://www.sellersprite.com/v2/keyword-miner/dynamic'

    amazon_url = 'https://www.amazon{0}?language=es_US'
    amazon_search_url = 'https://www.amazon.com/s?k={0}&language=en_US'
    amazon_participle_url = 'https://www.amz123.com/tools-wordcounter'

    url_three_country_dict = {0: 'US', 1: 'JP', 2: 'UK', 3: 'DE', 4: 'FR', 5: 'IT', 6: 'ES', 7: 'CA'}

    country_name_dict = {0: '美国', 1: '德国', 2: '法国', 3: '西班牙', 4: '意大利'}
    country_post_code_dict = {0: '10010', 1: '10115', 2: '75000', 3: '66030', 4: '04810'}
    country_url_dict = {0: '.com', 1: '.de', 2: '.fr', 3: '.es', 4: '.it'}

    # 尽量绕过amazon反爬
    def_cookie = 'session-id=141-0198602-5971905; session-id-time=2082787201l; skin=noskin; ubid-main=135-4979259-9456307; x-amz-captcha-1=1626333555817073; x-amz-captcha-2=Fh7ePzl89HNO2y/4YweOKg==; session-token=SHYIjafRjej7PZ0GTg1dQM8dpy3IFEKy557HttuHVB+xzjr++MlJRqZb4GuiRdafbt2+yRNEeYA7Ws9khV8jIRNo3bKw5JB9VuPyWhko/XtoVHk8J9Jdk66N364R1LgnwxrQxe9jqzXfRqRVqFsG2BuZzELbRkbfpe4a/FkKSEcocr+4MaRHm389bqe+yBbo; lc-main=en_US; i18n-prefs=USD; csm-hit=tb:VEXVVB8CM4BRPS90V52H+s-4A9M9F573TW3GHH27K5N|1626330696587&t:1626330696587&adb:adblk_no'
    def_ua = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
    cookie_list = []
    user_agent_list = []
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
    var_word_group_list = []

    # 需要查询的类目链接
    goods_category_url_set = set()
    # 亚马逊标题关键词
    goods_data_key_map = {}
    # 亚马逊商品信息 根据关键字分类
    category_goods_data_map = {}

    # 爬取亚马逊信息
    def get_amazon_info(self, key, country):
        # 亚马逊地址
        amazon_search_url = self.amazon_search_url.format(key)
        # 国家邮编
        country_post_code = self.country_post_code_dict[country]
        # 打开亚马逊页面
        driver = webdriver.Chrome(self.driver_path)
        driver.get(amazon_search_url)
        # 获取一下cookie
        self.get_amazon_cookies(driver)
        # 获取一下ua
        self.get_ie_ua(driver)
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
        # 获取top100商品
        goods_url_set = set()
        goods_elements = self.get_elements_by_tag_class_retry(driver, 's-no-outline')
        page = 2
        while len(goods_elements) > 0 and len(goods_url_set) < 100:
            for goods_element in goods_elements:
                goods_url_set.add(goods_element.get_attribute('href') + '&language=en_US')
                if len(goods_url_set) == 100:
                    break
            # 如果商品不足100个 则点击下一页
            if len(goods_url_set) < 100:
                driver.execute_script('window.location.href="' + amazon_search_url + '&page=' + str(page) + '"')
                goods_elements = self.get_elements_by_tag_class_retry(driver, 's-no-outline')
                page += 1
        # 关闭页面
        driver.close()
        # 爬取商品信息
        self.get_amazon_good_info_async(goods_url_set)
        # 根据类目获取各个类目下的top100商品
        category_goods_url_map = self.get_goods_url_by_category()
        # 爬取商品信息
        index = 0
        for category_url in category_goods_url_map:
            print('共' + str(len(category_goods_url_map)) + '个商品类目 正在查询第' + str(index) + '个')
            goods_data_map = self.get_amazon_good_info_async(category_goods_url_map[category_url])
            self.category_goods_data_map[category_url] = goods_data_map
            index += 1

    # 获取amazon cookie信息
    def get_amazon_cookies(self, driver):
        cookie_list = driver.get_cookies()
        if cookie_list is not None and len(cookie_list) > 0:
            cookies = ";".join([item['name'] + '=' + item['value'] for item in cookie_list])
            self.cookie_list.append(cookies)

    # 获取浏览器ua
    def get_ie_ua(self, driver):
        ua = driver.execute_script("return navigator.userAgent")
        self.user_agent_list.append(ua)

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

    # 导出csv文件
    def export_keyword_csv(self, file_name):
        path = self.code_path + '/' + str(time.time())
        # 创建文件夹
        folder = os.path.exists(path)
        if not folder:
            os.makedirs(path)
        # 写入csv文件
        with open(path + '/' + file_name + '.csv', 'w', encoding='utf_8_sig') as csvfile:
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
    def get_elements_by_tag_class_retry(self, driver, class_name):
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

    # 根据xpath不断尝试获取元素 阻塞
    def get_element_by_xpath_retry(self, driver, xpath):
        for i in range(1000000):
            try:
                element = driver.find_element_by_xpath(xpath)
                return element
            except:
                print('页面未加载完成 等待')
                time.sleep(0.1)

    # 根据xpath不断尝试获取元素 阻塞
    def get_elements_by_xpath_retry(self, driver, xpath):
        for i in range(1000000):
            try:
                elements = driver.find_elements_by_xpath(xpath)
                return elements
            except:
                print('页面未加载完成 等待')
                time.sleep(0.1)

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
                    if td_text is not None and len(td_text.split('. ')) == 2:
                        # 判断是否为数字或单个字母或介词
                        td_str = td_text.split('. ')[1]
                        if self.check_key_word(td_str):
                            data.append(td_str)
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
        for category_url in self.goods_category_url_set:
            print('共' + str(len(self.goods_category_url_set)) + '个类目 当前第' + str(index) + '个')
            category_goods_url_set = set()
            # 打开类目页面
            driver = webdriver.Chrome(self.driver_path)
            driver.get(category_url)
            # 获取一下cookie
            self.get_amazon_cookies(driver)
            goods_elements = self.get_elements_by_tag_class_retry(driver, 'a-text-normal')
            last_size = -1
            while len(goods_elements) > 0 and len(category_goods_url_set) < 100 and last_size != len(category_goods_url_set):
                last_size = len(category_goods_url_set)
                for goods_element in goods_elements:
                    category_goods_url_set.add(goods_element.get_attribute('href') + '&language=en_US')
                    if len(category_goods_url_set) == 100:
                        break
                # 如果商品不足100个 则点击下一页
                if len(category_goods_url_set) < 100:
                    self.click_element_by_xpath_retry(driver, '//*[@id="zg-center-div"]/div[2]/div/ul/li[4]', 5)
                    goods_elements = self.get_elements_by_tag_class_retry(driver, 'a-text-normal')
            category_goods_url_map[category_url] = category_goods_url_set
            index += 1
            # 关闭页面
            driver.close()
        return category_goods_url_map

    # 获取亚马逊商品信息 异步执行
    def get_amazon_good_info_async(self, urls):
        # 商品信息
        goods_data_map = {}
        thread_map = {}
        thread_key_list = []
        fail_url_list = []
        index = 0
        for url in urls:
            a_thread = amazon_goods_thread('共' + str(len(urls)) + '个页面 正在解析第' + str(index) + '个页面', url, self)
            a_thread.start()
            thread_map[url] = a_thread
            thread_key_list.append(url)
            time.sleep(0.5)
            index += 1
            # 控制并发度 5个线程同时执行
            if len(thread_key_list) >= 5:
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
    def get_amazon_good_info(self, url):
        cookie = ''
        if len(self.cookie_list) == 0:
            cookie = self.def_cookie
        else:
            cookie = random.choice(self.cookie_list)
        ua = ''
        if len(self.user_agent_list) == 0:
            ua = self.def_ua
        else:
            ua = self.user_agent_list[0]
        headers = {
            'authority': 'www.amazon.com',
            'cache-control': 'max-age=0',
            'rtt': '100',
            'downlink': '10',
            'ect': '4g',
            'sec-ch-ua': '" Not;A Brand";v="99", "Google Chrome";v="91", "Chromium";v="91"',
            'sec-ch-ua-mobile': '?0',
            'upgrade-insecure-requests': '1',
            'user-agent': ua,
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'sec-fetch-site': 'none',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-user': '?1',
            'sec-fetch-dest': 'document',
            'accept-language': 'zh-CN,zh;q=0.9',
            'cookie': cookie
        }
        url += '&language=en_US'
        try:
            resp = requests.get(url, headers=headers)
        except:
            return []
        html = etree.HTML(resp.text)
        # 获取标题
        title_data = ''
        title_data_html = html.xpath('//*[@class="a-size-large product-title-word-break"]')
        # 为了防止验证码 重试3次
        retry = 3
        while title_data == '' and retry > 0:
            if len(title_data_html) > 0 and title_data_html[0] is not None and title_data_html[0].text is not None:
                title_data = title_data_html[0].text.replace('\n', '')
            else:
                # 重试
                headers['cookie'] = random.choice(self.cookie_list)
                try:
                    resp = requests.get(url, headers=headers)
                except:
                    return []
                html = etree.HTML(resp.text)
            retry -= 1
        if title_data == '':
            # print('访问被拦截 ' + url)
            return []
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
            category_url = 'https://www.amazon.com' + category_url_html[0] + '?language=en_US'
            # 去除中文
            category_url = category_url.replace('-/zh/', '')
            self.goods_category_url_set.add(category_url)
        data = [title_data, detail_data, ','.join(five_detail_data), category_url]
        return [url, data]

    # 获取亚马逊商品信息
    def get_amazon_good_info_selenium(self, url):
        # 打开亚马逊商品页面
        driver = webdriver.Chrome(self.driver_path)
        driver.get(url)
        # 获取标题
        title_data = ''
        title_element = self.get_element_by_xpath_retry(driver, '//*[@id="productTitle"]')
        title_data = title_element.text
        # 获取五点
        five_detail_data = []
        i = 3
        five_detail_data_xpath = '//*[@id="feature-bullets"]/ul/li[2]/span'
        while self.element_exist_by_xpath_retry(driver, five_detail_data_xpath, 20):
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
            self.goods_category_url_set.add(category_url)
        driver.close()
        data = [title_data, detail_data, ','.join(five_detail_data), category_url]
        return [url, data]

# 亚马逊获取商品信息线程
class amazon_goods_thread(threading.Thread):
    def __init__(self, thread_name, url, thread_object):
        threading.Thread.__init__(self)
        self.thread_name = thread_name
        self.url = url
        self.thread_object = thread_object
    def run(self):
        print ("开始线程: " + self.thread_name)
        self.result = self.thread_object.get_amazon_good_info(self.url)
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

# 关键字
key = 'record weight'
# 国家
country = 0
s = handle()
s.get_amazon_info(key, country)
s.get_amazon_key_word()
s.export_keyword_csv(key)

# s.get_amazon_good_info_selenium('https://www.amz123.com/tools-wordcounter')