from .exceptions import CellNotFound, CellIdAlreadyUsed, ParticleParameterError, ParameterError, NotImplementedFeature
from .store import Store
from typing import Dict, List
from collections import namedtuple
from mcnp_input_reader.util.lines import remove_comments, add_space_to_parentheses, split_on_tag, get_comment_and_endline
from mcnp_input_reader.util.list_of_tuples import get_value_from_list_of_tuples, get_key_value_from_list_of_tuples

CELL_PARAMETERS = ['IMP', 'VOL', 'PWT', 'EXT',
                   'FCL', 'WWN', 'DXC', 'NONU',
                   'PD', 'TMP', 'U', 'TRCL',
                   'LAT', 'FILL', 'ELPT', 'COSY',
                   'BFLCL', 'UNC', 'MAT', 'RHO', 'LIKE', 'BUT']

CELL_PARAMETERS_TYPED = [('IMP', float), ('VOL', float), ('PWT', str), ('EXT', str),
                         ('FCL', str), ('WWN', float), ('DXC', str), ('NONU', str),
                         ('PD', str), ('TMP', float), ('U', int), ('TRCL', str),
                         ('LAT', str), ('FILL', str), ('ELPT', str), ('COSY', str),
                         ('BFLCL', str), ('UNC', str), ('MAT', int), ('RHO', float), ('LIKE', int), ('BUT', None)]


def print_table(table):
    col_width = [max(len(x) for x in col) for col in zip(*table)]
    table_list = []
    for line in table:
        row = "| " + " | ".join("{:{}}".format(x, col_width[i]) for i, x in enumerate(line)) + " |"
        table_list.append(row)
    return table_list

# pattern_cell = re.compile(r'''
#                     (?P<cell_id>^\d+)                 #CELL ID
#                     (\s+)?(\n)?(\s+)?
#                     (?P<mat_id>\d+)                   #MATERIAL ID
#                     (\s+)?(\n)?(\s+)?
#                     (?P<density>[-+]?(\d+(\.\d+)?(E)?[+-]?(\d+)?))?  #DENSITY
#                     (\s+)?(\n)?(\s+)?
#                     (?P<therest>.*?$)
#                    ''', re.VERBOSE|re.IGNORECASE)
#
# pattern_cell_2= re.compile(r'([A-Z]+:?\w?.*?(?=[A-Z]|$))', re.IGNORECASE)


# def get_key_value_from_tuple(parameter: str, parameters: List[tuple]):
#
#     column_index = index_containing_parameter(parameters, parameter)
#     if column_index != -1:
#         item = parameters[column_index]
#     elif ':' in parameter and column_index == -1:
#         parameter = parameter.split(':')[0]
#         column_index = index_containing_parameter(parameters, parameter)
#         if column_index != -1:
#             item = parameters[column_index]
#         else:
#             return None
#     else:
#         return None
#     return item
#

# def get_value(parameter: str, parameters: List, default):
#     parameter_value = get_key_value_from_tuple(parameter, parameters)
#     if parameter_value:
#         return parameter_value[1]
#     return default
#

def explode_particle_parameter(cell_id, parameter_splitted: List, ignore_parameters: List = []):
    ''' e.g.: IMP:N,P 1,0 => IMP:N=1 IMP:P=0 => [(IMP:N, 1), (IMP:P, 0)]
         or   IMP:N,P=1 => IMP:N=1 IMP:P=1 => [(IMP:N, 1), (IMP:P, 1)]
    '''
    key, particles = parameter_splitted[0].split(':', maxsplit=1)
    type_parameter = get_value_from_list_of_tuples(key, CELL_PARAMETERS_TYPED, default=str)
    particles = particles.split(',')
    values = parameter_splitted[1].split()
    if len(particles) == len(values):
        try:
            return [('{}:{}'.format(key, particle), type_parameter(values[i])) for i, particle in enumerate(particles) if '{}:{}'.format(key, particle) not in ignore_parameters]
        except ValueError:
            raise ParameterError("CELL {}: the parameter {} is not properly defined".format(cell_id, key))
    elif len(values) == 1:
        try:
            return [('{}:{}'.format(key, particle), type_parameter(values[0])) for particle in particles if '{}:{}'.format(key, particle) not in ignore_parameters]
        except ValueError:
            raise ParameterError("CELL {}: the parameter {} is not properly defined".format(cell_id, key))
    else:
        raise ParticleParameterError('CELL {}: the lenght of values for {} card is not correct'.format(cell_id, key))


