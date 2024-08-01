import streamlit as st
from page_resources import dump_to_json, init_page_cache, load_dmv, edit_pages, delete_page_list, delete_translate_page

pn = "设置"

init_page_cache()

if st.session_state['av'].get_current_app() != 'setting':
    if st.session_state['av'].get_current_app() != 'home':
        dump_to_json()
    st.session_state['av'].set_current_app('setting')
    st.session_state.messages = []
    st.rerun()

st.sidebar.subheader('设置')
st.sidebar.button("OpenAI")

openai_config = st.session_state['llm'].get_openai()
openai_api_key = st.text_input("OpenAI API密钥", placeholder = openai_config[0])
openai_model_name = st.text_input("OpenAI模型名称", placeholder = openai_config[1])

if not openai_api_key:
    openai_api_key = openai_config[0]
if not openai_model_name:
    openai_model_name = openai_config[1]

c11, c12 = st.columns(2)

if c11.button("确定", key='OpenAI确定'):
    st.session_state['llm'].set_openai(openai_api_key, openai_model_name)
    st.rerun()

if c12.button("恢复默认设置", key='OpenAI默认'):
    temp = load_dmv().get_default_openai()
    st.session_state['llm'].set_openai(temp[0], temp[1])
    st.rerun()

#edit_pages(pn)
