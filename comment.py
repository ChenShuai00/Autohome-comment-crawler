from urllib.parse import urlparse
import json
import os
import aiohttp
import asyncio
import aiofiles
from bs4 import BeautifulSoup
import re
import time


# 从汽车口碑url提取汽车ID
async def parse_car_url(url):
    url = url
    parsed_url = urlparse(url)
    path_segments = parsed_url.path.split('/', 2)  # Split the path into segments
    # Extract the number part, assuming it's always after the first '/'
    seriesld = path_segments[1] if len(path_segments) > 1 else None
    syearId = path_segments[2] if len(path_segments) > 1 else None
    return seriesld, syearId


def parse_comment_list_url(seriesld, pageIndex, syearId):
    return f"https://koubeiipv6.app.autohome.com.cn/pc/series/list?pm=3&seriesId={seriesld}&pageIndex={pageIndex}&syearId={syearId}"


async def request_url(url):
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,'
                  'application/signed-exchange;v=b3;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'Cache-Control': 'max-age=0',
        'Cookie': 'fvlid=1710042953599ZH4TIO1A0T; sessionid=9023F4D1-41EA-4C99-AD29-AF7BB6B47700%7C%7C2024-03-10+11'
                  '%3A56%3A01.940%7C%7Cwww.baidu.com;autoid=ce35a41e6e8a51ce7adac9508b100e63; '
                  'sessionuid=9023F4D1-41EA-4C99-AD29-AF7BB6B47700%7C%7C2024-03-10+11%3A56%3A01.940%7C%7Cwww.baidu'
                  '.com; __utma=1.538430978.1710042958.1710042958.1710042958.1; '
                  '__utmz=1.1710042958.1.1.utmcsr=autohome.com.cn|utmccn=(referral)|utmcmd=referral|utmcct=/; '
                  'pcpopclub=8ca94456a8164a0d963c73055b45f4380ea0f376; '
                  'clubUserShow=245429110|0|1|Jenson20|0|0|0|/g3/M07/02/53'
                  '/120X120_0_q87_autohomecar__ChsEm19Hd66AAEVzAACOJPdlhvA053.jpg|2024-03-10 11:57:03|0; '
                  'autouserid=245429110; __ah_uuid_ng=u_245429110; sessionuserid=245429110; '
                  'sessionlogin=7ba74c32682b426db63d703e1264e8ef0ea0f376; ahsids=6298_5761; '
                  'historyseries=6298%2C5761; sessionip=3.0.139.196; area=999999; ahpvno=65; v_no=32; '
                  'visit_info_ad=9023F4D1-41EA-4C99-AD29-AF7BB6B47700||165ACEED-D266-4FC9-8378-5951484AA97A||-1||-1'
                  '||32; ref=www.baidu.com%7C0%7C0%7C0%7C2024-03-19+19%3A25%3A33.016%7C2024-03-10+11%3A56%3A01.940',
        'Sec-Ch-Ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Microsoft Edge";v="122"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0',
        'X-Forwarded-For': '4.2.2.2'
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.ok:
                response_text = await response.text()
                return response_text
            else:
                return None


async def save_json(folder_name, filename, dict):
    if not os.path.exists(folder_name):
        os.mkdir(folder_name)
    json_data = json.dumps(dict, indent=4)
    async with aiofiles.open(filename, 'w') as file:
        await file.write(json_data)


async def extract_comment(html):
    soup = BeautifulSoup(html, 'html.parser')
    attribute_comment_list = []
    for div in soup.find_all('div', class_='kb-item'):
        split_text = div.text.split('\n', 2)
        # 提取属性
        attribute = split_text[1]
        text = "".join(split_text[2:]).replace('\n', '').replace(' ', '')
        # 去除开头数字
        text = re.sub(r'^\d+', '', text)
        attribute_comment_list.append({"attribute": attribute, "commment": text})
    return attribute_comment_list


async def main(url):
    # 输入汽车口碑url提取汽车ID
    url = url
    seriesld, syearId = await parse_car_url(url)
    pageIndex = 1
    while True:
        comment_list_url = parse_comment_list_url(seriesld, pageIndex, syearId)
        print(f"**********************爬取第{pageIndex}页评论列表url**************************\n")
        print(comment_list_url)
        response_text = await request_url(comment_list_url)
        if response_text:
            response_dict = json.loads(response_text)
            users_comment_list = response_dict["result"]["list"]
            syearld = users_comment_list[0]["syearId"]
            if not len(users_comment_list) or int(syearld) != int(syearId):
                break
            # 将list存储为json文件
            folder_name = f"{seriesld}"
            users_comment_list_filename = f"./{folder_name}/pageIndex{pageIndex}.json"
            await save_json(folder_name, users_comment_list_filename,
                            dict={f"pageIndex{pageIndex}": users_comment_list})
            print(f"**********************保存'{users_comment_list_filename}'**************************\n")
            total_comemnt_dic_list = []
            for user_index in range(len(users_comment_list)):
                showid = users_comment_list[user_index]["showId"]
                username = users_comment_list[user_index]["username"]
                comment_detail_url = f"https://k.autohome.com.cn/detail/view_{showid}.html"
                print(f"**********************爬取'{username}'详细评论**************************")
                print(comment_detail_url)
                comment_detail_html = await request_url(comment_detail_url)
                attribute_comment_list = await extract_comment(comment_detail_html)
                comemnt_dict = {"username": username, "attribute_comment_list": attribute_comment_list}
                total_comemnt_dic_list.append(comemnt_dict)
                time.sleep(5)
            detail_comment_filename = f"./{folder_name}/pageIndex{pageIndex}comment.json"
            await save_json(folder_name, detail_comment_filename,
                            dict={f"pageIndex{pageIndex}comment": total_comemnt_dic_list})
            print(f"**********************保存'{detail_comment_filename}'**************************\n")
            print(f"**********************已爬取'{pageIndex * len(users_comment_list)}'**************************\n")
            pageIndex = pageIndex + 1
        else:
            print(f"**********************爬取完成**************************\n")


if __name__ == "__main__":
    link = "https://k.autohome.com.cn/5769/19808#pvareaid=101477"

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main(link))
    except Exception as e:
        print(f"Caught exception: {e}")

