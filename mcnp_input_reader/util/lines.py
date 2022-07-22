def file_to_lines(filename: str) -> list:
    '''
    :param filename: String
    :return: A list containing the lines of the file
    '''
    with open(filename, 'r', errors='ignore') as f:
        lines = f.readlines()
    return lines


def remove_comments(string: str) -> str:
    """

    :param string: Must be a string of lines
    :return: A string representing the lines without comments (c or $)
    """
    return ' '.join([line.split('$')[0].strip() for line in string.splitlines() if line[0].lower() != 'c'])


def add_space_to_parentheses(string: str) -> str:
    """
    :param string: Must be a string
    :return: string with space before '(' and after ')'
    """
    return string.replace('(', ' (').replace(')', ') ')


def split_on_tag(string: str, tags=[]) -> list:
    """
    :param string: Must be a string
    :param tags: list of tags
    :return: A list of string splitted on tags (UPPER CASE)
    """
    string_upper = string.replace('\n', ' ').upper()
    for tag in tags:
        mytag = tag.upper()
        string_upper = string_upper.replace(' ' + mytag, '\n' + mytag).replace('*' + mytag, '\n*' + mytag)
    return string_upper.splitlines()


def get_comment_and_endline(input_string: str, start_line: int) -> tuple:
    """
    Remove the useless comment lines from the input description of the card

    :param input_string: Must be a string, it's the card description
    :param start_line: Must be an integer, it's the line number of the card in the mcnp input
    :return: tuple (input_description, comment, end_line)
    """

    input_string_splitted = input_string.splitlines()
    comment_lines = []
    for line in reversed(input_string_splitted):
        if line[0].lower() == 'c' or line.strip()[0] == '$':
            comment_lines.append(line.strip())
        else:
            break
    comment_list = [line[1:] for line in comment_lines if line[0] == '$']
    if len(comment_list) == 0:
        for line in reversed(comment_lines):
            comment_list.append(line[1:])
            if len(line.split()) > 1:
                break
    comment = ' '.join(comment_list).strip()
    if comment.lower().replace('c', '').replace('-', '').strip():
        len_comment_list = len(comment_list)
    else:
        comment = ''
        len_comment_list = 0
    len_description = len(input_string_splitted) - len(comment_lines) + len_comment_list
    input_description = '\n'.join(input_string_splitted[:len_description])
    end_line = start_line + len_description - 1
    return input_description, comment, end_line
