from tests.mocks.MockDTD import MockDTD
from xml_parser.dtd.Entity import Entity


class MockEntity(Entity):
    def __init__(self, name, expansion_text=None, entity_type=Entity.Type.GENERAL):
        # todo - unparsed entities
        Entity.__init__(self, MockDTD())

        # Store name
        self.name = name
        self.type = entity_type

        # Parsed entities
        if expansion_text:
            self.expansion_text = expansion_text