def add_parameter_value_to_list(cell_id: int, parameter: str, parameters_list: list, valid_parameters_list: list, ignore_parameters: list = []):
    '''

    :param cell_id: integer
    :param parameter: string, the parameter description from MCNP input e.g. IMP:P=1
    :param parameters_list: list, list of tuples containing all the previous parameters to be updated with new parameter
    :param valid_parameters_list: list, list containing all the valid parameters
    :param ignore_parameters: list, list of parameters to be ignored
    :return: list of tuples (parameter, value)
    '''
    parameter_splitted = parameter.replace('=', ' ').split(maxsplit=1)
    if ':' in parameter_splitted[0] and ',' in parameter_splitted[0]:
        exploded_particle_parameters = explode_particle_parameter(cell_id, parameter_splitted, ignore_parameters)
        if all(param.split(":")[0] in valid_parameters_list for param in list(map(list, zip(*exploded_particle_parameters)))[0]):
            if not any(param in list(map(list, zip(*parameters_list)))[0] for param in list(map(list, zip(*exploded_particle_parameters)))[0]):
                # parameters_list.extend(exploded_particle_parameters)
                return exploded_particle_parameters  # parameters_list
            else:
                raise ParameterError("CELL {}: the particle parameters are defined multiple times".format(cell_id))
        else:
            raise ParameterError("CELL {}: the particle parameters are not recognized".format(cell_id))
    else:
        if parameter_splitted[0] not in ignore_parameters:
            if len(parameter_splitted) == 2 and parameter_splitted[0].split(":")[0] in valid_parameters_list and parameter_splitted[0].split(":")[0] not in ignore_parameters:
                if parameter_splitted[0] not in list(map(list, zip(*parameters_list)))[0]:
                    type_parameter = get_value_from_list_of_tuples(parameter_splitted[0], CELL_PARAMETERS_TYPED, default=str)
                    try:
                        # parameters_list.append((parameter_splitted[0], type_parameter(parameter_splitted[1])))
                        # return parameters_list
                        return [(parameter_splitted[0], type_parameter(parameter_splitted[1]))]
                    except ValueError:
                        raise ParameterError("CELL {}: the parameter {} is not properly defined".format(cell_id, parameter))
                else:
                    raise ParameterError("CELL {}: the parameter {} is defined multiple times".format(cell_id, parameter_splitted[0]))
            elif parameter_splitted[0].split(":")[0] in ignore_parameters:
                return []  # parameters_list
            else:
                raise ParameterError("CELL {}: the parameter {} in the cell definition is not recognised".format(cell_id, parameter_splitted))
        else:
            return []  # parameters_list


