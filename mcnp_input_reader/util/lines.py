

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

def split_on_tag(string: str, tags = []):
    """
    
    :param string: Must be a string
    :param tags: list of tags
    :return: A list of string splitted on tags (UPPER CASE)
    """
    string_upper = string.upper()
    for tag in tags:
        mytag = tag.upper()
        string_upper = string_upper.replace(mytag, '\n' + mytag).replace('*\n'+mytag, '\n*'+mytag)
    return string_upper.splitlines()


