from flask import Flask, jsonify, request 

import requests
from bs4 import BeautifulSoup
import random

URL = 'https://news.sina.com.cn/'

def get_title(url):
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
        
    else:
        texts = response.status_code
    
    return texts

app = Flask(__name__)

@app.route('/news_title', methods=['GET'])
def get_news_title():
    
    n = request.args.get('n', type=int, default=None) 

    titles = get_title(URL)
    if not isinstance(titles, list):
        return jsonify({"error": f"Can't get touch with {URL}"})
    # 检查n是否有效
    if n is None or n < 0 or n > len(titles):
        return jsonify({"error": "Invalid value for 'n'. It must be a non-negative integer less than or equal to the length of the list."}), 400
    
    # 从预定义列表中随机选择n个元素（不重复）
    result = random.sample(titles, n)

    return jsonify({'result': result})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)  