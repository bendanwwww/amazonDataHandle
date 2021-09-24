#coding=gbk

import requests
from lxml import etree
import os
import xlrd
import csv

code_path = os.path.abspath(os.path.dirname(__file__))

def read_file(filepath):
    with open(filepath, encoding='utf8', errors='ignore') as fp:
        content = fp.read()
    return content

def xlsx_to_csv():
    workbook = xlrd.open_workbook(code_path + '/post_code.xlsx')
    table = workbook.sheet_by_index(0)
    with open(code_path + '/post_code.csv', 'w', encoding='utf-8') as f:
        write = csv.writer(f)
        for row_num in range(table.nrows):
            row_value = table.row_values(row_num)
            write.writerow(row_value)

def get_code(url, city, country):
    try:
        resp = requests.get(url, timeout=10).content.decode('utf-8')
    except Exception as e:
        print('失败 ' + url)
        print(e)
        return []
    html_text = resp
    html = etree.HTML(html_text)
    for i in range(1, 100):
        code_tr = html.xpath('/html/body/div[2]/div/div[2]/div[2]/div[3]/div/table/tbody/tr['+ str(i) +']')
        if len(code_tr) > 0:
            city_td_text = code_tr[0][1].text
            if city_td_text.lower() == city.lower():
                return [code_tr[0][2].text, code_tr[0][1].text]
        else:
            break
    if country == 'FR':
        code_tr = html.xpath('/html/body/div[2]/div/div[2]/div[2]/div[3]/div/table/tbody/tr[1]')
        if len(code_tr) > 0:
            return [code_tr[0][2].text, code_tr[0][1].text]
        else:
            return []
    return []


xlsx_to_csv()
ret = read_file(code_path + '/post_code.csv').split('\n')
url_map = {"DE": "https://www.nowmsg.com/findzip/de_postalcode.asp?CityName=", "IT": "https://www.nowmsg.com/findzip/it_postal_code.asp?CityName=", "FR": "https://www.nowmsg.com/findzip/fr_postal_code.asp?CityName="}

res_data = []
index = 0
for r in ret:
    data = []
    if index > 0 and len(r.split(',')) == 4:
        tmp = r.split(',')
        country = tmp[0]
        city = tmp[2]
        code = tmp[3]
        province_city = get_code(url_map[country] + str(code), city, country)
        if len(province_city) < 2:
            data = [country, tmp[1], city, code]
        else:
            data = [country, province_city[0], province_city[1], code]
        print(data)
        res_data.append(data)
    index += 1

filename = code_path + '/post_code.txt'
with open(filename, 'w', encoding='utf-8', errors='ignore') as file_object:
    for d in res_data:
        file_object.write(d[0] + '\t' + d[1] + '\t' + d[2] + '\t' + d[3] + '\n')