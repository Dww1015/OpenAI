import streamlit as st
from page_resources import dump_to_json, init_page_cache, init_chat_page, clear_chat_history, prompt_setting, init_chat_history, load_ch, llm_context_response, edit_pages

pn = '聊天'
welcome_msg = {"role": "assistant", "content": "欢迎使用聊天"}

init_page_cache()

init_chat_history(pn)

init_chat_page(pn, welcome_msg)

# Sidebar
with st.sidebar:
    st.subheader('功能')
    col1, col2 = st.sidebar.columns(2)

    if col1.button('清除聊天记录'):
        clear_chat_history(welcome_msg)
        load_ch(pn).clear_history()

    if col2.button("提示词"):
        prompt_setting()

if not st.session_state.messages:
    st.session_state.messages = [welcome_msg]
    dump_to_json()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# User-provided prompt
if user_input := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": user_input})
    dump_to_json()
    load_ch(pn).add_message("user", user_input)
    with st.chat_message("user"):
        st.write(user_input)

# Generate a new response if last message is not from assistant
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        res = llm_context_response(pn)
        placeholder = st.empty()
        placeholder.markdown(res)
    st.session_state.messages.append({"role": "assistant", "content": res})
    dump_to_json()
    load_ch(pn).add_message("assistant", res)

#edit_pages(pn)