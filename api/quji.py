from fastapi import APIRouter, HTTPException
import requests
import asyncio
import dicttoxml  # 导入用于将字典或JSON数据转换为XML格式的库
import feedparser  # 导入用于解析RSS等feed格式数据的库
from xml.etree.ElementTree import fromstring, tostring  # 导入ElementTree模块用于处理XML元素树，方便后续操作

router = APIRouter()

# 定义用于获取文章数据的路由函数，根据指定页码获取对应页的文章信息，是一个异步函数
@router.get("/fetch-articles")
async def fetch_articles(page: int):
    url = f"https://n.ifun.cool/api/articles/all?datasrc=articles&current={page}&size=12"
    headers = {
        'Host': 'n.ifun.cool',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # 若请求状态码不是200，抛出异常，确保只处理成功的请求
        return response.json()  # 将获取到的响应数据（假设为JSON格式）解析为Python对象并返回
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))  # 出现请求异常时，向外抛出HTTP 500错误及详细信息


# 定义用于生成RSS内容的路由函数，会动态获取多页文章数据来构建完整的RSS格式的XML内容，是一个异步函数
@router.get("/generate-rss")
async def generate_rss():
    all_articles = []  # 用于存储所有获取到的文章数据，后续基于这些数据构建RSS内容
    page = 1  # 初始化页码为1，从第一页开始获取文章数据
    page_fetch_delay = 10  # 设置获取下一页数据前等待的时间（秒），这里设置为10秒，可根据实际情况调整
    max_pages = None  # 可以设置最大获取页数限制，初始化为None表示不限制页数，可按需修改，比如设置为10表示最多获取10页
    pages_fetched = 0  # 记录已经获取的页数

    # 先直接获取第一页数据并添加到列表中，确保第一页内容能快速显示
    first_page_data = await fetch_articles(page)
    first_page_articles = first_page_data.get("data", {}).get("records", [])
    all_articles.extend(first_page_articles)
    pages_fetched += 1  # 已获取页数加1，表示第一页已获取

    # 如果设置了最大页数为1，说明只需要第一页内容，直接构建并返回RSS内容
    if max_pages == 1:
        rss_xml = build_rss_xml(all_articles)
        return rss_xml

    page += 1  # 页码加1，准备获取下一页数据

    while True:
        if max_pages is not None and pages_fetched >= max_pages:
            break  # 如果设置了最大页数限制，且已获取的页数达到或超过这个限制，就停止循环获取数据

        data = await fetch_articles(page)  # 异步获取当前页的文章数据
        articles = data.get("data", {}).get("records", [])  # 从返回的数据中提取文章列表，若无则返回空列表

        if not articles:
            break  # 如果当前页没有文章数据了（即文章列表为空），说明所有数据已获取完，跳出循环

        all_articles.extend(articles)  # 将当前页的文章数据添加到总文章列表中

        # 如果不是第一页，等待一段时间后再去获取下一页数据，避免过于频繁请求服务器
        if page > 1:
            await asyncio.sleep(page_fetch_delay)

        page += 1  # 页码加1，准备获取下一页数据
        pages_fetched += 1  # 已获取页数加1

    rss_xml = build_rss_xml(all_articles)
    # 可以在这里使用导入的库对生成的RSS XML内容进行进一步处理，比如验证格式是否正确等
    # 以下是使用feedparser库简单验证RSS XML内容是否能被正确解析的示例（可按需调整或扩展此功能）
    try:
        feed = feedparser.parse(rss_xml)
        if feed.bozo:
            print(f"RSS XML格式可能有问题: {feed.bozo_exception}")
    except Exception as e:
        print(f"验证RSS XML内容时出现异常: {e}")
    return rss_xml


def build_rss_xml(articles):
    # 先构建一个包含频道基本信息的字典，方便后续转换为XML格式
    rss_dict = {
        "rss": {
            "@version": "2.0",
            "channel": {
                "title": "趣集",
                "description": "故事盐选，盐选故事搬运工",
                "link": "https://n.ifun.cool",
                "item": [
                    {
                        "title": article['title'],
                        "author": article.get('author', ''),
                        "category": article.get('category', ''),
                        "tag": article.get('tag', ''),
                        "description": article['content'],
                        "guid": article['id']
                    } for article in articles
                ]
            }
        }
    }
    # 使用dicttoxml库将字典转换为XML格式字符串，设置自定义根元素（这里是'rss'）和缩进等格式化选项
    rss_xml = dicttoxml.dicttoxml(rss_dict, custom_root='rss', indent='    ')
    # 将生成的XML字节串转换为字符串，并指定编码为UTF-8
    rss_xml = rss_xml.decode('utf-8')
    return rss_xml
