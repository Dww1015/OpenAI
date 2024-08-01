import streamlit as st
from page_resources import dump_to_json, init_page_cache, edit_pages

# App title
st.set_page_config(page_title="小助手", initial_sidebar_state = "auto")

pn = "home"

init_page_cache()

st.title("欢迎使用AI智能小助手")
st.write("使用说明及注意事项  \n  \n1.根据工作的使用场景选择不同的功能，这选不同的功能后再进行翻译或错别字校对工作  \n  \n2.在正常使用时，系统中有默认提示词，默认为中翻韩，如果是其他的翻译场景需要自己修改提示词，可点击左侧提示词按钮进行修改  \n  \n注:如果在使用过程中遇到其他问题可以及时与工作人员进行沟通")

if st.session_state.messages:
    print(st.session_state.messages)
    if st.session_state['av'].get_current_app() != 'home':
        if st.session_state['av'].get_current_app() != 'setting':
            dump_to_json()

st.session_state['av'].set_current_app('home')
st.session_state.messages = []

#edit_pages(pn)
