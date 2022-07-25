from mcnp_input_reader import MCNPCells, MCNPCell, MCNPSurfs, MCNPSurf, MCNPMaterial, MCNPMaterials, MCNPTransformation, MCNPTransformations
import re
import multiprocessing
import itertools
from mcnp_input_reader.util.lines import file_to_lines
# from memory_profiler import profile
# import time
cell_pattern = re.compile(r'^\d')
surface_pattern = re.compile(r'^(\*)?\d+')
transformation_pattern = re.compile(r'^(\*)?TR\d+', re.IGNORECASE)
material_pattern = re.compile(r'^M\d+', re.IGNORECASE)
# space_pattern = re.compile(r'^\s+')
not_space_pattern = re.compile(r'^\S')
material_transf_comment_pattern = re.compile(r"""^M\d+|^(\*)?TR|^C|^\s""", re.IGNORECASE)
blank_line_pattern = re.compile(r"^\s*$")


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
                cells_of_universes = self.cells.filter(lambda cell: cell.universe_id in universe_ids)
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


def factory_of_cards(card_description, blank_line_indices):
    '''
    The factory produces the card according to the pattern and the
    position in the MCNP input

    :param card_description: tuple (line_number, card definition)
    :param blank_line_indices: indices of the MCNP input blank lines
    :return: card data structure
    '''
    line_number = card_description[0]
    card_string = card_description[1]
    if line_number < blank_line_indices[0]:
        return MCNPCell.from_string(card_string, line_number)
    elif line_number < blank_line_indices[1]:
        if surface_pattern.match(card_string):
            return MCNPSurf.from_string(card_string, line_number)
    else:  # section data
        if material_pattern.match(card_string):
            return MCNPMaterial.from_string(card_string, line_number)
        elif transformation_pattern.match(card_string):
            return MCNPTransformation.from_string(card_string, line_number)


# @profile
def read_file(filename):
    lines = file_to_lines(filename)
    line_indices = [index for index in range(1, len(lines)) if (lines[index][0] != ' ' and lines[index][0].upper() != 'C')]
    blank_line_indices = [index for index in range(len(lines)) if blank_line_pattern.match(lines[index])]
    cards_lines = ((line_indices[i], ''.join(lines[line_indices[i]:line_indices[i + 1]])) if i < len(line_indices) - 1 else (line_indices[i], ''.join(lines[line_indices[i]:-1])) for i in range(len(line_indices)))

    with multiprocessing.Pool() as p:
        output_cards = p.starmap(factory_of_cards, zip(cards_lines, itertools.repeat(blank_line_indices)))

    cells = MCNPCells([card for card in output_cards if type(card).__name__ == 'MCNPCell'])
    surfaces = MCNPSurfs([card for card in output_cards if type(card).__name__ == 'MCNPSurf'])
    materials = MCNPMaterials([card for card in output_cards if type(card).__name__ == 'MCNPMaterial'])
    transformations = MCNPTransformations([card for card in output_cards if type(card).__name__ == 'MCNPTransformation'])

    return MCNPInput(lines, cells, surfaces, materials, transformations)
