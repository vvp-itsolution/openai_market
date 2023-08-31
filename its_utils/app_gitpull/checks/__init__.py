# -*- coding: UTF-8 -*-

import django

version = django.get_version().split('.')

if int(version[0]) > 0 and not (int(version[0]) == 1 and int(version[1]) < 7):
    from .check_raw_id_fields import check_raw_id_fields
    # from .check_on_delete_protect import check_on_delete_protect
    from .check_gitignore import check_gitignore
    from .check_gitpull import check_gitpull
    from .check_allowed_hosts import check_allowed_hosts
    from .check_mail_settings import check_mail_settings
    # from .check_redis_logging import check_redis_logging
    # from .check_app_logging_cron import check_app_logging_cron
    from .check_crontab import check_crontab
    from .check_debug_mode import check_debug_mode
    from .check_its_500 import check_its_500
    from .check_unapplied_migrations import check_unapplied_migrations
    from .check_pyc_files import check_pyc_files
    from .check_app_logger_cron import check_app_logger_cron
    from .check_ilogger import check_ilogger
