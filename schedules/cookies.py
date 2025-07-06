import redis
import logging

import connection
from settings_manager import Settings

settings = Settings()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class CookieWriter:
    def __init__(self):
        try:
            self.server = connection.from_settings(settings)

            if self.server.ping():
                logger.info("redis connect successful.")
            else:
                raise ValueError("redis connect failed.")
        except redis.ConnectionError as e:
            logger.error(f"redis happened error: {e}")
            raise e

    def write_raw(self, domain: str, raw_cookie: str):
        """
        将整个原始 Cookie 字段串写入 Redis。
        key: cookies:<domain>:raw
        """
        key = f"cookies:{domain}:raw"
        self.server.set(key, raw_cookie)
        logger.info(f"📥 写入 Redis：{key} ({len(raw_cookie)} 字符)")

        # 📤 读取并打印刚写入的内容
        saved = self.server.get(key)
        if saved:
            logger.info(f"✅ Redis 内容为：{saved}")
        else:
            logger.warning("⚠️ 获取不到写入的 Cookie 内容")

if __name__ == "__main__":
    domain = "www.ft.com"
    raw_input = '''FTClientSessionId=04847631-184a-4910-a76e-3892c91366bc; spoor-id=04847631-184a-4910-a76e-3892c91366bc; __exponea_etc__=8fe5cccc-0a43-4735-8043-2e8f46237e72; __exponea_time2__=-3.0803701877593994; _csrf=HrWpDD3CHbdTQeireMEU1btS; FTSession_s=077X3ps7eEIO04jBS46-Q1bZ0wAAAZem37tcw8I.MEYCIQDIPwX2ghsu-9sfKYOwwBpCquK_DWcGVzJURg44U6NLqQIhAPBUhncvdGimkJPuOOey1a0offBMBzB76ANiIZAU2y4A; FTAllocation=bed7de9b-3b78-420e-88c1-4b8ebe4356d9; _cb=uWdMRBS1inVBl85Cn; usnatUUID=fd512fcb-4fec-4bac-8dc5-1125bebb7bb4; FTCookieConsentGDPR=true; FTConsent=behaviouraladsOnsite%3Aon%2CcookiesOnsite%3Aon%2CcookiesUseraccept%3Aon%2CdemographicadsOnsite%3Aon%2CenhancementByemail%3Aon%2CenhancementByfax%3Aoff%2CenhancementByphonecall%3Aon%2CenhancementBypost%3Aoff%2CenhancementBysms%3Aoff%2CmarketingByemail%3Aon%2CmarketingByfax%3Aoff%2CmarketingByphonecall%3Aon%2CmarketingBypost%3Aoff%2CmarketingBysms%3Aoff%2CmembergetmemberByemail%3Aoff%2CpermutiveadsOnsite%3Aon%2CpersonalisedmarketingOnsite%3Aon%2CprogrammaticadsOnsite%3Aon%2CrecommendedcontentOnsite%3Aon; ft-access-decision-policy=SUBSCRIPTION_POLICY; _gcl_au=1.1.1926413018.1750851393; permutive-id=e7434414-81d3-4f46-90ee-a8d43eb7a9d4; _clck=1ns0jwc%7C2%7Cfx2%7C0%7C2002; zit.data.toexclude=0; _sxh=1697,; _sanba=0; _sxo={"R":1,"tP":0,"tM":0,"sP":1,"sM":0,"dP":2,"dM":0,"dS":2,"tS":0,"cPs":110,"lPs":[0,1],"sSr":1,"sWids":[],"wN":0,"cdT":-3934855,"F":1,"RF":1,"w":0,"SFreq":2,"last_wid":0,"bid":1036,"accNo":"","clientId":"","isEmailAud":0,"isPanelAud":0,"hDW":0,"isRegAud":0,"isExAud":0,"isDropoff":0,"devT":0,"exPW":0,"Nba":-1,"userName":"","dataLayer":"","localSt":"","emailId":"","emailTag":"","subTag":"","lVd":"2025-6-25","oS":"04847631-184a-4910-a76e-3892c91366bc","cPu":"https://www.ft.com/content/611fb4d1-1939-4401-85b7-1ba5d4455619","pspv":1,"pslv":78,"pssSr":0,"pswN":0,"psdS":1,"pscdT":0,"RP":0,"TPrice":0,"ML":"","isReCaptchaOn":false,"reCaptchaSiteKey":"","reCaptchaSecretKey":"","extRefer":"","dM2":0,"tM2":0,"sM2":0,"RA":0,"ToBlock":-1,"CC":null,"groupName":null}; _rdt_uuid=1750851396587.6a607f35-d4d7-4e2f-96e1-04902e277545; _uetsid=a6f9260051b811f0923ad1ede329d52b; _uetvid=a6f920b051b811f0ae4ec11306f031b9; _fs_cd_cp_pRdRgnTnF68pCV2F=AQ3CGJRPBRKsEgGDQjhrv7pIFfr0PC2JJpQQzFnyXMs_qxPHpD7bq4xdn-A31TGGdIKuWQPB5XsAbpTMhL1kvNl0J10jE7WGujba5Q0Zj8WyJAFcTbq3_7o0gT15Z2T5oU7PV_oOpfdxm7bVo-ba55U2PnEJ; OriginalReferer=None; FtComEntryPoint=/content/e55f27db-3ebe-44fd-b621-228238ca04ef; _chartbeat2=.1750851374835.1750866623657.1.BOIaXABRAW9WBZMdo5BWQ0CzBdTfdf.1; _cb_svref=external; __gads=ID=0d9ac09dfad25a9b:T=1750851377:RT=1750867162:S=ALNI_MZN-61XF085hK9f1hf9JFrcawkV1Q; __eoi=ID=ffefd9a920b0f0f5:T=1750851377:RT=1750867162:S=AA-AfjZUEgD-sqti7ciYSJO2mmKl; _chartbeat5=666|1222|www.ft.com%2F%3Fedition%3Dinternational|https%3A%2F%2Fwww.ft.com%2Fcontent%2Fe4b862cf-2c62-42a4-9d70-724f8ed66d64|Cg-elmGvS87BT8tyLCsE6D8GZoYX||c|Dlr6uODCtBUFDyynRYBDwQgYBtMiF3|ft.com|; _chartbeat4=t=Clj6YBDimVB_H-z7KB8hVtfCs_ZIl&E=36&x=187&c=37.27&y=9962&w=1352'''
    raw_cookie = raw_input.strip()
    writer = CookieWriter()
    writer.write_raw(domain, raw_cookie)
