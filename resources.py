import csv
import os.path

from openai import AzureOpenAI
import requests
import json
import re

# 和文件主要直接交互的class和function都在这里，不包含streamlit相关函数

# 关联文件：app_vars.json
# 页面和功能状态
class AppVariables:

    def __init__(self):
        # 0:当前页面 1:模型种类 2:当前最大页面编号 3:页面名称  4:页面名称和编号对应
        self.app_vars = ['home', True, 11, ["home", "设置", "错别字", "聊天", "DNF-端游-韩翻中",  "DNF-端游-中翻韩", "DNF-手游", "冒险岛-手游", "黑色沙漠-端游", "黑色沙漠-手游", "TGF", "FM"], {"home": 0, "设置": 1, "错别字": 2, "聊天": 3, "DNF-端游-韩翻中": 4, "DNF-端游-中翻韩": 5, "DNF-手游": 6, "冒险岛-手游": 7, "黑色沙漠-端游": 8, "黑色沙漠-手游": 9, "TGF": 10, "FM": 11}]
        try:
            with open('app_vars.json',encoding='utf-8') as json_file:
                self.app_vars = json.load(json_file)
                print("读取成功：app_vars.json")
        except Exception:
            print("app_vars.json无法打开")

    def set_current_app(self, current_app: str):
        self.app_vars[0] = current_app
        try:
            with open('app_vars.json', 'w',encoding='utf-8') as f:
                json.dump(self.app_vars, f)
                print("写入成功：app_vars.json")
        except Exception:
            print("app_vars.json无法打开")

    def get_current_app(self):
        return self.app_vars[0]

    def set_current_model(self, current_model: bool):
        self.app_vars[1] = current_model
        try:
            with open('app_vars.json', 'w',encoding='utf-8') as f:
                json.dump(self.app_vars, f)
                print("写入成功：app_vars.json")
        except Exception:
            print("app_vars.json无法打开")

    def get_current_model(self):
        return self.app_vars[1]
    
    def add_page(self, pn: str):
        # 新建页面时最大页面编码增加
        self.app_vars[2] += 1
        self.app_vars[3].append(pn)
        self.app_vars[4].update({pn: self.app_vars[2]})
        try:
            with open('app_vars.json', 'w',encoding='utf-8') as f:
                json.dump(self.app_vars, f)
                print("写入成功：app_vars.json")
        except Exception:
            print("app_vars.json无法打开")

    # 删除时最大页面编码不减少 这样就不用都重命名
    def remove_page(self, pn: str):
        if pn == "home" or pn == "设置" or pn == "错别字" or pn == "聊天":
            print("无法删除：" + pn)
        else:
            try:
                self.app_vars[3] = [value for value in self.app_vars[3] if value != pn]
                self.app_vars[4].pop(pn)
                with open('app_vars.json', 'w',encoding='utf-8') as f:
                    json.dump(self.app_vars, f)
                    print("写入成功：app_vars.json")
            except Exception:
                print("app_vars.json无法打开")
    
    def get_page_num(self):
        return self.app_vars[2]
    
    def get_page_index(self, pn: str):
        return self.app_vars[4].get(pn)

    def get_page_names(self):
        return self.app_vars[3]

# 关联文件：default_model_vars.json
# 默认模型配置
class DefaultModelVariables:
    def __init__(self):
        # 0: openai_api_key, 1: openai_model_name, 2: azure_endpoint, 3: azure_api_key, 4: azure_model_name, 5: azure_api_version
        self.default_model_vars = ['ntRg23Av0MXK4P709Gj9V5U3XHmJgYx37991Oh9RUbM7neXT', 'gpt-4o', 'https://guoxh4o.openai.azure.com/', '94a744516fcc43ac90948e4d3927e6e0', 'guoxhgpt4o', '2023-05-15']
        try:
            with open('default_model_vars.json',encoding='utf-8') as json_file:
                self.default_model_vars = json.load(json_file)
                print("读取成功：default_model_vars.json")
        except Exception:
            print("default_model_vars.json无法打开")

    def get_default_openai(self):
        output = [self.default_model_vars[0], self.default_model_vars[1]]
        return output

    def get_default_azure(self):
        output = [self.default_model_vars[2], self.default_model_vars[3], self.default_model_vars[4], self.default_model_vars[5]]
        return output

