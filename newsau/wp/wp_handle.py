from requests.auth import HTTPBasicAuth
import requests
import base64
from newsau.settings import WP_URL, WP_USER, WP_PASSWORD

# Configuration
# WORDPRESS_URL = 'https://blog.emacsvi.com/wp-json/wp/v2'

def update_post(title, content, status='publish',
                excerpt='', author=None, format='standard',
                categories=[], tags=[],
                featured_image=None, menu_order=0, comment_status='open', ping_status='open', meta={}):

    if title == "" or content == "":
        return

    credentials = f"{WP_USER}:{WP_PASSWORD}"

    token = base64.b64encode(credentials.encode())
    post_url = "https://blog.emacsvi.com/wp-json/wp/v2/posts"

    header = {"Authorization": "Basic " + token.decode('utf-8'), "Content-Type":"application/json"}

    data = {
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
    }

    response = requests.post(post_url, json=data, headers=header)
    print(response.status_code)
    print(response.content)
    if response.status_code == 200:
        print(f'Post updated successfully:{title}')
        print(response.json())
    else:
        print(f'Failed to update post: {response.status_code}')
        print(response.text)


# Function to update a post
def update_post_by_id(post_id, title, content, status='publish', excerpt='', author=None, format='standard', categories=[],
                tags=[], featured_image=None, menu_order=0, comment_status='open', ping_status='open', meta={}):
    url = f'{WP_URL}/posts/{post_id}'
    data = {
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
    }

    response = requests.post(url, json=data, auth=HTTPBasicAuth(WP_USER, WP_PASSWORD))

    if response.status_code == 200:
        print('Post updated successfully!')
        print(response.json())
    else:
        print(f'Failed to update post: {response.status_code}')
        print(response.text)


# Example usage
if __name__ == '__main__':
    title = "test232342134v 23134123412"
    content = "content 2341342134"
    update_post(title, content)
