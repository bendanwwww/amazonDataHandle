# 亚马逊数据处理工具

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
import time
import requests
from lxml import etree
import threading
import os
import csv

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

    # 亚马逊商品信息
    goods_data_map = {}
    # 需要查询的类目链接
    goods_category_url_set = set()
    # 亚马逊标题关键词
    goods_data_key_map = {}

    # 爬取亚马逊信息
    def getAmazonInfo(self, key, country):
        # 亚马逊地址
        amazon_search_url = self.amazon_search_url.format(key)
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
        self.click_element_by_xpath_retry(driver, '//*[@id="a-popover-4"]/div/div[2]/span/span', 5)
        # 获取top100商品
        goods_url_list = []
        goods_elements = self.get_elements_by_tag_class_retry(driver, 's-no-outline')
        while len(goods_elements) > 0 and len(goods_url_list) < 100:
            for goods_element in goods_elements:
                goods_url_list.append(goods_element.get_attribute('href'))
                if len(goods_url_list) == 100:
                    break
            # 如果商品不足100个 则点击下一页
            if len(goods_url_list) < 100:
                self.click_element_by_xpath_retry(driver, '//*[@id="search"]/div[1]/div/div[1]/div/span[3]/div[2]/div[67]/span/div/div/ul/li[7]', 5)
                goods_elements = self.get_elements_by_tag_class_retry(driver, 's-no-outline')
        # 关闭页面
        driver.close()
        # 爬取商品信息
        self.get_amazon_good_info_async(goods_url_list)
        # 根据类目获取各个类目下的top100商品
        # category_goods_url_list = self.get_goods_url_by_category()
        # 爬取商品信息
        # self.get_amazon_good_info_async(category_goods_url_list)


    # 根据商品标题获取关键字
    def getAmazonKeyWord(self):
        # 打开分词网页
        driver = webdriver.Chrome(self.driver_path)
        driver.get(self.amazon_participle_url)
        # 遍历map 查询关键词
        index = 0
        for url in self.goods_data_map:
            print('共' + str(len(self.goods_data_map)) + '个关键词列表 正在查询第' + str(index) + '个')
            goods_data = self.goods_data_map[url]
            title = goods_data[0]
            self.goods_data_key_map[url] = [self.getKeyWord(driver, title)]
            index += 1
        # 关闭网页
        driver.close()

    # 导出csv文件
    def export_csv(self, key):
        path = self.code_path + str(time.time())
        # 创建文件夹
        folder = os.path.exists(path)
        if not folder:
            os.makedirs(path)
        # 写入csv文件
        with open(path + '/' + key + '.csv', 'w', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            # 先写入columns_name
            writer.writerow(['商品标题', '链接', '描述', '五点', '关键字列表(1个单词)', '关键字列表(2个单词)', '关键字列表(3个单词)'])
            # 写入多行用writerows
            for url in self.goods_data_map:
                key_word_list = []
                if url in self.goods_data_key_map:
                    key_word_list = self.goods_data_key_map[url]
                writer.writerow([self.goods_data_map[url][0], url, self.goods_data_map[url][1], self.goods_data_map[url][2],
                                  ','.join('%s' %id for id in key_word_list[0]), ','.join('%s' %id for id in key_word_list[1]), ','.join('%s' %id for id in key_word_list[2])])


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
        cycle_num = 10
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
        self.download_excel_async(goods_data_key_map, url_three_cookie, country)
        # 关闭第三个网页
        driver_three.close()

    # 下载最终excel 异步执行
    def download_excel_async(self, goods_data_key_map, url_three_cookie, country):
        path = self.code_path + str(time.time())
        # 创建文件夹
        folder = os.path.exists(path)
        if not folder:
            os.makedirs(path)
        print('共' + str(len(goods_data_key_map)) + '个url')
        # thread_list = []
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
                # excel_thread.start()
                excel_thread.run()
                # thread_list.append(excel_thread)
                time.sleep(1)
                data_index += 1
        #     # 控制并发度 1个线程同时执行
        #     if len(thread_list) >= 1:
        #         while thread_list:
        #             thread_list.pop().join()
            index += 1
        # while thread_list:
        #     thread_list.pop().join()


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
                # ActionChains(driver).click(element).perform()
                return
                # element.click()
            except:
                # print(RuntimeError)
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
        # 切换关键字个数
        click_element = driver.find_element_by_xpath('//*[@id="ui-id-' + str(num) + '"]')
        click_element.click()
        # 获取结果
        try:
            table_element = driver.find_element_by_xpath('//*[@id="keyword_density-tab-' + str(num) + '-table"]/tbody')
        except:
            return data
        if table_element is not None:
            tr_elements = table_element.find_elements_by_tag_name('tr')
            for tr in tr_elements:
                td_elements = tr.find_elements_by_tag_name('td')
                if len(td_elements) == 2:
                    td_text = td_elements[0].text
                    td_number = 1
                    if td_elements[1].text is not None:
                        td_number = int(td_elements[1].text.split(' (')[0])
                    if td_text is not None and len(td_text.split('. ')) == 2:
                        # 判断td_number是否大于1
                        if int(td_number) > 1:
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
        goods_url_list = []
        index = 0
        for category_url in self.goods_category_url_set:
            print('共' + str(len(self.goods_category_url_set)) + '个类目 当前第' + str(index) + '个')
            category_goods_url_list = []
            # 打开类目页面
            driver = webdriver.Chrome(self.driver_path)
            driver.get(category_url)
            goods_elements = self.get_elements_by_tag_class_retry(driver, 'a-link-normal')
            while len(goods_elements) > 0 and len(category_goods_url_list) < 100:
                for goods_element in goods_elements:
                    category_goods_url_list.append(goods_element.get_attribute('href'))
                    if len(category_goods_url_list) == 100:
                        break
                # 如果商品不足100个 则点击下一页
                if len(category_goods_url_list) < 100:
                    self.click_element_by_xpath_retry(driver, '//*[@id="zg-center-div"]/div[2]/div/ul/li[4]', 5)
                    goods_elements = self.get_elements_by_tag_class_retry(driver, 'a-link-normal')
            goods_url_list += category_goods_url_list
            index += 1
            # 关闭页面
            driver.close()
        return goods_url_list

    # 获取亚马逊商品信息 异步执行
    def get_amazon_good_info_async(self, urls):
        thread_list = []
        index = 0
        for url in urls:
            a_thread = amazon_goods_thread('共' + str(len(urls)) + '个页面 正在解析第' + str(index) + '个页面', url, self)
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
            'downlink': '10',
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
            'cookie': 'session-id=141-0198602-5971905; session-id-time=2082787201l; skin=noskin; ubid-main=135-4979259-9456307; sp-cdn="L5Z9:CN"; session-token=qJu4niG0cdup6NL0TC+J/w8lDwU0DO1YzQaCj6ZnrvACo+CBp3+/SfhygoXjs67xuJkAAxPKGHR0DnHN1UdAuN6DvIS9JYf4xDwHmEHcdFPZxHHxVIGcG7BKVB3CLm+SOyb7pInWI8g0MO1GVyJCyWffaZQNOJE3rAWJ2LL9DP6dj7iIX2LXjhvhyPcn4Fi6; lc-main=en_US; i18n-prefs=USD'
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
key = 'armchairs'
# 国家
country = 0
s = handle()
s.getAmazonInfo(key, country)
s.getAmazonKeyWord()
s.export_csv(key)
# s.get_amazon_good_info('https://www.amazon.com/Furmax-Assembled-Century-Plastic-Kitchen/dp/B075DCHX5G/ref=sr_1_5?dchild=1&keywords=chairs&qid=1626267682&sr=8-5&th=1')