import re
from urllib.parse import urlparse

pattern_id = re.compile(r"/([\da-f]{32})\?")  # 提取图片唯一ID
pattern_size = re.compile(r"width=(\d+)&height=(\d+)")

# 记录每张唯一图片的最大尺寸和 URL
image_dict = dict()

# 提取所有图片 URL（ImageEmbed 和 picture）
src_urls = []

# 1. ImageEmbed 块
blocks = response.xpath("//div[contains(@class, 'ImageEmbed')]")
for block in blocks:
    url = block.xpath(".//img/@src").get()
    if not url:
        srcsets = block.xpath(".//source/@srcset").getall()
        for srcset in srcsets:
            parts = [s.strip().split()[0] for s in srcset.split(",") if s.strip()]
            if parts:
                url = parts[-1]
                break
    if url:
        src_urls.append(url)

# 2. 独立 <picture>
pictures = response.xpath("//picture[not(ancestor::div[contains(@class, 'ImageEmbed')])]")
for pic in pictures:
    srcsets = pic.xpath(".//source/@srcset").getall()
    for srcset in srcsets:
        parts = [s.strip().split()[0] for s in srcset.split(",") if s.strip()]
        if parts:
            src_urls.append(parts[-1])

# 3. 去重逻辑，保留最大尺寸版本
for url in src_urls:
    m_id = pattern_id.search(url)
    m_size = pattern_size.search(url)
    if not m_id:
        continue
    image_id = m_id.group(1)
    width = int(m_size.group(1)) if m_size else 0
    height = int(m_size.group(2)) if m_size else 0
    pixels = width * height

    if image_id not in image_dict or pixels > image_dict[image_id]["pixels"]:
        image_dict[image_id] = {
            "url": url,
            "width": width,
            "height": height,
            "pixels": pixels
        }

# 4. 打印结果
for img in image_dict.values():
    w, h = img["width"], img["height"]
    print(f"{img['url']}  ({w}×{h})")

print(f"\n✅ Total unique images (by content): {len(image_dict)}")
