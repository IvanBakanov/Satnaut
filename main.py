# -*- coding: utf-8 -*-

'''
Author: Bakanov I. P.

Version: 26.04.26.0
'''

import streamlit as st
from unit import units_library, check_args, run_engine
from parsers import read_data
from pandas import DataFrame


st.set_page_config(
    layout="wide", 
    page_title="Satnaut"
)

MAIN_COLOR = "#1E3A8A" 

st.markdown(f"""
    <style>
        /* ФОН */
        .stApp {{
            background-color: white;
        }}

        /* КНОПКА */
        div.stButton > button:first-child {{
            background-color: {MAIN_COLOR};
            color: white;
            border-radius: 5px;
            border: none;
        }}
        /* Цвет при наведении на кнопку */
        div.stButton > button:first-child:hover {{
            background-color: #1D4ED8;
            color: white;
            border: none;
        }}

        /* ИСКЛЮЧЕНИЯ */
        div[data-baseweb="notification"] {{
            background-color: #EFF6FF !important;
            color: {MAIN_COLOR} !important;
            border: 1px solid {MAIN_COLOR} !important;
        }}
        
        /* Иконка внутри уведомления об ошибке */
        div[data-baseweb="notification"] svg {{
            fill: {MAIN_COLOR} !important;
        }}

        /* РАЗДЕЛИТЕЛИ */
        hr {{
            border-top: 1px solid {MAIN_COLOR};
        }}
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <style>
        .block-container {
            padding-top: 3rem; 
        }
        img {
            image-rendering: -webkit-optimize-contrast;
        }
    </style>
""", unsafe_allow_html=True)

header_col1, header_col2 = st.columns([1, 4])

with header_col1:
    st.image(
        "logo.png", 
        width=175,
        output_format="PNG"
    )
    
with header_col2:
    st.title("Satnaut")
    st.caption('"Keep on space exploration"')

st.divider()

top_row = st.columns(2)
bottom_row = st.columns(2)

with top_row[0]:
    st.subheader("User Console")
    user_input = st.text_area(
        "Enter commands line by line:", 
        placeholder="UNIT_ID: arg1, arg2...",
        height=250,
        label_visibility="collapsed"
    )
    run_button = st.button("RUN", use_container_width=True, type="primary")

with top_row[1]:
    st.subheader("Unit Library")
    with st.container(height=250):
        for u in units_library:
            with st.expander(f"**{u.name}** ({u.unit_id})"):
                st.write(f"*{u.description}*")
                args = check_args(u)
                st.info(f"**Input:**  {u.input}")
                st.info(f"**Output:**  {u.output}")
                st.code(f"{u.unit_id}: {u.example}", language="text")
                st.write(f"Associated program variables:  {args}")

with bottom_row[0]:
    st.subheader("Output")
    terminal_container = st.container(border=True, height=350)
    
    # Логика обработки при нажатии кнопки
    if run_button:

        parsed_units = read_data(user_input, units_library)
        
        if isinstance(parsed_units, str):
            terminal_container.error(parsed_units)
        else:
            for unit in parsed_units:
                result = run_engine(unit)
                
                if isinstance(result, str) and result.startswith("ERROR:"):
                    terminal_container.error(f"[{unit.unit_id}]: {result}")
                else:
                    last_result = result[-1]
                    terminal_container.success(f"[{unit.unit_id}] Success")
                    df = DataFrame({"Параметр": unit.output.split(', '), "Значение": last_result})
                    terminal_container.dataframe(df, hide_index=True)

with bottom_row[1]:
    st.subheader("Visualizer")
    visual_container = st.container(border=True, height=350)
    