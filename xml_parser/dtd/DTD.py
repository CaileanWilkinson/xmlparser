import os
import re
from typing import Dict, List, Optional

from xml_parser.regular_expressions import RegEx
from xml_parser.errors import XMLError, DisallowedCharacterError


class DTD:
    """
        An internal storage class to allow DTD objects to be passed around the xml classes
    """

    def __init__(self, file_path: str, file_encoding: str):
        from .Entity import Entity

        # File info
        self.file_path = file_path
        self.file_root = os.path.dirname(file_path)
        self.file_encoding = file_encoding

        # dtd-info
        self.root_name = None

        self.general_entities = {}  # type: Dict[Entity]
        self.parameter_entities = {}  # type: Dict[Entity]
        self.__load_default_entities()

        # Declarations
        self.element_declarations = {}  # type: Dict
        self.element_attributes = {}  # type: Dict[str, Dict]
        self.element_default_attributes = {}  # type: Dict[str, Dict]
        self.notations = {}  # type: Dict

        self.processing_instructions = []  # type: List

    def __load_default_entities(self):
        """
            Loads the initial set of entities (lt, gt, amp, apos, quot)
        """
        from xml_parser.dtd.Entity import EntityFactory
        lt, _ = EntityFactory.parse_from_xml('<!ENTITY lt "&#38;#60;">', dtd=self)
        self.general_entities["lt"] = lt

        gt, _ = EntityFactory.parse_from_xml('<!ENTITY gt "&#62;">', dtd=self)
        self.general_entities["gt"] = gt

        amp, _ = EntityFactory.parse_from_xml('<!ENTITY amp "&#38;#38;">', dtd=self)
        self.general_entities["amp"] = amp

        apos, _ = EntityFactory.parse_from_xml('<!ENTITY apos "&#39;">', dtd=self)
        self.general_entities["apos"] = apos

        quot, _ = EntityFactory.parse_from_xml('<!ENTITY quot "&#34;">', dtd=self)
        self.general_entities["quot"] = quot


