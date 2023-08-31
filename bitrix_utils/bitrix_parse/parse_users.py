import json

from bs4 import BeautifulSoup

from bitrix_utils.bitrix_parse.get_session_data import get_session_data


DEFAULT_FILTERS = {
    'params[FILTER_ID]': 'INTRANET_USER_LIST_s1',
    'params[GRID_ID]': 'INTRANET_USER_GRID_s1',
    'params[action]': 'setFilter',
    'params[forAll]': 'false',
    'params[commonPresetsId]': '',
    'params[apply_filter]': 'Y',
    'params[clear_filter]': 'N',
    'params[with_preset]': 'N',
    'params[save]': 'Y',
    'data[fields][FIND]': '',
    'data[fields][LAST_NAME]': '',
    'data[fields][DEPARTMENT]': '',
    'data[fields][DEPARTMENT_label]': '',
    'data[fields][TAGS]': '',
    'data[fields][ADMIN]': '',
    'data[rows]': 'LAST_NAME,DEPARTMENT,TAGS,ADMIN',
    'data[preset_id]': 'tmp_filter',
    'data[name]': '',
}


def parse_users(portal_domain, login, password, session=None, sessid=None, columns=None, filters=None):
    from settings import ilogger

    ilogger.debug('bitrix_parse.parse_users', '{} - parse_users started | Columns: {} | Filteres: {}'.format(portal_domain, columns, filters))

    if columns is None:
        columns = []
    if filters is None:
        filters = {}

    if session is None or sessid is None:
        session, sessid = get_session_data('https://{}/stream/'.format(portal_domain), login, password)

    response = session.get('https://{}/company'.format(portal_domain))
    soup = BeautifulSoup(response.text)

    if not len(soup.find_all('label', {'class': 'main-grid-settings-window-list-item-label'})):
        ilogger.debug('bitrix_parse.parse_users', '{} - searching cache'.format(portal_domain))

        bx_cache_response = session.get(
            'https://{}/company'.format(portal_domain),
            headers={'BX-ACTION-TYPE': 'get_dynamic', 'BX-CACHE-MODE': 'HTMLCACHE'},
            auth=(login, password)
        )
        bx_cache_response_json = json.loads(
            bx_cache_response.text.replace("'", '"').replace('\t', '').replace('\n', ''))
        columns_block = None
        if 'dynamicBlocks' in bx_cache_response_json:
            for block in bx_cache_response_json['dynamicBlocks']:
                if block['ID'] == 'content-table':
                    columns_block = block
            if columns_block:
                soup = BeautifulSoup(columns_block['CONTENT'], "html.parser")

    columns_code_names = {column_data.text: column_data['for'].replace('-checkbox', '') for column_data
                          in soup.find_all('label', {'class': 'main-grid-settings-window-list-item-label'})}

    ilogger.debug('bitrix_parse.parse_users', '{} - columns_code_names: {}'.format(portal_domain, columns_code_names))

    if columns:
        headers = {"bx-ajax": "true"}
        params = {
            'bath[0][action]': 'setColumns',
            'bath[0][columns]': ','.join(columns),
            'bath[1][action]': 'setCustomNames',
            'bath[2][action]': 'setStickedColumns',
            'sessid': sessid
        }
        url = 'https://{}/bitrix/components/bitrix/main.ui.grid/settings.ajax.php?GRID_ID=' \
              'INTRANET_USER_GRID_s1&action=saveBath'.format(portal_domain)
        session.post(url, params, headers=headers)

    if filters:
        headers = {"bx-ajax": "true"}
        params = DEFAULT_FILTERS
        for k, v in filters.items():
            params[k] = v
        params['sessid'] = sessid
        url = 'https://{}/bitrix/services/main/ajax.php?analyticsLabel[FILTER_ID]=' \
              'INTRANET_USER_LIST_s1&analyticsLabel[GRID_ID]=INTRANET_USER_GRID_s1&analyticsLabel[PRESET_ID]=' \
              'tmp_filter&analyticsLabel[FIND]=N&analyticsLabel[ROWS]=N&mode=ajax&c=bitrix%3Amain.ui.filter' \
              '&action=setFilter'.format(portal_domain)
        session.post(url, params, headers=headers)

    url = 'https://{}/bitrix/services/main/ajax.php?action=export&type=excel&c=bitrix%3Aintranet.user.' \
          'list&mode=class'.format(portal_domain)
    response = session.get(url)
    table = BeautifulSoup(response.text)

    ilogger.debug('bitrix_parse.parse_users', '{} - response.text: {}'.format(portal_domain, response.text))

    headers = [header.text for header in table.find_all('th')]
    user_list = [{headers[i]: {'value': cell.string, 'code_name': columns_code_names[headers[i]]}
                  for i, cell in enumerate(row.find_all('td'))} for row in table.find_all('tr')]

    del (user_list[0])

    return user_list