from .exceptions import CellNotFound, CellIdAlreadyUsed
from .store import Store
from dataclasses import dataclass, field
from typing import Dict, List
from joblib import Parallel, delayed
from collections import namedtuple

CELL_PARAMETERS = ['IMP', 'VOL', 'PWT', 'EXT',
                    'FCL', 'WWN', 'DXC', 'NONU',
                    'PD', 'TMP', 'U', 'TRCL',
                    'LAT', 'FILL', 'ELPT', 'COSY', 'BFLCL', 'UNC']

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
                                       'imp_n','transf','transf_id','start_line','end_line',
                                       'comment','input_cell_description','surfaces','not_cells'])):
    """MCNPCell is an immutable and lightweight object"""
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
        cell_desc_split = cell_desc.splitlines()
        cell_pure = ' '.join([line.split('$')[0].strip() for line in cell_desc_split if line[0].lower() != 'c']).replace('(', ' (').replace(')', ') ')
        cell_pure_split=cell_pure.split()
        cell_id=int(cell_pure_split[0])
        mat_id=int(cell_pure_split[1])
        if mat_id==0:
            the_rest=' '.join(cell_pure_split[2:]).upper()
            density = 0.0
        else:
            the_rest=' '.join(cell_pure_split[3:]).upper()
            density = float(cell_pure_split[2])
        
        for x in CELL_PARAMETERS:
            the_rest=the_rest.replace(x,f'\n{x} ')
        
        the_rest=the_rest.replace('*\nFILL','\n*FILL').splitlines()
        geometry=' '.join(the_rest[0].split())#.replace(' (','(').replace(') ',')')
        geom = geometry.replace('(', ' ').replace(')', ' ').replace(':', ' ').replace('-', ' ').replace('+', ' ').split()
        surfaces=set([int(s) for s in geom if s[0] != '#'])
        not_cells=set([int(s[1:]) for s in geom if (s[0] == '#') and (len(s) > 1)])
        parameters={}
        for p in the_rest[1:]:
            k_v = p.replace('=',' ').split()
            k=k_v[0]
            v=k_v[1:]
            parameters[k]=v
        imp_n=float(parameters.get('IMP:N',[0])[0])
        imp_p=float(parameters.get('IMP:P', [0])[0])
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
            universe_id=universe_id, imp_p=imp_p, imp_n=imp_n, transf=transf, transf_id=transf_id, start_line=start_line,\
            end_line=end_line, comment=comment, input_cell_description=input_cell_description, surfaces=surfaces, not_cells=not_cells)

class MCNPCells(Store):
    
    def __init__(self, cell_list = []):
        super().__init__(cell_list)
        self.cardnotfound_exception = CellNotFound
        self.cardidalreadyused_exception = CellIdAlreadyUsed
        self.card_name = 'cell'
    
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


def generate_one_cell2(cell_des):
    line_des = cell_des['text_line']
    # cell_id = cell_des['cell_id']
    line_num = cell_des['start_line']
    return MCNPCell.from_string(line_des, line_num)
    


@dataclass
class MCNPCells_old:
    '''Dictonary container for MCNP cell'''

    cells: Dict[int, MCNPCell] = field(init=False)
    cells_line: Dict[int, Dict] = field(init=False, repr=False)
    
    def add_cell(self, cell: MCNPCell):
        if self.cells.get(cell.id, False):
           raise CellIdAlreadyUsed('Vaffanculo, the cell_id {} has been already used'.format(cell.id))
        else:
            self.cells[cell.id] = cell    

    def add_cell_line(self, cell_id: int, line_number: int = 0, line: str = ''):
        if cell_id in self.cells_line.keys():
           raise CellIdAlreadyUsed('Vaffanculo, the cell_id {} has been already used'.format(cell_id))
        else:
            self.cells_line[cell_id] = {'cell_id': cell_id, 'start_line': line_number, 'text_line': line} 

    def generate_cells(self):
        for cell_des in self.cells_line.values():
            #cell = MCNPCell()
            line_des = cell_des['text_line']
            cell_id = cell_des['cell_id']
            line_num = cell_des['start_line']
            self.cells[cell_id] = MCNPCell2.from_string(line_des, line_num)
   
    def parallel_generate_cells(self):
        cells = Parallel(n_jobs=-1)(delayed(generate_one_cell2)(cell_des) for cell_des in self.cells_line.values())
        self.cells = {cell.id: cell for cell in cells}

    def append_line_to_cell(self, cell_id: int, line: str):
        if cell_id in self.cells_line.keys():
            self.cells_line[cell_id]['text_line'] += line
        else:
            raise CellNotFound('Vaffanculo, cell_id {} does not exist!'.format(cell_id))
    
    def __post_init__(self):
        self.cells = {}
        self.cells_line = {}
        
    def __getitem__(self, cell_id:int):
        if cell_id in self.cells.keys():
            return self.cells[cell_id]
        else:
            raise CellNotFound('Vaffanculo, cell_id {} does not exist!'.format(cell_id))
    
    def __len__(self):
        return len(self.cells)

    def __iter__(self):
        return (cell for cell in self.cells.values())
    
    def filter_cells(self, p, all_levels=False):
        filtered_cells= MCNPCells()
        for cell in list(filter(p, self.__iter__())):
            filtered_cells.add_cell(cell)
            
        if all_levels==True:
            universe_ids = filtered_cells.get_fill_ids()
            while len(universe_ids)>0:
                cells_of_universes = list(filter(lambda cell: cell.universe_id in universe_ids, self.__iter__()))
                universe_ids=set()
                for cell in cells_of_universes:
                    filtered_cells.add_cell(cell)
                    if cell.fill_id!=0:
                        universe_ids.update([cell.fill_id])
        return filtered_cells
    
    def get_surfaces(self):
        surfaces=set()
        for cell in self.cells.values():
            surfaces.update(cell.surfaces)
        return surfaces

    def get_materials(self):
        return set([cell.mat_id for cell in self.cells.values() if cell.mat_id!=0])

    def get_transformations(self):
        return set([cell.transf_id for cell in self.cells.values() if cell.transf_id!=0])

    def get_universe_ids(self):
        return set([cell.universe_id for cell in self.cells.values() if cell.universe_id!=0])

    def get_fill_ids(self):
        return set([cell.fill_id for cell in self.cells.values() if cell.fill_id!=0])
