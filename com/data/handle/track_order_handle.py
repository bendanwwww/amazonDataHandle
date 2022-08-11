#coding=gbk

import time
import os
import json

def read_file(filepath):
    with open(filepath) as fp:
        content = fp.read();
    return content

code_path = os.path.abspath(os.path.dirname(__file__))

ret = read_file(code_path + '/test.csv').split('\n')
url = 'https://t.17track.net/restapi/track'

track_order = []
index = 0
last = 0
for r in ret:
    if index < last:
        index += 1
        continue
    track_order.append(r)
    index += 1

headers = {}
headers['referer'] = 'https://t.17track.net/zh-cn'
headers['cookie'] = 'country=CN; _yq_bid=G-B8E4326D94D89642; v5_Culture=zh-cn; _ga=GA1.2.285024683.1660130328; _gid=GA1.2.1634478300.1660130328; __gads=ID=e4e6a71a3b12e5e4:T=1660130333:S=ALNI_MYX91hQgUJ8ZceV1mybZNfFasXc7w; __gpi=UID=00000876d1c51ace:T=1660130333:RT=1660130333:S=ALNI_MbrMjo2UWAdh4gNW38M-pw5KgqbkQ; crisp-client%2Fsession%2F115772b1-4fc7-471c-a364-05246aac2f53=session_24d6836e-0a85-4594-ae36-986780cb731f; _ati=163270314626; uid=80915BFE84E94E7BBD72D306C4206F4C; _yq_rc_=yq.5.301.zh-cn.0.0.4095936322528469225; v5_TranslateLang=zh-Hans; _gat_cnGa=1; Last-Event-ID=657572742f6335332f36363964646237383238312f363339376239356664343a303731373638343331323a65736c61663a6f676f6c2d746c75616665642d71792073782d656c6269736976206f676f6c2d646e6172622d72616276616e192332a584ad6fecfa8e'
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

# 物流商目前全为DPD
org = 'DPD'

# 先执行一次 减少报错
index = 0
for order_data in track_order:
    order = order_data
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
-H 'cookie: country=CN; _yq_bid=G-B8E4326D94D89642; v5_Culture=zh-cn; _ga=GA1.2.285024683.1660130328; _gid=GA1.2.1634478300.1660130328; __gads=ID=e4e6a71a3b12e5e4:T=1660130333:S=ALNI_MYX91hQgUJ8ZceV1mybZNfFasXc7w; __gpi=UID=00000876d1c51ace:T=1660130333:RT=1660130333:S=ALNI_MbrMjo2UWAdh4gNW38M-pw5KgqbkQ; crisp-client/session/115772b1-4fc7-471c-a364-05246aac2f53=session_24d6836e-0a85-4594-ae36-986780cb731f; _ati=163270314626; uid=80915BFE84E94E7BBD72D306C4206F4C; _yq_rc_=yq.5.301.zh-cn.0.0.4095936322528469225; v5_TranslateLang=zh-Hans; v5_HisExpress=100007; Last-Event-ID=657572742f6435332f64663935336437383238312f343966393038383031633a303731373638343331323a65736c61663a6c742d696e612d7179207466656c2d756e656d2d6e776f64706f726420756e656d2d6e776f64706f72642223132eda1909c9f86e' \
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
    print("预处理: " + str(index))
    index += 1
    time.sleep(0.5)


