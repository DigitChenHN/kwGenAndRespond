# keyword generator and responder
A server to generate keywords and respond to client's requests.  

# configuration 
Before running the server, you need to go to [spark ai](https://console.xfyun.cn/app/myapp) and create you own app. Copy the app id and app key to the config.ini file.  
The config file is as follow:  
```ini
[api]
url = wss://spark-api.xf-yun.com/v1.1/chat
app_id = your_app_id
api_secret = your_api_secret
api_key = your_api_key
domain = lite

[news]
url = https://news.sina.com.cn/
```