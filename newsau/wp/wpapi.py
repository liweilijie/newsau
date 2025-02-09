import base64

import requests
from newsau.settings import WP_URL, WP_USER, WP_PASSWORD


class WpApi2():

   def __init__(self, user, password, url):
       self.url = url
       self.credentials = user + ':' + password
       self.token = base64.b64encode(self.credentials.encode())
       self.header = {"Authorization": "Basic " + self.token.decode('utf-8'), "Accept": "application/json", "Content-Type": "application/json"}

   def update_post(self, title, content, status='publish',
                   excerpt='', author=None, format='standard',
                   categories=[], tags=[],
                   featured_image=None, menu_order=0, comment_status='open', ping_status='open', meta={}):

       if title == "" or content == "":
           return

       post = {
           'title': title,
           'content': content,
           'status': status,
           'excerpt': excerpt,
           'author': author,
           'format': format,
           'categories': categories,
           'tags': tags,
           'featured_media': featured_image,
           'menu_order': menu_order,
           'comment_status': comment_status,
           'ping_status': ping_status,
           'meta': meta
           # 'date': str(datetime.now().date())
       }

       rsp = requests.post(self.url, headers=self.header, json=post)
       print(rsp.status_code)
       print(rsp.content)
       if rsp.status_code == 200 or rsp.status_code == 201:
           print(f'Post updated successfully:{title}')
           print(rsp.json())
       else:
           print(f'Failed to update post: {rsp.status_code}')
           print(rsp.text)


if __name__ == "__main__":
    title = "Requirement already satisfied: charset-normaliz"
    content = " DEPRECATION: Loading egg at /Users/liwei/Desktop/py/newsau/.venv/lib/python3.13/site-packages/zope.interface-7.1.0-py3.13-macosx-12.0-x86_64.egg is deprecated. pip 23.3 will enforce this behaviour change. A possible replacement is to use pip for package installation.. Collecting python_wpapi Obtaining dependency information for python_wpapi from https://files.pythonhosted.org/packages/8f/0b/bb51359498a5a7de30939cba458ad50a9f9ad1a8599e80595de210f80c31/python_wpapi-0.3.1-py2.py3-none-any.whl.metadata"
    api = WpApi2(WP_USER, WP_PASSWORD, WP_URL)
    api.update_post(title, content)