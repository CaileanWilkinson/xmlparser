from xml.classes.document.Entity import Entity


class MockEntity(Entity):
    def __init__(self, name, expansion_text=None, entity_type=Entity.Type.GENERAL):
        # Store name
        self.name = name
        self.type = entity_type

        # Parsed entities
        if expansion_text:
            self.expansion_text = expansion_text

        # todo - unparsed entities
        pass
