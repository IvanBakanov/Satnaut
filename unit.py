# -*- coding: utf-8 -*-

'''
Author: Bakanov I. P.

Version: 26.04.26.0
'''

import engine
import parsers


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
                # **{} эквивалентно вызову без аргументов
                last_result = method(**args)

            elif func_id in objects:
                # Создание объекта
                last_result = getattr(engine, func_id)(**args)
                objects[func_id] = last_result

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
        return f"<Unit {self.unit_id}: {self.name}>"


# -----------------------------------------------------------------------------
# UNITS LIBRARY

units_library = []

unit_bi1 = Unit(
    unit_id = "SAT_SUBPOINT",
    name = "Координаты подспутниковой точки",
    description = "Вычисляет широту и долготу подспутниковой точки на основе данных TLE.",
    unit_input = "<satellite name>, <location>",
    example = "ISS (ZARYA), Europe/Moscow",
    unit_output = "latitude, longitude"
)

unit_bi1.add_step("parsers.get_tle", {"sat": "user"})
unit_bi1.add_step("Satellite", {"sat": "user", "TLE_parsed": "prev"})
unit_bi1.add_step("engine.get_dt", {"location": "user"})
unit_bi1.add_step("get_state_vector", {"now": "prev"}, "Satellite")
unit_bi1.add_step("get_subsatellite_point", {"state": "step 4", "now": "step 3"}, "Satellite")


unit_bi2 = Unit(
    unit_id = "SAT_TLE",
    name = "Two-Line Element set",
    description = "Get latest TLE data.",
    unit_input = "<satellite name>",
    example = "ISS (ZARYA)",
    unit_output = "TLE string 1, TLE string 2"
)

unit_bi2.add_step("parsers.get_tle", {"sat": "user"})


unit_bi3 = Unit(
    unit_id = "SAT_OMM",
    name = "Orbit Mean-Elements Message",
    description = "Get latest MMO data.",
    unit_input = "<satellite name>",
    example = "ISS (ZARYA)",
    unit_output = "OMM"
)

unit_bi3.add_step("parsers.get_omm", {"sat": "user"})
unit_bi3.add_step("parsers.parse_omm", {"omm_data": "prev"})


unit_bi4 = Unit(
    unit_id = "TEME_TO_ECEF",
    name = "TEME -> ECEF",
    description = "Преобразование координат: TEME -> ECEF.",
    unit_input = "<satellite name>, <location>",
    example = "ISS (ZARYA), Europe/Moscow",
    unit_output = "x, y, z"
)

unit_bi4.add_step("parsers.get_tle", {"sat": "user"})
unit_bi4.add_step("Satellite", {"sat": "user", "TLE_parsed": "prev"})
unit_bi4.add_step("engine.get_dt", {"location": "user"})
unit_bi4.add_step("get_state_vector", {"now": "prev"}, "Satellite")
unit_bi4.add_step("engine.teme_to_ecef", {"state": "step 4", "now": "step 3"})


units_library.append(unit_bi2)

units_library.append(unit_bi3)

units_library.append(unit_bi1)

units_library.append(unit_bi4)
