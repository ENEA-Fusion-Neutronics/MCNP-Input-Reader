from collections import namedtuple
from .exceptions import MaterialNotFound, MaterialIdAlreadyUsed
from .store import Store
from mcnp_input_reader.util.lines import remove_comments, add_space_to_parentheses, split_on_tag, get_comment_and_endline


class MCNPMaterial(namedtuple('MCNPMaterial', ['id', 'composition', 'start_line', 'end_line', 'input_material_description', 'parent'])):
    """MCNPMaterial is an immutable and lightweight object"""
    __slots__ = ()

    @classmethod
    def from_string(cls, material_desc, start_line, parent=None):
        material_pure = remove_comments(material_desc.upper())
        # material_desc_split = material_desc.upper().splitlines()
        # material_pure = ' '.join([line.split('$')[0].strip() for line in material_desc_split if line[0].lower() != 'c']).replace('(', ' (').replace(')', ') ')
        material_pure_split = material_pure.split()
        material_id = int(material_pure_split[0][1:])
        composition = ' '.join(material_pure_split[1:])

        # comment_lines = []
        # for l in reversed(material_desc_split):
        #     if l[0].lower() == 'c' or l.strip()[0] == '$':
        #         comment_lines.append(l.strip())
        #     else:
        #         break
        # comment_list = [l[1:] for l in comment_lines if l[0] == '$']
        # if len(comment_list) == 0:
        #     for l in reversed(comment_lines):
        #         comment_list.append(l[1:])
        #         if len(l.split()) > 1:
        #             break
        # comment = ' '.join(comment_list).strip()
        # if comment.lower().replace('c', '').replace('-', '').strip():
        #     len_comment_list = len(comment_list)
        # else:
        #     comment = ''
        #     len_comment_list = 0
        # len_material_description = len(material_desc_split) - len(comment_lines)+len_comment_list
        # input_material_description = '\n'.join(material_desc_split[:len_material_description])
        # end_line = start_line+len_material_description-1

        input_material_description, comment, end_line = get_comment_and_endline(material_desc, start_line)
        return cls(id=material_id, composition=composition,
                   start_line=start_line, end_line=end_line,
                   input_material_description=input_material_description, parent=parent)


class MCNPMaterials(Store):

    def __init__(self, material_list=[], parent=None):
        super().__init__(material_list, parent)
        self.cardnotfound_exception = MaterialNotFound
        self.cardidalreadyused_exception = MaterialIdAlreadyUsed
        self.card_name = 'material'
