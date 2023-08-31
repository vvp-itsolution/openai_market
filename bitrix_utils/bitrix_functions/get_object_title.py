

def get_object_title(obj):
    return (
            obj.get('TITLE')
            or '{} {}'.format(obj.get('NAME') or '', obj.get('LAST_NAME') or '').strip()
            or obj.get('ID')
    )