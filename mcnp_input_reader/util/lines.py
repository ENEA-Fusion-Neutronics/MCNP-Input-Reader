

def remove_comments(string: str):
    """

    :param string: Must be a string of lines
    :return: A string representing the lines without comments (c or $)
    """
    return ' '.join([line.split('$')[0].strip() for line in string.splitlines() if line[0].lower() != 'c'])


def add_space_to_parentheses(string: str):
    """
    :param string: Must be a string
    :return: string with space before '(' and after ')'
    """
    return string.replace('(', ' (').replace(')', ') ')


def split_on_tag(string: str, tags=[]):
    """
    :param string: Must be a string
    :param tags: list of tags
    :return: A list of string splitted on tags (UPPER CASE)
    """
    string_upper = string.upper()
    for tag in tags:
        mytag = tag.upper()
        string_upper = string_upper.replace(' ' + mytag, '\n' + mytag).replace('*' + mytag, '\n*' + mytag)
    return string_upper.splitlines()


def get_comment_and_endline(input_string: str, start_line: int):
    """
    Remove the useless comment lines from the input description of the card
    
    :param input_string: Must be a string, it's the card description
    :param start_line: Must be an integer, it's the line number of the card in the mcnp input
    :return: tuple (input_description, comment, end_line)
    
    """

    input_string_splitted = input_string.splitlines()
    comment_lines = []
    for l in reversed(input_string_splitted):
        if l[0].lower() == 'c' or l.strip()[0] == '$':
            comment_lines.append(l.strip())
        else:
            break
    comment_list = [l[1:] for l in comment_lines if l[0] == '$']
    if len(comment_list) == 0:
        for l in reversed(comment_lines):
            comment_list.append(l[1:])
            if len(l.split()) > 1:
                break
    comment = ' '.join(comment_list).strip()
    if comment.lower().replace('c', '').replace('-', '').strip():
        len_comment_list = len(comment_list)
    else:
        comment = ''
        len_comment_list = 0
    len_description = len(input_string_splitted)-len(comment_lines)+len_comment_list
    input_description = '\n'.join(input_string_splitted[:len_description])
    end_line = start_line + len_description - 1
    return input_description, comment, end_line
