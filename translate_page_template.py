import streamlit as st
from page_resources import dump_to_json, init_page_cache, init_chat_page, clear_chat_history, prompt_setting, format_text_translate, translate_response, edit_pages

# 翻译聊天页面的模版
# 参考：https://github.com/dataprofessor/llama2/tree/master

def translate_page(pn: str, welcome_msg: str):
    init_page_cache()

    init_chat_page(pn, welcome_msg)

    # Sidebar
    with st.sidebar:
        st.subheader('功能')
        col1, col2 = st.sidebar.columns(2)
        if col1.button('清除聊天记录'):
            clear_chat_history(welcome_msg)
        if col2.button("提示词"):
            prompt_setting(pn)

    if not st.session_state.messages:
        st.session_state.messages = [welcome_msg]
        dump_to_json()

    # loop显示所有聊天记录
    # Display or clear chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            formatted_text = format_text_translate(message["content"])
            st.write(formatted_text)

    # 用户输入
    # User-provided prompt
    if user_input := st.chat_input():
        st.session_state.messages.append({"role": "user", "content": user_input})
        dump_to_json()
        with st.chat_message("user"):
            st.write(user_input)

    # 假如上一条消息不是大模型返回的消息，生成一条大模型回复
    # Generate a new response if last message is not from assistant
    if st.session_state.messages[-1]["role"] != "assistant":
        with st.chat_message("assistant"):
            translated_text = translate_response(pn, user_input)
            placeholder = st.empty()
            placeholder.markdown(format_text_translate(translated_text))
        st.session_state.messages.append({"role": "assistant", "content": translated_text})
        dump_to_json()

    #edit_pages(pn)
