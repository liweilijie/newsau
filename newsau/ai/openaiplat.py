import os
import time
import logging

from openai import OpenAI
from newsau.settings import OPENAI_API_KEY
logger = logging.getLogger('ai')


os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

# translate all Chinese to English
class OpenAiPlat(object):

    def __init__(self):
        self.gpt_4_turbo = "gpt-4-turbo"
        self.gpt_4 = "gpt-4"
        self.gpt_4o_mini = "gpt-4o-mini"

        self.client = OpenAI()
        self.categories = ["国际新闻", "中国新闻", "生活指南", "社论点评", "健康医药", "旅游、娱乐", "房产、物业", "国际新闻", "澳洲新闻", "人生感悟", "澳洲新闻", "华人参政", "华人活动", "投资、理财", "教育、留学", "宗教、信仰", "文学世界", "生命探索", "生活品味", "美食养生", "饮食文化"]
        self.newsflashes_tags = ["互联网", "人文", "信仰", "心情", "房地产", "旅游", "时政", "最前沿", "金融"]


    def retry_translate_c2c_title(self, tr_title, max_retries=8, delay=2):

        start_time = time.time()
        retries = 0
        while retries < max_retries:
            try:
                print(f"do c2c title the {retries}th retry")

                completion = self.client.chat.completions.create(
                    model=self.gpt_4_turbo,
                    messages=[
                        {
                            "role": "system",
                            "content": "请帮我换一种表达方式改写下面这段话，字数不要超过30个中文字数，最好不要超过原文的字数，使用抓眼球的醒目简短标题, 标题尽可能简短精炼，可以正式一点，学术一点，新闻一点的表达。"
                                       # "content": "请帮我用不同的表达方式改写下面这段话，字数不要超过30个中文字数，最好不要超过原文的字数，使用抓眼球的醒目简短标题, 标题尽可能简短精炼，可以正式一点，学术一点，新闻一点的表达，但是一定要换一种方式表达出来。"
                },
                        {
                            "role": "user",
                            "content": tr_title
                        }
                    ],
                )
                end_time = time.time()
                total_time = end_time - start_time
                print(f"translate title took total time：{total_time:.2f} s")

                if completion is None:
                    raise ValueError("API return is None.")

                # check choices
                if not hasattr(completion, 'choices') or not completion.choices:
                    raise ValueError("API return is not include choices or choices is empty.")

                # check message if exist
                if not hasattr(completion.choices[0], 'message') or completion.choices[0].message is None:
                    raise ValueError("API miss message or message is empty.")

                # check content if exist
                if not hasattr(completion.choices[0].message, 'content') or not completion.choices[0].message.content:
                    raise ValueError("API miss content or content is empty.")

                # successful
                logger.info(f'c2c title:{tr_title}=>{completion.choices[0].message.content}')
                return completion.choices[0].message.content

            except Exception as e:
                print(f"translate title {retries} happened error: {e}")

            retries += 1
            print(f"translate title failed and we will sleep and try again: {retries}th.")
            if retries < max_retries:
                time.sleep(delay)
            else:
                print(f"finally we translated too many times {max_retries} and give up this translator.")
                return None

    def retry_generate_c2c_tag(self, tr_content, max_retries=5, delay=2):

        start_time = time.time()
        retries = 0
        cate = ",".join(self.newsflashes_tags)
        while retries < max_retries:
            try:
                logger.info(f"generate c2c tag the {retries}th retry")

                completion = self.client.chat.completions.create(
                    model=self.gpt_4o_mini,
                    messages=[
                        {
                            "role": "system",
                            "content": f"请你从给出的新闻分类里面归纳总结出新闻分类，新闻分类只能从这个列表({cate})里面选择一个，结果不要包含新闻分类字样，只要列表里面的分类。"
                        },
                        {
                            "role": "user",
                            "content": tr_content
                        }
                    ],
                )
                end_time = time.time()
                total_time = end_time - start_time
                logger.info(f"generate c2c tag took total time：{total_time:.2f} s")

                if completion is None:
                    raise ValueError("API return is None.")

                # check choices
                if not hasattr(completion, 'choices') or not completion.choices:
                    raise ValueError("API return is not include choices or choices is empty.")

                # check message if exist
                if not hasattr(completion.choices[0], 'message') or completion.choices[0].message is None:
                    raise ValueError("API miss message or message is empty.")

                # check content if exist
                if not hasattr(completion.choices[0].message, 'content') or not completion.choices[0].message.content:
                    raise ValueError("API miss content or content is empty.")

                # successful
                return completion.choices[0].message.content

            except Exception as e:
                print(f"generate category {retries} happened error: {e}")

            retries += 1
            logger.error(f"generate tag failed and we will sleep and try again: {retries}th.")
            if retries < max_retries:
                time.sleep(delay)
            else:
                logger.error(f"finally we translated too many times {max_retries} and give up this translator.")
                return None

    def retry_translate_c2c_content(self, tr_content, max_retries=10, delay=2):

        start_time = time.time()
        retries = 0

        while retries < max_retries:
            try:
                logger.info(f"translate c2c content and the {retries}th retry")

                completion = self.client.chat.completions.create(
                    model=self.gpt_4o_mini,
                    messages=[
                        {
                            "role": "system",
                            "content": "用户想将原来的内容用另外一种表达方式进行描述，描述的字数尽可能的和原来保持一致，可以偏差但是不要太大，请一定要保留原来的html标签，并且在内容的最后总结全篇的思想，总结性的内容用单独一个div标签包裹，另外不用出来总结两个字，总结性的中文内容不超过200字。另外一种表达出来的内容要确保符合中文语言习惯，利用新闻风格来调整语气和风格，并考虑到某些词语的文化内涵和地区差异。同时作为翻译家，需将原文翻译成具有信达雅标准的译文。\"信\" 即忠实于原文的内容与意图；\"达\" 意味着译文应通顺易懂，表达清晰；\"雅\" 则追求译文的文化审美和语言的优美。目标是创作出既忠于原作精神，又符合目标语言文化和读者审美的表达。"
                        },
                        {
                            "role": "user",
                            "content": tr_content,
                        }
                    ],
                )

                end_time = time.time()
                total_time = end_time - start_time
                logger.info(f"translate c2c content took total time：{total_time:.2f} s")

                if completion is None:
                    raise ValueError("API return is None.")

                # check choices
                if not hasattr(completion, 'choices') or not completion.choices:
                    raise ValueError("API return is not include choices or choices is empty.")

                # check message if exist
                if not hasattr(completion.choices[0], 'message') or completion.choices[0].message is None:
                    raise ValueError("API miss message or message is empty.")

                # check content if exist
                if not hasattr(completion.choices[0].message, 'content') or not completion.choices[0].message.content:
                    raise ValueError("API miss content or content is empty.")

                # successful
                rst = completion.choices[0].message.content
                logger.info(f'origin: {tr_content}\nnew:{rst}')
                return rst

            except Exception as e:
                logger.error(f"translate title {retries} happened error: {e}")

            retries += 1
            logger.error(f"translate title failed and we will sleep and try again: {retries}th.")
            if retries < max_retries:
                time.sleep(delay)
            else:
                logger.error(f"finally we translated too many times {max_retries} and give up this translator.")
                return None



    def retry_generate_category(self, tr_content, max_retries=5, delay=2):

        start_time = time.time()
        retries = 0
        cate = ",".join(self.categories)
        while retries < max_retries:
            try:
                print(f"generate category the {retries}th retry")

                completion = self.client.chat.completions.create(
                    model=self.gpt_4o_mini,
                    messages=[
                        {
                            "role": "system",
                            "content": f"请你从给出的新闻内容里面归纳总结出新闻分类，新闻分类只能从这个列表({cate})里面选择一个，结果不要包含新闻分类字样，只要列表里面的分类。"
                        },
                        {
                            "role": "user",
                            "content": tr_content
                        }
                    ],
                )
                end_time = time.time()
                total_time = end_time - start_time
                print(f"generate category took total time：{total_time:.2f} s")

                if completion is None:
                    raise ValueError("API return is None.")

                # check choices
                if not hasattr(completion, 'choices') or not completion.choices:
                    raise ValueError("API return is not include choices or choices is empty.")

                # check message if exist
                if not hasattr(completion.choices[0], 'message') or completion.choices[0].message is None:
                    raise ValueError("API miss message or message is empty.")

                # check content if exist
                if not hasattr(completion.choices[0].message, 'content') or not completion.choices[0].message.content:
                    raise ValueError("API miss content or content is empty.")

                # successful
                print(completion)
                return completion.choices[0].message.content

            except Exception as e:
                print(f"generate category {retries} happened error: {e}")

            retries += 1
            print(f"generate category failed and we will sleep and try again: {retries}th.")
            if retries < max_retries:
                time.sleep(delay)
            else:
                print(f"finally we translated too many times {max_retries} and give up this translator.")
                return None



    def retry_translate_title(self, tr_title, max_retries=8, delay=2):

        start_time = time.time()
        retries = 0
        while retries < max_retries:
            try:
                print(f"do title the {retries}th retry")

                completion = self.client.chat.completions.create(
                    model=self.gpt_4o_mini,
                    messages=[
                        {
                            "role": "system",
                            "content": "你是一个中英文翻译专家，用户需要将英文标题翻译成中文，翻译后的字数和原英文字数接近,不要相差太多，最长也要控制内容在200个字以内，翻译的内容要确保符合中文语言习惯，利用新闻风格来调整语气和风格，并考虑到某些词语的文化内涵和地区差异。同时作为翻译家，需将原文翻译成具有信达雅标准的译文。\"信\" 即忠实于原文的内容与意图；\"达\" 意味着译文应通顺易懂，表达清晰；\"雅\" 则追求译文的文化审美和语言的优美。目标是创作出既忠于原作精神，又符合目标语言文化和读者审美的翻译。在开头和结尾不要擅自加上'```html'"
                        },
                        {
                            "role": "user",
                            "content": tr_title
                        }
                    ],
                )
                end_time = time.time()
                total_time = end_time - start_time
                print(f"translate title took total time：{total_time:.2f} s")

                if completion is None:
                    raise ValueError("API return is None.")

                # check choices
                if not hasattr(completion, 'choices') or not completion.choices:
                    raise ValueError("API return is not include choices or choices is empty.")

                # check message if exist
                if not hasattr(completion.choices[0], 'message') or completion.choices[0].message is None:
                    raise ValueError("API miss message or message is empty.")

                # check content if exist
                if not hasattr(completion.choices[0].message, 'content') or not completion.choices[0].message.content:
                    raise ValueError("API miss content or content is empty.")

                # successful
                print(completion)
                return completion.choices[0].message.content

            except Exception as e:
                print(f"translate title {retries} happened error: {e}")

            retries += 1
            print(f"translate title failed and we will sleep and try again: {retries}th.")
            if retries < max_retries:
                 time.sleep(delay)
            else:
                 print(f"finally we translated too many times {max_retries} and give up this translator.")
                 return None


    def retry_translate_content(self, tr_content, max_retries=10, delay=2):

        start_time = time.time()
        retries = 0

        while retries < max_retries:
            try:
                print(f"translate content and the {retries}th retry")

                completion = self.client.chat.completions.create(
                    model=self.gpt_4o_mini,
                    messages=[
                        {
                            "role": "system",
                            "content": "你是一个中英文翻译专家，用户想将内容翻译成中文，翻译的时候保留html标签，并且在内容的最后总结全篇的思想，总结性的内容用单独一个div标签包裹，另外不用出来总结两个字，总结性的中文内容不超过200字。翻译的内容要确保符合中文语言习惯，利用新闻风格来调整语气和风格，并考虑到某些词语的文化内涵和地区差异。同时作为翻译家，需将原文翻译成具有信达雅标准的译文。\"信\" 即忠实于原文的内容与意图；\"达\" 意味着译文应通顺易懂，表达清晰；\"雅\" 则追求译文的文化审美和语言的优美。目标是创作出既忠于原作精神，又符合目标语言文化和读者审美的翻译。"
                        },
                        {
                            "role": "user",
                            "content": tr_content,
                        }
                    ],
                )

                end_time = time.time()
                total_time = end_time - start_time
                print(f"translate content took total time：{total_time:.2f} s")

                if completion is None:
                    raise ValueError("API return is None.")

                # check choices
                if not hasattr(completion, 'choices') or not completion.choices:
                    raise ValueError("API return is not include choices or choices is empty.")

                # check message if exist
                if not hasattr(completion.choices[0], 'message') or completion.choices[0].message is None:
                    raise ValueError("API miss message or message is empty.")

                # check content if exist
                if not hasattr(completion.choices[0].message, 'content') or not completion.choices[0].message.content:
                    raise ValueError("API miss content or content is empty.")

                # successful
                return completion.choices[0].message.content

            except Exception as e:
                print(f"translate title {retries} happened error: {e}")

            retries += 1
            print(f"translate title failed and we will sleep and try again: {retries}th.")
            if retries < max_retries:
                time.sleep(delay)
            else:
                print(f"finally we translated too many times {max_retries} and give up this translator.")
                return None


