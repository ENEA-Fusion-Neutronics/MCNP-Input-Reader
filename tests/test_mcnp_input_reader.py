from mcnp_input_reader import MCNPCells, MCNPCell



def test_cell_string_1():
    '''Test for MCNPCell Class, generate_cell_from_lines method'''

    cell_string = '''427006     0   ( 427119 (-427120:427015) -427001 -427121 427122 : -427122
          428577 -428615 : -427122 428577 -428616 )
               -427022 427024
              (-428634:428635:428632:428633)
              (428649:-428650:428651:-428664:428665)
              IMP:N=1.000000  IMP:P=1.000000
              FILL=6 (41)
C'''
    cell = MCNPCell.from_string(cell_string, 0)
    geometry = ' '.join('''( 427119 (-427120:427015) -427001 -427121 427122 : 
-427122 428577 -428615 : -427122 428577 -428616 ) -427022 427024
(-428634:428635:428632:428633)
(428649:-428650:428651:-428664:428665)'''.split())
    surfaces = set(geometry.replace('(',' ').replace(')', ' ').replace(':',' ').replace('-', ' ').split())
    surfaces = set([int(surf) for surf in surfaces])
    input_cell_description = '''427006     0   ( 427119 (-427120:427015) -427001 -427121 427122 : -427122
          428577 -428615 : -427122 428577 -428616 )
               -427022 427024
              (-428634:428635:428632:428633)
              (428649:-428650:428651:-428664:428665)
              IMP:N=1.000000  IMP:P=1.000000
              FILL=6 (41)'''
    cell_check = MCNPCell(id = 427006, mat_id = 0, density = 0.0,
                          geometry=geometry, fill_type='FILL',
                          fill_id=6, transf_id=41, lat = 0, universe_id = 0, imp_n = 1.0, 
                          imp_p = 1.0, imp_e = 0.0, transf = '', start_line = 0, 
                          end_line = 6, input_cell_description = input_cell_description, comment = '', not_cells = set() , surfaces = surfaces)
    assert cell == cell_check


                                       
