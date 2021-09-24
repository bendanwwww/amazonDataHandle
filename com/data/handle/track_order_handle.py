#coding=gbk

import time
import os
import json

def read_file(filepath):
    with open(filepath) as fp:
        content = fp.read();
    return content

code_path = os.path.abspath(os.path.dirname(__file__))

ret = read_file(code_path + '/0828.csv').split('\n')
url = 'https://t.17track.net/restapi/track'

track_order = []
index = 0
first = 0
last = 8000
for r in ret:
    if index < first:
        index += 1
        continue
    if index >= last:
        break
    if index > 0 and len(r.split(',')) == 4:
        data = r.split(',')
        track_order.append([data[0], data[3]])
    index += 1

headers = {}
headers['referer'] = 'https://t.17track.net/zh-cn'
headers['cookie'] = 'v5_TranslateLang=zh-Hans; v5_Culture=zh-cn; _yq_bid=G-6A5194650B1B3747; _ga=GA1.2.700929545.1629363921; _gid=GA1.2.1579923650.1629363921; __gads=ID=66213d92ee802fdd:T=1629363921:S=ALNI_MaqSAs12-ikPQOFQn_wcyyP7ub-8w; Last-Event-ID=657572742f3064332f38366164616264356237312f306463623132363138353a343536393939363034333a65736c61663a737070612d646165682d71792034322d6e6f6349756e656d2d72616276616e2d717931336412ede0453151a'
headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
headers['sec-ch-ua'] = '"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"'
headers['user-agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36'
headers['x-requested-with'] = 'XMLHttpRequest'
headers['accept'] = 'application/json, text/javascript, */*; q=0.01'

track_status_map = {
        "00": "查询不到",
        "10": "运输途中",
        "20": "运输过久",
        "30": "到达待取",
        "35": "投递失败",
        "40": "成功签收",
        "50": "可能异常"
    }

track_org_map = {
        "DPD": 100007,
        "DHL": 7041
    }

index = 0
res_data = []
for order_data in track_order:
    order = order_data[0]
    org = order_data[1]
    curl = """
curl 'https://t.17track.net/restapi/track' \
-H 'authority: t.17track.net' \
-H 'sec-ch-ua: "Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"' \
-H 'accept: application/json, text/javascript, */*; q=0.01' \
-H 'x-requested-with: XMLHttpRequest' \
-H 'sec-ch-ua-mobile: ?0' \
-H 'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36' \
-H 'content-type: application/x-www-form-urlencoded; charset=UTF-8' \
-H 'origin: https://t.17track.net' \
-H 'sec-fetch-site: same-origin' \
-H 'sec-fetch-mode: cors' \
-H 'sec-fetch-dest: empty' \
-H 'referer: https://t.17track.net/zh-cn' \
-H 'accept-language: zh-CN,zh;q=0.9' \
-H 'cookie: v5_TranslateLang=zh-Hans; v5_Culture=zh-cn; _yq_bid=G-6A5194650B1B3747; _ga=GA1.2.700929545.1629363921; _gid=GA1.2.1579923650.1629363921; __gads=ID=66213d92ee802fdd:T=1629363921:S=ALNI_MaqSAs12-ikPQOFQn_wcyyP7ub-8w; v5_HisExpress=07041; Last-Event-ID=657572742f3739332f33383834383632366237312f386430393736656137623a343536393939363034333a65736c61663a7261626c6f6f742d72616276616e2d71792074686769722d7261626c6f6f742d72616276616e2074686769722d72616276616e207261626c6f6f742d72616276616e2076616e113706d4d6918044dc8' \
--data-raw '{\"data\": [{\"num\": \"""" + order + """\",\"fc\": """+ str(track_org_map[org]) +""",\"sc\": 0}],\"guid\": \"\",\"timeZoneOffset\": -480}' \
--compressed
"""
    res = json.loads(os.popen(curl).readlines()[0])
    # 获取guid
    try:
        guid = res['g']
    except Exception as e:
        print(e)
        continue
    time.sleep(1)
    curl = """
curl 'https://t.17track.net/restapi/track' \
-H 'authority: t.17track.net' \
-H 'sec-ch-ua: "Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"' \
-H 'accept: application/json, text/javascript, */*; q=0.01' \
-H 'x-requested-with: XMLHttpRequest' \
-H 'sec-ch-ua-mobile: ?0' \
-H 'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36' \
-H 'content-type: application/x-www-form-urlencoded; charset=UTF-8' \
-H 'origin: https://t.17track.net' \
-H 'sec-fetch-site: same-origin' \
-H 'sec-fetch-mode: cors' \
-H 'sec-fetch-dest: empty' \
-H 'referer: https://t.17track.net/zh-cn' \
-H 'accept-language: zh-CN,zh;q=0.9' \
-H 'cookie: v5_TranslateLang=zh-Hans; v5_Culture=zh-cn; _yq_bid=G-6A5194650B1B3747; _ga=GA1.2.700929545.1629363921; _gid=GA1.2.1579923650.1629363921; __gads=ID=66213d92ee802fdd:T=1629363921:S=ALNI_MaqSAs12-ikPQOFQn_wcyyP7ub-8w; v5_HisExpress=07041; Last-Event-ID=657572742f3739332f33383834383632366237312f386430393736656137623a343536393939363034333a65736c61663a7261626c6f6f742d72616276616e2d71792074686769722d7261626c6f6f742d72616276616e2074686769722d72616276616e207261626c6f6f742d72616276616e2076616e113706d4d6918044dc8' \
--data-raw '{\"data\": [{\"num\": \"""" + order + """\",\"fc\": """+ str(track_org_map[org]) +""",\"sc\": 0}],\"guid\": \""""+ guid +"""\",\"timeZoneOffset\": -480}' \
--compressed
"""
    res = json.loads(os.popen(curl).readlines()[0])
    try:
        track_status_type = res['dat'][0]['track']['e']
        track_status = track_status_map[str(track_status_type)]
        track_time = res['dat'][0]['track']['z0']['a']
        track_time_str = ''
        timeArray = time.strptime(track_time, "%Y-%m-%d %H:%M")
        timeStamp = int(time.mktime(timeArray))
        if int(track_status_type) < 35 and int(time.time()) - timeStamp > 3 * 24 * 60 * 60:
            track_time_str = '超过' + str(int((int(time.time()) - timeStamp) / (24 * 60 * 60))) + '天 最后更新时间 ' + track_time
        res_data.append([str(order).replace(' ', ''), str(track_status).replace(' ', ''), track_time_str, org.replace(' ', '')])
    except Exception as e:
        print(e)
        res_data.append([str(order).replace(' ', ''), '', '', org.replace(' ', '')])
    print(index)
    index += 1

filename = code_path + '/track_order_0828.txt'
with open(filename, 'w') as file_object:
    for d in res_data:
        file_object.write(d[0] + '\t' + d[1] + '\t' + d[2] + '\t' + d[3] + '\n')

