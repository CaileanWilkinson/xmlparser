from typing import Dict, Optional

from ...RegularExpressions import RegEx
from ..Error import XMLError, DisallowedCharacterError


class Entity:
    # Entity types
    class Type:
        GENERAL = "&"
        PARAMETER = "%"

    def __init__(self, remaining_xml: str):
        self.__raw_declaration = remaining_xml

        self.name = ''  # type: str
        self.expansion_text = None  # type: Optional[str]

        # External identifications
        self.system_URI = None  # type: Optional[str]
        self.public_URI = None  # type: Optional[str]
        self.notation = None  # type: Optional[str]

        # Entity categorisation
        self.type = Entity.Type.GENERAL  # type: str
        self.external = False  # type: bool
        self.parsed = True  # type: bool

    """
        ==============
        BASIC PARSING
        ==============
        These functions parse the entity up to either:
        - the value string (for internal entities), or
        - the external reference (for external entites).
    """

    def parse_to_end(self, parameter_entities: Dict[str, 'Entity']) -> str:
        remaining_xml = self.__raw_declaration

        # Strip leading fluff (<!ENTITY and whitespace)
        whitespace = RegEx.Whitespace.search(remaining_xml)
        if not whitespace:
            raise XMLError("Missing whitespace after entity declaration", source=self.__raw_declaration)
        remaining_xml = remaining_xml[whitespace.end():]

        # Parse entity type & name
        remaining_xml = self.categorise_entity(remaining_xml)
        remaining_xml = self.parse_name(remaining_xml)

        self.external = (remaining_xml[0] not in "\"\'")

        # Continue parsing with dedicated function for entity type
        if self.external:
            return self.parse_external_reference(remaining_xml)
        else:
            return self.parse_internal_value(remaining_xml, parameter_entities)

    def categorise_entity(self, remaining_xml: str) -> str:
        # Parameter entities have an additional '%' before the name
        if remaining_xml[0] == "%":
            self.type = Entity.Type.PARAMETER

            # Remove the '%' before parsing name
            whitespace = RegEx.Whitespace.search(remaining_xml)
            if not whitespace:
                raise XMLError("Missing whitespace after '%' in entity", source=self.__raw_declaration)
            return remaining_xml[whitespace.end():]

        # General entities go directly into the name
        else:
            self.type = Entity.Type.GENERAL
            return remaining_xml

    def parse_name(self, remaining_xml: str) -> str:
        # Entity name is everything up to the next whitespace
        whitespace = RegEx.Whitespace.search(remaining_xml)
        if not whitespace:
            raise XMLError("Missing whitespace after entity name", source=self.__raw_declaration)

        self.name = remaining_xml[:whitespace.start()]
        remaining_xml = remaining_xml[whitespace.end():]

        # Entity name must conform to xmlspec::Name
        if not RegEx.Name.fullmatch(self.name):
            raise DisallowedCharacterError(self.name, "entity name", conforms_to="Name", source=self.__raw_declaration)

        return remaining_xml

    """
        ==================
        INTERNAL ENTITIES
        ==================
    """

    def parse_internal_value(self, remaining_xml: str, parameter_entities: Dict[str, 'Entity']) -> str:
        # Import here to avoid import loop
        from xml.Helpers import parse_string_literal

        # Find the end of the string literal
        delimiter = remaining_xml[0]
        value_end_index = remaining_xml.find(delimiter, 1)
        if not value_end_index:
            raise XMLError("Unable to find end of entity value", source=self.__raw_declaration)

        # Parse the value
        value = remaining_xml[1:value_end_index]
        remaining_xml = remaining_xml[value_end_index + 1:]

        # Expand all parameter & character entities within the value
        self.expansion_text = parse_string_literal(value, parameter_entities=parameter_entities,
                                                   expand_general_entities=False)

        # Entity value must conform to xmlspec::Char
        if not RegEx.CharSequence.fullmatch(self.expansion_text):
            raise DisallowedCharacterError(self.expansion_text,
                                           "entity value",
                                           conforms_to="Char",
                                           source=self.__raw_declaration)

        # Strip leading whitespace
        whitespace = RegEx.Whitespace.match(remaining_xml)
        if whitespace:
            remaining_xml = remaining_xml[whitespace.end():]

        # Ensure entity declaration closes & return remaining xml
        if remaining_xml[:1] != ">":
            raise XMLError("Illegal extra characters after value in entity", source=self.__raw_declaration)
        return remaining_xml[1:]

    """
        ==================
        EXTERNAL ENTITIES    
        ==================
    """

    def parse_external_reference(self, remaining_xml: str) -> str:
        # Import here to avoid import loop
        from xml.Helpers import parse_external_reference

        # Parse the external reference
        remaining_xml, self.system_URI, self.public_URI, self.notation = parse_external_reference(remaining_xml)

        # If there is a notation, this must be an unparsed entity
        if self.notation:
            self.parsed = False

        # Unparsed parameter entities are not allowed
        if self.type == Entity.Type.PARAMETER and not self.parsed:
            raise XMLError("Parameter entities may not specify a notation", source=self.__raw_declaration)

        # Strip leading whitespace
        whitespace = RegEx.Whitespace.match(remaining_xml)
        if whitespace:
            remaining_xml = remaining_xml[whitespace.end():]

        # Ensure entity declaration closes & return remaining xml
        if remaining_xml[:1] != ">":
            raise XMLError("Illegal extra characters after value in entity", source=self.__raw_declaration)
        return remaining_xml[1:]
