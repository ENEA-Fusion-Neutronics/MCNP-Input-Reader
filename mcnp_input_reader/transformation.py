from collections import namedtuple
from .exceptions import TransformationNotFound, TransformationIdAlreadyUsed
from .store import Store
from mcnp_input_reader.util.lines import remove_comments, add_space_to_parentheses, split_on_tag, get_comment_and_endline


class MCNPTransformation(namedtuple('MCNPTransf', ['id', 'parameters', 'start_line', 'end_line', 'input_transf_description', 'parent'])):
    """MCNPTransf is an immutable and lightweight object"""
    __slots__ = ()

    @classmethod
    def from_string(cls, transf_desc, start_line, parent=None):
        transf_pure = remove_comments(transf_desc.upper())
        transf_pure_split = transf_pure.split()
        transf_id = int(transf_pure_split[0].lower().replace('*', '').replace('tr', ''))
        parameters = ' '.join(transf_pure_split[1:])

        input_transf_description, comment, end_line = get_comment_and_endline(transf_desc, start_line)
        return cls(id=transf_id, parameters=parameters, start_line=start_line,
                   end_line=end_line, input_transf_description=input_transf_description, parent=parent)


class MCNPTransformations(Store):

    def __init__(self, transf_list=[], parent=None):
        super().__init__(transf_list, parent)
        self.cardnotfound_exception = TransformationNotFound
        self.cardidalreadyused_exception = TransformationIdAlreadyUsed
        self.card_name = 'transformation'
