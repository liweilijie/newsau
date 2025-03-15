import os
import time
import logging
from datetime import datetime, timedelta
from typing import Optional

from openai import OpenAI
from newsau.settings import OPENAI_API_KEY
from newsau.settings import DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL

logger = logging.getLogger('ai')
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY


# ------------------ 基础重试逻辑 ------------------
class BaseTranslator:
    def _retry_api_call(self, call_func, func_desc: str, max_retries: int, delay: int) -> Optional[str]:
        start_time = time.time()
        retries = 0
        while retries < max_retries:
            try:
                logger.info(f"{func_desc} attempt {retries}")
                result = call_func()
                elapsed = time.time() - start_time
                logger.info(f"{func_desc} succeeded in {elapsed:.2f} seconds, result: {result}")
                if result is None or result.strip() == "":
                    raise ValueError(f"{func_desc} returned empty result")
                return result
            except Exception as e:
                logger.error(f"{func_desc} attempt {retries} error: {e}")
                retries += 1
                if retries < max_retries:
                    time.sleep(delay)
                else:
                    logger.error(f"{func_desc} exceeded max retries ({max_retries}), giving up.")
                    return None


# ------------------ OpenAI 翻译器 ------------------
class OpenAiTranslator(BaseTranslator):
    def __init__(self):
        self.models = {
            'gpt_4_turbo': 'gpt-4-turbo',
            'gpt_4': 'gpt-4',
            'gpt_4o_mini': 'gpt-4o-mini'
        }
        self.client = OpenAI()
        self.categories = [
            "国际新闻", "中国新闻", "生活指南", "社论点评", "健康医药", "旅游、娱乐",
            "房产、物业", "国际新闻", "澳洲新闻", "人生感悟", "澳洲新闻", "华人参政",
            "华人活动", "投资、理财", "教育、留学", "宗教、信仰", "文学世界", "生命探索",
            "生活品味", "美食养生", "饮食文化"
        ]
        self.newsflashes_tags = [
            "互联网", "人文", "信仰", "心情", "房地产", "旅游", "时政", "最前沿", "金融"
        ]

    def retry_translate_title(self, tr_title: str, max_retries: int = 8, delay: int = 2) -> Optional[str]:
        system_msg = (
            "你是一个中英文翻译专家，用户需要将英文标题翻译成中文，翻译后的字数和原英文字数接近，"
            "不要相差太多，最长也要控制内容在200个字以内，翻译的内容要确保符合中文语言习惯，"
            "利用新闻风格来调整语气和风格，并考虑到某些词语的文化内涵和地区差异。"
            "同时作为翻译家，需将原文翻译成具有信达雅标准的译文。"
            "\"信\" 即忠实于原文的内容与意图；\"达\" 意味着译文应通顺易懂，表达清晰；"
            "\"雅\" 则追求译文的文化审美和语言的优美。"
            "在开头和结尾不要擅自加上'```html'。"
        )

        def api_call():
            completion = self.client.chat.completions.create(
                model=self.models['gpt_4o_mini'],
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": tr_title}
                ]
            )
            message = completion.choices[0].message
            return message.content if message and hasattr(message, 'content') else None

        return self._retry_api_call(api_call, "retry_translate_title (OpenAI)", max_retries, delay)

    def retry_translate_content(self, tr_content: str, max_retries: int = 10, delay: int = 2) -> Optional[str]:
        system_msg = (
            "你是一个中英文翻译专家，用户想将内容翻译成中文，翻译的时候保留html标签，并且在内容的最后总结全篇的思想，"
            "总结性的内容用单独一个div标签包裹，另外不用出来总结两个字，总结性的中文内容不超过200字。"
            "翻译的内容要确保符合中文语言习惯，利用新闻风格来调整语气和风格，并考虑到某些词语的文化内涵和地区差异。"
            "同时作为翻译家，需将原文翻译成具有信达雅标准的译文。"
            "\"信\" 即忠实于原文的内容与意图；\"达\" 意味着译文应通顺易懂，表达清晰；"
            "\"雅\" 则追求译文的文化审美和语言的优美。"
        )

        def api_call():
            completion = self.client.chat.completions.create(
                model=self.models['gpt_4o_mini'],
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": tr_content}
                ]
            )
            message = completion.choices[0].message
            return message.content if message and hasattr(message, 'content') else None

        return self._retry_api_call(api_call, "retry_translate_content (OpenAI)", max_retries, delay)

    def retry_generate_category(self, tr_content: str, max_retries: int = 5, delay: int = 2) -> Optional[str]:
        cate = ",".join(self.categories)
        system_msg = f"请你从给出的新闻内容里面归纳总结出新闻分类，新闻分类只能从这个列表({cate})里面选择一个，结果不要包含新闻分类字样，只要列表里面的分类。"

        def api_call():
            completion = self.client.chat.completions.create(
                model=self.models['gpt_4o_mini'],
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": tr_content}
                ]
            )
            message = completion.choices[0].message
            return message.content if message and hasattr(message, 'content') else None

        return self._retry_api_call(api_call, "retry_generate_category (OpenAI)", max_retries, delay)

    def retry_translate_c2c_title(self, tr_title: str, max_retries: int = 8, delay: int = 2) -> Optional[str]:
        system_msg = (
            "请帮我换一种表达方式改写下面这段话，字数不要超过30个中文字数，最好不要超过原文的字数，"
            "使用抓眼球的醒目简短标题, 标题尽可能简短精炼，可以正式一点，学术一点，新闻一点的表达。"
            "不要出现'标题'这两个字。"
        )

        def api_call():
            completion = self.client.chat.completions.create(
                model=self.models['gpt_4_turbo'],
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": tr_title}
                ]
            )
            message = completion.choices[0].message
            return message.content if message and hasattr(message, 'content') else None

        return self._retry_api_call(api_call, "retry_translate_c2c_title (OpenAI)", max_retries, delay)

    def retry_translate_c2c_content(self, tr_content: str, max_retries: int = 10, delay: int = 2) -> Optional[str]:
        system_msg = (
            "用户想将原来的内容用另外一种表达方式进行描述，描述的字数尽可能的和原来保持一致，可以偏差但是不要太大，"
            "请一定要保留原来的html标签，并且在内容的最后总结全篇的思想，总结性的内容用单独一个div标签包裹，"
            "另外不用出来总结两个字，总结性的中文内容不超过200字。"
            "另外一种表达出来的内容要确保符合中文语言习惯，利用新闻风格来调整语气和风格，"
            "并考虑到某些词语的文化内涵和地区差异。同时作为翻译家，需将原文翻译成具有信达雅标准的译文。"
        )

        def api_call():
            completion = self.client.chat.completions.create(
                model=self.models['gpt_4o_mini'],
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": tr_content}
                ]
            )
            message = completion.choices[0].message
            return message.content if message and hasattr(message, 'content') else None

        return self._retry_api_call(api_call, "retry_translate_c2c_content (OpenAI)", max_retries, delay)

    def retry_generate_c2c_tag(self, tr_content: str, max_retries: int = 5, delay: int = 2) -> Optional[str]:
        cate = ",".join(self.newsflashes_tags)
        system_msg = f"请你从给出的新闻分类里面归纳总结出新闻分类，新闻分类只能从这个列表({cate})里面选择一个，结果不要包含新闻分类字样，只要列表里面的分类。"

        def api_call():
            completion = self.client.chat.completions.create(
                model=self.models['gpt_4o_mini'],
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": tr_content}
                ]
            )
            message = completion.choices[0].message
            return message.content if message and hasattr(message, 'content') else None

        return self._retry_api_call(api_call, "retry_generate_c2c_tag (OpenAI)", max_retries, delay)