# 关联文件：Resource/"页面名称"/config.json
# 每个页面自己的配置文件，包含名字，提示词，术语文件名字
class AppConfig:
    def __init__(self, name: str):
        # 0: name, 1: prompt, 2: default_prompt 3: terms (list)
        self.app_config = ['', '', '', []]
        # 第一项为韩文，第二项为中文
        self.term_list = [ [] for _ in range(2) ]
        # 第一项为用韩文检索中文，第二项为用中文检索韩文
        self.term_dict = [ {} for _ in range(2) ]
        try:
            file_name= 'Resources/' + name + '/config.json'
            with open(file_name,encoding='utf-8') as json_file:
                self.app_config = json.load(json_file)
                print("读取成功：" + file_name)
        except Exception:
            print(file_name + "无法打开")

        # 录入中韩名词文本
        for filename in self.app_config[3]:
            try:
                with open("Resources/" + name + "/" + filename + ".csv", newline='',encoding='utf-8') as f:
                    reader = csv.reader(f)
                    data = [tuple(row) for row in reader]

                for row in data:
                    # 韩文第一列
                    self.term_list[0].append(row[0])
                    # 中文第二列
                    self.term_list[1].append(row[1])

                    # 韩文检索中文
                    self.term_dict[0][row[0]] = row[1]
                    # 中文检索韩文
                    self.term_dict[1][row[1]] = row[0]

                print(filename + ".csv成功录入")

            except:
                print(filename + ".csv无法打开")

    def set_prompt(self, prompt: str):
        self.app_config[1] = prompt
        try:
            file_name= 'Resources/' + self.app_config[0] + '/config.json'
            with open(file_name, 'w',encoding='utf-8') as f:
                json.dump(self.app_config, f)
                print("写入成功：" + file_name)
        except Exception:
            print(file_name + "无法打开")

    def get_prompt(self):
        return self.app_config[1]

    def get_default_prompt(self):
        return self.app_config[2]

    def get_term_filenames(self):
        return self.app_config[3]

    def check_kr(self, user_input: str):
        res = any(ele in user_input for ele in self.term_list[0])
        if res == False:
            print("未监测到相关韩文术语")
        else:
            print("检测到相关韩文术语")
        return res

    def check_zh(self, user_input: str):
        res = any(ele in user_input for ele in self.term_list[1])
        if res == False:
            print("未监测到相关中文术语")
        else:
            print("检测到相关中文术语")
        return res
    
# 关联文件：Resource/"页面名称"/"页面名称".json
# 读取聊天记录给上下文用，目前只有“聊天”页面有用到
class ChatHistory:
    def __init__(self, name: str):
        self.messages = []
        # 计数用utf-8编码，一个中文字符算3个，openai token计数一个中文字符算1.5个，因此设置为上限128000应该远远达不到超限的程度
        self.MAX_INPUT_TOKENS = 128000
        self.token_count = 0
        try:
            file_name= 'Resources/' + name + '/' + name + '.json'
            with open(file_name,encoding='utf-8') as json_file:
                messages = json.load(json_file)
                for message in messages[1:]:
                    self.messages.append(message)
                    self.token_count += len(message.get("content").encode('utf-8'))

                self.check_MAX()
                print("读取成功：" + file_name)
        except Exception:
            print(file_name + "无法打开")

    def check_MAX(self):
        while self.token_count >= self.MAX_INPUT_TOKENS:
            # 假如token数量超出最大值，把最老的消息去掉
            self.token_count -= len(self.messages[0].get("content").encode('utf-8'))
            self.messages.pop(0)

            # 聊天记录中去掉一条用户消息的话把大模型回复一起去掉
            # 假如有下一条大模型的回复，一起去除
            if len(self.messages) >= 1:
                if self.messages[0].get("role") == "assistant":
                    self.token_count -= len(self.messages[0].get("content").encode('utf-8'))
                    self.messages.pop(0)
    
    def add_message(self, role: str, message: str):
        self.messages.append({"role": role, "content": message})
        self.token_count += len(message.encode('utf-8'))
        self.check_MAX()

    def clear_history(self):
        self.token_count = 0
        self.messages.clear()
    
    def get_chat_history(self):
        self.check_MAX()
        return self.messages
    
