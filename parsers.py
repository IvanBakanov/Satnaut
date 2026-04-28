# -*- coding: utf-8 -*-

'''
Author: Bakanov I. P.

Version: 28.04.26

Name: minimum working
'''

import os
import csv
import copy
from skyfield.api import load, EarthSatellite
from sgp4.exporter import export_tle


SAT_FILE = "satellites.csv"
DAYS_UPDATE = 0.5


def search_csv(sat_name, filename):
    with open(filename, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        
        for row in reader:
            if not row:
                continue
                
            if row[0].strip().upper() == sat_name.strip().upper():
                return row
                
    return None


def get_omm(sat: str):  
    base = "https://celestrak.org/NORAD/elements/gp.php"
    url = base + "?GROUP=active&FORMAT=csv"

    if not load.exists(SAT_FILE) or load.days_old(SAT_FILE) >= DAYS_UPDATE:
        load.download(url, filename=SAT_FILE)

    fields = search_csv(sat, SAT_FILE)

    if not fields:
        return f"ERROR: Объект '{sat}' не найден в базе данных"
    
    return fields


def parse_omm(omm_data: list):
    string = ','.join(omm_data)
    
    return string
    
    
def get_tle(sat: str):
    fields = get_omm(sat)
    
    if isinstance(fields, str): return fields
    
    ts = load.timescale()

    omm_dict = {
        'OBJECT_NAME': fields[0],
        'OBJECT_ID': fields[1],
        'EPOCH': fields[2],
        'MEAN_MOTION': fields[3],
        'ECCENTRICITY': fields[4],
        'INCLINATION': fields[5],
        'RA_OF_ASC_NODE': fields[6],
        'ARG_OF_PERICENTER': fields[7],
        'MEAN_ANOMALY': fields[8],
        'EPHEMERIS_TYPE': fields[9],
        'CLASSIFICATION_TYPE': fields[10],
        'NORAD_CAT_ID': fields[11],
        'ELEMENT_SET_NO': fields[12],
        'REV_AT_EPOCH': fields[13],
        'BSTAR': fields[14],
        'MEAN_MOTION_DOT': fields[15],
        'MEAN_MOTION_DDOT': fields[16]
        }

    sat_obj = EarthSatellite.from_omm(ts, omm_dict)
    
    l1, l2 = export_tle(sat_obj.model)
    
    return [l1, l2]


def read_data(raw_text, unit_library):
    """
    Парсит ввод вида: 
    UNIT_ID: arg1, arg2
    Возвращает список сконфигурированных объектов Unit.
    """
    if not raw_text.strip():
        return "ERROR: Ввод пуст. Пожалуйста, введите команду."

    executed_units = []
    
    lines = raw_text.strip().split('\n')
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line: continue
            
        # Проверка формата
        if ":" not in line:
            return f"ERROR: Строка {line_num}: неверный формат. Ожидается 'UNIT_ID: arg1, arg2,...'."
        
        parts = line.split(":", 1)
        u_id = parts[0].strip()
        
        # Проверка существования ID в библиотеке
        if u_id not in unit_library:
            return f"ERROR: Строка {line_num}: модуль '{u_id}' не найден в библиотеке."
        
        args_raw = [a.strip() for a in parts[1].split(",") if a.strip()]
        
        # Создаем копию юнита
        new_unit = copy.deepcopy(unit_library[u_id])
        
        # Собираем имена аргументов, помеченных как "user"
        user_arg_names = []
        for step in new_unit.pipeline:
            for arg_name, source in step["mapping"].items():
                if source == "user" and arg_name not in user_arg_names:
                    user_arg_names.append(arg_name)
        
        # Проверка количества аргументов
        if len(args_raw) != len(user_arg_names):
            return (f"ERROR: Строка {line_num}: неверное количество аргументов для {u_id}. "
                    f"Ожидается {len(user_arg_names)} ({', '.join(user_arg_names)}), "
                    f"получено {len(args_raw)}.")
        
        # Заполняем данными
        for i, val in enumerate(args_raw):
            new_unit.input_values[user_arg_names[i]] = val
            
        executed_units.append(new_unit)
            
    return executed_units


def save_result(unit, data, filename):
    with open(filename, "a", encoding="utf-8") as f:
        f.write(f"{unit}\n")
        f.write(f"{data}\n\n")


def read_results(filename):
    if not os.path.exists(filename):
        return ""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""
