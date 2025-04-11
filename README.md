# newsau

my project about news of Australia to download.

# deploy

```bash
# ssh login by free
cat ~/.ssh/id_rsa.pub | pbcopy

# create venv
python3 -m venv news
sudo apt install python3.12-venv
python3 -m venv news
source news/bin/activate

# upload requirements.txt and install
pip list
pip freeze > requirements.txt
pip install -r requirements.txt
deactivate

pip freeze > requirments.txt
# pip install -r requirements.txt 
sudo apt-get install pkg-config python3-dev default-libmysqlclient-dev build-essential

sudo apt-get install supervisor
sudo systemctl status supervisor.service

tail -200f /var/log/supervisor/supervisord.log

cat /etc/supervisor/supervisord.conf
vim scrapyd_supervisor.conf
sudo cp scrapyd_supervisor.conf /etc/supervisor/conf.d/

sudo mkdir -p /home/bk/py/news/logs
sudo mkdir -p /etc/scrapyd
sudo cp scrapyd.conf /etc/scrapyd/
sudo cp scrapyd_supervisor.conf /etc/supervisor/conf.d/
sudo cp push_url_supervisor.conf /etc/supervisor/conf.d/

sudo supervisorctl reread
sudo supervisorctl update

pip install scrapyd

scrapyd-deploy news

curl http://localhost:6800/daemonstatus.json
curl http://localhost:6800/schedule.json -d project=newsau -d spider=abc
curl http://localhost:6800/cancel.json -d project=newsau -d job=cfd256c2e7b011efb76a9c6b006349d6
curl http://localhost:6800/delversion.json -d project=newsau

lpush 'abcspider:start_urls' '{ "url": "https://www.abc.net.au/news/2025-02-10/trump-to-announce-new-tariffs-on-steel-and-aluminium/104917334", "meta": {"job-id":"123xsd", "start-date":"dd/mm/yy"}}'
redis-cli lpush 'abcspider:start_urls' '{ "url": "https://www.abc.net.au/news/2025-02-10/china-outlines-conditions-for-dalai-lama-to-return-to-tibet/104920862", "meta": {"job-id":"123xsd", "start-date":"dd/mm/yy"}}'

```


https://scrapyd.readthedocs.io/en/latest/api.html

https://scrapyd.readthedocs.io/en/latest/config.html#config-sources

## configs

**cat scrapyd_supervisor.conf**

```ini
[program:scrapyd]
command=/home/srv/py/news/news/bin/python3 scrapyd
directory=/home/srv/py/news/news/bin
environment=PATH=/home/srv/py/news/news/bin
user=srv
startsecs=0
stopwaitsecs=0
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/srv/py/news/logs/scrapyd.log
```

**cat scrapyd.conf**

```ini
[scrapyd]
# Application options
application       = scrapyd.app.application
bind_address      = 0.0.0.0
http_port         = 6800
logs_dir          = /home/srv/py/news/logs/scarpyd_news.log
eggs_dir          = /home/srv/py/news/eggs
```

## php debug

```php
error_log(print_r($variable, TRUE)); 
```

## ubuntu server install chrome and chromedriver

```bash
# download chrome latest version
sudo apt update
sudo apt upgrade
wget -nc https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install -f ./google-chrome-stable_current_amd64.deb
google-chrome --version

# download chrome driver
wget https://storage.googleapis.com/chrome-for-testing-public/133.0.6943.98/linux64/chromedriver-linux64.zip
unzip chromedriver-linux64.zip
sudo mv chromedriver-linux64/chromedriver /usr/bin/
ls -lhta /usr/bin/chromedriver
sudo chown root:root /usr/bin/chromedriver
sudo chmod +x /usr/bin/chromedriver
# to test
chromedriver --url-base=/wd/hub
```

## python env

在supervisor配置文件中添加一行配置，指定supervisor启动加载的python环境：

```ini
environment=PYTHONPATH='/home/ec2-user/.local/lib/python3.6/site-packages/'
```

## mysql 主从复制