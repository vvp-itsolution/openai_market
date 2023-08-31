import os
import random
import string
from pathlib import Path

import pandas as pd
from django.conf import settings


def array_to_csv(array):
    df = pd.DataFrame(array)
    random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=50))
    path_to_file = os.path.join('temp', random_string)
    Path(os.path.join(settings.MEDIA_ROOT, path_to_file)).mkdir(parents=True, exist_ok=True)
    #df.to_csv(os.path.join(settings.MEDIA_ROOT, path_to_file, 'array.csv'))
    df.to_excel(os.path.join(settings.MEDIA_ROOT, path_to_file, 'output1.xlsx'))
    return os.path.join(path_to_file, 'output1.xlsx')
