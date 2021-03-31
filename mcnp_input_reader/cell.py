from .exceptions import CellNotFound, CellIdAlreadyUsed, ParticleParameterError, ParameterError, NotImplementedFeature
from .store import Store
from typing import Dict, List
from collections import namedtuple
from mcnp_input_reader.util.lines import remove_comments, add_space_to_parentheses, split_on_tag, get_comment_and_endline


CELL_PARAMETERS = ['IMP', 'VOL', 'PWT', 'EXT',
                   'FCL', 'WWN', 'DXC', 'NONU',
                   'PD', 'TMP', 'U', 'TRCL',
                   'LAT', 'FILL', 'ELPT', 'COSY', 
                   'BFLCL', 'UNC', 'MAT', 'RHO', 'LIKE', 'BUT']

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


class MCNPCell(namedtuple('MCNPCell', ['id', 'like', 'mat_id','density','geometry',
                                       'fill_id','fill_transformation_unit','universe_id','imp_p',
                                       'imp_n', 'imp_e', 'fill_transformation','fill_transformation_id', 
                                       'lat', 'start_line','end_line', 'comment','input_cell_description',
                                       'surfaces','not_cells'])):

    """MCNPCell is an immutable object for cell parameters"""

    __slots__ = ()

    @classmethod
    def from_string(cls, cell_description: str, start_line: int):
        cell_desc_space = add_space_to_parentheses(cell_description)
        cell_description_wo_comments = remove_comments(cell_desc_space)
        cell_description_splitted = split_on_tag(cell_description_wo_comments, tags = CELL_PARAMETERS)
        cell_part_one = cell_description_splitted[0].split()
        cell_id=int(cell_part_one[0])
        parameters = []
        if len(cell_part_one) > 1:
            mat_id=int(cell_part_one[1])
            density = float(cell_part_one[2]) if mat_id else 0.0
            max_split = 3 if mat_id else 2
            geometry = cell_description_splitted[0].split(maxsplit = max_split)[-1]
            parameters.extend([('MAT', mat_id), ('RHO', density), ('GEOMETRY', geometry), ('LIKE', 0)])
        
        def explode_particle_parameter(parameter_splitted: List):
            ''' e.g.: IMP:N,P 1,0 => IMP:N=1 IMP:P=0 => [(IMP:N, 1), (IMP:P, 0)] 
                 or   IMP:N,P=1 => IMP:N=1 IMP:P=1 => [(IMP:N, 1), (IMP:P, 1)]
            '''
            key, particles = parameter_splitted[0].split(':', maxsplit = 1)
            particles = particles.split(',')
            values = parameter_splitted[1].split()
            if len(particles) == len(values):
                return [('{}:{}'.format(key, particle), values[i]) for i, particle in enumerate(particles)]
            elif len(values) == 1:    
                return [('{}:{}'.format(key, particle), values[0]) for particle in particles]
            else:
                raise ParticleParameterError('CELL {}: the lenght of values for {} card is not correct'.format(cell_id, key))

        for parameter in cell_description_splitted[1:]:
            parameter_splitted = parameter.replace(', ',',').replace('=',' ').split(maxsplit = 1)
            if ':' in parameter_splitted[0] and ',' in parameter_splitted[0]:
                exploded_particle_parameters = explode_particle_parameter(parameter_splitted) 
                if all(param.split(":")[0] in CELL_PARAMETERS for param in list(map(list, zip(*exploded_particle_parameters)))[0]): 
                    if not any(param in list(map(list, zip(*parameters)))[0] for param in list(map(list, zip(*exploded_particle_parameters)))[0]):
                        parameters.extend(exploded_particle_parameters)
                    else:
                        raise ParameterError("CELL {}: the particle parameters are defined multiple times".format(cell_id))
                else:
                    raise ParameterError("CELL {}: the particle parameters are not recognized".format(cell_id))
            else:
                if len(parameter_splitted) == 2 and parameter_splitted[0].split(":")[0] in CELL_PARAMETERS:
                    if parameter_splitted[0] not in list(map(list, zip(*parameters)))[0]:
                        parameters.append((parameter_splitted[0], parameter_splitted[1]))
                    else:
                        raise ParameterError("CELL {}: the parameter {} is defined multiple times".format(cell_id, parameter_splitted[0]))
                else:
                    raise ParameterError("CELL {}: the parameter {} in the cell definition is not recognised".format(cell_id, parameter_splitted))

        def get_parameter(parameter: str):
            column_index = index_containing_parameter(parameters, parameter)
            if column_index != -1:
                item = parameters[column_index]
            elif ':' in parameter and column_index == 1:
                parameter = parameter.split(':')[0]
                column_index = index_containing_parameter(parameters, parameter)
                if column_index != -1:
                    item = parameters[column_index] 
                else:
                    return None
            else:
                return None
            return item
        
        def get_value(parameter: str, default):
            type_parameter = type(default)
            value = get_parameter(parameter)
            if value:
                try:
                    return type_parameter(value[1])
                except ValueError:
                    raise ParameterError("CELL {}: the parameter {} is not properly defined".format(cell_id, parameter))
            return default

        def get_unit_rotation(parameter: str):
            parameter_key = get_parameter(parameter)
            if parameter_key:
                if parameter_key[0][0]=='*':
                    return 'degrees'
                else:
                    return 'cosines'
            return ''
        
        def get_rotational_parameters(parameter: str):
            if parameter != '':
                transformation = parameter.replace('(',' ').replace(')',' ').strip() if len(parameter) > 0 else ''
                len_transf = len(transformation.split())
                transformation_id = int(transformation) if len_transf == 1 else 0
                transformation = transformation if len_transf > 1 else ''
                return transformation_id, transformation
            else:
                return 0, ''

        material_id = get_value('MAT', 0)
        density = get_value('RHO', 0.0)
        geometry = get_value('GEOMETRY', '')
        like = get_value('LIKE', 0)
        imp_n = get_value('IMP:N', 0.0)
        imp_p = get_value('IMP:P', 0.0)
        imp_e = get_value('IMP:E', 0.0)
        lat = get_value('LAT', 0)
        fill = get_value('FILL', '')
        fill_splitted = fill.split(maxsplit=1)
        fill_id = int(fill_splitted[0]) if len(fill_splitted) > 0 and ':' not in fill_splitted[0] else 0
        fill_transformation_id, fill_transformation = get_rotational_parameters(fill_splitted[1] if ':' not in fill_splitted[0] else fill) if len(fill_splitted) == 2 else (0, '')
        fill_transformation_unit = get_unit_rotation('FILL')
        TRCL_id, TRCL_transformation = get_rotational_parameters(get_value('TRCL',''))
        TRCL_unit = get_unit_rotation('TRCL')
        universe_id = get_value('U', 0)
        
        geometry_splitted = geometry.replace('(', ' ').replace(')', ' ').replace(':', ' ').replace('-', ' ').replace('+', ' ').split()
        surfaces = set([int(s) for s in geometry_splitted if s[0] != '#'])
        not_cells = set([int(s[1:]) for s in geometry_splitted if (s[0] == '#') and (len(s) > 1)])
        
        input_cell_description, comment, end_line = get_comment_and_endline(cell_description, start_line)
       
        return cls(id=cell_id, like=like, mat_id=material_id, density=density, geometry=geometry, 
                   fill_id=fill_id, fill_transformation_unit=fill_transformation_unit, 
                   universe_id=universe_id, imp_p=imp_p, imp_n=imp_n, imp_e=imp_e, 
                   fill_transformation=fill_transformation, lat=lat, 
                   fill_transformation_id=fill_transformation_id, 
                   start_line=start_line, end_line=end_line, comment=comment, 
                   input_cell_description=input_cell_description, surfaces=surfaces, 
                   not_cells=not_cells)
   
        @property
        def surfaces(self):
            if self.like != 0:
                if self.parent:
                    return self.parent[self.like].surfaces
            else:
                return self.surfaces

    def __str__(self):
        return '''<MCNPCell>
id = {}
mat_id = {}
density = {}
geometry = {}
surfaces = {}
not_cells = {}
fill_id = {}
universe_id = {}
imp_p = {}
imp_n = {}
imp_e = {}
transformation = {}
fill_transformation_id = {}
lat = {}
start_line = {}
end_line = {}
comment = {}
input_cell_description: 
{}
'''.format(self.id, self.mat_id, self.density, self.geometry, self.surfaces, self.not_cells, self.fill_id, 
           self.universe_id, self.imp_p, self.imp_n, self.imp_e, 
           self.fill_transformation, self.fill_transformation_id, self.lat, self.start_line, self.end_line,
           self.comment, self.input_cell_description)