# class MCNPCell(namedtuple('MCNPCell', ['id', 'like', 'mat_id', 'density', 'geometry',
#                                        'fill_id', 'fill_transformation_unit', 'universe_id', 'imp_p',
#                                        'imp_n', 'imp_e', 'fill_transformation', 'fill_transformation_id',
#                                        'lat', 'start_line', 'end_line', 'comment',
#                                        'surfaces', 'not_cells', 'parent'])):
#
#     """MCNPCell is an immutable object for cell parameters"""
#
#     __slots__ = ()
#
#     @classmethod
#     def from_string(cls, cell_description: str, start_line: int, parent=None):
#         cell_desc_space = add_space_to_parentheses(cell_description)
#         cell_description_wo_comments = remove_comments(cell_desc_space)
#         cell_description_splitted = split_on_tag(cell_description_wo_comments, tags=CELL_PARAMETERS)
#         cell_header_splitted = cell_description_splitted[0].split()
#         cell_id = int(cell_header_splitted[0])
#         parameters = []
#         if len(cell_header_splitted) > 1:
#             mat_id = int(cell_header_splitted[1])
#             density = float(cell_header_splitted[2]) if mat_id else 0.0
#             max_split = 3 if mat_id else 2
#             geometry = cell_description_splitted[0].split(maxsplit=max_split)[-1]
#             parameters.extend([('MAT', mat_id), ('RHO', density), ('GEOMETRY', geometry), ('LIKE', 0)])
#
#         for parameter in cell_description_splitted[1:]:
#             parameters = add_parameter_value_to_list(cell_id, parameter, parameters, CELL_PARAMETERS, ignore_parameters='BUT')
#
#         def get_parameter(parameter: str):
#             column_index = index_containing_parameter(parameters, parameter)
#             if column_index != -1:
#                 item = parameters[column_index]
#             elif ':' in parameter and column_index == 1:
#                 parameter = parameter.split(':')[0]
#                 column_index = index_containing_parameter(parameters, parameter)
#                 if column_index != -1:
#                     item = parameters[column_index]
#                 else:
#                     return None
#             else:
#                 return None
#             return item
#
#         def get_value(parameter: str, default):
#             type_parameter = type(default)
#             value = get_parameter(parameter)
#             if value:
#                 try:
#                     return type_parameter(value[1])
#                 except ValueError:
#                     raise ParameterError("CELL {}: the parameter {} is not properly defined".format(cell_id, parameter))
#             return default
#
#         def get_unit_rotation(parameter: str):
#             parameter_key = get_parameter(parameter)
#             if parameter_key:
#                 if parameter_key[0][0] == '*':
#                     return 'degrees'
#                 else:
#                     return 'cosines'
#             return ''
#
#         def get_rotational_parameters(parameter: str):
#             if parameter != '':
#                 transformation = parameter.replace('(', ' ').replace(')', ' ').strip() if len(parameter) > 0 else ''
#                 len_transf = len(transformation.split())
#                 transformation_id = int(transformation) if len_transf == 1 else 0
#                 transformation = transformation if len_transf > 1 else ''
#                 return transformation_id, transformation
#             else:
#                 return 0, ''
#
#         material_id = get_value('MAT', 0)
#         density = get_value('RHO', 0.0)
#         geometry = get_value('GEOMETRY', '')
#         like = get_value('LIKE', 0)
#         imp_n = get_value('IMP:N', 0.0)
#         imp_p = get_value('IMP:P', 0.0)
#         imp_e = get_value('IMP:E', 0.0)
#         lat = get_value('LAT', 0)
#         fill = get_value('FILL', '')
#         fill_splitted = fill.split(maxsplit=1)
#         fill_id = int(fill_splitted[0]) if len(fill_splitted) > 0 and ':' not in fill_splitted[0] else 0
#         fill_transformation_id, fill_transformation = get_rotational_parameters(fill_splitted[1] if ':' not in fill_splitted[0] else fill) if len(fill_splitted) == 2 else (0, '')
#         fill_transformation_unit = get_unit_rotation('FILL')
#         TRCL_id, TRCL_transformation = get_rotational_parameters(get_value('TRCL', ''))
#         TRCL_unit = get_unit_rotation('TRCL')
#         universe_id = get_value('U', 0)
#
#         geometry_splitted = geometry.replace('(', ' ').replace(')', ' ').replace(':', ' ').replace('-', ' ').replace('+', ' ').split()
#         surfaces = set([int(s) for s in geometry_splitted if s[0] != '#'])
#         not_cells = set([int(s[1:]) for s in geometry_splitted if (s[0] == '#') and (len(s) > 1)])
#
#         input_cell_description, comment, end_line = get_comment_and_endline(cell_description, start_line)
#
#         return cls(id=cell_id, like=like, mat_id=material_id, density=density,
#                    geometry=geometry, fill_id=fill_id, fill_transformation_unit=fill_transformation_unit,
#                    universe_id=universe_id, imp_p=imp_p, imp_n=imp_n, imp_e=imp_e,
#                    fill_transformation=fill_transformation, lat=lat,
#                    fill_transformation_id=fill_transformation_id,
#                    start_line=start_line, end_line=end_line, comment=comment,
#                    surfaces=surfaces,
#                    not_cells=not_cells, parent=None)
#
#     @property
#     def surfaces(self):
#         if self.like != 0:
#             if self.parent:
#                 return self.parent[self.like].surfaces
#         else:
#             return self.surfaces
#
#     def __str__(self):
#         return '''<MCNPCell>
# id = {}
# mat_id = {}
# density = {}
# geometry = {}
# surfaces = {}
# not_cells = {}
# fill_id = {}
# universe_id = {}
# imp_p = {}
# imp_n = {}
# imp_e = {}
# transformation = {}
# fill_transformation_id = {}
# lat = {}
# start_line = {}
# end_line = {}
# comment = {}
# input_cell_description:
# {}
# '''.format(self.id, self.mat_id, self.density, self.geometry, self.surfaces, self.not_cells, self.fill_id,
#            self.universe_id, self.imp_p, self.imp_n, self.imp_e,
#            self.fill_transformation, self.fill_transformation_id, self.lat, self.start_line, self.end_line,
#            self.comment, self.input_cell_description)
#

