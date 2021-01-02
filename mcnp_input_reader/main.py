from mcnp_input_reader import MCNPCells, MCNPCell, MCNPSurfs, MCNPSurf
import re
import multiprocessing
from joblib import Parallel, delayed
import time
cell_pattern = re.compile(r'^\d')
#surface_pattern = re.compile(r'^(\*)?\d+')
transformation_pattern = re.compile(r'^(\*)?TR\d+', re.IGNORECASE)
#material_pattern = re.compile(r'^M\d+', re.IGNORECASE)

def read_mcnp_input(inputfile):

    cells = MCNPCells()
    with open(inputfile, errors='ignore') as f:
        title = next(f)
        section_id = 0
        start_tr = 0
        start_mat = 0
        cell_id = 0
        for n, line in enumerate(f, 1):
            if line == '\n' or line == '':
                if section_id == 0:
                    cells.parallel_generate_cells()
                    #cells.generate_cells()
                section_id += 1
            if section_id == 0:
                if line.strip() == '':
                    continue
                if start_d_pattern.match(line):
                    cell_id = int(line.split()[0])
                    cells.add_cell_line(cell_id, n, line)
                elif cell_id > 0:
                    cells.append_line_to_cell(cell_id, line)
            elif section_id == 1:
                pass
            elif section_id == 2:
                pass
            else:
                break
    return cells

def generate_cell(cell_description):
    line_number = cell_description[0]
    cell_string = cell_description[1]
    return MCNPCell.from_string(cell_string, line_number)

def generate_surface(surface_description):
    line_number = surface_description[0]
    surface_string = surface_description[1]
    return MCNPSurf.from_string(surface_string, line_number)



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
                elif start_line_char == 'M':
                    start_tr = 0
                    start_mat = 1
                    materials_list.append([n, line])
                elif start_mat == 1:
                    materials_list[-1][1] += line
            else:
                break

    #output_cells = Parallel(n_jobs=-1)(delayed(generate_cell)(cell_des) for cell_des in cells)
    with multiprocessing.Pool() as p:
        output_cells=p.map(generate_cell, cells_list)
    with multiprocessing.Pool() as p:
        output_surfaces = p.map(generate_surface, surfaces_list)
    #output_cells=p.apply_async(generate_cell,args=(cells,))
    #p.close()
    #p.join()
        #cells.generate_cells()
    cells = MCNPCells(output_cells)
    #for cell in output_cells:
    #    cells.add_cell(cell)
    surfs = MCNPSurfs(output_surfaces)
    #for surf in output_surfaces:
    #    surfs.add_surf(surf)
    return cells, surfs


if __name__=='__main__':
    cells, surfs = read_file('/home/giovanni/lavoro/ITER/ITER_lower_port_14_sector7/E-lite_R200430')
    #print(surfs)
