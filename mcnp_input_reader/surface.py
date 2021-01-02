from collections import namedtuple
from dataclasses import dataclass, field
from .exceptions import CellNotFound, CellIdAlreadyUsed, SurfNotFound, SurfIdAlreadyUsed
from .store import Store
from typing import Dict, List


_SURFS_TYPE={'P':'Plane',
            'PX':'Plane',
            'PY':'Plane',
            'PZ':'Plane',
            'SO':'Sphere',
            'S':'Sphere',
            'SX':'Sphere',
            'SY':'Sphere',
            'SZ':'Sphere',
            'C/X':'Cylinder',
            'C/Y':'Cylinder',
            'C/Z':'Cylinder',
            'CX':'Cylinder',
            'CY':'Cylinder',
            'CZ':'Cylinder',
            'K/X':'Cone',
            'K/Y':'Cone',
            'K/Z':'Cone',
            'KX':'Cone',
            'KY':'Cone',
            'KZ':'Cone',
            'TX':'Torus',
            'TY':'Torus',
            'TZ':'Torus',
            'GQ':'GQ',
            'SQ':'SQ',
            'XYZP':'XYZP',
            'X':'X',
            'Y':'Y',
            'Z':'Z',
            'RPP':'RPP',
            'BOX':'BOX',
            'RPP':'RPP',
            'SPH':'SPH',
            'RCC':'RCC',
            'RHP':'RHP',  
            'HEX':'HEX',
            'REC':'REC',
            'TRC':'TRC',
            'ELL':'ELL',
            'WED':'WED',
            'ARB':'ARB'
           }

class MCNPSurf(namedtuple('MCNPSurf', ['id','surface_type','surface_parameters','transf_id','start_line','end_line','input_surface_description'])):
    """MCNPSurf is an immutable and lightweight object"""
    __slots__ = ()

    @classmethod
    def from_string(cls, surface_desc, start_line):
        surf_desc_split = surface_desc.upper().splitlines()
        surf_pure = ' '.join([line.split('$')[0].strip() for line in surf_desc_split if line[0].lower() != 'c']).replace('(', ' (').replace(')', ') ')
        surf_pure_split = surf_pure.split()
        surf_id = int(surf_pure_split[0])
        
        if surf_pure_split[1] in _SURFS_TYPE.keys():
            surface_type = surf_pure_split[1]
            transf_id = 0
            surface_parameters = ' '.join(surf_pure_split[2:])
        else:
            transf_id = int(surf_pure_split[1])
            surface_type = surf_pure_split[2]
            surface_parameters = ' '.join(surf_pure_split[3:])
        
        comment_lines = []
        for l in reversed(surf_desc_split):
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
        len_surf_description = len(surf_desc_split)-len(comment_lines)+len_comment_list
        input_surface_description = '\n'.join(surf_desc_split[:len_surf_description])
        end_line = start_line+len_surf_description-1

        return cls(id = surf_id, surface_type = surface_type, surface_parameters = surface_parameters, transf_id = transf_id, start_line = start_line, end_line = end_line, input_surface_description = input_surface_description)



class MCNPSurfs(Store):
    
    def __init__(self, surface_list = []):
        super().__init__(surface_list)
        self.cardnotfound_exception = SurfNotFound
        self.cardidalreadyused_exception = SurfIdAlreadyUsed
        self.card_name = 'surface'


    def get_transformations(self):
        return set([surf.transf_id for surf in self._store.values() if surf.transf_id!=0])


@dataclass
class MCNPSurfs_old:
    '''Dictonary container for MCNP cell'''

    surfs: Dict[int, MCNPSurf] = field(init=False)
    
    def add_surf(self, surf: MCNPSurf):
        if self.surfs.get(surf.id, False):
           raise CellIdAlreadyUsed('Vaffanculo, the surface {} has been already used'.format(surf.id))
        else:
            self.surfs[surf.id] = surf    

        
    def __post_init__(self):
        self.surfs = {}
        
    def __getitem__(self, surf_id:int):
        if surf_id in self.surfs.keys():
            return self.surfs[surf_id]
        else:
            raise CellNotFound('Vaffanculo, surface {} does not exist!'.format(surf_id))
    
    def __len__(self):
        return len(self.surfs)

    def __iter__(self):
        return (surf for surf in self.surfs.values())
    
    def filter_surfaces(self, p):
        filtered_surfaces= MCNPSurfs()
        for surf in list(filter(p, self.__iter__())):
            filtered_surfs.add_surf(surf)
            
        return filtered_surfs
    
    def get_transformations(self):
        return set([surf.transf_id for surf in self.surfs.values() if surf.transf_id!=0])

