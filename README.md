# newsau

my project about news of Australia to download.

# deploy

```bash
pip freeze > requirments.txt
# pip install -r requirements.txt 
sudo apt-get install pkg-config python3-dev default-libmysqlclient-dev build-essential

sudo apt-get install supervisor
sudo systemctl status supervisor.service

tail -200f /var/log/supervisor/supervisord.log

cat /etc/supervisor/supervisord.conf
vim scrapyd_supervisor.conf
sudo cp scrapyd_supervisor.conf /etc/supervisor/conf.d/

sudo mkdir -p /etc/scrapyd
sudo cp scrapyd.conf /etc/scrapyd/

sudo supervisorctl reread
sudo supervisorctl update

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
