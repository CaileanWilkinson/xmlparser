from xml_parser.helpers import parse_external_reference, expand_parameter_entity_references
from xml_parser.regular_expressions import RegEx
from xml_parser.dtd.DTD import DTD
from xml_parser.errors import XMLError, DisallowedCharacterError


class Notation:
    def __init__(self, dtd: DTD):
        self.__dtd = dtd

        self.name = None
        self.system_uri = None
        self.public_uri = None


class NotationFactory:
    @staticmethod
    def parse_from_xml(xml: str, dtd: DTD, external: bool) -> (Notation, str):
        """
            NotationDecl	::=	'<!NOTATION' S Name S (ExternalID |  PublicID) S? '>'
        """
        notation = Notation(dtd)
        source = xml

        # Strip leading fluff
        whitespace = RegEx.Whitespace.match(xml, pos=10)
        if not whitespace:
            raise XMLError("Missing whitespace after '<!NOTATION' declaration", source)
        xml = xml[whitespace.end():]

        # Parse notation
        notation.name, xml = NotationFactory.parse_name(xml, source, dtd, external)
        *uri_details, xml = NotationFactory.parse_external_ref(xml, dtd, external)
        notation.system_uri, notation.public_uri = uri_details

        # Strip trailing whitespace
        whitespace = RegEx.OptionalWhitespace.match(xml)
        xml = xml[whitespace.end():]

        # Ensure notation ends with '>'
        if xml[:1] != ">":
            raise XMLError("Illegal extra content at end of notation declaration", source=source)

        return notation, xml[1:]

    @staticmethod
    def parse_name(xml: str,
                   source: str,
                   dtd: DTD,
                   external: bool) -> (str, str):
        # Notation name is everything up to the next whitespace
        whitespace = RegEx.Whitespace.search(xml)
        if not whitespace:
            raise XMLError("Missing external reference in notation declaration", source=source)

        name = xml[:whitespace.start()]
        xml = xml[whitespace.end():]

        # Expand all entities in name
        if external:
            name = expand_parameter_entity_references(name, dtd, source)

        # Notation names must conform to xmlspec::Name
        if not RegEx.Name.fullmatch(name):
            raise DisallowedCharacterError(name, "notation declaration",
                                           conforms_to="Name", source=source)

        return name, xml

    @staticmethod
    def parse_external_ref(xml: str, dtd: DTD, external: bool) -> (str, str, str):
        system_uri, public_uri, _, xml = parse_external_reference(xml, dtd,
                                                                  look_for_notation=False,
                                                                  require_full_public_exp=False,
                                                                  allow_parameter_entities=external)
        return system_uri, public_uri, xml