def index_containing_parameter(the_list, substring):
    for i, s in enumerate(the_list):
        if substring == s[0]:
            return i
    return -1

class MCNPCells(Store):
    
    def __init__(self, cell_list = [], parent = None):
        super().__init__(cell_list, parent)
        self.cardnotfound_exception = CellNotFound
        self.cardidalreadyused_exception = CellIdAlreadyUsed
        self.card_name = 'cell'
        self.DEFAULT_FIELDS = ['id', 'mat_id', 'density', 'imp_n', 'imp_p', 'universe_id', 'fill_id']

    def filter_cells(self, p, all_levels=False):
        filtered_cells = MCNPCells(list(filter(p, self.__iter__())))
           
        if all_levels==True:
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
        surfaces=set()
        for cell in self._store.values():
            surfaces.update(cell.surfaces)
        return surfaces

    def get_materials(self):
        return set([cell.mat_id for cell in self._store.values() if cell.mat_id!=0])

    def get_transformations(self):
        return set([cell.fill_transformation_id for cell in self._store.values() if cell.fill_transformation_id != 0])

    def get_universe_ids(self):
        return set([cell.universe_id for cell in self._store.values() if cell.universe_id!=0])

    def get_fill_ids(self):
        return set([cell.fill_id for cell in self._store.values() if cell.fill_id!=0])
    
    def get_comments(self):
        return set([cell.comment for cell in self._store.values() if cell.comment != ''])
    
