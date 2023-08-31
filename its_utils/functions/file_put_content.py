

def file_put_content(file_path, text):
    """
        Сохраняет текст в файл
    """

    with open(file_path, 'w') as f:
        f.write(text)

    return True
