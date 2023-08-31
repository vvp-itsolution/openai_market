from typing import Optional
from xml.etree import ElementTree

from django.utils.functional import cached_property


class OneSMetadata:
    def __init__(self, xml_content: str):
        self.xml_content = xml_content

    @cached_property
    def schema(self):
        xml_root = ElementTree.fromstring(self.xml_content)
        return xml_root[0][0]

    def get_entity_data(self, entity: str) -> dict:
        entity_type = self.schema.find(
            "{{http://schemas.microsoft.com/ado/2009/11/edm}}EntityType[@Name='{entity}']".format(entity=entity)
        )

        if not entity_type:
            raise ValueError("Entity not found '{}'".format(entity))

        key = list(entity_type.findall('{http://schemas.microsoft.com/ado/2009/11/edm}Key')[0])
        nav_properties = entity_type.findall('{http://schemas.microsoft.com/ado/2009/11/edm}NavigationProperty')

        property_container = self._get_complex_type(entity)
        if property_container is None:
            property_container = entity_type

        properties = property_container.findall('{http://schemas.microsoft.com/ado/2009/11/edm}Property')

        return dict(
            **entity_type.attrib,
            key=[item.attrib for item in key],
            properties=[prop.attrib for prop in properties],
            nav_properties=[prop.attrib for prop in nav_properties],
        )

    def get_association(self, entity: str, field: str) -> Optional[dict]:
        name = (
            '{entity}_RecordType_{field}' if self._is_complex_type(entity) else '{entity}_{field}'
        ).format(entity=entity, field=field)

        association = self.schema.find(
            "{{http://schemas.microsoft.com/ado/2009/11/edm}}Association[@Name='{}']".format(name)
        )

        if not association:
            return None

        begin, end = association.findall('{http://schemas.microsoft.com/ado/2009/11/edm}End')
        return dict(
            begin=begin.attrib,
            end=end.attrib,
        )

    def _get_complex_type(self, entity: str) -> Optional[ElementTree.Element]:
        return self.schema.find(
            "{{http://schemas.microsoft.com/ado/2009/11/edm}}ComplexType[@Name='{entity}_RowType']".format(
                entity=entity,
            )
        )

    def _is_complex_type(self, entity: str) -> bool:
        return self._get_complex_type(entity) is not None