# def index_containing_parameter(the_list, substring):
#     for i, s in enumerate(the_list):
#         if substring == s[0]:
#             return i
#     return -1
#

class MCNPCells(Store):

    def __init__(self, cell_list=[], parent=None):
        super().__init__(cell_list, parent)
        self.cardnotfound_exception = CellNotFound
        self.cardidalreadyused_exception = CellIdAlreadyUsed
        self.card_name = 'cell'
        self.DEFAULT_FIELDS = ['id', 'material_id', 'density', 'imp_n', 'imp_p', 'universe_id', 'fill_id']

    def filter_cells(self, p, all_levels=False):
        filtered_cells = MCNPCells(list(filter(p, self.__iter__())))

        if all_levels:
            universe_ids = filtered_cells.get_fill_ids()
            while len(universe_ids) > 0:
                cells_of_universes = list(filter(lambda cell: cell.universe_id in universe_ids, self.__iter__()))
                universe_ids = set()
                for cell in cells_of_universes:
                    filtered_cells.add(cell)
                    if cell.fill_id != 0:
                        universe_ids.update([cell.fill_id])
        return filtered_cells

    def get_surfaces(self):
        surfaces = set()
        for cell in self._store.values():
            surfaces.update(cell.surfaces)
        return surfaces

    def get_materials(self):
        return set([cell.material_id for cell in self._store.values() if cell.material_id != 0])

    def get_transformations(self):
        return set([cell.fill_transformation_id for cell in self._store.values() if cell.fill_transformation_id != 0])

    def get_universe_ids(self):
        return set([cell.universe_id for cell in self._store.values() if cell.universe_id != 0])

    def get_fill_ids(self):
        return set([cell.fill_id for cell in self._store.values() if cell.fill_id != 0])

    def get_comments(self):
        return set([cell.comment for cell in self._store.values() if cell.comment != ''])

    def to_dataframe(self):
        try:
            import pandas as pd
            df = pd.DataFrame(self)
            df = pd.concat([df[['id', 'start_line', 'end_line', 'comment']], pd.DataFrame(df['parameters'].apply(dict).tolist())], axis=1).fillna(0, downcast='infer')
            return df
        except ModuleNotFoundError:
            print("Pandas is not present")


def get_unit_rotation(parameter: str, parameters):
    parameter_key = get_key_value_from_list_of_tuples(parameter, parameters)
    if parameter_key:
        if parameter_key[0][0] == '*':
            return 'degrees'
        else:
            return 'cosines'
    return ''


def get_rotational_parameters(parameter: str):
    if parameter != '':
        transformation = parameter.replace('(', ' ').replace(')', ' ').strip() if len(parameter) > 0 else ''
        len_transf = len(transformation.split())
        transformation_id = int(transformation) if len_transf == 1 else 0
        transformation = transformation if len_transf > 1 else ''
        return transformation_id, transformation
    else:
        return 0, ''


