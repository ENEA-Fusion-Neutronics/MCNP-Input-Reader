from collections import namedtuple
from .exceptions import TransformationNotFound, TransformationIdAlreadyUsed
from .store import Store
from mcnp_input_reader.util.lines import remove_comments, add_space_to_parentheses, split_on_tag, get_comment_and_endline


class MCNPTransformation(namedtuple('MCNPTransf', ['id', 'parameters', 'start_line', 'end_line', 'input_transf_description', 'parent'])):
    """MCNPTransf is an immutable and lightweight object"""
    __slots__ = ()

    @classmethod
    def from_string(cls, transf_desc, start_line, parent=None):
        # transf_desc_split = transf_desc.upper().splitlines()
        # transf_pure = ' '.join([line.split('$')[0].strip() for line in transf_desc_split if line[0].lower() != 'c']).replace('(', ' (').replace(')', ') ')
        transf_pure = remove_comments(transf_desc.upper())
        transf_pure_split = transf_pure.split()
        transf_id = int(transf_pure_split[0].lower().replace('*', '').replace('tr', ''))
        parameters = ' '.join(transf_pure_split[1:])

        # comment_lines = []
        # for l in reversed(transf_desc_split):
        #     if l[0].lower() == 'c' or l.strip()[0] == '$':
        #         comment_lines.append(l.strip())
        #     else:
        #         break
        # comment_list = [l[1:] for l in comment_lines if l[0] == '$']
        # if len(comment_list)==0:
        #     for l in reversed(comment_lines):
        #         comment_list.append(l[1:])
        #         if len(l.split())>1:
        #             break
        # comment=' '.join(comment_list).strip()
        # if comment.lower().replace('c', '').replace('-', '').strip():
        #     len_comment_list = len(comment_list)
        # else:
        #     comment = ''
        #     len_comment_list = 0
        # len_transf_description = len(transf_desc_split)-len(comment_lines)+len_comment_list
        # input_transf_description = '\n'.join(transf_desc_split[:len_transf_description])
        # end_line = start_line + len_transf_description - 1

        input_transf_description, comment, end_line = get_comment_and_endline(transf_desc, start_line)
        return cls(id=transf_id, parameters=parameters, start_line=start_line,
                   end_line=end_line, input_transf_description=input_transf_description, parent=parent)


class MCNPTransformations(Store):

    def __init__(self, transf_list=[], parent=None):
        super().__init__(transf_list, parent)
        self.cardnotfound_exception = TransformationNotFound
        self.cardidalreadyused_exception = TransformationIdAlreadyUsed
        self.card_name = 'transformation'
