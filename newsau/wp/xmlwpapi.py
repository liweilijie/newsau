from datetime import datetime

import pytz
from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.posts import NewPost, GetPosts
from newsau.utils import common


class WpApi():

  def __init__(self, url, user, password):
    # authenticate
    self.url = url
    self.user = user
    self.password = password
    self.client = Client(self.url, self.user, self.password)
    self.sydney_tz = pytz.timezone("Australia/Sydney")


  def post(self, title, content, post_date=None, status='publish', categories=['澳洲新闻'], tags=[], post_type=None):
    # post and activate new post
    if title == "" or content == "":
      return

    post = WordPressPost()
    post.title = title
    post.content = content
    # newsflash = "newsflashes"
    if post_type:
      post.post_type = post_type

    # Save the post as a draft for review
    # post.post_status = 'draft'

    post.post_status = status

    if post_date is None or post_date == "":
      post.date = datetime.now(pytz.timezone('Etc/GMT+0'))
    else:
      if post_type and post_type == "newsflashes":
        post.date = post_date
      else:
        try:
          sydney_time = datetime.strptime(post_date, "%Y-%m-%d %H:%M:%S")
          sydney_time = self.sydney_tz.localize(sydney_time)

          post.date = sydney_time.astimezone(pytz.utc)
        except Exception as e:
          print(f'convert {post_date} to datetime error: {e}')
          post.date = datetime.now(pytz.timezone('Etc/GMT+0'))

    # print(f'post utc date:{post.date}')

    # post.terms_names = {
    #   'post_tag': ['test', 'firstpost'],
    #   'category': ['Introductions', 'Tests']
    # }
    if post_type is not None and post_type == "newsflashes":
      post.terms_names = {
        'newsflashes_tags': tags
      }

    else:
      post.terms_names = {
        'post_tag': tags,
        'category': categories
      }

    post_id = self.client.call(NewPost(post))
    print(f'send wordpress successful and post_id:{post_id}')
    return post_id

if __name__ == "__main__":
  title = 'A possible replacement is to use pip for package installation..'
  content = '''
  Collecting python-wordpress-xmlrpc
  Downloading python-wordpress-xmlrpc-2.3.zip (19 kB)
  Installing build dependencies ... done
  Getting requirements to build wheel ... done
  Preparing metadata (pyproject.toml) ... done
Building wheels for collected packages: python-wordpress-xmlrpc
  Building wheel for python-wordpress-xmlrpc (pyproject.toml) ... done
  Created wheel for python-wordpress-xmlrpc: filename=python_wordpress_xmlrpc-2.3-py3-none-any.whl size=16403 sha256=188c9d3caa94a02072caa71ef18e5e235c6d7fa14d884232069100e0e4fd08a3
  Stored in directory: /Users/liwei/Library/Caches/pip/wheels/65/bb/ea/1d7b32a64a1435f06115b832e18d66f3c449e10555ad9bc1a7'''

  from newsau.settings import WP_XMLURL, WP_USER, WP_PASSWORD
  wp = WpApi(WP_XMLURL, WP_USER, WP_PASSWORD)
  date_str = "2025-02-20T04:55:05.000Z"
  wp.post(title, content, post_date=common.convert_to_datetime(date_str), tags=["abc", "wordpress"], categories=["news"], post_type="newsflashes")