class DTDFactory:
    """
        ============
        DTD PARSING
        ============
    """

    @staticmethod
    def empty(file_path: str, file_encoding: str):
        return DTD(file_path, file_encoding)

    @staticmethod
    def parse_from_xml(xml: str, file_path: str, file_encoding: str) -> (DTD, str):
        source = xml
        dtd = DTD(file_path, file_encoding)

        # Remove fluff
        xml = xml[9:]
        whitespace = RegEx.Whitespace.match(xml)
        if not whitespace:
            raise XMLError("Missing whitespace after '<!DOCTYPE'", source=xml)
        xml = xml[whitespace.end():]

        # Parse root element name
        dtd.name, xml = DTDFactory.parse_name(xml, source=xml)

        # If there is an external subset, get it's reference but do not parse it yet
        is_external_subset = re.match(f"{RegEx.whitespace}(SYSTEM|PUBLIC)", xml)
        system = public = None
        if is_external_subset:
            system, public, xml = DTDFactory.parse_external_subset_reference(xml, source, dtd)

        # If there is an internal subset, parse it
        is_internal_subset = re.match(f"({RegEx.whitespace})?\\[", xml)
        if is_internal_subset:
            xml = DTDFactory.parse_internal_subset_into_dtd(xml, dtd)

        # Now parse the external subset
        if system or public:
            DTDFactory.parse_external_subset_into_dtd(system, public, dtd)

        # Strip optional trailing whitespace
        whitespace = RegEx.Whitespace.match(xml)
        if whitespace:
            xml = xml[whitespace.end():]

        # Ensure DTD is closed
        if xml[:1] != ">":
            raise XMLError("Illegal extra text at end of DTD", source=xml)

        # Return the built DTD and the remaining non-DTD xml
        return dtd, xml[1:]

    @staticmethod
    def parse_name(xml: str, source: str) -> (str, str):
        # Name is everything up to either whitespace, '>' or '['
        name_end = re.search(f"({RegEx.whitespace})|>|\\[", xml)
        if not name_end:
            raise XMLError("Error while parsing root element name from DTD", source=source)
        name = xml[:name_end.start()]

        # Name must conform to xmlspec::Name
        if not RegEx.Name.fullmatch(name):
            raise DisallowedCharacterError(name, "DTD root name", conforms_to="Name", source=source)

        return name, xml[name_end.start():]

    @staticmethod
    def parse_internal_subset_into_dtd(xml: str, dtd: DTD) -> str:
        # Remove leading fluff
        whitespace = RegEx.Whitespace.match(xml)
        if whitespace:
            xml = xml[whitespace.end():]
        xml = xml[1:]

        # Parse this subset
        xml = DTDFactory.parse_subset_into_dtd(xml, dtd, external=False)

        # Strip optional trailing whitespace
        whitespace = RegEx.Whitespace.match(xml)
        if whitespace:
            xml = xml[whitespace.end():]

        # The internal subset must end on ']'
        if xml[:1] != "]":
            raise XMLError("Error while parsing internal subset", source=xml)

        return xml[1:]

    """
        ===============
        SUBSET PARSING
        ===============
    """

    @staticmethod
    def parse_subset_into_dtd(xml: str, dtd: DTD,
                              external: bool, previous_entities: List[str] = []) -> str:
        from xml_parser.dtd.Entity import EntityFactory, Entity
        from xml_parser.dtd.ElementDeclaration import ElementDeclFactory
        from xml_parser.dtd.AttListDeclaration import AttributeDeclFactory
        from xml_parser.dtd.Notation import NotationFactory
        from xml_parser.content.Comment import CommentFactory

        while True:
            # Strip leading whitespace
            whitespace = RegEx.Whitespace.match(xml)
            if whitespace:
                xml = xml[whitespace.end():]

            # If we've reached the end of the subset
            if len(xml) == 0 or xml[:1] == "]":
                return xml

            # Expand and parse parameter entities in isolation from current subset
            if xml[:1] == "%":
                xml = DTDFactory.parse_parameter_entity_into_dtd(xml, dtd, previous_entities)
                continue

            # Parse conditional sections
            if xml[:3] == "<![":
                xml = DTDFactory.parse_conditional_section_into_dtd(xml, dtd, external, previous_entities)
                continue

            # Entities
            if xml.startswith("<!ENTITY"):
                entity, xml = EntityFactory.parse_from_xml(xml, dtd, external)

                # Entities must be unique in their namespace
                if entity.type == Entity.Type.GENERAL:
                    if entity.name not in dtd.general_entities.keys():
                        dtd.general_entities[entity.name] = entity
                else:
                    if entity.name not in dtd.parameter_entities.keys():
                        dtd.parameter_entities[entity.name] = entity
                continue

            # Notation declarations
            if xml.startswith("<!NOTATION"):
                notation, xml = NotationFactory.parse_from_xml(xml, dtd, external)
                # Notation names must be unique
                if notation.name not in dtd.notations.keys():
                    dtd.notations[notation.name] = notation
                continue

            # Element declarations
            if xml.startswith("<!ELEMENT"):
                element, xml = ElementDeclFactory.parse_from_xml(xml, dtd, external)

                # Element declaration names must be unique
                if element.name not in dtd.element_declarations.keys():
                    dtd.element_declarations[element.name] = element
                continue

            # Attlist declarations
            if xml.startswith("<!ATTLIST"):
                element, attributes, xml = AttributeDeclFactory.parse_from_xml(xml, dtd,
                                                                               external)

                element_attributes = dtd.element_attributes.get(element, {})
                element_default_attributes = dtd.element_default_attributes.get(element, {})

                # New attributes for a previously-declared element should be merged in
                for name, attribute in attributes.items():
                    if name not in element_attributes.keys():
                        element_attributes[name] = attribute
                        if attribute.default_declaration in ["FIXED", "DEFAULT"]:
                            element_default_attributes[name] = attribute

                dtd.element_attributes[element] = element_attributes
                dtd.element_default_attributes[element] = element_default_attributes
                continue

            # Comments
            if xml.startswith("<!--"):
                xml = CommentFactory.parse_from_xml(xml, dtd)
                continue

            # Anything else is a well-formedness error
            raise XMLError("Unrecognised markup in DTD", source=xml)

    @staticmethod
    def parse_parameter_entity_into_dtd(xml: str, dtd: DTD,
                                        previous_entities: List[str] = []) -> str:
        from xml_parser.helpers import parse_parameter_entity_reference

        # Isolate entity reference
        reference_end = xml.find(";")
        if reference_end == -1:
            raise XMLError("Unable to find end of parameter entity reference", source=xml)
        reference = xml[:reference_end + 1]

        # Check for infinite recursion
        if reference in previous_entities:
            raise XMLError(f"Infinite recursion in parameter entity {reference}", source=xml)

        entity, reference_expansion_text, _ = parse_parameter_entity_reference(reference, dtd, xml)

        # Parse this entity subset in isolation from current subset
        remaining_xml = DTDFactory.parse_subset_into_dtd(reference_expansion_text,
                                                         dtd,
                                                         entity.external,
                                                         previous_entities + [reference])

        # If there is remaining unparsed xml, the entity must be ill-formed
        if len(remaining_xml) != 0:
            raise XMLError(f"Unable to parse entity {reference} as a dtd subset", source=xml)

        return xml[reference_end + 1:]

    @staticmethod
    def parse_conditional_section_into_dtd(xml, dtd: DTD, external: bool,
                                           previous_entities: List[str] = []) -> str:
        from xml_parser.helpers import expand_parameter_entity_references

        if not external:
            raise XMLError("Conditional sections are not permitted in the internal subset",
                           source=xml)

        source = xml
        whitespace = RegEx.Whitespace.match(xml, pos=3)
        xml = xml[(whitespace.end() if whitespace else 3):]

        # Parse conditional block
        condition_end = re.search(fr"{RegEx.optional_whitespace}\[", xml)
        if not condition_end:
            raise XMLError("Error parsing conditional section", source)
        block_end = xml.find("]]>", condition_end.end())
        if block_end == -1:
            raise XMLError("Unable to find end of conditional block", source)

        condition = xml[:condition_end.start()]
        conditional_block = xml[condition_end.end(): block_end]
        xml = xml[block_end + 3:]

        # Expand all PEs in condition
        condition = expand_parameter_entity_references(condition, dtd, xml)

        # Remove leading & trailing whitespace
        start_whitespace = RegEx.OptionalWhitespace.match(condition)
        end_whitespace = re.search(f"({RegEx.optional_whitespace})$", condition)
        condition = condition[start_whitespace.end(): end_whitespace.start()]

        # Parse block if condition is "INCLUDE"
        if condition == "INCLUDE":
            remaining_xml = DTDFactory.parse_subset_into_dtd(conditional_block, dtd, external=True,
                                                             previous_entities=previous_entities)
            if remaining_xml:
                raise XMLError("Ill-formed xml in conditional block", source)

            return xml

        elif condition == "IGNORE":
            return xml

        else:
            raise XMLError(f"Invalid identifier for xml conditional section '{condition}'", source)

    """
        ================
        EXTERNAL SUBSET
        ================
    """

    @staticmethod
    def parse_external_subset_reference(xml: str, source: str, dtd: DTD) -> (str, str, str):
        from xml_parser.helpers import parse_external_reference

        # Strip leading whitespace
        whitespace = RegEx.Whitespace.match(xml)
        if not whitespace:
            raise XMLError("Missing whitespace before external subset declaration", source)
        xml = xml[whitespace.end():]

        system, public, _, xml = parse_external_reference(xml, look_for_notation=False)

        return system, public, xml

    @staticmethod
    def parse_external_subset_into_dtd(system: str, public: str, dtd: DTD):
        external_subset, encoding, root = DTDFactory.fetch_external_subset(system, public, dtd)

        remaining_xml = DTDFactory.parse_subset_into_dtd(external_subset, dtd, external=True)

        if remaining_xml:
            raise XMLError(f"Ill-formed dtd subset in file {root}", source=external_subset)

    @staticmethod
    def fetch_external_subset(system_uri: Optional[str],
                              public_uri: Optional[str],
                              dtd: DTD) -> (str, str, str):
        from xml_parser.helpers import fetch_content_at_uri, parse_text_declaration

        subset = None
        subset_root = None

        # Try public uri first
        if public_uri:
            subset, _, subset_root = fetch_content_at_uri(public_uri,
                                                          current_path=dtd.file_root,
                                                          encoding=dtd.file_encoding)

        # Fall back on system uri
        if subset is None:
            subset, _, subset_root = fetch_content_at_uri(system_uri,
                                                          current_path=dtd.file_root,
                                                          encoding=dtd.file_encoding)

        if subset is None:
            raise XMLError(
                f"Unable to fetch external subset at uri '{public_uri}'' or '{system_uri}'")

        # Parse fetched xml
        return (*parse_text_declaration(subset, encoding=dtd.file_encoding), subset_root)
