# -*- coding: utf-8 -*-

'''
Author: Bakanov I. P.

Version: 28.04.26

Name: minimum working
'''

import engine
import parsers
import ast
import streamlit as st


objects_array = []


def run_engine(unit):
    last_result = None
    results = []
    
    objects = {
        "Satellite": None,
        "GroundStation": None
    }
    
    for step in unit.pipeline:
        if isinstance(last_result, str) and last_result.startswith("ERROR:"):
            return last_result
        
        func_id = step["func"]
        mapping = step.get("mapping", {})
        target_class = step["target_class"]
    
        # Сбор аргументов (если mapping не пуст)
        args = {}
        if mapping:
            for arg_name, source in mapping.items():
                if source == "user":
                    args[arg_name] = unit.input_values.get(arg_name)
                elif source == "prev":
                    args[arg_name] = results[-1] if results else None
                elif source.startswith("step"):
                    try:
                        idx = int(source[5])-1
                        args[arg_name] = results[idx]
                    except:
                        return f"ERROR: Обращение к несуществующему шагу {source}."

        try:
            if target_class and target_class in objects:
                active_obj = objects[target_class]
                method = getattr(active_obj, func_id)
                last_result = method(**args)

            elif func_id in objects:
                # Создание объекта
                last_result = getattr(engine, func_id)(**args)
                objects[func_id] = last_result
                objects_array.append(last_result)

            else:
                # Внешняя функция
                if func_id.startswith("parsers."):
                    f_name = func_id.split(".")[1]
                    func = getattr(parsers, f_name)
                elif func_id.startswith("engine."):
                    f_name = func_id.split(".")[1]
                    func = getattr(engine, f_name)
                else:
                    func = getattr(engine, func_id)
                
                last_result = func(**args)
            
            results.append(last_result)
            
            if isinstance(last_result, str) and last_result.startswith("ERROR:"): raise ValueError("некорректный ввод данных")
            
        except Exception as e:
            return f"ERROR: Не удалось выполнить расчет. Проверьте входные данные. Полное описание ошибки: {e}. Последняя команда: {func_id}. Последний промежуточный результат: {last_result}."
        
    return results


def check_args(unit):
    """
    Сканирует pipeline юнита и возвращает строку с именами пользовательских аргументов.
    Сохраняет порядок их появления в алгоритме.
    """
    user_args = []
    
    for step in unit.pipeline:
        mapping = step.get("mapping", {})
        for arg_name, source in mapping.items():
            # Если источник помечен как "user" и мы еще не добавили этот аргумент
            if source == "user" and arg_name not in user_args:
                user_args.append(arg_name)
    
    if not user_args:
        return "no args"
        
    return ", ".join(user_args)


# -----------------------------------------------------------------------------
# CLASS UNIT

class Unit:
    def __init__(self, unit_id: str, name: str, description: str, unit_input: str, example: str, unit_output: str):
        self.unit_id = unit_id
        self.name = name
        self.description = description
        self.pipeline = []
        self.input_values = {}
        self.input = unit_input
        self.example = example
        self.output = unit_output

    def add_step(self, func, arg_mapping: dict, target_class=None):
        '''
        Добавляет функцию в цепочку внутри узла.
        arg_mapping определяет, откуда брать каждый аргумент функции:
        {"altitude": "user"} - взять из ввода пользователя
        {"velocity": "prev"} - взять из результата предыдущей функции
        '''
        self.pipeline.append({
            "func": func,
            "mapping": arg_mapping,
            "target_class": target_class
        })

    def __repr__(self):
        return f"Unit {self.unit_id}: {self.name}"


# -----------------------------------------------------------------------------
# UNITS LIBRARY

@st.cache_data
def parse_units(file_path):
    unit_library = {}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip().split('\n\n')
            
            for block in content:
                lines = [l.strip() for l in block.split('\n') if l.strip()]
                
                if len(lines) < 6:
                    continue
                
                # МЕТАДАННЫЕ (строки 0-5)
                u = Unit(
                    unit_id=lines[0],
                    name=lines[1],
                    description=lines[2],
                    unit_input=lines[3],
                    example=lines[4],
                    unit_output=lines[5]
                )
                
                # ШАГИ ВЫПОЛНЕНИЯ (строки 6+)
                for step_line in lines[6:]:
                    parts = [p.strip() for p in step_line.split(';')]
                    
                    if len(parts) < 2:
                        continue
                    
                    func_name = parts[0]
                    params_str = parts[1]
                    
                    try:
                        params = ast.literal_eval(params_str)
                    except Exception as e:
                        st.error(f"ERROR: Ошибка в словаре параметров. Полное описание ошибки: {e}.")
                        params = {}

                    call_obj = parts[2] if len(parts) > 2 else None
                    
                    u.add_step(func_name, params, call_obj)
                
                unit_library[u.unit_id] = u
                
    except Exception as e:
        st.error(f'ERROR: Ошибка парсинга "unit_library.txt". Полное описание ошибки: {e}.')
    
    return unit_library
