from enum import Enum
from typing import Optional, List

from xml_parser import helpers
from xml_parser.dtd.DTD import DTD
from xml_parser.helpers import (parse_text_declaration,
                                parse_character_reference,
                                expand_parameter_entity_references,
                                expand_parameter_entity_reference)
from xml_parser.regular_expressions import RegEx
from ..errors import XMLError, DisallowedCharacterError


class Entity:
    class Type(Enum):
        GENERAL = "&"
        PARAMETER = "%"

    def __init__(self, dtd: DTD):
        self.__dtd = dtd

        self.name = ''  # type: str
        self.expansion_text = None  # type: Optional[str]

        # Entity categorisation
        self.type = Entity.Type.GENERAL  # type: Entity.Type
        self.external = False  # type: bool
        self.parsed = True  # type: bool

        # External identifications
        self.system_uri = None  # type: Optional[str]
        self.public_uri = None  # type: Optional[str]
        self.notation = None  # type: Optional[str]

        self.root = None  # type: Optional[str]
        self.encoding = None  # type: Optional[str]


class EntityFactory:
    @staticmethod
    def parse_from_xml(xml: str, dtd: DTD, external: bool = False) -> (Entity, str):
        """
            GEDecl  ::= '<!ENTITY' S Name S EntityDef S? '>'
            PEDecl  ::= '<!ENTITY' S '%' S Name S PEDef S? '>'
        """
        entity = Entity(dtd)
        entity.root = dtd.file_root
        entity.encoding = dtd.file_encoding

        source = xml

        # Strip leading fluff
        whitespace = RegEx.Whitespace.match(xml, pos=8)
        if not whitespace:
            raise XMLError("Missing whitespace after entity declaration", source=source)
        xml = xml[whitespace.end():]

        # Parse entity
        entity.type, xml = EntityFactory.parse_entity_type(xml, source)
        entity.name, xml = EntityFactory.parse_name(xml, source, dtd, external)

        # Continue parsing entity in dedicated function for entity-type
        entity.external = (xml[0] not in "\"\'")
        if entity.external:
            xml = EntityFactory.parse_xml_into_external_entity(xml, entity, source)
        else:
            entity.expansion_text, xml = EntityFactory.parse_internal_entity_value(xml, source,
                                                                                   dtd, external)

        # Strip optional closing whitespace
        whitespace = RegEx.OptionalWhitespace.match(xml)
        xml = xml[whitespace.end():]

        # Ensure entity declaration closes
        if xml[:1] != ">":
            raise XMLError("Illegal extra content at end of entity declaration", source=source)

        return entity, xml[1:]

    @staticmethod
    def parse_entity_type(xml: str,
                          source: str) -> (Entity.Type, str):
        # Remove the '%' from parameter entities before returning
        if xml[:1] == "%":
            whitespace = RegEx.Whitespace.match(xml, pos=1)
            if not whitespace:
                raise XMLError("Missing whitespace after '%' in entity", source=source)
            return Entity.Type.PARAMETER, xml[whitespace.end():]

        # General entities
        return Entity.Type.GENERAL, xml

    @staticmethod
    def parse_name(xml: str,
                   source: str,
                   dtd: DTD,
                   external: bool) -> (str, str):
        # Entity name is everything up to the next whitespace
        whitespace = RegEx.Whitespace.search(xml)
        if not whitespace:
            raise XMLError("Error while parsing entity name", source=source)

        name = xml[:whitespace.start()]
        xml = xml[whitespace.end():]

        # Expand all entities in name
        if external:
            name = expand_parameter_entity_references(name, dtd, source)

        # Entity name must conform to xmlspec::Name
        if not RegEx.Name.fullmatch(name):
            raise DisallowedCharacterError(name, "entity name", conforms_to="Name", source=source)

        return name, xml

    """
        ==================
        INTERNAL ENTITIES
        ==================
    """

    @staticmethod
    def parse_internal_entity_value(xml: str,
                                    source: str,
                                    dtd: DTD,
                                    external: bool) -> (str, str):
        # Expand all entities in name
        if xml.startswith("%") and external:
            xml = expand_parameter_entity_reference(xml, dtd, source)
            whitespace = RegEx.OptionalWhitespace.match(xml)
            xml = xml[whitespace.end():]

        # Find the end of the string literal
        delimiter = xml[:1]
        value_end_index = xml.find(delimiter, 1)
        if not value_end_index:
            raise XMLError("Unable to find end of entity value", source=source)

        # Parse the value
        value = xml[1:value_end_index]
        xml = xml[value_end_index + 1:]

        # Only expand parameter entities if this is an external entity
        expansion_text = EntityFactory.normalise_entity_value(value, source, dtd, external)

        # Entity expansion text must conform to xmlspec::Char*
        if not RegEx.CharSequence.fullmatch(expansion_text):
            raise DisallowedCharacterError(expansion_text, "entity value",
                                           conforms_to="Char", source=source)

        return expansion_text, xml

    @staticmethod
    def normalise_entity_value(value: str,
                               source: str,
                               dtd: DTD,
                               external: bool,
                               entity_chain: List[str] = []) -> str:
        normalised_value = ""

        # Iterate through all entity references
        last_index = 0
        for match in RegEx.Reference.finditer(value):
            reference = match.group()

            # Append skipped text
            skipped_text = value[last_index: match.start()]
            normalised_value += skipped_text
            last_index = match.end()

            # Entity value may not contain unescaped & or %
            if "&" in skipped_text:
                raise DisallowedCharacterError(value, "entity value",
                                               conforms_to="&", source=value)
            if "%" in skipped_text:
                raise DisallowedCharacterError(value, "entity value",
                                               conforms_to="%", source=value)

            # Append character references & continue
            if reference.startswith("&#"):
                character, _ = parse_character_reference(reference)
                normalised_value += character
                continue

            # Ignore general entities
            if reference.startswith("&"):
                normalised_value += reference
                continue

            # Parameter entities are only allowed in the external subset
            if not external:
                raise XMLError("Parameter entity references are not allowed within markup in the "
                               "internal subset", source)

            # Check for parameter entity recursion
            if reference in entity_chain:
                raise XMLError(f"Recursion within entities is prohibited "
                               f"(reference loop in {reference})")

            # Normalise entity expansion text before appending
            entity = dtd.parameter_entities.get(reference[1:-1], None)
            if not entity:
                raise XMLError(f"Reference to undeclared entity {reference}", source=value)

            normalised_value += EntityFactory.normalise_entity_value(entity.expansion_text, source,
                                                                     dtd, external,
                                                                     entity_chain + [reference])

        # Append final text (after last reference) unless it contains unescaped '&' or '%'
        if "&" in value[last_index:]:
            raise DisallowedCharacterError(value, "entity value",
                                           conforms_to="&", source=value)
        if "%" in value[last_index:]:
            raise DisallowedCharacterError(value, "entity value",
                                           conforms_to="%", source=value)
        normalised_value += value[last_index:]

        return normalised_value

    """
        ==================
        EXTERNAL ENTITIES
        ==================
    """

    @staticmethod
    def parse_xml_into_external_entity(xml: str, entity: Entity, source: str) -> str:
        # Import here to avoid import loop
        from xml_parser.helpers import parse_external_reference

        # Parse the external reference
        entity.system_uri, entity.public_uri, entity.notation, xml = parse_external_reference(xml)

        # If there is a notation, this must be an unparsed entity
        if entity.notation:
            entity.parsed = False

        # Unparsed parameter entities are not allowed
        if entity.type == Entity.Type.PARAMETER and not entity.parsed:
            raise XMLError("Parameter entities may not specify a notation", source=source)

        # If this is a parsed entity, fetch the expansion text
        if entity.parsed:
            EntityFactory.fetch_external_entity_expansion_text(entity)

        return xml

    @staticmethod
    def fetch_external_entity_expansion_text(entity: Entity):
        xml = None
        root = None

        # Try public uri first
        if entity.public_uri:
            xml, _, root = helpers.fetch_content_at_uri(entity.public_uri, entity.root,
                                                        entity.encoding)

        # Fall back on system uri
        if xml is None:
            xml, _, root = helpers.fetch_content_at_uri(entity.system_uri, entity.root,
                                                        entity.encoding)

        # Remove text declaration from entity expansion text
        if xml is not None:
            entity.expansion_text, entity.encoding = parse_text_declaration(xml, entity.encoding)
            entity.root = root