class DeepseekAiTranslator(BaseTranslator):
    def __init__(self, api_key=DEEPSEEK_API_KEY, base_url=DEEPSEEK_BASE_URL):
        # 初始化 deepseek 客户端，假设 DeepSeekApi 已提供类似 chat.completions.create 的接口
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def retry_translate_title(self, tr_title: str, max_retries: int = 5, delay: int = 2) -> Optional[str]:
        system_msg = (
            "你是一个中英文翻译专家，用户需要将英文标题翻译成中文，翻译后的字数和原英文字数接近，"
            "不要相差太多，最长也要控制内容在200个字以内，翻译的内容要确保符合中文语言习惯，"
            "利用新闻风格来调整语气和风格，并考虑到某些词语的文化内涵和地区差异。"
            "同时作为翻译家，需将原文翻译成具有信达雅标准的译文。"
            "在开头和结尾不要擅自加上'```html'。最终的结果不要有解析说明，只需要有干干净净的翻译结果即可。"
            "作为专业中英翻译专家，严格遵循："
            "1. 仅返回最终译文"
            "2. 禁用任何注释/说明"
            "3. 字数与原文匹配"
            "4. 专业术语准确"
        )
        def api_call():
            completion = self.client.chat.completions.create(
                model="deepseek-reasoner",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": tr_title}
                ]
            )
            message = completion.choices[0].message
            return message.content if message and hasattr(message, 'content') else None
        return self._retry_api_call(api_call, "retry_translate_title (Deepseek)", max_retries, delay)

    def retry_translate_content(self, tr_content: str, max_retries: int = 5, delay: int = 2) -> Optional[str]:
        system_msg = (
            "你是一个中英文翻译专家，用户想将内容翻译成中文，翻译时请保留HTML标签，并在内容最后总结全篇思想，"
            "总结性内容使用单独一个div标签包裹，且中文总结不超过200字。同时确保译文符合中文语言习惯，不使用'总结'等显性引导词,表现得自然一点。\n"
            "补充段落与正文保持连贯\n"
            "利用新闻风格调整语气和风格，并考虑词语的文化内涵与地区差异。最终的结果不要有解析说明，只需要有干干净净的翻译结果即可。\n"
            "文化意象自动转换（例：'英里'→'公里'）\n"
            "中英新闻翻译要求："
            "1. 仅输出翻译结果"
            "2. 无附加说明"
        )
        def api_call():
            completion = self.client.chat.completions.create(
                model="deepseek-reasoner",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": tr_content}
                ]
            )
            message = completion.choices[0].message
            return message.content if message and hasattr(message, 'content') else None
        return self._retry_api_call(api_call, "retry_translate_content (Deepseek)", max_retries, delay)

    def retry_generate_category(self, tr_content: str, max_retries: int = 5, delay: int = 2) -> Optional[str]:
        cate = "国际新闻,中国新闻,生活指南,社论点评,健康医药,旅游、娱乐,房产、物业,澳洲新闻,人生感悟,华人参政,华人活动,投资、理财,教育、留学,宗教、信仰,文学世界,生命探索,生活品味,美食养生,饮食文化"
        system_msg = f"请你从给出的新闻内容中归纳出新闻分类，新闻分类只能从列表({cate})中选择一个，不要包含多余描述，仅返回列表中的分类。"
        def api_call():
            completion = self.client.chat.completions.create(
                model="deepseek-reasoner",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": tr_content}
                ]
            )
            message = completion.choices[0].message
            return message.content if message and hasattr(message, 'content') else None
        return self._retry_api_call(api_call, "retry_generate_category (Deepseek)", max_retries, delay)

    def retry_translate_c2c_title(self, tr_title: str, max_retries: int = 5, delay: int = 2) -> Optional[str]:
        system_msg = (
            "请帮我换一种表达方式改写下面这段话，要求字数不超过30个中文字，尽量不超过原文，"
            "使用醒目、简短的标题表达，尽可能简洁精炼，风格正式、学术且具新闻感，且不要出现“标题”二字。最终的结果不要有解析说明，只需要有干干净净的翻译结果即可。"
        )
        def api_call():
            completion = self.client.chat.completions.create(
                model="deepseek-reasoner",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": tr_title}
                ]
            )
            message = completion.choices[0].message
            return message.content if message and hasattr(message, 'content') else None
        return self._retry_api_call(api_call, "retry_translate_c2c_title (Deepseek)", max_retries, delay)

    def retry_translate_c2c_content(self, tr_content: str, max_retries: int = 5, delay: int = 2) -> Optional[str]:
        system_msg = (
            "请用另一种表达方式改写下面的内容，要求在保持原文意思的同时保留HTML标签，"
            "并在最后总结全文思想，使用独立div标签包裹总结内容，中文总结不超过200字。最终的结果不要有解析说明，只需要有干干净净的翻译结果即可。"
        )
        def api_call():
            completion = self.client.chat.completions.create(
                model="deepseek-reasoner",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": tr_content}
                ]
            )
            message = completion.choices[0].message
            return message.content if message and hasattr(message, 'content') else None
        return self._retry_api_call(api_call, "retry_translate_c2c_content (Deepseek)", max_retries, delay)

    def retry_generate_c2c_tag(self, tr_content: str, max_retries: int = 5, delay: int = 2) -> Optional[str]:
        cate = "互联网,人文,信仰,心情,房地产,旅游,时政,最前沿,金融"
        system_msg = f"请从以下分类({cate})中选择一个作为新闻标签，不需要多余描述，仅返回分类名称。"
        def api_call():
            completion = self.client.chat.completions.create(
                model="deepseek-reasoner",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": tr_content}
                ]
            )
            message = completion.choices[0].message
            return message.content if message and hasattr(message, 'content') else None
        return self._retry_api_call(api_call, "retry_generate_c2c_tag (Deepseek)", max_retries, delay)


