# coding: utf-8

import difflib
import string


def text_diff(a, b):

    def create_block(action, data):
        return {'type': action, 'data': data}

    out = []
    a, b = html2list(a), html2list(b)

    try:
        s = difflib.SequenceMatcher(None, a, b)
    except TypeError:
        s = difflib.SequenceMatcher(None, a, b)
    for e in s.get_opcodes():
        block = None

        if e[0] == "replace":
            diff = difflib.ndiff(a[e[1]:e[2]], b[e[3]:e[4]])
            block = create_block('replace', '!!!REPLACE\n%s\n!!!END REPLACE\n' % '\n'.join(diff))
            # block = '!!!REPLACE\n%s\n!!!END REPLACE\n' % '\n'.join(diff)
        elif e[0] == "delete":
            diff = difflib.ndiff(a[e[1]:e[2]], '')
            block = create_block('delete', '!!!DELETE\n%s\n!!!END DELETE\n' % '\n'.join(diff))
            # block = '!!!DELETE\n%s\n!!!END DELETE\n' % '\n'.join(diff)
        elif e[0] == "insert":
            diff = difflib.ndiff('', b[e[3]:e[4]])
            block = create_block('insert', '!!!INSERT\n%s\n!!!END INSERT\n' % '\n'.join(diff))
            # block = '!!!INSERT\n%s\n!!!END INSERT\n' % '\n'.join(diff)
        elif e[0] == "equal":
            pass
        else:
            raise RuntimeError("Um, something's broken. I didn't expect a {!r}.".format(e[0]))

        # if block is not None and not Snippet.objects.filter(snippet=block[:-1]).exists():
        #     out.append(block)

        if block is not None:
            out.append(block)

    return out


def html2list(x):
    mode = 'char'
    cur = ''
    out = []
    for c in x:
        if mode == 'tag':
            if c == '>':
                cur += c
                out.append(cur)
                cur = ''
                mode = 'char'
            else:
                cur += c
        elif mode == 'char':
            if c == '<':
                out.append(cur)
                cur = c
                mode = 'tag'
            elif c in string.whitespace:
                pass
            else:
                cur += c
    out.append(cur)
    return filter(lambda x: x is not '', out)
