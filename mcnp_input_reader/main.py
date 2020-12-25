from . import MCNPCell, MCNPCells

def funzione(inputfile): 
    cells=MCNPCells()
    with open(inputfile, errors='ignore') as f:
        title=next(f)
        section_id=0
        start_tr=0
        start_mat=0
        cell_id=0
        for n, line in enumerate(f,1):
            if line=='\n' or line=='':
                if section_id==0:
                    cells.parallel_generate_cells()
                section_id+=1
            if section_id==0:
             
                if line.strip()=='':
                    continue
                if re.match(r'^\d', line):
                    cell_id=int(line.split()[0])
                    cells.add_cell_line(cell_id, n, line)
                elif cell_id>0:
                    cells.append_line_to_cell(cell_id, line)
            elif section_id==1:
                
                pass
               
            elif section_id==2:
                pass
                
    
            else:
                break
    return cells

