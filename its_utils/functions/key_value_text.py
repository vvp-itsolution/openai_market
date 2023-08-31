# coding=utf-8

def key_value_to_text(obj, prefix=[], suffix=[], separator=" - ", newline="\n\r"):
    res = key_value_to_list_of_strings(obj, separator)
    return newline.join(prefix+res+suffix)


def key_value_to_list_of_strings(obj, separator=" - "):
    res = []
    for k, v in obj.items():
        res.append(u"{}{}{}".format(k, separator, v))
    return res