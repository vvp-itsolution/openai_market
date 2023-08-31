# coding=utf8

from jsondiff import diff


def dict_keys_to_string(dct):
    for key in list(dct.keys()):
        if type(dct[key]) is dict:
            dct[key] = dict_keys_to_string(dct[key])

        key_is_not_str = type(key) is not str
        try:
            # python 2
            key_is_not_str = key_is_not_str and type(key) is not unicode

        except NameError:
            pass

        if key_is_not_str:
            try:
                dct[str(key)] = dct[key]
            except:
                dct[repr(key)] = dct[key]
            del dct[key]

    return dct


def get_json_diff(first, second, syntax='symmetric'):
    df = diff(first, second, syntax=syntax)
    return df
