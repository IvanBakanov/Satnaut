# -*- coding: utf-8 -*-

'''
Author: Bakanov I. P.

Version: 28.04.26

Name: minimum working
'''

import engine
from pandas import DataFrame
import matplotlib.pyplot as plt
import streamlit as st


def create_output(unit, result):
    df = DataFrame({"Параметр": unit.output.split(', '), "Значение": result})

    return df


def create_empty_plot():
    fig, ax = plt.subplots(figsize=(5, 3))
    
    ax.grid(True, linestyle='--', alpha=0.6)
    
    ax.set_xlim([-180, 180])
    ax.set_ylim([-90, 90])
    
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("Satellite Ground Track", fontsize=10)
    
    fig.patch.set_alpha(0)
    
    plt.tight_layout()
    
    return fig


def update_trace_plot(fig, lats, lons):
    ax = fig.gca()
    
    ax.clear()
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.set_xlim([-180, 180])
    ax.set_ylim([-90, 90])
    
    # Отрисовка трассы поточечно
    ax.scatter(lons, lats, s=2, color="#1f77b4", label="Ground track")
    
    # Выделяем текущее положение спутника
    ax.scatter(lons[0], lats[0], color="red", s=20, marker='X', label="Current position")
    
    ax.legend(loc="upper right", fontsize="small")
    
    return fig


def sat_subpoint(sat):
    now = engine.get_dt_UTC_0() 
    
    period = sat.get_orbital_period()
    
    lats, lons = engine.trace_simulation(sat, now, period)
    
    fig = create_empty_plot()
    
    st.session_state.current_fig = update_trace_plot(fig, lats, lons)
    