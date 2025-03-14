from flask import Flask, jsonify, request 

import requests
from bs4 import BeautifulSoup
import random

import configparser 
import time
import re 
import os 
import json 
import random 

from sparkai.llm.llm import ChatSparkLLM, ChunkPrintHandler
from sparkai.core.messages import ChatMessage

config = configparser.ConfigParser()
script_dir = os.path.dirname(os.path.abspath(__file__))
config_dir = os.path.join(script_dir, 'config.ini')
config.read(config_dir)

SPARKAI_URL = config.get('api', 'url')
#星火认知大模型调用秘钥信息
SPARKAI_APP_ID = config.get('api', 'app_id')
SPARKAI_API_SECRET = config.get('api', 'api_secret')
SPARKAI_API_KEY = config.get('api', 'api_key')
#星火认知大模型domain值
SPARKAI_DOMAIN = config.get('api', 'domain')
NEWS_URL = config.get('news', 'url')

URL = 'https://news.sina.com.cn/'

def get_news_title(url, trys:int):
    times = 0
    while times < trys:

        response = requests.get(url)
        response.encoding = 'utf-8'
    
        # 检查请求是否成功（状态码200表示成功）
        if response.status_code == 200:
            # 获取响应的HTML内容
            html_content = response.text 

            # 使用BeautifulSoup解析HTML内容
            soup = BeautifulSoup(html_content, 'html.parser')

            # 查找所有<a>标签
            a_tags = soup.find_all('a', target='_blank')

            # 提取这些标签中的文本并保存到一个列表中
            texts = [tag.get_text() for tag in a_tags if len(tag.get_text()) > 12]

            break 
        
        else:
            texts = response.status_code
            print(f'Request failed, status code {texts}!')
            trys += 1 
    
    return texts

class KeywordGen():
    def __init__(self, news_url:str, news_path:str, max_try:int):
        self.today_news = news_path
        self.news_url = news_url 

        if os.path.exists(path=self.today_news):
            with open(self.today_news, 'r') as file:
                self.titles = json.load(file)
            if len(self.titles) == 0:
                # 如果本地的新闻标题为空，则通过网络获取标题
                self.titles = get_news_title(self.news_url, max_try) 
        else:
            # 如果本地没有新闻标题，则通过网络获取标题
            self.titles = get_news_title(self.news_url, max_try)
    
    def get_keyword_list(self, sparkLLM, keyword_number:int):
        title = random.choice(self.titles) 
        self.titles.remove(title) 

        messages = [ChatMessage(
        role="user",
        content=f'这是今天新闻的标题{title}，为了能够更好的了解这则新闻的内容，\
需要你从这个新闻标题延申，生成{keyword_number}个相关的关键词或句子，方便我在搜索引擎搜索，\
注意，不要简单的摘取关键词，要进行延申提问。\
每一个生成的关键词或句子用*标记出来，格式为*关键词或句子*，仅回复关键词或句子即可，不要回复其他内容，\
生成的关键词的数量不要超过{keyword_number}'
    )]
        handler = ChunkPrintHandler()
        a = sparkLLM.generate([messages], callbacks=[handler])

        reply = a.generations[0][0].text
        klist = re.findall(r'\*(.+?)\*', reply)
        klist = [s for s in klist if s.strip()]
        klist = klist[:min(keyword_number,len(klist))]
        return klist 

app = Flask(__name__)

@app.route('/news_title', methods=['GET'])
def main():

    max_trys = 3
    
    n = request.args.get('n', type=int, default=None) 

    date = time.localtime()
    when = time.strftime('%Y-%m-%d', date) 
    today_file = when + '.json'
    path = os.path.join(script_dir, 'daily_news', today_file) 

    generator = KeywordGen(URL, path, max_trys) 

    if not isinstance(generator.titles, list):
        return jsonify({"error": f"Can't get touch with {URL}"})
    
    spark = ChatSparkLLM(
        spark_api_url=SPARKAI_URL,
        spark_app_id=SPARKAI_APP_ID,
        spark_api_key=SPARKAI_API_KEY,
        spark_api_secret=SPARKAI_API_SECRET,
        spark_llm_domain=SPARKAI_DOMAIN,
        streaming=False,
    )
    try: 
        result = generator.get_keyword_list(spark, n)
    except Exception as e:
        return jsonify({'error': "llm goes wrong, try later."})

    with open(path, 'w') as file:
                json.dump(generator.titles, file)
                
    return jsonify({'result': result})

    

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)  