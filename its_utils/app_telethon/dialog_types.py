from telethon.tl.custom import Dialog as TlDialog

PRIVATE = 'private'
GROUP = 'group'
SUPERGROUP = 'supergroup'
CHANNEL = 'channel'

_SUPERCHAT_VAR = int(-1e12)


def get_dialog_type(dialog: TlDialog) -> str:
    if dialog.is_channel:
        return CHANNEL

    if dialog.is_group:
        return GROUP if dialog.id > _SUPERCHAT_VAR else SUPERGROUP

    return PRIVATE
