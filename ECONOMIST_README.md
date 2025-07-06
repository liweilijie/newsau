# Economist 爬虫使用说明

## 概述

Economist爬虫已经改为使用cookie方式进行认证，不再使用Selenium。这种方式更稳定、更高效。

## 设置步骤

### 1. 获取Cookie

1. 在浏览器中访问 [economist.com](https://www.economist.com)
2. 登录你的账户
3. 打开开发者工具 (F12)
4. 在 Console 中运行以下命令获取cookie：
   ```javascript
   document.cookie
   ```
5. 复制输出的cookie字符串

### 2. 将Cookie写入Redis

有两种方式：

#### 方式一：使用帮助脚本（推荐）

```bash
python newsau/spiders/economist_cookie_helper.py
```

然后粘贴cookie字符串。

#### 方式二：直接使用Redis命令

```bash
redis-cli set "cookies:www.economist.com:raw" "your_cookie_string_here"
```

### 3. 运行爬虫

```bash
python -m scrapy crawl economist
```

## 功能特性

### 自动图片处理
- 自动提取文章中的图片
- 去重并保留最大尺寸版本
- 处理`<source>`标签和`<img>`标签
- 替换HTML中的图片链接

### 内容清理
- 删除广告和无关内容
- 清理HTML标签
- 保留文章正文内容

### 智能URL验证
- 只处理符合格式的新闻URL
- 格式：`/YYYY/MM/DD/article-title`
- 自动跳过已处理的文章

## 配置说明

### Redis键值
- Cookie存储：`cookies:www.economist.com:raw`
- URL队列：`economistspider:start_urls`
- 已处理URL：`economist:seen_urls`

### 环境变量
确保以下设置正确：
- `REDIS_URL`：Redis连接地址
- `NEWS_ACCOUNTS`：爬虫配置信息

## 故障排除

### 问题1：Cookie无效
- 确保在浏览器中已登录
- 检查cookie是否过期
- 重新获取cookie并更新Redis

### 问题2：无法获取文章内容
- 检查cookie是否正确写入Redis
- 确认网站结构是否发生变化
- 查看日志获取详细错误信息

### 问题3：图片处理失败
- 检查网络连接
- 确认图片URL是否可访问
- 查看图片处理相关日志

## 日志级别

- `INFO`：基本运行信息
- `DEBUG`：详细调试信息
- `WARNING`：警告信息
- `ERROR`：错误信息

## 注意事项

1. Cookie会定期过期，需要定期更新
2. 请遵守网站的robots.txt和使用条款
3. 建议设置合理的爬取频率
4. 定期检查Redis中的数据量，避免内存溢出

## 更新日志

- 2025-01-XX：移除Selenium依赖，改用cookie认证
- 2025-01-XX：优化图片处理逻辑
- 2025-01-XX：增强错误处理和日志记录 