from mcnp_input_reader import __version__
from mcnp_input_reader import MCNPCells, MCNPCell


def test_version():
    assert __version__ == '0.1.0'


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
    cell = MCNPCell()
    for line in cell_string.splitlines():
        cell.append_line(line)
    cell.generate_cell_from_lines()
    geometry = ' '.join('''( 427119 (-427120:427015) -427001 -427121 427122 : 
-427122 428577 -428615 : -427122 428577 -428616 ) -427022 427024
(-428634:428635:428632:428633)
(428649:-428650:428651:-428664:428665)'''.split())
    cell_check = MCNPCell(cell_id=427006, mat_id=0, density=0.0,
                          geometry=geometry, fill_type='FILL',
                          fill_id=6, transf_id=41)
    assert cell == cell_check
