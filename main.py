# -*- coding: utf-8 -*-

'''
Author: Bakanov I. P.

Version: 28.04.26

Name: minimum working
'''

import os
import streamlit as st
from unit import parse_units, check_args, run_engine, objects_array
from parsers import read_data, save_result, read_results
import visualizer


UNIT_FILE = "unit_library.txt"
RESULTS_FILE = "results.txt"


st.set_page_config(
    layout="wide", 
    page_title="Satnaut"
)


unit_library = parse_units(UNIT_FILE)


MAIN_COLOR = "#1E3A8A" 

st.markdown(f"""
    <style>
        /* ФОН */
        .stApp {{
            background-color: white;
        }}

        /* КНОПКА */
        button[data-testid="baseButton-primary"]:enabled {{
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


header_col1, header_col2, header_col3 = st.columns([1, 2, 1.5])

with header_col1:
    st.image(
        "logo.png", 
        width=125,
        output_format="PNG"
    )
    
with header_col2:
    st.title("Satnaut")
    st.caption("Interactive developer of satellite systems")
    
with header_col3:
    with st.popover("Instruction"):
        st.markdown("""
        We use units - functional blocks - to create calculation programs.
        The units are divided into simple and composite - multi-stage.
        Select the appropriate unit/units from the Unit Library
        and write your program in the User Console.
        Press RUN and the result of the program will be displayed in the Output window.
        The corresponding graphs and diagrams will appear in the Graphics window.
        """)


st.divider()


top_row = st.columns(2)
bottom_row = st.columns(2)

with top_row[0]:
    st.subheader("User Console")
    
    user_input = st.text_area(
        "Enter commands line by line:", 
        placeholder="UNIT_ID: arg1, arg2,...",
        height=250,
        label_visibility="collapsed")
    
    col1, col2, col3 = st.columns([1.5, 1, 1])

    with col1:
        run_button = st.button("RUN", type="primary", use_container_width=True)

    with col2:
        if st.button("CLEAR OUTPUT", type="secondary", use_container_width=True):
            if os.path.exists(RESULTS_FILE):
                open(RESULTS_FILE, "w").close()
            
            objects_array.clear()
            
            st.rerun()

    with col3:
        current_log = read_results(RESULTS_FILE)
    
        has_data = len(current_log.strip()) > 0
    
        st.download_button(
            label="DOWNLOAD RES",
            data=current_log,
            file_name="satnaut_results.txt",
            mime="text/plain",
            use_container_width=True)


with top_row[1]:
    st.subheader("Unit Library")
    
    with st.container(height=250):
        for u in unit_library.values():
            with st.expander(f"**{u.name}** ({u.unit_id})"):
                st.write(f"*{u.description}*")
                args = check_args(u)
                st.info(f"**Input:**  {u.input}")
                st.info(f"**Output:**  {u.output}")
                st.code(f"{u.unit_id}: {u.example}", language="text")
                st.write(f"Associated variables:  {args}")

with bottom_row[0]:
    st.subheader("Output")
    
    terminal_container = st.container(border=True, height=350)
    
    # Логика обработки при нажатии кнопки RUN
    if run_button:
        parsed_units = read_data(user_input, unit_library)
        
        if isinstance(parsed_units, str):
            terminal_container.error(parsed_units)
        else:
            for unit in parsed_units:
                result = run_engine(unit)
                
                if isinstance(result, str) and result.startswith("ERROR:"):
                    terminal_container.error(f"[{unit.unit_id}]: {result}")
                else:
                    if unit.unit_id == "SAT_SUBPOINT":
                        sat = objects_array[-1]
                        visualizer.sat_subpoint(sat)
                        
                    last_result = result[-1]
                    save_result(unit, last_result, RESULTS_FILE)
                    terminal_container.success(f"[{unit.unit_id}]: completed successfully")
                    df = visualizer.create_output(unit, last_result)
                    terminal_container.dataframe(df, hide_index=True)


if "current_fig" not in st.session_state:
    st.session_state.current_fig = visualizer.create_empty_plot()


with bottom_row[1]:
    st.subheader("Graphics")
    visual_container = st.container(border=True, height=350)
    
    visual_container.pyplot(st.session_state.current_fig)
    
