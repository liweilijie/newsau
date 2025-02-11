-- insert relative category between abc and news
insert into wp_scrapy_category(news_category, scrapy_category, source_website) values('澳洲新闻', 'default', 'abc');
insert into wp_scrapy_category(news_category, scrapy_category, source_website) values('国际新闻', 'Trade', 'abc');
insert into wp_scrapy_category(news_category, scrapy_category, source_website) values('生活指南', 'Supermarkets and Grocery Retailers', 'abc');
insert into wp_scrapy_category(news_category, scrapy_category, source_website) values('澳洲新闻', 'Courts', 'abc');
insert into wp_scrapy_category(news_category, scrapy_category, source_website) values('澳洲新闻', 'Bushfires', 'abc');
insert into wp_scrapy_category(news_category, scrapy_category, source_website) values('澳洲新闻', 'State and Territory Government', 'abc');
insert into wp_scrapy_category(news_category, scrapy_category, source_website) values('社论点评', 'Animal Attacks', 'abc');
insert into wp_scrapy_category(news_category, scrapy_category, source_website) values('健康医药', 'Health', 'abc');
insert into wp_scrapy_category(news_category, scrapy_category, source_website) values('健康医药', 'Alcohol', 'abc');
insert into wp_scrapy_category(news_category, scrapy_category, source_website) values('旅游、娱乐', 'American Football, Basketball, NBL, Sports Record, Music', 'abc');
insert into wp_scrapy_category(news_category, scrapy_category, source_website) values('澳洲新闻', 'Federal Government', 'abc');
insert into wp_scrapy_category(news_category, scrapy_category, source_website) values('房产、物业', 'Steel', 'abc');
insert into wp_scrapy_category(news_category, scrapy_category, source_website) values('澳洲新闻', 'Weather', 'abc');
insert into wp_scrapy_category(news_category, scrapy_category, source_website) values('旅游、娱乐', 'Music', 'abc');
insert into wp_scrapy_category(news_category, scrapy_category, source_website) values('澳洲新闻', 'Fires', 'abc');
insert into wp_scrapy_category(news_category, scrapy_category, source_website) values('国际新闻', 'Unrest, Conflict and War', 'abc');
insert into wp_scrapy_category(news_category, scrapy_category, source_website) values('生活指南', 'Public Transport, Transport, Trains, Events', 'abc');
insert into wp_scrapy_category(news_category, scrapy_category, source_website) values('人生感悟', 'ABC Lifestyle, Relationships', 'abc');

update wp_scrapy_category set scrapy_category = 'American Football, Basketball, NBL, Sports Record, Music,Sports Record,AFL,Swimming,Marathon' where news_category = '旅游、娱乐';