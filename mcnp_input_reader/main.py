from mcnp_input_reader import MCNPCells, MCNPCell, MCNPSurfs, MCNPSurf, MCNPMaterial, MCNPMaterials, MCNPTransformation, MCNPTransformations
import re
import multiprocessing
#import time
cell_pattern = re.compile(r'^\d')
#surface_pattern = re.compile(r'^(\*)?\d+')
transformation_pattern = re.compile(r'^(\*)?TR\d+', re.IGNORECASE)
material_pattern = re.compile(r'^M\d+', re.IGNORECASE)
#space_pattern = re.compile(r'^\s+')
not_space_pattern = re.compile(r'^\S')

class MCNPInput:

    def __init__(self, title, cells, surfaces, materials, transformations):
        self.title = title
        self.cells = cells
        self.surfaces = surfaces
        self.materials = materials
        self.transformations = transformations
    
    def extract(self, p, only_level_zero = False):
        filtered_cells = self.cells.filter(p)
        universe_ids = filtered_cells.get_fill_ids()
        if only_level_zero == False:
            while len(universe_ids) > 0:
                cells_of_universes = self.cells.filter(lambda cell: cell.universe_id in universe_ids)
                universe_ids = set()
                for cell in cells_of_universes:
                    if cell not in filtered_cells:
                        filtered_cells.add(cell)
                        if cell.fill_id != 0:
                            universe_ids.update([cell.fill_id])
        surfaces_ids = filtered_cells.get_surfaces()
        materials_ids = filtered_cells.get_materials()
        transformations_ids = filtered_cells.get_transformations()
        surfaces = self.surfaces.filter(lambda surf: surf.id in surfaces_ids)
        transformations_ids = transformations_ids.union(surfaces.get_transformations())

        materials = self.materials.filter(lambda mat: mat.id in materials_ids)
        transformations = self.transformations.filter(lambda transf: transf.id in transformations_ids)
        title = 'Extracted from ' + self.title 
        return MCNPInput(title, filtered_cells, surfaces, materials, transformations)

    def get_start_end_lines(self):
        start_stop = self.cells.get_start_end_lines()+self.surfaces.get_start_end_lines()+self.materials.get_start_end_lines()+self.transformations.get_start_end_lines()
        return sorted(start_stop, key=lambda tup: tup[0])
    
    def __repr__(self):
        return '''Title: {}

The input contains:
# of cells: {}
# of surfaces: {}
# of materials: {}
# of transformations: {}'''.format(self.title, len(self.cells), len(self.surfaces), len(self.materials), len(self.transformations))

def generate_cell(cell_description):
    line_number = cell_description[0]
    cell_string = cell_description[1]
    return MCNPCell.from_string(cell_string, line_number)

def generate_surface(surface_description):
    line_number = surface_description[0]
    surface_string = surface_description[1]
    return MCNPSurf.from_string(surface_string, line_number)

def generate_material(material_description):
    line_number = material_description[0]
    material_string = material_description[1]
    return MCNPMaterial.from_string(material_string, line_number)

def generate_transformation(transformation_description):
    line_number = transformation_description[0]
    transformation_string = transformation_description[1]
    return MCNPTransformation.from_string(transformation_string, line_number)


def read_file(inputfile):
          
    cells_list = []
    surfaces_list = []
    materials_list = []
    transformations_list = []
    with open(inputfile, errors='ignore') as f:
        title = next(f)
        section_id = 0
        start_tr = 0
        start_mat = 0
        cell_id = 0
        for n, line in enumerate(f, 1):
            if line == '\n' or line == '':
                section_id += 1
            if line.strip() == '':
                continue
            if section_id == 0:
                if cell_pattern.match(line):
                    cells_list.append([n, line])
                elif cells_list:
                    cells_list[-1][1] += line
            elif section_id == 1:
                if cell_pattern.match(line) or line[0] == '*':
                    surfaces_list.append([n, line])
                elif surfaces_list:
                    surfaces_list[-1][1] += line
            elif section_id == 2:
                start_line_char = line.strip().upper()[0]
                if transformation_pattern.match(line):
                    start_tr = 1
                    start_mat = 0
                    transformations_list.append([n, line])
                elif start_tr == 1 and start_line_char != 'M':
                    transformations_list[-1][1] += line
                elif material_pattern.match(line):
                    start_tr = 0
                    start_mat = 1
                    materials_list.append([n, line])
                elif start_line_char != 'C' and not_space_pattern.match(line):
                    start_tr = 0
                    start_mat = 0
                elif start_mat == 1:
                    materials_list[-1][1] += line
            else:
                break

    with multiprocessing.Pool() as p:
        output_cells=p.map(generate_cell, cells_list)
    #with multiprocessing.Pool() as p:
        output_surfaces = p.map(generate_surface, surfaces_list)
        output_materials = p.map(generate_material, materials_list) 
        output_transformations = p.map(generate_transformation, transformations_list) 
    cells = MCNPCells(output_cells)
    surfs = MCNPSurfs(output_surfaces)
    materials = MCNPMaterials(output_materials)
    transformations = MCNPTransformations(output_transformations)
    title = title.replace('\n','')
    return MCNPInput(title, cells, surfs, materials, transformations)



