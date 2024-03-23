# 汽车之家口碑爬虫



## 1. 需求

输入某个特定汽车口碑URL（例：https://k.autohome.com.cn/5761#pvareaid=3454440）获取用户评论列表的所有信息，用户评论列表如下图：![image-20240321155237598](./汽车之家口碑爬虫.assets/image-20240321155237598.png)

以及完整的评论。爬取过程要求异步操作

## 2. python环境配置

建议使用Anaconda虚拟环境,如何安裝配置Anaconda可在网上搜索资料

1. 安装虚拟环境

```
conda create -n spider python=3.9
```

2. 激活环境并安装依赖

```
conda activate spider
pip install aiohttp asyncio BeautifulSoup4 
```

## 3. 代码解释

1. 根据特定汽车口碑URL提取seriesld 

```python
async def parse_car_url(url):#参数：特定汽车口碑URL
    url = url   
    parsed_url = urlparse(url)
    path_segments = parsed_url.path.split('/')  # Split the path into segments
    # Extract the number part, assuming it's always after the first '/'
    seriesld = path_segments[1] if len(path_segments) > 1 else None
    return seriesld #返回seriesld
```

2. 拼接 用户评论列表URL(需要通过网络调试得出其构成)

```python
def parse_comment_list_url(seriesld,pageIndex):#参数：seriesld，pageIndex
    return f"https://koubeiipv6.app.autohome.com.cn/pc/series/list?pm=3&seriesId={seriesld}&pageIndex={pageIndex}"#返回 第pageIndex页用户评论列表URL
```

3.向URL发出请求，header需要自己填写

```python
async def request_url(url): #参数：url
        headers = {}
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.ok:
                    response_text = await response.text()
                    return response_text #返回：响应
                else:
                    return None
```

4. 保存数据为json格式

```python
async def save_json(folder_name, filename, dict):#参数：文件夹名，文件地址，字典数据
    if not os.path.exists(folder_name):
        os.mkdir(folder_name)
    json_data = json.dumps(dict, indent=4)
    async with aiofiles.open(filename, 'w') as file:
        await file.write(json_data)
```

5. 提取完整评论数据

```python
async def extract_comment(html):
    soup = BeautifulSoup(html, 'html.parser')
    attribute_comment_list = []
    for div in soup.find_all('div', class_='kb-item'):
        split_text = div.text.split('\n',2)
        #提取属性
        attribute = split_text[1]
        text = "".join(split_text[2:]).replace('\n', '').replace(' ', '')
        #去除开头数字
        text = re.sub(r'^\d+', '', text)
        attribute_comment_list.append({"attribute":attribute, "commment":text})
    return attribute_comment_list
```

6. main函数

```python
async def main(url):
    #输入汽车口碑url提取汽车ID
    url = url
    seriesld = await parse_car_url(url)
    pageIndex = 2
    while True:
        comment_list_url = parse_comment_list_url(seriesld, pageIndex)
        print(f"**********************爬取第{pageIndex}页评论列表url**************************\n")
        print(comment_list_url)
        response_text = await request_url(comment_list_url)
        if response_text:
            response_dict = json.loads(response_text)
            users_comment_list = response_dict["result"]["list"]
            if len(urers_comment_list):
                break
            #将list存储为json文件
            folder_name = f"{seriesld}"
            users_comment_list_filename = f"./{folder_name}/pageIndex{pageIndex}.json"
            await save_json(folder_name, users_comment_list_filename, dict={f"pageIndex{pageIndex}" : users_comment_list})
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
                comemnt_dict = {"username":username,"attribute_comment_list":attribute_comment_list}
                total_comemnt_dic_list.append(comemnt_dict)
                time.sleep(5)
            detail_comment_filename = f"./{folder_name}/pageIndex{pageIndex}comment.json"
            await save_json(folder_name, detail_comment_filename, dict={f"pageIndex{pageIndex}comment" : total_comemnt_dic_list})
            pageIndex = pageIndex + 1
            print(f"**********************保存'{detail_comment_filename}'**************************\n")
            print(f"**********************已爬取'{pageIndex*len(users_comment_list)}'**************************\n")
        else:
            print(f"**********************爬取完成**************************\n")
```

7. 运行

```python
links = [] #可放要爬取的汽车口碑链接

for link in links:
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main(link))
    except Exception as e:
        print(f"Caught exception: {e}")
    finally:
        loop.stop()  # 停止事件循环
        loop.run_until_complete(loop.shutdown_asyncgens())  # 关闭所有异步生成器
        loop.close()  # 完全关闭事件循环
```

