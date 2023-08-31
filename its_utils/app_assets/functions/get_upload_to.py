# coding=utf8
from its_utils.app_assets.settings import ITS_ASSETS_UPLOAD_TO


def get_upload_to(subdir):
    base = '%s/%s/' % (ITS_ASSETS_UPLOAD_TO, subdir)
    return base + '%Y-%m-%d/'