index = 0
res_data = []
error_order = []
for order_data in track_order:
    order = order_data
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
-H 'cookie: country=CN; _yq_bid=G-B8E4326D94D89642; v5_Culture=zh-cn; _ga=GA1.2.285024683.1660130328; _gid=GA1.2.1634478300.1660130328; __gads=ID=e4e6a71a3b12e5e4:T=1660130333:S=ALNI_MYX91hQgUJ8ZceV1mybZNfFasXc7w; __gpi=UID=00000876d1c51ace:T=1660130333:RT=1660130333:S=ALNI_MbrMjo2UWAdh4gNW38M-pw5KgqbkQ; crisp-client/session/115772b1-4fc7-471c-a364-05246aac2f53=session_24d6836e-0a85-4594-ae36-986780cb731f; _ati=163270314626; uid=80915BFE84E94E7BBD72D306C4206F4C; _yq_rc_=yq.5.301.zh-cn.0.0.4095936322528469225; v5_TranslateLang=zh-Hans; v5_HisExpress=100007; Last-Event-ID=657572742f6435332f64663935336437383238312f343966393038383031633a303731373638343331323a65736c61663a6c742d696e612d7179207466656c2d756e656d2d6e776f64706f726420756e656d2d6e776f64706f72642223132eda1909c9f86e' \
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
    time.sleep(2)
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
-H 'cookie: country=CN; _yq_bid=G-B8E4326D94D89642; v5_Culture=zh-cn; _ga=GA1.2.285024683.1660130328; _gid=GA1.2.1634478300.1660130328; __gads=ID=e4e6a71a3b12e5e4:T=1660130333:S=ALNI_MYX91hQgUJ8ZceV1mybZNfFasXc7w; __gpi=UID=00000876d1c51ace:T=1660130333:RT=1660130333:S=ALNI_MbrMjo2UWAdh4gNW38M-pw5KgqbkQ; crisp-client/session/115772b1-4fc7-471c-a364-05246aac2f53=session_24d6836e-0a85-4594-ae36-986780cb731f; _ati=163270314626; uid=80915BFE84E94E7BBD72D306C4206F4C; _yq_rc_=yq.5.301.zh-cn.0.0.4095936322528469225; v5_TranslateLang=zh-Hans; v5_HisExpress=100007; Last-Event-ID=657572742f6435332f64663935336437383238312f343966393038383031633a303731373638343331323a65736c61663a6c742d696e612d7179207466656c2d756e656d2d6e776f64706f726420756e656d2d6e776f64706f72642223132eda1909c9f86e' \
--data-raw '{\"data\": [{\"num\": \"""" + order + """\",\"fc\": """+ str(track_org_map[org]) +""",\"sc\": 0}],\"guid\": \""""+ guid +"""\",\"timeZoneOffset\": -480}' \
--compressed
"""
    res = json.loads(os.popen(curl).readlines()[0])
    try:
        # 订单状态
        track_status_type = res['dat'][0]['track']['e']
        track_status = track_status_map[str(track_status_type)]
        # 订单节点时间
        track_time_list = res['dat'][0]['track']['z1']
        track_time_timestamp_list = []
        for track_time in track_time_list:
            timeArray = time.strptime(track_time['a'], "%Y-%m-%d %H:%M")
            timeStamp = int(time.mktime(timeArray))
            track_time_timestamp_list.append(timeStamp)
        # 判断时间
        # 若只有一个节点
        if len(track_time_timestamp_list) == 1 and track_status_type != 40:
            if int(time.time()) - timeStamp > 3 * 24 * 60 * 60:
                res_data.append([str(order).replace(' ', ''), str(track_status).replace(' ', ''), '只有一个物流节点且未完成配送'])
        # 若有多个节点
        if len(track_time_timestamp_list) > 1:
            # 判断是否有节点相隔超过7天
            is_set = False
            for i in range(1, len(track_time_timestamp_list)):
                if track_time_timestamp_list[i - 1] - track_time_timestamp_list[i] > 7 * 24 * 60 * 60:
                    res_data.append([str(order).replace(' ', ''), str(track_status).replace(' ', ''), '有相邻两个物流节点间隔时间超过7天'])
                    is_set = True
                    break
            # 判断最近时间节点据今是否超过7天且为非异常状态
            if not is_set and track_status_type != 40 and int(time.time()) - track_time_timestamp_list[len(track_time_timestamp_list) - 1] > 7 * 24 * 60 * 60:
                res_data.append([str(order).replace(' ', ''), str(track_status).replace(' ', ''), '物流节点近7天未更新且为未送达状态'])
        #
        # if int(track_status_type) < 35 and int(time.time()) - timeStamp > 3 * 24 * 60 * 60:
        #     track_time_str = '超过' + str(int((int(time.time()) - timeStamp) / (24 * 60 * 60))) + '天 最后更新时间 ' + track_time
        # res_data.append([str(order).replace(' ', ''), str(track_status).replace(' ', ''), track_time_str, org.replace(' ', '')])
    except Exception as e:
        error_order.append(order)
        print(e)
        # res_data.append([str(order).replace(' ', ''), '', '', org.replace(' ', '')])
    print(index)
    index += 1

filename = code_path + '/test_20220811.txt'
with open(filename, 'w') as file_object:
    for d in res_data:
        file_object.write(d[0] + '\t' + d[1] + '\t' + d[2] + '\n')

filename = code_path + '/test_20220811_error.txt'
with open(filename, 'w') as file_object:
    for d in error_order:
        file_object.write(d + '\n')

