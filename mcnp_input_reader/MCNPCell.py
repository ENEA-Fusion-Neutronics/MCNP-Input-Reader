# import re
from dataclasses import dataclass, field
from typing import Dict, List
from joblib import Parallel, delayed


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


@dataclass
class MCNPCell:
    cell_id: int = 0
    mat_id: int = 0
    density: float = 0.0
    geometry: str = ''
    fill_id: int = 0
    fill_type: str = ''
    universe_id: int = 0
    imp_p: float = 0.0
    imp_n: float = 0.0
    transf: str = ''
    transf_id: int = 0
    start_line: int = 0
    end_line: int = 0
    comment: str = ''
    input_cell_description: str = ''
    surfaces: List[int] = field(init=False)
    not_cells: List[int] = field(init=False)
    lines: List[str] = field(init=False, repr=False, compare=False)

    def from_string(self, cell_desc: str, start_line: int = 0):
        cell_desc_split = cell_desc.splitlines()
        cell_pure = ' '.join([line.split('$')[0].strip() for line in cell_desc_split if line[0].lower() != 'c']).replace('(', ' (').replace(')', ') ')
        self.generate_cell_parameters_from_string(cell_pure)
        self.start_line = start_line
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
        if comment.lower().replace('c','').replace('-','').strip():
            self.comment=comment 
            len_comment_list=len(comment_list)
        else:
            len_comment_list=0
        len_cell_description=len(cell_desc_split)-len(comment_lines)+len_comment_list
        self.input_cell_description='\n'.join(cell_desc_split[:len_cell_description])
        self.end_line=start_line+len_cell_description-1

    def append_line(self, line:str):
        self.lines.append(line)

    def __post_init__(self):
        self.lines = []
        if self.geometry:
            self.geometry=' '.join(self.geometry.split())
            geom = self.geometry.replace('(',' ').replace(')',' ').replace(':',' ').replace('-',' ').replace('+',' ').split()
            self.surfaces=set([int(s) for s in geom if s[0]!='#'])
            self.not_cells=set([int(s[1:]) for s in geom if (s[0]=='#') and (len(s)>1)])

    
    def generate_cell_from_lines(self):
        cell_pure=' '.join([l.split('$')[0].replace('\n',' ').strip() for l in self.lines if l[0].lower()!='c']).replace('(',' (').replace(')',') ')
        #cell_dict=re.match(pattern_cell, cell_pure, flags=0).groupdict()
        self.generate_cell_parameters_from_string(cell_pure)

    def generate_cell_parameters_from_string(self, cell_pure:str):
        cell_pure_split=cell_pure.split()
        self.cell_id=int(cell_pure_split[0])
        self.mat_id=int(cell_pure_split[1])
        #self.density=float(cell_pure_split[2]) if self.mat_id != 0 else 0.0
        if self.mat_id==0:
            the_rest=' '.join(cell_pure_split[2:]).upper()
            self.density = 0.0
        else:
            the_rest=' '.join(cell_pure_split[3:]).upper()
            self.density = float(cell_pure_split[2])
        
        for x in CELL_PARAMETERS:
            the_rest=the_rest.replace(x,f'\n{x} ')
        
        the_rest=the_rest.replace('*\nFILL','\n*FILL').splitlines()
        #the_rest=re.split(pattern_cell_2,the_rest)
        #the_rest=[s.strip() for s in the_rest if s]
        self.geometry=' '.join(the_rest[0].split())#.replace(' (','(').replace(') ',')')
        geom = self.geometry.replace('(', ' ').replace(')', ' ').replace(':', ' ').replace('-', ' ').replace('+', ' ').split()
        self.surfaces=set([int(s) for s in geom if s[0] != '#'])
        self.not_cells=set([int(s[1:]) for s in geom if (s[0] == '#') and (len(s) > 1)])
        parameters={}
        for p in the_rest[1:]:
            k_v = p.replace('=',' ').split()
            k=k_v[0]
            v=k_v[1:]
            parameters[k]=v
        self.imp_n=float(parameters.get('IMP:N',[0])[0])
        self.imp_p=float(parameters.get('IMP:P', [0])[0])
        if '*FILL' in parameters.keys():
            self.fill_id= int(parameters['*FILL'][0])
            self.fill_type='*FILL'
            transf  = ' '.join(parameters['*FILL'][1:]).replace('(',' ').replace(')',' ').strip()
            len_transf=len(transf.split())
            self.transf_id = int(transf) if len_transf==1 else 0
            self.transf = transf if len_transf > 1 else ''
        elif 'FILL' in parameters.keys():
            self.fill_id = int(parameters['FILL'][0])
            self.fill_type='FILL'
            transf  = ' '.join(parameters['FILL'][1:]).replace('(',' ').replace(')',' ').strip()
            len_transf = len(transf.split())
            self.transf_id = int(transf) if len_transf==1 else 0
            self.transf = transf if len_transf > 1 else ''
        self.universe_id = int(parameters.get('U',[0])[0])
 
