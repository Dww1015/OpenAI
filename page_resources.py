import streamlit as st
import re
import os
import json
import shutil
from resources import AppVariables, DefaultModelVariables, llmModel, AppConfig, ChatHistory, WarningStatus

# streamlit页面会常用到的函数在这里

# 因为streamlit限制所以用cache_resource形式存储
@st.cache_resource
def load_av():
    av = AppVariables()
    return av

@st.cache_resource
def load_dmv():
    dmv = DefaultModelVariables()
    return dmv

@st.cache_resource
def load_llm():
    llm = llmModel()
    return llm

@st.cache_resource
def load_ac(page_name):
    ac = AppConfig(page_name)
    return ac

@st.cache_resource
def load_ch(pn):
    ch = ChatHistory(pn)
    return ch

@st.cache_resource
def load_ws():
    ws = WarningStatus()
    return ws

# 因为无法保证home页面一定会先运行和保证刷新后依然能运行，每个页面都跑初始化
def init_page_cache():
    if 'av' not in st.session_state:
        st.session_state['av'] = load_av()
    if 'dmv' not in st.session_state:
        st.session_state['dmv'] = load_dmv()
    if 'llm' not in st.session_state:
        st.session_state['llm'] = load_llm()
    if 'ws' not in st.session_state:
        st.session_state['ws'] = load_ws()
        load_ws().set_warning_status("None")
    # 初始化 'messages' 键
    if "messages" not in st.session_state.keys():
        st.session_state.messages = []

def init_chat_history(pn: str):
    if 'ch' not in st.session_state:
        st.session_state['ch'] = load_ch(pn)

# 把聊天记录存储到Resources/"页面名称"/"页面名称".json
def dump_to_json():
    try:
        # 检查并初始化 'av' 键
        if 'av' not in st.session_state:
            st.session_state['av'] = None  # 或者你需要的默认值

        # 确保 'av' 已被正确初始化
        if st.session_state['av'] is not None:
            current_app = st.session_state['av'].get_current_app()
            file_name = f'Resources/{current_app}/{current_app}.json'

            # 确保目录存在
            os.makedirs(os.path.dirname(file_name), exist_ok=True)

            with open(file_name, 'w', encoding='utf-8') as f:
                json.dump(st.session_state.messages, f)
        else:
            print("session_state['av'] is None")
    except Exception as e:
        print(f"无法保存：{current_app}.json, 错误: {e}")
        pass

# 从文件中加载聊天记录
def load_history():
    try:
        # 检查并初始化 'av' 键
        if 'av' not in st.session_state:
            st.session_state['av'] = None  # 或者你需要的默认值

        # 确保 'av' 已被正确初始化
        if st.session_state['av'] is not None:
            current_app = st.session_state['av'].get_current_app()
            file_name = f'Resources/{current_app}/{current_app}.json'

            # 尝试打开并加载 JSON 文件
            if os.path.exists(file_name):
                with open(file_name, encoding='utf-8') as json_file:
                    st.session_state.messages = json.load(json_file)
            else:
                print(f"文件不存在：{file_name}")
        else:
            print("session_state['av'] is None")
    except Exception as e:
        print(f"加载历史记录时发生错误: {e}")
        pass

# 同时从页面和文件中清除聊天记录
def clear_chat_history(welcome_msg: str):
    st.session_state.messages = [welcome_msg]
    dump_to_json()

# 初始化当前页面
def init_chat_page(pn: str, welcome_msg: str):
    # 处理当前页面刷性情况
    if st.session_state['av'].get_current_app() == pn:
        if not st.session_state.messages:
            load_history()

    # 处理从别的页面切换过来情况
    if st.session_state['av'].get_current_app() != pn:
        if (st.session_state['av'].get_current_app() != 'home') & (st.session_state['av'].get_current_app() != 'setting'):
            dump_to_json()

        st.session_state['av'].set_current_app(pn)
        st.session_state.messages = [welcome_msg]
        load_history()
        # 默认刷新一次解决显示滞留问题
        st.rerun()

@st.dialog("提示词设置")
def prompt_setting(pn: str):
    t_prompt = st.text_input("提示词", placeholder=load_ac(pn).get_prompt())

    c1, c2 = st.columns(2)

    if c1.button("确定"):
        load_ac(pn).set_prompt(t_prompt)
        st.rerun()

    if c2.button("恢复默认设置"):
        load_ac(pn).set_prompt(load_ac(pn).get_default_prompt())
        st.rerun()

# 术语标红只标红术语
def format_text_translate(input_text):
    formatted_text = re.sub(r'#(.*?)#', r':red[\1]', input_text)
    return formatted_text

# 错别字标红标红错别字和前后各一个词
def format_text_spellcheck(input_text):
    temp1 = re.sub(r'(.?)#(.*?)#(.?)', r':red[\1\2\3]', input_text)
    temp2 = re.sub(r'#(.*?)#(.?)', r':red[\1\2]', temp1)
    temp3 = re.sub(r'(.?)#(.*?)#', r':red[\1\2]', temp2)
    formatted_text = re.sub(r'#(.*?)#', r':red[\1]', temp3)
    return formatted_text

