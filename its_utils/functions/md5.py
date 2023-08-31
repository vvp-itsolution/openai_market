
def get_md5(txt):
    import hashlib
    m = hashlib.md5()
    m.update(txt)
    return m.hexdigest()