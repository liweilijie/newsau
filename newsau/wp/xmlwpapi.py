import datetime

from wordpress_xmlrpc import Client, WordPressPost
from wordpress_xmlrpc.methods.posts import NewPost, GetPosts


class WpApi():

  def __init__(self, url, user, password):
    # authenticate
    self.url = url
    self.user = user
    self.password = password
    self.client = Client(self.url, self.user, self.password)


  def post(self, title, content, status='publish', categories=['澳洲新闻'], tags=[]):
    # post and activate new post
    if title == "" or content == "":
      return

    post = WordPressPost()
    post.title = title
    post.content = content
    post.post_status = status
    post.date = datetime.datetime.now() - datetime.timedelta(hours=11)

    # post.terms_names = {
    #   'post_tag': ['test', 'firstpost'],
    #   'category': ['Introductions', 'Tests']
    # }
    post.terms_names = {
      'post_tag': tags,
      'category': categories
    }

    self.client.call(NewPost(post))

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
  wp.post(title, content, tags=["abc", "wordpress"], categories=["news"])