def generate_one_cell(cell_des):
    cell = MCNPCell()
    line_des = cell_des['text_line']
    # cell_id = cell_des['cell_id']
    line_num = cell_des['start_line']
    cell.from_string(line_des, line_num)
    return cell
       
@dataclass
class MCNPCells:
    '''Dictonary container for MCNP cell'''

    cells: Dict[int, MCNPCell] = field(init=False)
    cells_line: Dict[int, Dict] = field(init=False, repr=False)
    
    def add_cell(self, cell: MCNPCell):
        if self.cells.get(cell.cell_id, False):
           raise Exception('Vaffanculo, the cell_id {} has been already used'.format(cell.cell_id))
        else:
            self.cells[cell.cell_id] = cell    

    def add_cell_line(self, cell_id: int, line_number: int = 0, line: str = ''):
        if cell_id in self.cells_line.keys():
           raise Exception('Vaffanculo, the cell_id {} has been already used'.format(cell_id))
        else:
            self.cells_line[cell_id] = {'cell_id': cell_id, 'start_line': line_number, 'text_line': line}
    
    def generate_one_cell(self, cell_des): 
        cell=MCNPCell()
        line_des=cell_des['text_line']
        cell_id=cell_des['cell_id']
        line_num=cell_des['start_line']
        cell.from_string(line_des, line_num)
        return cell

    def generate_cells(self): 
        for cell_des in self.cells_line.values():
            cell=MCNPCell()
            line_des=cell_des['text_line']
            cell_id=cell_des['cell_id']
            line_num=cell_des['start_line']
            cell.from_string(line_des, line_num)
            self.cells[cell_id]=cell
   
    def parallel_generate_cells(self):
        cells=Parallel(n_jobs=-1)(delayed(generate_one_cell)(cell_des) for cell_des in self.cells_line.values())
        self.cells={cell.cell_id:cell for cell in cells}

    def append_line_to_cell(self, cell_id: int, line: str):
        if cell_id in self.cells_line.keys():
            self.cells_line[cell_id]['text_line']+=line
        else:
            raise Exception('Vaffanculo, cell_id {} does not exist!'.format(cell_id))
    
    def __post_init__(self):
        self.cells={}
        self.cells_line={}
        
    def __getitem__(self, cell_id:int):
        if cell_id in self.cells.keys():
            return self.cells[cell_id]
        else:
            raise Exception('Vaffanculo, cell_id {} does not exist!'.format(cell_id))
    
    def __len__(self):
        return len(self.cells)

    def __iter__(self):
        return (cell for cell in self.cells.values())
    
    def filter_cells(self, p, all_levels=False):
        filtered_cells= MCNPCells()
        universe_ids = set()
        for cell in list(filter(p, self.__iter__())):
            filtered_cells.add_cell(cell)
            if all_levels==True and cell.fill_id!=0:
                universe_ids.update([cell.fill_id])
        if all_levels==True:
            while len(universe_ids)>0:
                cells_of_universes=list(filter(lambda cell: cell.universe_id in universe_ids, self.__iter__()))
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
