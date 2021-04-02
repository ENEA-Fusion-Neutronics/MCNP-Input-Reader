from mcnp_input_reader import MCNPCells, MCNPCell, MCNPSurfs, MCNPSurf, MCNPMaterial, MCNPMaterials, MCNPTransformation, MCNPTransformations
import re
import multiprocessing
import itertools

# import time
cell_pattern = re.compile(r'^\d')
# surface_pattern = re.compile(r'^(\*)?\d+')
transformation_pattern = re.compile(r'^(\*)?TR\d+', re.IGNORECASE)
material_pattern = re.compile(r'^M\d+', re.IGNORECASE)
# space_pattern = re.compile(r'^\s+')
not_space_pattern = re.compile(r'^\S')
material_transf_comment_pattern = re.compile(r"""^M\d+|^(\*)?TR|^C|^\s""", re.IGNORECASE)


def get_line_numbers_of_data(lines):
    # only_data = []
    only_data_line_numbers = []
    counter = 0
    add_next_line = False
    for n, line in enumerate(lines):
        if line == '\n':
            counter += 1
        if counter == 2:
            exclude_line = material_transf_comment_pattern.match(line)
            if line[0] == ' ' and add_next_line:
                # only_data.append(l)
                only_data_line_numbers.append(n)
            elif exclude_line:
                add_next_line = False
            elif not exclude_line:
                add_next_line = True
                # only_data.append(l)
                only_data_line_numbers.append(n)
    return only_data_line_numbers


class MCNPInput:

    def __init__(self, lines=[], cells=[], surfaces=[], materials=[], transformations=[]):
        self.lines = lines
        self.title = lines[0]
        self.cells = cells
        self.surfaces = surfaces
        self.materials = materials
        self.transformations = transformations
        self._set_parent()

    def __call__(self, lines=[], cells=[], surfaces=[], materials=[], transformations=[]):
        self.lines = lines
        self.title = lines[0]
        self.cells = cells
        self.surfaces = surfaces
        self.materials = materials
        self.transformations = transformations
        self._set_parent()

    def _set_parent(self):
        self.cells.parent = self
        self.surfaces.parent = self
        self.materials.parent = self
        self.transformations.parent = self

    def extract(self, p, deep=True, remove_comments=False):
        filtered_cells = self.cells.filter(p)
        universe_ids = filtered_cells.get_fill_ids()
        if deep:
            while len(universe_ids) > 0:
                cells_of_universes = self.cells.filter(lambda cell: cell.universe_id in universe_ids )
                filtered_cells.union(cells_of_universes)
                universe_ids = cells_of_universes.get_fill_ids()

        surfaces_ids = filtered_cells.get_surfaces()
        materials_ids = filtered_cells.get_materials()
        transformations_ids = filtered_cells.get_transformations()
        surfaces = self.surfaces.filter(lambda surf: surf.id in surfaces_ids)
        transformations_ids = transformations_ids.union(surfaces.get_transformations())

        materials = self.materials.filter(lambda mat: mat.id in materials_ids)
        transformations = self.transformations.filter(lambda transf: transf.id in transformations_ids)

        start_stop_line_numbers = filtered_cells.get_start_end_lines() + surfaces.get_start_end_lines() + materials.get_start_end_lines() + transformations.get_start_end_lines()
        line_numbers_of_data = get_line_numbers_of_data(self.lines)
        iter_tools_line_numers = itertools.chain.from_iterable([*map(range, *zip(*start_stop_line_numbers))])
        dict_line_numbers_itertools = {n: True for n in iter_tools_line_numers}
        dict_line_numbers_data = {n: True for n in line_numbers_of_data}
        dict_line_numbers = {**dict_line_numbers_itertools, **dict_line_numbers_data}
        lines = []
        check = 0
        for n, line in enumerate(self.lines):
            if line == '\n':
                check += 1
            if (line.upper()[0] == 'C' and not remove_comments) or dict_line_numbers.get(n, False) or line == '\n' or check > 2:
                lines.append(line)
        return MCNPInput(lines, filtered_cells, surfaces, materials, transformations)

    def write_to_file(self, filename):
        with open(filename, 'w') as fw:
            fw.writelines(self.lines)

    # def get_start_end_lines(self):
    #    start_stop = self.cells.get_start_end_lines()+self.surfaces.get_start_end_lines()+self.materials.get_start_end_lines()+self.transformations.get_start_end_lines()
    #    return sorted(start_stop, key=lambda tup: tup[0])

    def extract_universe(self, universe_id, deep=False, remove_comments=False):
        return self.extract(lambda cell: cell.universe_id == universe_id, deep=deep, remove_comments=remove_comments)

    def __repr__(self):
        return '''Title: {}

The input contains:
# of cells: {}
# of surfaces: {}
# of materials: {}
# of transformations: {}'''.format(self.title, len(self.cells), len(self.surfaces), len(self.materials), len(self.transformations))


def generate_cell(cell_description, parent=None):
    line_number = cell_description[0]
    cell_string = cell_description[1]
    return MCNPCell.from_string(cell_string, line_number, parent)


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


# @profile
def read_file(inputfile):

    lines = []
    cells_list = []
    surfaces_list = []
    materials_list = []
    transformations_list = []
    with open(inputfile, errors='ignore') as f:
        section_id = 0
        start_tr = 0
        start_mat = 0
        cell_id = 0
        for n, line in enumerate(f):
            lines.append(line)
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
        output_cells = p.map(generate_cell, cells_list)
        # with multiprocessing.Pool() as p:
        output_surfaces = p.map(generate_surface, surfaces_list)
        output_materials = p.map(generate_material, materials_list)
        output_transformations = p.map(generate_transformation, transformations_list)

    cells = MCNPCells(output_cells)
    surfaces = MCNPSurfs(output_surfaces)
    materials = MCNPMaterials(output_materials)
    transformations = MCNPTransformations(output_transformations)

    return MCNPInput(lines, cells, surfaces, materials, transformations)