# ------------------ Unified 翻译器 ------------------
class UnifiedTranslator:
    def __init__(self):
        self.deepseek_translator = DeepseekAiTranslator()
        self.openai_translator = OpenAiTranslator()
        self.last_successful = "deepseek"  # 默认优先 Deepseek
        self.last_deepseek_failure = None
        self.retry_interval = timedelta(hours=1)

    def should_retry_deepseek(self) -> bool:
        if self.last_successful == "openai" and self.last_deepseek_failure:
            return datetime.now() - self.last_deepseek_failure >= self.retry_interval
        return False

    def _translate(self, method_name: str, text: str, max_retries: int, delay: int) -> Optional[str]:
        # 如果满足重试条件，则恢复优先 Deepseek
        if self.should_retry_deepseek():
            self.last_successful = "deepseek"
        translator = self.deepseek_translator if self.last_successful == "deepseek" else self.openai_translator

        translate_method = getattr(translator, method_name, None)
        if not translate_method:
            logger.error(f"{self.last_successful} translator does not support method {method_name}")
            return None

        result = translate_method(text, max_retries=max_retries, delay=delay)
        # 若当前为 Deepseek 且翻译失败，则记录失败时间并切换到 OpenAI
        if self.last_successful == "deepseek" and (result is None or result.strip() == ""):
            self.last_successful = "openai"
            self.last_deepseek_failure = datetime.now()
            translate_method = getattr(self.openai_translator, method_name, None)
            if translate_method:
                result = translate_method(text, max_retries=max_retries, delay=delay)
        return result

    # 统一接口
    def retry_translate_title(self, text: str, max_retries: int = 5, delay: int = 2) -> Optional[str]:
        return self._translate("retry_translate_title", text, max_retries, delay)

    def retry_translate_content(self, text: str, max_retries: int = 5, delay: int = 2) -> Optional[str]:
        return self._translate("retry_translate_content", text, max_retries, delay)

    def retry_generate_category(self, text: str, max_retries: int = 5, delay: int = 2) -> Optional[str]:
        return self._translate("retry_generate_category", text, max_retries, delay)

    def retry_translate_c2c_title(self, text: str, max_retries: int = 5, delay: int = 2) -> Optional[str]:
        return self._translate("retry_translate_c2c_title", text, max_retries, delay)

    def retry_translate_c2c_content(self, text: str, max_retries: int = 5, delay: int = 2) -> Optional[str]:
        return self._translate("retry_translate_c2c_content", text, max_retries, delay)

    def retry_generate_c2c_tag(self, text: str, max_retries: int = 5, delay: int = 2) -> Optional[str]:
        return self._translate("retry_generate_c2c_tag", text, max_retries, delay)



# ------------------ 示例调用 ------------------
if __name__ == "__main__":
    sample_content = "<div>示例新闻内容...</div>"
    sample_title = "Example Title to Translate"
    translator = UnifiedTranslator()
    print("Translated Title:", translator.retry_translate_title(sample_title))
    print("Translated Content:", translator.retry_translate_content(sample_content))