# 先检测语言，之后根据术语检测把术语加入提示词
def translate_response(pn: str, user_input: str):
    language = st.session_state['llm'].language_detection(user_input)
    contain_term = False
    if language == 0:
        contain_term = load_ac(pn).check_kr(user_input)
    elif language == 1:
        contain_term = load_ac(pn).check_zh(user_input)

    prompt_terms = ""
    if contain_term == True:
        temp = [word for word in load_ac(pn).term_list if word in user_input]
        matches = []
        [matches.append(x) for x in temp if x not in matches]

        # language = 0 韩文，language = 1 中文
        # 查询用户输入中存在的对应的韩文/中文
        for word in matches:
            print(word + " " + load_ac(pn).term_dict[language][word])
            prompt_terms += "请将" + word + "翻译为" + load_ac(pn).term_dict[language][word] + "，"

    prompt = prompt_terms + load_ac(pn).get_prompt()

    translated_text = st.session_state['llm'].llm_agent(prompt, user_input)

    if contain_term == True:
        matches = [word for word in load_ac(pn).term_list[language] if word in user_input]

        for word in matches:
            temp = load_ac(pn).term_dict[language][word].strip()
            translated_text = translated_text.replace(temp, '#' + temp + '#')
    
    return translated_text

# 检测大模型返回结果中的大括号和井号来判定有没有错别字
def spellcheck_response(user_input: str):
    output = ""
    res = st.session_state['llm'].llm_agent(load_ac(pn).get_prompt(), user_input)

    try:
        # 检索大模型返回中包不包括大括号
        exist = re.search(r'{[\S\s]*}', res)
        if exist:
            text1 = exist.group(0)
            # 去除大括号
            text1 = text1[1:-1]
            temp = re.search('[#][^#]+[#]', text1)
            if temp:
                # 分句
                text2 = re.split(r'。|？|！', text1)
                for text in text2:
                    # 检索#来寻找错别字
                    if '#' in text:
                        output += text
                        output += '  \n'
        else:
            print("返回结果无大括号")
            output = "模型识别错误"
    except:
        pass

    if output:
        if output != "模型识别错误":
            output = output[:-3]
    else:
        output = "未检测到错别字"

    return output

# 带上下文的大模型交互
def llm_context_response(pn: str):
    return st.session_state['llm'].llm_context_agent(load_ac(pn).get_prompt(), load_ch(pn).get_chat_history())

def get_warning_status():
    return load_ws().get_warning_status()

def set_warning_status(status: str):
    load_ws().set_warning_status(status)

@st.dialog("创建新翻译聊天页面")
def add_translate_page():
    input = st.text_input("聊天名称", placeholder="")
    t_prompt = input

    if st.button("确定"):
        # 页面名字不能为空
        if t_prompt:
            # 页面名字不能和已有的重复
            if t_prompt in load_av().get_page_names():
                print(f'{t_prompt}页面已存在')
                set_warning_status("Duplicate")
            else:
                try:
                    # 创建新页面并写入标准页面代码
                    page_num = str(load_av().get_page_num() + 1)
                    file = open(f'pages/{page_num}-{t_prompt}.py', 'a')
                    p_name = "\'" + t_prompt + "\'"
                    w_message = "welcome_msg = {\"role\": \"assistant\", \"content\": \"欢迎使用" + p_name + "翻译\"}"
                    content = "from translate_page_template import translate_page\n\npn = " + p_name + "\n" + w_message + "\n\ntranslate_page(pn, welcome_msg)\n"
                    file.write(content)
                    file.close()
                    load_av().add_page(t_prompt)
                except Exception:
                    print(f'pages/{page_num}-{t_prompt}.py 创建失败')

                try:
                    # 创建页面对应的Resource文件夹和json文件
                    os.mkdir(f'Resources/{t_prompt}')
                    config = [p_name, "请将以下中文内容翻译成韩文，内容简洁，不要有翻译腔：", "请将以下中文内容翻译成韩文，内容简洁，不要有翻译腔：", []]
                    history = [{"role": "assistant", "content": f'欢迎使用{t_prompt}翻译'}]

                    config_file_name = f'Resources/{t_prompt}/config.json'
                    with open(config_file_name, 'a', encoding='utf-8') as f:
                        json.dump(config, f)

                    file_name = f'Resources/{t_prompt}/{t_prompt}.json'
                    with open(file_name, 'a', encoding='utf-8') as f:
                        json.dump(history, f)
                    
                    print(f'{t_prompt}页面创建成功')

                except Exception:
                    print(f'Resources/{t_prompt} 创建失败')
        st.rerun()

# 可以删除的页面列表，不能包含主页，设置，错别字，聊天和当前页面
def delete_page_list(current_pn: str):
    page_list = load_av().get_page_names()
    page_list = [value for value in page_list if value != current_pn]
    page_list = [value for value in page_list if value != "home"]
    page_list = [value for value in page_list if value != "设置"]
    page_list = [value for value in page_list if value != "错别字"]
    page_list = [value for value in page_list if value != "聊天"]
    return page_list

def delete_translate_page(pn: str):
    page_num = load_av().get_page_index(pn)
    page_path = f'pages/{page_num}-{pn}.py'
    res_path = f'Resources/{pn}'

    try:
        # 删除Resources里的对应文件夹以及内容
        if os.path.isdir(res_path):
            shutil.rmtree(res_path)
        # 删除pages里的py文件
        if os.path.exists(page_path):
            os.remove(page_path)
    except Exception:
        print(f'{pn} 删除失败')
    
    load_av().remove_page(pn)

# 创建和删除页面的streamlit component
def edit_pages(pn):
    if st.sidebar.button('创建新翻译聊天页面'):
        add_translate_page()

    if get_warning_status() == "Duplicate":
        st.toast("创建新翻译聊天页面，同名页面已存在")
        set_warning_status("None")
    
    selected_page = ""
    selected_page = st.sidebar.selectbox('选择要删除的翻译页面', delete_page_list(pn), index=None, key='selected_page', placeholder = "")

    if st.sidebar.button("删除", key="删除页面"):
        if selected_page:
            delete_translate_page(selected_page)
            st.rerun()