class MCNPCell(namedtuple('MCNPCell', ['id', 'parameters', 'start_line', 'end_line', 'comment', 'parent'])):

    """MCNPCell is an immutable object for cell parameters"""

    __slots__ = ()

    @classmethod
    def from_string(cls, cell_description: str, start_line: int, parent: MCNPCells):
        cell_desc_space = add_space_to_parentheses(cell_description)
        cell_description_wo_comments = remove_comments(cell_desc_space)
        cell_description_splitted = split_on_tag(cell_description_wo_comments, tags=CELL_PARAMETERS)
        cell_header_splitted = cell_description_splitted[0].split()
        cell_id = int(cell_header_splitted[0])
        parameters = []
        if len(cell_header_splitted) > 1:
            mat_id = int(cell_header_splitted[1])
            density = float(cell_header_splitted[2]) if mat_id else 0.0
            max_split = 3 if mat_id else 2
            geometry = cell_description_splitted[0].split(maxsplit=max_split)[-1]
            parameters.extend([('MAT', mat_id), ('RHO', density), ('GEOMETRY', geometry), ('LIKE', 0)])

        for parameter in cell_description_splitted[1:]:
            parameters += add_parameter_value_to_list(cell_id, parameter, parameters, CELL_PARAMETERS, ignore_parameters=['BUT'])

        input_cell_description, comment, end_line = get_comment_and_endline(cell_description, start_line)

        return cls(id=cell_id, parameters=parameters,
                   start_line=start_line, end_line=end_line, comment=comment,
                   parent=parent)

    @property
    def geometry(self):
        return get_value_from_list_of_tuples('GEOMETRY', self.parameters, '')

    @property
    def surfaces(self):
        if self.like != 0:
            if self.parent:
                try:
                    return self.parent[self.like].surfaces
                except KeyError:
                    raise Exception(f"The cell {self.like} is not defined!")
            raise Exception(f"The cell {self.like} is not defined!")
        else:
            geometry_splitted = self.geometry.replace('(', ' ').replace(')', ' ').replace(':', ' ').replace('-', ' ').replace('+', ' ').split()
            return set([int(s) for s in geometry_splitted if s[0] != '#'])

    @property
    def cells_negated(self):
        if self.like:
            if self.parent:
                try:
                    return self.parent[self.like].cells_negated
                except KeyError:
                    raise Exception(f"The cell {self.like} is not defined!")
            raise Exception(f"The cell {self.like} is not defined!")
        else:
            geometry_splitted = self.geometry.replace('(', ' ').replace(')', ' ').replace(':', ' ').replace('-', ' ').replace('+', ' ').split()
            return set([int(s[1:]) for s in geometry_splitted if (s[0] == '#') and (len(s) > 1)])

    @property
    def like(self):
        return get_value_from_list_of_tuples('LIKE', self.parameters, 0)

    @property
    def material_id(self):
        return get_value_from_list_of_tuples('MAT', self.parameters, 0)

    @property
    def universe_id(self):
        return get_value_from_list_of_tuples('U', self.parameters, 0)

    @property
    def imp_n(self):
        return get_value_from_list_of_tuples('IMP:P', self.parameters, 0.0)

    @property
    def imp_p(self):
        return get_value_from_list_of_tuples('IMP:N', self.parameters, 0.0)

    @property
    def imp_e(self):
        return get_value_from_list_of_tuples('IMP:E', self.parameters, 0.0)

    @property
    def input_cell_definition(self):
        if self.parent and self.parent.parent:
            return ''.join(self.parent.parent.lines[self.start_line:self.end_line + 1])
        else:
            raise Exception("The input file is not loaded")

    @property
    def fill_definition(self):
        return get_value_from_list_of_tuples('FILL', self.parameters, '')

    @property
    def fill_id(self):
        fill_splitted = self.fill_definition.split(maxsplit=1)
        return int(fill_splitted[0]) if len(fill_splitted) > 0 and ':' not in fill_splitted[0] else 0

    @property
    def fill_transformation_id(self):
        fill_splitted = self.fill_definition.split(maxsplit=1)
        fill_transformation_id, _ = get_rotational_parameters(fill_splitted[1] if ':' not in fill_splitted[0] else self.fill_definition) if len(fill_splitted) == 2 else (0, '')
        return fill_transformation_id

    @property
    def fill_transformation(self):
        fill_splitted = self.fill_definition.split(maxsplit=1)
        _, fill_transformation = get_rotational_parameters(fill_splitted[1] if ':' not in fill_splitted[0] else self.fill_definition) if len(fill_splitted) == 2 else (0, '')
        return fill_transformation

    @property
    def fill_transformation_unit(self):
        return get_unit_rotation('FILL')

    @property
    def trcl_id(self):
        TRCL_id, _ = get_rotational_parameters(get_value_from_list_of_tuples('TRCL', self.parameters, ''))
        return TRCL_id

    @property
    def trcl_transformation(self):
        _, TRCL_transformation = get_rotational_parameters(get_value_from_list_of_tuples('TRCL', self.parameters, ''))
        return TRCL_transformation

    @property
    def trcl_unit(self):
        return get_unit_rotation('TRCL')

    def __repr__(self):
        parameters_string = '\n'.join([f'{parameter[0]}: {parameter[1]}' for parameter in self.parameters])
        return f'<MCNPCell> CELL: {self.id}\n{parameters_string}\ncomment: {self.comment}'

    def __str__(self):
        parameters_string = '\n'.join([f'{parameter[0]}: {parameter[1]}' for parameter in self.parameters])
        return f'Cell: {self.id}\n{parameters_string}\ncomment: {self.comment}'
