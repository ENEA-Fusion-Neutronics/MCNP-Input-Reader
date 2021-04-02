from typing import List


def get_key_value_from_list_of_tuples(parameter: str, parameters: List[tuple]):

    column_index = index_containing_key(parameter, parameters)
    if column_index != -1:
        item = parameters[column_index]
    elif ':' in parameter and column_index == -1:
        parameter = parameter.split(':')[0]
        column_index = index_containing_key(parameter, parameters)
        if column_index != -1:
            item = parameters[column_index]
        else:
            return None
    else:
        return None
    return item


def get_value_from_list_of_tuples(parameter: str, parameters: List, default):
    parameter_value = get_key_value_from_list_of_tuples(parameter, parameters)
    if parameter_value:
        return parameter_value[1]
    return default


def index_containing_key(key: str, list_of_tuples: List[tuple]):
    for i, s in enumerate(list_of_tuples):
        if key == s[0]:
            return i
    return -1