if __name__ == "__main__":

    content = """
    <div class="ArticleRender_article__7i2EW"><p class="paragraph_paragraph__iYReA">Holly McNamara celebrated her Matildas call-up by scoring a first-half hat-trick to deliver unbeaten A-League Women leaders Melbourne City a 5-1 win over Western United.</p><p class="paragraph_paragraph__iYReA">Brilliant attacker McNamara, 22, was on Tuesday named in <a class="Link_link__kR0xA Link_link__5eL5m ScreenReaderOnly_srLinkHint__OysWz Link_showVisited__C1Fea Link_showFocus__ALyv2" data-component="Link" data-uri="coremedia://article/104894584" href="/news/2025-02-04/matildas-name-23-player-squad-shebelieves-cup/104894584">Australia's squad for the SheBelieves Cup</a>, which includes matches against Japan, the United States and Colombia, later this month.</p><p class="paragraph_paragraph__iYReA">It is the three-cap Matilda's first call-up in two years, and first since returning from a third ACL tear.</p><p class="paragraph_paragraph__iYReA">McNamara scored in the third minute before Western United skipper Chloe Logarzo, who was overlooked for the Matildas, levelled the scores with a wonderful long-range strike in the 26th.</p><p class="paragraph_paragraph__iYReA">But McNamara tapped home in the 36th minute then completed her hat-trick with a wonderful chip two minutes later, before being substituted with apparent cramp in the 57th minute.</p><p class="paragraph_paragraph__iYReA">She now has six goals for the season, plus an assist, while City sit five points clear of second-placed Melbourne Victory.</p><figure class="ContentAlignment_marginBottom__4H_6E ContentAlignment_overflowAuto__c1_IL ContentAlignment_outdentDesktop__ijbiK Figure_figure__xLyBy Figure_docImage__DSvk4" data-component="Figure" data-print="inline-media" data-uri="coremedia://imageproxy/104902244" id="104902244"><div class="Figure_content__8xRH4"><div class="FigureContent_content__GnImC"><div class="ContentImage_ratio__0yYeG"><div class="AspectRatio_container__FC_XH" data-component="AspectRatioContainer" style="--aspect-ratio:1.5"><img alt="Holly McNamara points" class="Image_image__5tFYM ContentImage_image__DQ_cq" data-component="Image" data-lazy="true" loading="lazy" sizes="100vw" src="https://cdn.emacsvi.com/news/abc/2025-02/dc886/364841b22c.jpg"/></div></div></div></div><figcaption class="Figure_caption__fS2lN"><p class="Typography_base__sj2RP FigureCaption_text__zDxQ5 Typography_sizeMobile12__w_FPC Typography_lineHeightMobile20___U7Vr Typography_regular__WeIG6 Typography_colourInherit__dfnUx" data-component="Typography">Holly McNamara has scored six goals this season.<!-- --> <cite>(<span>Getty Images: Kelly Defina</span>)</cite></p></figcaption></figure><p class="paragraph_paragraph__iYReA">Rhianna Pollicina, who assisted in two of McNamara's goals, added a fourth in the 59th minute, before Lourdes Bosch completed the rout in the 71st, ensuring City's first ever win over their crosstown rivals.</p><aside class="ContentAlignment_marginBottom__4H_6E ContentAlignment_overflowAuto__c1_IL ContentAlignment_floatRight__nfR_t RelatedCard_relatedCard__4Im5s interactive_focusContext__yRhc_ interactive_defaults__AKxUU interactive_hoverContext__LDUDX interactive_defaults__AKxUU" data-component="RelatedCard" data-uri="coremedia://article/104902206"><a class="RelatedCard_link__rsgR9 FullBleedLink_root__lTw_U interactive_focusContext__yRhc_ interactive_defaults__AKxUU FullBleedLink_showVisited__g3Xvz" href="/news/2025-02-04/matildas-name-23-player-squad-shebelieves-cup/104894584"><h3 class="Typography_base__sj2RP RelatedCard_heading__S_nm2 Typography_sizeMobile18__eJCIB Typography_lineHeightMobile24__crkfh Typography_bold__FqafP Typography_serif__qU2V5 Typography_colourInherit__dfnUx" data-component="Typography">Fowler back in green and gold for Matildas</h3><div aria-hidden="true" class="Panel_root__dh8kN FullBleedLink_expander__yoyds interactive_focusTarget__KyPuK interactive_inset__Gs5Xy" data-panel="true"></div></a><div class="Thumbnail_mediaThumbnail__U4Q53 Thumbnail_fill__leMSg" data-component="Thumbnail"><span class="ScreenReaderOnly_srOnly__bnJwm" data-component="ScreenReaderOnly" id="thumbnail-undefined">Photo shows <!-- -->Mary Fowler warming up before a match, looking at the crowd</span><img alt="Mary Fowler warming up before a match, looking at the crowd" class="Image_image__5tFYM Thumbnail_image__wkJbb interactive_hoverZoomTarget__NejVm" data-component="Image" loading="lazy" src="https://cdn.emacsvi.com/news/abc/2025-02/dc886/1818be6e3d.jpg"/></div><p class="Typography_base__sj2RP RelatedCard_synopsis__cFwMW Typography_sizeMobile14__u7TGe Typography_lineHeightMobile20___U7Vr Typography_regular__WeIG6 Typography_colourInherit__dfnUx" data-component="Typography">A rejuvenated and in-form Mary Fowler has been named to return to the Matildas set-up after opting to withdraw from the side's most recent international window.</p></aside><p class="paragraph_paragraph__iYReA">But there were concerns over United midfielder Melissa Taranto, who suffered a potentially serious left knee injury in the build-up to Pollicina's goal.</p><p class="paragraph_paragraph__iYReA">City opened the scoring when McNamara played the ball to Pollicina, who found her again with a wonderful through ball.</p><p class="paragraph_paragraph__iYReA">McNamara burst forward to get away one-on-one with Matildas goalkeeper Chloe Lincoln, who denied her first strike with an outstretched leg, before the striker controlled the rebound and buried her second attempt.</p><p class="paragraph_paragraph__iYReA">McNamara could have made it 2-0 in the 19th minute but took a loose touch as she charged towards Lincoln, who brilliantly blocked her attempt on goal.</p><p class="paragraph_paragraph__iYReA">Seven minutes later, City lost the ball under pressure and Logarzo unleashed a powerful, fizzing long-range strike.</p><p class="paragraph_paragraph__iYReA">City goalkeeper Malena Mieres denied several United attacks, before Bosch went on a dazzling run down the right then cut the ball back for McNamara to tap home.</p><p class="paragraph_paragraph__iYReA">Two minutes later, Pollicina brilliantly found McNamara, who spotted Lincoln off her line and deftly chipped her.</p><p class="paragraph_paragraph__iYReA">McNamara's return to the field is a heartwarming story of perseverance.</p><p class="paragraph_paragraph__iYReA">"It's just time. A lot of time," she told Paramount Plus in November of her return from yet another ACL injury.</p><p class="paragraph_paragraph__iYReA">"Finding that right balance, getting all those numbers I need to get it. It's a million things into one." </p><p class="paragraph_paragraph__iYReA">Logarzo hit the crossbar in the 54th minute but five minutes later Mariana Speckmaier slipped through Pollicina to score, before Bosch added a fifth.</p><p class="paragraph_paragraph__iYReA">City travel to face Newcastle on Saturday while sixth-placed United play Sydney FC away on Sunday.</p><p class="paragraph_paragraph__iYReA"><strong>AAP/ABC</strong></p><aside class="ContentAlignment_marginBottom__4H_6E ContentAlignment_overflowAuto__c1_IL ContentAlignment_floatRight__nfR_t RelatedCard_relatedCard__4Im5s interactive_focusContext__yRhc_ interactive_defaults__AKxUU interactive_hoverContext__LDUDX interactive_defaults__AKxUU" data-component="RelatedCard" data-uri="coremedia://externallink/101115870"><a class="RelatedCard_link__rsgR9 FullBleedLink_root__lTw_U interactive_focusContext__yRhc_ interactive_defaults__AKxUU FullBleedLink_showVisited__g3Xvz" href="https://www.abc.net.au/radio/programs/abc-sport-daily"><h3 class="Typography_base__sj2RP RelatedCard_heading__S_nm2 Typography_sizeMobile18__eJCIB Typography_lineHeightMobile24__crkfh Typography_bold__FqafP Typography_serif__qU2V5 Typography_colourInherit__dfnUx" data-component="Typography">ABC Sport Daily podcast</h3><div aria-hidden="true" class="Panel_root__dh8kN FullBleedLink_expander__yoyds interactive_focusTarget__KyPuK interactive_inset__Gs5Xy" data-panel="true"></div></a><div class="Thumbnail_mediaThumbnail__U4Q53 Thumbnail_fill__leMSg" data-component="Thumbnail"><img alt="" class="Image_image__5tFYM Thumbnail_image__wkJbb interactive_hoverZoomTarget__NejVm" data-component="Image" loading="lazy" src="https://cdn.emacsvi.com/news/abc/2025-02/dc886/05a2d3fad1.jpg"/></div><p class="Typography_base__sj2RP RelatedCard_synopsis__cFwMW Typography_sizeMobile14__u7TGe Typography_lineHeightMobile20___U7Vr Typography_regular__WeIG6 Typography_colourInherit__dfnUx" data-component="Typography">ABC Sport Daily is your daily sports conversation. We dive into the biggest story of the day and get you up to speed with everything else that's making headlines.</p></aside><div data-component="EmbedBlock"><div class="Panel_root__dh8kN Newsletter_newsletterContainer__VPEvh undefined" data-component="Newsletter" data-panel="true"><div class="Panel_content__qJqjK Panel_responsive__XVabU"><div class="Rail_header__cjOJE Newsletter_header__WdIsB"><h2 class="Typography_base__sj2RP Rail_heading__L1PE4 Typography_sizeMobile24__GzKLB Typography_sizeDesktop32__LR_G6 Typography_lineHeightMobile28__58YCp Typography_lineHeightDesktop36__PAEA8 Typography_bold__FqafP Typography_colourInherit__dfnUx Typography_normalise__u5o1s" data-component="Typography">The ABC of SPORT</h2><div class="Typography_base__sj2RP Rail_subHeading__H6gKX Typography_sizeMobile12__w_FPC Typography_sizeDesktop16__zyLf4 Typography_lineHeightMobile14__qdqYi Typography_lineHeightDesktop24__Fh_y5 Typography_regular__WeIG6 Typography_colourInherit__dfnUx" data-component="Typography">Sports content to make you think... or allow you not to. A newsletter delivered each Saturday.</div></div><div class="Newsletter_newsletterForm__bODLx" data-component="NewsletterForm"><div class="Newsletter_subscribeForm__G0_KS"><div class="SubscribeForm_container__2Ija8"><div class="SubscribeForm_privacyWrapper__0fLl3"><div class="PrivacyStatement_privacyStatement__B0_5O" data-component="PrivacyStatement">Your information is being handled in accordance with the<!-- --> <a class="PrivacyStatement_privacyStatementLink__9e8TJ Link_link__5eL5m ScreenReaderOnly_srLinkHint__OysWz Link_showFocus__ALyv2" data-component="Link" href="https://help.abc.net.au/hc/en-us/articles/360001511015" target="_blank">ABC Privacy Collection Statement</a>.</div></div><form class="SubscribeForm_form__oJHOQ" data-component="SubscribeForm" novalidate=""><div class="SubscribeForm_input__94dT1" data-component="TextInput"><label class="TextInput_label__0JU9o ScreenReaderOnly_srOnly__bnJwm" data-component="ScreenReaderOnly" for="subscribe-form-email-address">Email address</label><div class="TextInput_relative__aJzPt"><input aria-invalid="false" class="TextInput_inputField__o6Tdo" id="subscribe-form-email-address" name="subscribe-form-email-address" placeholder="Enter your email address" required="" type="email" value=""/></div></div><div class="SubscribeForm_buttonWrapper__yXCdD"><button class="Button_btn___qFSk SubscribeForm_button__Pk8Q7 Button_filled__Z0XIL Button_uppercase__u_om3" data-component="Button" disabled="" type="submit">Subscribe</button></div></form></div></div></div></div></div></div></div>
    """

    title = "acqui Lambie rails against unfair dismissal laws, after claim by staffer she says 'painted nails at their desk'"
    op = OpenAiPlat()
    # print(op.retry_translate_title(title))
    print(op.retry_translate_content(content))
