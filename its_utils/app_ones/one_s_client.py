from typing import Optional

import requests
from its_utils.app_ones.errors import OneSClientError
from its_utils.app_ones.one_s_metadata import OneSMetadata

#AccumulationRegister
# Catalog
# Document
# DocumentJournal
# Constant
# ExchangePlan
# ChartOfAccounts
# ChartOfCalculationTypes
# ChartOfCharacteristicTypes
# InformationRegister
# AccumulationRegister
# CalculationRegister
# AccountingRegister
# BusinessProcess
# Task

class OneSClient:
    REQUEST_TIMEOUT = 300

    def __init__(self, user: str, password: str, base_url: str):
        self.user = user
        self.password = password
        self.base_url = base_url

        self.session = requests.Session()
        self.session.auth = (self.user, self.password)

    def get_all(self, object_type, object_name):
        # object_type - Catalog
        # object_name - Пользователи
        return self.get_from_odata("f{object_type}_{object_name}")

    def get_element(self, object_type, object_name, guid):
        return self.get_from_odata(f"{object_type}_{object_name}", guid=guid)

    def get_navigation_link_url(self, navigation_link_url):
        # например "Document_АТСУслуга(guid'f7f31491-dac7-11ed-b3f8-c9bb792a9c82')/Проект"
        return self.get_from_odata(navigation_link_url)

    def get_from_odata(self,
                       entity: str,
                       guid: str = None,
                       filter_: str = None,
                       expand: str = None,
                       select: str = None,
                       orderby: str = None,
                       skip: int = None,
                       top: int = None,
                       inlinecount: bool = False,
                       timeout: int = REQUEST_TIMEOUT) -> dict:
        """
        Поучение объектов из 1С через odata

        :param entity: тип объекта (Catalog_Номенклатура)
        :param guid: гуид (если не передавать, возвращает список)
        :param filter_: строка-фильтр ("Code eq '0001234' and Сумма gt 42") (параметр $filter)
        :param expand: получение значений связанных сущностей (параметр $expand)
        :param select: свойства сущности, которые необходимо получить (параметр $select)
        :param orderby: сортировка
        :param skip: количество записей, которые нужно пропустить
        :param top: ограниечни количества записей
        :param timeout: timeout
        :param inlinecount: возвращать коичество записей

        :raises: OneSClientError
        """

        url = (
            '{base_url}odata/standard.odata/'
            '{entity}{guid}?$format=json{filter}{expand}{select}{orderby}{skip}{top}{inlinecount}'
        ).format(
            base_url=self.base_url,
            entity=entity,
            guid='(%s)' % guid if guid else '',
            filter='&$filter={}'.format(filter_) if filter_ else '',
            expand='&$expand={}'.format(expand) if expand else '',
            select='&$select={}'.format(select) if select else '',
            orderby='&$orderby={}'.format(orderby) if orderby else '',
            skip='&$skip={}'.format(skip) if skip else '',
            top='&$top={}'.format(top) if top is not None else '',
            inlinecount='&$inlinecount=allpages' if inlinecount and not select else '',
        )

        resp = self.session.get(url, timeout=timeout)

        if resp.ok:
            return resp.json()

        raise OneSClientError(resp)

    def call_hs(self, method: str, service: str, params: Optional[dict]) -> dict:
        kwargs = dict()
        if method == 'get':
            kwargs['params'] = params
        else:
            kwargs['json'] = params

        url = '{}hs/{}'.format(self.base_url, service)
        resp = self.session.request(method, url, **kwargs)
        if resp.ok:
            return resp.json()

        raise OneSClientError(resp)

    def get_metadata(self) -> OneSMetadata:
        response = self.session.get('{base_url}odata/standard.odata/$metadata'.format(base_url=self.base_url))
        return OneSMetadata(response.text)
