from .exceptions import CellNotFound, CellIdAlreadyUsed, NotImplementedFeature
from .store import Store
from typing import Dict, List
from collections import namedtuple
from mcnp_input_reader.util.lines import remove_comments, add_space_to_parentheses, split_on_tag
CELL_PARAMETERS = ['IMP', 'VOL', 'PWT', 'EXT',
                    'FCL', 'WWN', 'DXC', 'NONU',
                    'PD', 'TMP', 'U', 'TRCL',
                    'LAT', 'FILL', 'ELPT', 'COSY', 'BFLCL', 'UNC']
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


class MCNPCell(namedtuple('MCNPCell', ['id','mat_id','density','geometry',
                                       'fill_id','fill_type','universe_id','imp_p',
                                       'imp_n', 'imp_e', 'transf','transf_id', 'lat', 'start_line','end_line',
                                       'comment','input_cell_description','surfaces','not_cells'])):
    """MCNPCell is an immutable object for cell parameters"""
    __slots__ = ()
#class MCNPCell2(NamedTuple):
# @dataclass
# class MCNPCell2:
    # __slots__ = ('cell_id', 'mat_id', 'density', 'geometry', 'fill_id', 'fill_type', 
    #              'universe_id', 'imp_p', 'imp_n', 'transf', 'transf_id', 'start_line', 
    #              'end_line', 'comment', 'input_cell_description', 'surfaces', 'not_cells')
    # cell_id: int 
    # mat_id: int 
    # density: float 
    # geometry: str 
    # fill_id: int 
    # fill_type: str 
    # universe_id: int 
    # imp_p: float 
    # imp_n: float 
    # transf: str 
    # transf_id: int 
    # start_line: int
    # end_line: int
    # comment: str 
    # input_cell_description: str 
    # surfaces: List[int]  
    # not_cells: List[int] 


    @classmethod
    def from_string(cls, cell_desc: str, start_line: int):
        cell_desc_space = add_space_to_parentheses(cell_desc)
        # cell_pure = ' '.join([line.split('$')[0].strip() for line in cell_desc_split if line[0].lower() != 'c']).replace('(', ' (').replace(')', ') ')
        cell_pure = remove_comments(cell_desc_space)
        cell_pure_split = split_on_tag(cell_pure, tags = CELL_PARAMETERS)
        cell_part_one = cell_pure_split[0].split()
        cell_id=int(cell_part_one[0])
        if cell_part_one[1].upper() != 'LIKE':
            
            mat_id=int(cell_part_one[1])
            density = float(cell_part_one[2]) if mat_id else 0.0
            index_geometry = 3 if mat_id else 2
            geometry = ' '.join(cell_part_one[index_geometry:])
            geom = geometry.replace('(', ' ').replace(')', ' ').replace(':', ' ').replace('-', ' ').replace('+', ' ').split()
            surfaces=set([int(s) for s in geom if s[0] != '#'])
            not_cells=set([int(s[1:]) for s in geom if (s[0] == '#') and (len(s) > 1)])
            parameters={}
            for p in cell_pure_split[1:]:
                k_v = p.replace(', ',',').replace('=',' ').split()
                k=k_v[0]
                v=k_v[1:]
                
                if 'IMP' in k and ',' in k:
                    keys = k.split(':')[1].split(',') 
                    for new_key in keys:
                        new_key = 'IMP:' + new_key
                        parameters[new_key] = v
                else:
                    parameters[k]=v
            imp_n = float(parameters.get('IMP:N',[0])[0])
            imp_p = float(parameters.get('IMP:P', [0])[0])
            imp_e = float(parameters.get('IMP:E', [0])[0])
            lat = int(parameters.get('LAT', [0])[0])
            if '*FILL' in parameters.keys():
                fill_id= int(parameters['*FILL'][0])
                fill_type='*FILL'
                transf  = ' '.join(parameters['*FILL'][1:]).replace('(',' ').replace(')',' ').strip()
                len_transf=len(transf.split())
                transf_id = int(transf) if len_transf==1 else 0
                transf = transf if len_transf > 1 else ''
            elif 'FILL' in parameters.keys():
                fill_id = int(parameters['FILL'][0])
                fill_type='FILL'
                transf  = ' '.join(parameters['FILL'][1:]).replace('(',' ').replace(')',' ').strip()
                len_transf = len(transf.split())
                transf_id = int(transf) if len_transf==1 else 0
                transf = transf if len_transf > 1 else ''
            else:
                fill_id = 0
                fill_type = ''
                transf_id = 0
                transf = ''
            universe_id = int(parameters.get('U',[0])[0])
        else:
            raise NotImplementedFeature('LIKE has not been implemented yet!')
        cell_desc_split = cell_desc.splitlines()
        comment_lines = []
        for l in reversed(cell_desc_split):
            if l[0].lower() == 'c' or l.strip()[0] == '$':
                comment_lines.append(l.strip())
            else:
                break
        comment_list = [l[1:] for l in comment_lines if l[0] == '$']
        if len(comment_list)==0:
            for l in reversed(comment_lines):
                comment_list.append(l[1:])
                if len(l.split())>1:
                    break
        comment=' '.join(comment_list).strip()
        if comment.lower().replace('c', '').replace('-', '').strip():
            len_comment_list = len(comment_list)
        else:
            comment = ''
            len_comment_list = 0
        len_cell_description = len(cell_desc_split)-len(comment_lines)+len_comment_list
        input_cell_description = '\n'.join(cell_desc_split[:len_cell_description])
        end_line = start_line+len_cell_description-1
        
        return cls(id=cell_id, mat_id=mat_id, density=density, geometry=geometry, fill_id=fill_id, fill_type=fill_type, 
            universe_id=universe_id, imp_p=imp_p, imp_n=imp_n, imp_e=imp_e, transf=transf, lat=lat, transf_id=transf_id, start_line=start_line,\
            end_line=end_line, comment=comment, input_cell_description=input_cell_description, surfaces=surfaces, not_cells=not_cells)
    
    def __str__(self):
        return '''<MCNPCell>
id = {}
mat_id = {}
density = {}
geometry = {}
surfaces = {}
not_cells = {}
fill_id = {}
fill_type = {}
universe_id = {}
imp_p = {}
imp_n = {}
imp_e = {}
transf = {}
transf_id = {}
lat = {}
start_line = {}
end_line = {}
comment = {}
input_cell_description: 
{}
'''.format(self.id, self.mat_id, self.density, self.geometry, self.surfaces, self.not_cells, self.fill_id, self.fill_type, self.universe_id,
               self.imp_p, self.imp_n, self.imp_e, self.transf, self.transf_id, self.lat, self.start_line, self.end_line,
               self.comment, self.input_cell_description)

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
        return set([cell.transf_id for cell in self._store.values() if cell.transf_id!=0])

    def get_universe_ids(self):
        return set([cell.universe_id for cell in self._store.values() if cell.universe_id!=0])

    def get_fill_ids(self):
        return set([cell.fill_id for cell in self._store.values() if cell.fill_id!=0])
    
    def get_comments(self):
        return set([cell.comment for cell in self._store.values() if cell.comment != ''])
    