# 关联文件：warning_status.json
# 需不需要显示一条警告消息，需要显示什么样的警告消息
class WarningStatus:
    def __init__(self):
        self.warning_status = ["None"]
        try:
            with open('warning.json',encoding='utf-8') as json_file:
                self.warning_status = json.load(json_file)
                print("读取成功：warning.json")
        except Exception:
            print("warning.json无法打开")

    def set_warning_status(self, warning_status: str):
        self.warning_status[0] = warning_status
        try:
            with open('warning.json', 'w',encoding='utf-8') as f:
                json.dump(self.warning_status, f)
                print("写入成功：warning.json")
        except Exception:
            print("warning.json无法打开")

    def get_warning_status(self):
        return self.warning_status[0]

# 接受一个处理好的带消息历史的message object的openai交互函数
def openai_context_agent(messages, api_key: str, model: str, temperature: str):
    url = 'https://api.myhispreadnlp.com/v1/chat/completions'
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': 'Bearer ' + api_key
    }
    data = {
        "model": model,
        "stream": False,
        # "max_tokens": 512,
        "messages": messages,
        "temperature": temperature
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        res = response.json()
        output = res.get('choices')[0].get('message').get('content')
        return output
    else:
        print("Failed to get response:", response.status_code, response.text)
        return "GPT返回异常，请与管理员联系"

# 分别接受用户输入和提示词的openai交互函数
def openai_agent(prompt: str, user_input: str, api_key: str, model: str, temperature: str):
    url = 'https://api.myhispreadnlp.com/v1/chat/completions'
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': 'Bearer ' + api_key
    }
    data = {
        "model": model,
        "stream": False,
        # "max_tokens": 512,
        "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_input},
        ],
        "temperature": temperature
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        res = response.json()
        output = res.get('choices')[0].get('message').get('content')
        return output
    else:
        print("Failed to get response:", response.status_code, response.text)
        return "GPT返回异常，请与管理员联系"

# 分别接受用户输入和提示词的azure openai交互函数
def azure_agent(prompt: str, user_input: str, azure_endpoint: str, api_key: str, model: str, api_version: str, temperature: str):
    try:
        client = AzureOpenAI(
            azure_endpoint = azure_endpoint,
            api_key = api_key,
            api_version = api_version
        )
        response = client.chat.completions.create(
            model = model,  # model = "deployment_name".
            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_input},
            ],
            temperature = temperature,
        )

        return response.choices[0].message.content
    except:
        print("Failed to get response")
        return "GPT返回异常，请与管理员联系"

