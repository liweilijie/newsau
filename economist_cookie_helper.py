#!/usr/bin/env python3
"""
Economist Cookie Helper Script

这个脚本帮助你将从浏览器复制的cookie字符串写入Redis，
以便economist爬虫使用。

使用方法：
1. 在浏览器中登录 economist.com
2. 打开开发者工具 (F12)
3. 在 Console 中运行: document.cookie
4. 复制输出的cookie字符串
5. 运行此脚本并粘贴cookie字符串

或者直接运行：
python economist_cookie_helper.py "your_cookie_string_here"
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
        domain = "www.economist.com"
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
    cookie_string = '''economist_has_visited_app_before=true; optimizelyEndUserId=oeu1748581700861r0.5964055828985964; _sp_su=false; blaize_session=43ca9843-d157-4e82-a3b5-6f68998328bf; blaize_tracking_id=5da3174a-ad90-40b5-a333-7ede945e9642; utag_main_v_id=01971f975ae5005a7764398a98dc05075001a06d0093c; permutive-id=318f4831-4d7a-4e89-ac97-3c703fb62d73; __spdt=451a24e0042942489d640e66033c7330; _fbp=fb.1.1748581703363.583016347358474113; _lc2_fpi=6b85dc1d2bba--01jwfseqqppjgt8x63c20rz3yz; wall_session=43ca9843-d157-4e82-a3b5-6f68998328bf; _mibhv=anon-1748581703506-3879045742_9933; _gcl_au=1.1.438967510.1748581704; _tt_enable_cookie=1; _ttp=01JWFSERDMZJRHFV7HN0RDNCA5_.tt.1; _hjSessionUser_3355938=eyJpZCI6IjY5NTIyOTY1LWU4MmUtNTAyMi05ZDE1LTA2MGU5MmJiZTQ2NyIsImNyZWF0ZWQiOjE3NDg1ODE3MDM1ODUsImV4aXN0aW5nIjp0cnVlfQ==; ttcsid=1748581704129::oRUY4XFRWFu_NraGFhE4.1.1748582338330; ttcsid_C9V6D2JC77UE268F335G=1748581704127::nn64ZiwyDNNRf-ppGog5.1.1748582339002; __gads=ID=67965e384e773897:T=1748581702:RT=1748596411:S=ALNI_Ma8p2Xq8iOeSAzw2moHIShCljXQEA; __gpi=UID=000011075e56d2f1:T=1748581702:RT=1748596411:S=ALNI_Ma2DBOSfzxGXKmqwiPuTaXZdE1TCw; __eoi=ID=cb283c0a9214ce13:T=1748581702:RT=1748596411:S=AA-AfjYJ7Mzb2lrmm6sx3H0Vazjx; optimizelySession=0; _gid=GA1.2.1520729366.1751704219; newsletters_signed_up_to=te_this_week%2Cespresso%2Cthe_bottom_line%2Cmoney_talks%2Cdrum_tower; isGroupSub=true; euconsent-v2=CQUFC4AQUFC4AAGABCENBvFgAP_gAEPAACQwJQsB8G5MSSFKYCp3YJsEMIQWxUBpQMAABAAAAwABABIQIIwAACAAIACAAAACEBIAIEQAAAAAGAAAAAAAYAAAIACAAEAQAAAAIAAAAAAAAAAAAAAIAAAAAAAAgGBQAAAAgAQAABAAQEgAAAAgAAAAIKAFAAAAAAAAAAAAQAAAAAAAgCgAAAAAAAAAAAAAABAAAAAAAAACCM0BcABQADgAKgAXABAACQAE4AKgAaABFACYAFUANAAhABOADugIOAhABFgFqAMWAZIAywCMwB4SAgAAsACgAHAAZAA8AD8AIgATQA7gB7AD9APaAo8BeYDcwG6hQAoACgATgAqACKBGYIABACOOgLgALAAoABwAGQAPAAxAB-AEQAJoATgAowBogD2AH6AR0A6gB7QFHgLzAZYA00BuoD-x4AUABQAJwAVABFAjMOABgBHACgA3MhAHAAWABQAKoAYgB3AHUAf2RAAgAqJQDAAFgAUAA4ADwAMQAiABRgHUAPaAo8BeYDJCYAEAE5IACAEcpATAAXABQAFQAOAAgAB4AEwAMQAfgBEACjAGiAP0AjoB1AD2gLzAZYA3UB_ZUAGAAoAE4EZigAYAGQARwAoABbADaA3MtABAHcAA.YAAACHAAAAAA; consentUUID=7aec7480-1859-4005-9a2a-a4ea45fc54c4_45; consentDate=2025-07-05T08:31:18.580Z; _li_dcdm_c=.economist.com; __podscribe_theeconomist_referrer=https://myaccount.economist.com/; __podscribe_theeconomist_landing_url=https://www.economist.com/; BCSessionID=38e38d08-0402-42a9-b54c-c6613d43c16b; _parsely_session={%22sid%22:8%2C%22surl%22:%22https://www.economist.com/business/2025/07/03/kim-kardashian-ryan-reynolds-and-the-age-of-the-celebrity-brand%22%2C%22sref%22:%22https://www.economist.com/%22%2C%22sts%22:1751723624346%2C%22slts%22:1751721212922}; _parsely_visitor={%22id%22:%22pid=23e44c28-bf75-47e1-80b3-a257ddc96269%22%2C%22session_count%22:8%2C%22last_session_ts%22:1751723624346}; _hjSession_3355938=eyJpZCI6IjgwNjM5MWFlLWM2NzMtNDJkZS04ZTYyLTRjOTc1N2ZmMDE4YSIsImMiOjE3NTE3MjM3MjY3NzMsInMiOjAsInIiOjAsInNiIjowLCJzciI6MCwic2UiOjAsImZzIjowLCJzcCI6MH0=; state-ae78a06163eb616e754dd85a07d3b7aa=%7B%22returnUrl%22%3A%22https%3A%2F%2Fwww.economist.com%2Fbusiness%2F2025%2F07%2F03%2Fkim-kardashian-ryan-reynolds-and-the-age-of-the-celebrity-brand%22%7D; state-aead6b02637be73c00e717b43ff2a5ed=%7B%22returnUrl%22%3A%22https%3A%2F%2Fwww.economist.com%2F%22%7D; state-b5026ad799f775badf04ecb811f5cc15=%7B%22returnUrl%22%3A%22https%3A%2F%2Fwww.economist.com%2F%22%7D; AMP_TOKEN=%24NOT_FOUND; state-40b0c4b93554fbbbd86f137e20ddc96b=%7B%22returnUrl%22%3A%22https%3A%2F%2Fwww.economist.com%2F%22%7D; _rdt_uuid=1748581702589.7659c55b-17f4-4fef-b3a4-94d111334ae3; _uetsid=749ef200597a11f0a7f58b016bb7840b; _uetvid=1c815c003d1411f08429ef4e8625e194; _parsely_slot_click={%22url%22:%22https://www.economist.com/%22%2C%22x%22:1257%2C%22y%22:357%2C%22xpath%22:%22//*[@id=%5C%22__next%5C%22]/div[1]/div[1]/div[2]/header[1]/div[1]/div[2]/div[1]/div[1]/div[1]/a[2]%22%2C%22href%22:%22https://www.economist.com/api/auth/login%22}; __cf_bm=ErGhj_iMPSC9p5o8fLuBW60n0sa3dn5iIL2vYjQV29M-1751727224-1.0.1.1-YBvXWEsVzo62N.CX8NrgEC2MAYVjwO4_YTlCMRu0GS6pRKlRAd2128lID3YSauNCnJlA.DAw.4CgcOBr5gi0_mABRY0GxBV1VbA0AGI6uXY; _cfuvid=p.0i0gHjVSFkV5ynabOj2IzXTvj0C4oq1c1ImZFDxdQ-1751727224470-0.0.1.1-604800000; utag_main__sn=5; utag_main_ses_id=1751727231211%3Bexp-session; utag_main_dc_visit=5; utag_main_dc_region=ap-east-1%3Bexp-session; utag_main__ss=0%3Bexp-session; economist_auth_complete=1751727239; fcx_contact_id=003WT00000Hib0UYAR; economist_piano_id=003WT00000Hib0UYAR; fcx_access_token=00D3z000002Jvyi!AQEAQB8aTehYu8Wi68geOwJFTQ4dFK2YRPLaX9djko5ACtwxcQKnO36lq28lznFY7D9to4RY8qOHOIMihhU9n9DGS4BfcrOX; fcx_refresh_token=5Aep861ikeX7i6YENc9Sn4e4tYFRWdbjVaKAcXUif_t_6ahU0Muuz._ZtWASNGOk0NVypyGt2mSbL1zZVS0mEWt; fcx_access_state=eyJvd25lckFjY291bnRJZCI6IjAwMTN6MDAwMDJvTU5WU0FBNCIsIm93bmVyIjoiTWljcm9zb2Z0IExpYnJhcnkiLCJzdWJzY3JpcHRpb25UeXBlIjoiQjJCX0dST1VQIiwiY29udGFjdElkIjoiMDAzV1QwMDAwMEhpYjBVWUFSIiwiZW1haWwiOiJ5YW5nLmh1YUBtaWNyb3NvZnQuY29tIiwiZmlyc3ROYW1lIjoiSHVnaCIsImxhc3ROYW1lIjoiWWFuZyIsInBob25lIjpudWxsLCJpc0VtYWlsVmVyaWZpZWQiOiJ0cnVlIiwiaXNCMmJDbGllbnRBZG1pbiI6ImZhbHNlIiwiaXNTdWJzY3JpYmVyIjp0cnVlLCJpc0xhcHNlZCI6ZmFsc2UsImxhcHNlZE1vbnRocyI6MCwiY3VzdG9tZXJTZWdtZW50IjpudWxsLCJsb2dnZWRJbiI6dHJ1ZSwicmVnaXN0ZXJlZEF0IjoiMjAyNS0wNS0yOVQxMzowMDowNy4wMDArMDAwMCIsImlzRXNwcmVzc29TdWJzY3JpYmVyIjpmYWxzZSwiaXNQb2RjYXN0U3Vic2NyaWJlciI6ZmFsc2UsImVudGl0bGVtZW50cyI6W3sicHJvZHVjdENvZGUiOiJURS5ESUdJVEFMIiwiZW50aXRsZW1lbnRDb2RlIjpbeyJjb2RlIjoiVEUuQVBQIiwiZXhwaXJlcyI6IjIwMjYtMDUtMDRUMjM6NTk6NTkuMDAwWiJ9LHsiY29kZSI6IlRFLldFQiIsImV4cGlyZXMiOiIyMDI2LTA1LTA0VDIzOjU5OjU5LjAwMFoifSx7ImNvZGUiOiJURS5ORVdTTEVUVEVSIiwiZXhwaXJlcyI6IjIwMjYtMDUtMDRUMjM6NTk6NTkuMDAwWiJ9LHsiY29kZSI6IlRFLlBPRENBU1QiLCJleHBpcmVzIjoiMjAyNi0wNS0wNFQyMzo1OTo1OS4wMDBaIn1dfV0sImxvZ29VcmwiOiJodHRwczovL2Vjb25vbWlzdC5maWxlLmZvcmNlLmNvbS9zZmMvZGlzdC92ZXJzaW9uL2Rvd25sb2FkLz9vaWQ9MDBEM3owMDAwMDJKdnlpJmlkcz0wNjgzejAwMDAwaVJvcXUmZD0lMkZhJTJGM3owMDAwMDBPTmtTJTJGdy5rWVJOZ3U4UktUXzhSXzNkc0FRUFhLcF9ITmkyMVdwak1KT1guUkR5USZhc1BkZj1mYWxzZSIsImxhcmdlTG9nb1VybCI6bnVsbCwic2hvd1dlbGNvbWVNb2RhbExvZ28iOiJ0cnVlIiwic2hvd09yZ2FuaXNhdGlvbkxvZ28iOiJmYWxzZSJ9; state-is-subscriber=true; fcx_auth_type=fcx; fcx_user=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIwMDNXVDAwMDAwSGliMFVZQVIiLCJlbnRpdGxlbWVudHMiOlsiVEUuQVBQIiwiVEUuV0VCIiwiVEUuTkVXU0xFVFRFUiIsIlRFLlBPRENBU1QiXSwidXNlclR5cGUiOiJzdWJzY3JpYmVyIiwiZXhwIjoxNzU5NTA2ODQ1LCJyZWdpc3RyYXRpb25UaW1lc3RhbXAiOjE3NDg1MjM2MDcsInN1YnNjcmlwdGlvblRpbWVzdGFtcCI6MTc0NjQwMzE5OSwiaWF0IjoxNzUxNzI3MjQ1fQ.IlpelgCPqOsPR0QyK9oBSO_10N7FBy06i9ecNfzbvD4; cf_clearance=zfldKWeyNjg4RS_mNgdMcxYSYb9rnZmVbXd9sox.3WM-1751727247-1.2.1.1-GAbp7Zwl3U9SY9V_lE5_JSSJxtA7G6jsKSC_dbYFKSUrIYwN1D91PRUDTZ5G.r0VypknnkNLdWOGzm4X7A4RZLOghHU13fwOFeMkzBl85O_l.ExZCW2tQ.7Sfx.Bzzv166_boqv_uJV9tU2NL5YowJyxqpCmGnjyjbH_shSoy_LBNv7EriGHv5yqZJyAxF6sB4ntt2B7iQpYpR8UrY3p8nJzO0AxuYS4QmBvWkUle5A; uspv=0; utag_main__pn=2%3Bexp-session; utag_main_dc_event=3%3Bexp-session; _consentT=true; utag_main__se=10%3Bexp-session; utag_main__st=1751729051650%3Bexp-session; _gat_tealium_0=1; _ga=GA1.1.240557291.1748581703; _ga_CWJ8XWVBYS=GS2.1.s1751727226$o6$g1$t1751727252$j34$l0$h0; _ga_WL00EXBGPS=GS2.1.s1751727226$o6$g1$t1751727252$j34$l0$h0'''
    
    # 写入Redis
    success = write_cookie_to_redis(cookie_string)
    
    if success:
        print("\n🎉 设置完成！现在可以运行爬虫了:")
        print("python -m scrapy crawl economist")
    else:
        print("\n❌ 设置失败，请检查Redis连接和cookie格式")

if __name__ == "__main__":
    main() 