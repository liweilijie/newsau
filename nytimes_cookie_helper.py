#!/usr/bin/env python3
"""
NYTimes Cookie Helper Script

这个脚本帮助你将从浏览器复制的cookie字符串写入Redis，
以便nytimes爬虫使用。

使用方法：
1. 在浏览器中登录 nytimes.com
2. 打开开发者工具 (F12)
3. 在 Console 中运行: document.cookie
4. 复制输出的cookie字符串
5. 运行此脚本并粘贴cookie字符串

或者直接运行：
python nytimes_cookie_helper.py "your_cookie_string_here"
"""

import sys
import redis
from newsau.settings import REDIS_URL
from newsau.utils.common import get_md5

def write_cookie_to_redis(cookie_string):
    """
    将cookie字符串写入Redis
    
    Args:
        cookie_string: 从浏览器复制的cookie字符串
    """
    try:
        # 连接Redis
        r = redis.from_url(REDIS_URL, decode_responses=True)
        
        # 生成domain的MD5
        domain = "www.nytimes.com"
        domain_md5 = get_md5(domain)
        
        # 设置cookie key
        cookie_key = f"cookie:{domain_md5}"
        
        # 写入Redis
        r.hset(cookie_key, "value", cookie_string)
        
        # 验证写入
        stored_cookie = r.hget(cookie_key, "value")
        if stored_cookie == cookie_string:
            print(f"✅ Cookie 已成功写入 Redis (hashtable)")
            print(f"Key: {cookie_key}")
            print(f"Domain MD5: {domain_md5}")
            print(f"Cookie 长度: {len(cookie_string)} 字符")
            return True
        else:
            print("❌ Cookie 写入验证失败")
            return False
            
    except Exception as e:
        print(f"❌ 写入 Cookie 时出错: {e}")
        return False

def main():
    cookie_string = '''nyt-a=a-TUOtLNxcv5ZTposIdyNZ; nyt-purr=cfhhcfhhhckfhcfshgas2fdnd; purr-pref-agent=<G_<C_<T0<Tp1_<Tp2_<Tp3_<Tp4_<Tp7_<a0_; gpp-string=",,DBABLA~BVQqAAAAAABo.QA"; _cb=Cxfhusd5b3GCSroM; _gcl_au=1.1.1426058051.1751721468; purr-cache=<G_<C_<T0<Tp1_<Tp2_<Tp3_<Tp4_<Tp7_<a0_<K0<S0<r<ur; nyt-auth-method=username; iter_id=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhaWQiOiI2ODM4NTc2ZGU2ZWE2MWI2MWMyMDJhZmUiLCJhaWRfZXh0Ijp0cnVlLCJjb21wYW55X2lkIjoiNWMwOThiM2QxNjU0YzEwMDAxMmM2OGY5IiwiaWF0IjoxNzUxNzIxNTAyfQ.8x376pFnXfZZGySxOpwpfNwFT88KJDscebuRmLHX66o; nyt-gdpr=0; NYT-MPS=0000000c3d867bdfac33bc37810721b97359345d83955d1813556ab24acdbf2b6cbb904e71eb7efddb826b8807aecb644d9303d218d049d0a782f0bd3ff2fc; RT="z=1&dm=nytimes.com&si=708ca326-fa40-456f-9087-75886baabb87&ss=mcrtisuj&sl=1&tt=1kl&bcn=%2F%2F684d0d4a.akstat.io%2F&ld=26p&ul=2p0&nu=z6erqpcv&cl=2yb&hd=36d"; nyt-us=0; nyt-geo=SG; regi_cookie=ndslap=7&news_tenure=38&regi_id=283504034; _cb_svref=https%3A%2F%2Fwww.nytimes.com%2Fsubscription%2Fonboarding-offer%3FcampaignId%3D7JFJX%26EXIT_URI%3Dhttps%253A%252F%252Fwww.nytimes.com%252F2025%252F07%252F05%252Fworld%252Faustralia%252Fjewish-synagogue-restaurant-violence.html%26login%3Dsmartlock%26auth%3Dlogin-smartlock; nyt.et.dd=iv=BD0786AA6DD24DCF9B5734C4D142B758&val=crwQT+4tEXxO9ZUFndKBzupDU/72eq1BjULsVlaGNqDqC2+22+YMvCmpMiSa539hNahd3ZLjrl2p7ymr6yMU9IG92I4YvZtXDHDcbvcEMBhxmQU4DBkg2ZbntYdfh6siADyj79C85QVLdt1D5d1q+Hh7gzi4EXmye7Ql4rff+eIYJT1lklKrrtced8ty2M8MWa0qPaWzjFBJCCAZ9oQC4QDielLVHJJfDGg54i3rcp0=; nyt-traceid=00000000000000002d00baa20c0fd49d; SIDNY=CBwSMgiFqKrDBhCvrarDBhoSMS04jC9Jzi-Wmpt5Pln1MhslIKLbl4cBKgIeVTiPy-HBBkIAGkBxy0GV1Mb-N9t-xyYn4gTMFsSQWI6lhHL-vMWrfLGu6am0w38LC8lEwnHgAzi_0Uv7IbClBy7KoWv69gyaHyQD; NYT-S=0^CBwSMgiFqKrDBhCvrarDBhoSMS04jC9Jzi-Wmpt5Pln1MhslIKLbl4cBKgIeVTiPy-HBBkIAGkBxy0GV1Mb-N9t-xyYn4gTMFsSQWI6lhHL-vMWrfLGu6am0w38LC8lEwnHgAzi_0Uv7IbClBy7KoWv69gyaHyQD; __gads=ID=c04265d03dee4da2:T=1751721449:RT=1751815737:S=ALNI_MaSXGMHoxmSyY59IlhU5VoooxwhJw; __gpi=UID=0000114a1d59a2ae:T=1751721449:RT=1751815737:S=ALNI_Mar8-rxx7mrHTAm4Tzgf3pz_3a8kw; __eoi=ID=54f07931b2efaac0:T=1751721449:RT=1751815737:S=AA-AfjZAPr-4d_XWP_zdMpj192jJ; nyt-jkidd=uid=283504034&lastRequest=1751815738681&activeDays=%5B0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C0%2C1%2C1%5D&adv=2&a7dv=2&a14dv=2&a21dv=2&lastKnownType=sub&newsStartDate=1748508496&entitlements=AAA+AUD+CKG+MM+MOW+MSD+MTD+WC; _chartbeat2=.1751721457526.1751815740459.11.Bwg624yVzJBDN26UO2jqUDXXRub.3; _chartbeat5=; datadome=lo4QwLo98aeVI0meSq7_uWStA382ua3Y~zAE_ummH~2YMIQj7VXMuMO2A1Dba491Ktax5Y0oNH6rVnXbZ9H9Y9X2H_LOLb8GSc3fuGtpY_qSONW4Ib4T52zTqPmttj5e; _dd_s=rum=0&expire=1751816651097'''
    success = write_cookie_to_redis(cookie_string)
    if success:
        print("\n🎉 设置完成！现在可以运行爬虫了:")
        print("python -m scrapy crawl nytimes")
    else:
        print("\n❌ 设置失败，请检查Redis连接和cookie格式")

if __name__ == "__main__":
    main() 