# 关联文件：model_var.json
# 大模型交互class 模型参数，提示词在这里
class llmModel:
    def __init__(self):
        # Openai: True, Azure: False
        self.model_type = True

        # 0: openai_api_key, 1: openai_model_name, 2: azure_endpoint, 3: azure_api_key, 4: azure_model_name, 5: azure_api_version
        self.model_vars = ['ntRg23Av0MXK4P709Gj9V5U3XHmJgYx37991Oh9RUbM7neXT', 'gpt-4o', 'https://guoxh4o.openai.azure.com/', '94a744516fcc43ac90948e4d3927e6e0', 'guoxhgpt4o', '2023-05-15']

        self.openai_temperature = 0.1
        self.azure_temperature = 0.1

        self.translate_prompt_base = "请将以下中文内容翻译成韩文，内容简洁，不要有翻译腔："
        self.language_detection_prompt = """你是一个翻译助手，请根据用户输入，识别用户的源语言。仅返回用户的源语言，源语言与目标语言仅会从中文和韩文中出现，如果识别源语言不在中文和韩文范围内，返回0，示例：
用户输入：请将以下中文内容翻译成韩文，内容简洁，不要有翻译腔：昨天的晚饭真好吃。
返回：{zh-cn}
用户输入：请将以下内容翻译成中文：괜찮아요, 물건이 도착하면 돼요
返回：{ko_kr}
用户输入：请将以下内容翻译成英文：明天晚上我们去哪里好呢？
返回：{0}"""

        try:
            with open('model_vars.json',encoding='utf-8') as json_file:
                self.model_vars = json.load(json_file)
                print("读取成功：model_vars.json")
        except Exception:
            print("model_vars.json无法打开")

    def set_openai(self, openai_api_key: str, openai_model_name: str):
        self.model_vars[0:2] = [openai_api_key, openai_model_name]
        try:
            with open('model_vars.json', 'w',encoding='utf-8') as f:
                json.dump(self.model_vars, f)
                print("写入成功：model_vars.json")
        except Exception:
            print("model_vars.json无法打开")

    def get_openai(self):
        output = [self.model_vars[0], self.model_vars[1]]
        return output

    def set_azure(self, azure_endpoint: str, azure_api_key: str, azure_model_name: str, azure_api_version: str):
        self.model_vars[2:6] = [azure_endpoint, azure_api_key, azure_model_name, azure_api_version]
        try:
            with open('model_vars.json', 'w',encoding='utf-8') as f:
                json.dump(self.model_vars, f)
                print("写入成功：model_vars.json")
        except Exception:
            print("model_vars.json无法打开")

    def get_azure(self):
        output = [self.model_vars[2], self.model_vars[3], self.model_vars[4], self.model_vars[5]]
        return output
    
    # 不带消息历史的大模型交互函数
    def llm_agent(self, prompt, user_input):
        if self.model_type == True:
            res = openai_agent(prompt, user_input, self.model_vars[0], self.model_vars[1], self.openai_temperature)
        # Azure: False
        else:
            res = azure_agent(prompt, user_input, self.model_vars[2], self.model_vars[3], self.model_vars[4], self.model_vars[5], self.azure_temperature)
        return res
    
    # 带消息历史的大模型交互函数
    def llm_context_agent(self, prompt, chat_history):
        messages = [{"role": "system", "content": prompt}] + chat_history
        res = openai_context_agent(messages, self.model_vars[0], self.model_vars[1], self.openai_temperature)
        return res
    
    def language_detection(self, user_input: str):
        # 检测语言 0是韩文，1是中文，2为其它，-1为无法识别
        language = -1
        res = self.llm_agent(self.language_detection_prompt, user_input)
        # 去除openai回复中除了字母数字_-,空格以外的字符
        try:
            result = re.search("{[a-zA-Z0-9_,， -]+}", res)
            if result:
                # 回复的为源语言
                parsed = result.group(0)

                # 回复为ko_kr则为韩翻中
                if "ko_kr" in parsed:
                    # 查询有没有术语
                    print("检测为韩文")
                    language = 0
                # 回复为zh-cn则为中翻韩
                elif "zh-cn" in parsed:
                    # 查询有没有术语
                    print("检测为中文")
                    language = 1
                # 回复为0则为其它
                elif "0" in parsed:
                    print("检测为其它语言")
                    language = 2
                else:
                    print("未能识别语言种类")
                    language = -1
        except:
            print("未能识别语言种类")
            language = -1
        return language


# 关联文件：Resource/"页面名称"/config.json
# 每个页面自己的配置文件，包含名字，提示词，术语文件名字
class SpecialAppConfig:
    def __init__(self, name: str):
        # 0: name, 1: prompt, 2: default_prompt 3: terms (list)
        self.app_config = ['', '', '', []]
        # 第一项为韩文，第二项为中文
        self.term_list = []
        # 第一项为用韩文检索中文，第二项为用中文检索韩文
        self.term_dict = {}
        try:
            file_name= 'Resources/' + name + '/config.json'
            with open(file_name,encoding='utf-8') as json_file:
                self.app_config = json.load(json_file)
                print("读取成功：" + file_name)
        except Exception:
            print(file_name + "无法打开")

        # 录入中韩名词文本
        for filename in self.app_config[3]:
            try:
                with open("Resources/" + name + "/" + filename + ".csv", newline='',encoding='utf-8') as f:
                    reader = csv.reader(f)
                    data = [tuple(row) for row in reader]

                for row in data:
                    # 原文第一列
                    self.term_list.append(row[0])

                    # 原文检索译文
                    self.term_dict[row[0]] = row[1]

                print(filename + ".csv成功录入")

            except:
                print(filename + ".csv无法打开")

    def set_prompt(self, prompt: str):
        self.app_config[1] = prompt
        try:
            file_name= 'Resources/' + self.app_config[0] + '/config.json'
            with open(file_name, 'w',encoding='utf-8') as f:
                json.dump(self.app_config, f)
                print("写入成功：" + file_name)
        except Exception:
            print(file_name + "无法打开")

    def get_prompt(self):
        return self.app_config[1]

    def get_default_prompt(self):
        return self.app_config[2]

    def get_term_filenames(self):
        return self.app_config[3]

    def check_term(self, user_input: str):
        res = any(ele in user_input for ele in self.term_list)
        if res == False:
            print("未监测到相关术语")
        else:
            print("检测到相关术语")
        return res
