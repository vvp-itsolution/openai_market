export const POPUP_ID = 'selector-popup';

export const MODE = {
  USER: 'user',
  GROUP: 'sonet_group',
  DEPARTMENT: 'department',
};


export const BX24_URLS = {
  [MODE.USER]: {
    url: 'user.get',
    params: {
      FILTER: { ACTIVE: 'Y' },
      ADMIN_MODE: 'Y',
    },
  },
  [MODE.GROUP]: {
    url: 'sonet_group.get',
    params: { IS_ADMIN: 'Y' },
  },
  [MODE.DEPARTMENT]: {
    url: 'department.get',
    params: {},
  },
};


export const MSG = {
  GET_LIST_ERROR: {
    [MODE.USER]: 'message.error_fetching_users_list',
    [MODE.GROUP]: 'message.error_fetching_groups_list',
    [MODE.DEPARTMENT]: 'message.error_fetching_departments_list',
  },
  PERMISSION_ERROR: {
    [MODE.USER]: 'message.error_users_permission',
    [MODE.GROUP]: 'message.error_groups_permission',
    [MODE.DEPARTMENT]: 'message.error_departments_permission',
  },
  SELECT_ONE: {
    [MODE.USER]: 'message.select_user',
    [MODE.GROUP]: 'message.select_group',
    [MODE.DEPARTMENT]: 'message.select_department',
  },
  SELECT_MANY: {
    [MODE.USER]: 'message.select_users',
    [MODE.GROUP]: 'message.select_groups',
    [MODE.DEPARTMENT]: 'message.select_departments',
  },
  EXTRANET: {
    [MODE.USER]: 'message.extranet_user',
    [MODE.GROUP]: 'message.extranet_group',
    [MODE.DEPARTMENT]: 'message.extranet',
  },
};
