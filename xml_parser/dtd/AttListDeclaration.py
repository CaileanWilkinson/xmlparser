import re
from typing import Dict, List

from xml_parser.helpers import (expand_parameter_entity_references,
                                parse_parameter_entity_reference, expand_parameter_entity_reference)
from xml_parser.regular_expressions import RegEx
from xml_parser.dtd.DTD import DTD
from xml_parser.errors import XMLError, DisallowedCharacterError


class AttributeDeclaration:
    def __init__(self):
        self.name = None
        self.value_type = None
        self.options = []

        self.default_declaration = None
        self.default_value = None


class AttributeDeclFactory:
    @staticmethod
    def parse_from_xml(xml: str,
                       dtd: DTD,
                       external: bool) -> (str, Dict[str, AttributeDeclaration], str):
        """
            AttlistDecl ::== '<!ATTLIST' S Name AttDef* S? '>'
            AttDef      ::== S Name S AttType S DefaultDeclaration
        """
        source = xml
        xml = xml[9:]

        element, xml = AttributeDeclFactory.parse_element_name(xml, source, dtd, external)
        attributes, xml = AttributeDeclFactory.parse_attributes(xml, source, dtd, external)

        # Strip optional whitespace
        whitespace = RegEx.Whitespace.match(xml)
        if whitespace:
            xml = xml[whitespace.end():]

        return element, attributes, xml

    @staticmethod
    def parse_element_name(xml: str,
                           source: str,
                           dtd: DTD,
                           external: bool) -> (str, str):
        # Expand entity
        if re.match(f"{RegEx.optional_whitespace}%", xml) and external:
            xml = expand_parameter_entity_reference(xml, dtd, source)

        # Strip leading whitespace
        whitespace = RegEx.Whitespace.match(xml)
        if not whitespace:
            raise XMLError("Missing whitespace before element name in ATTLIST declaration", source)
        xml = xml[whitespace.end():]

        # Name is everything up to following whitespace or '>'
        name_end = RegEx.Whitespace_Or_GT.search(xml)
        if not name_end:
            raise XMLError("Error parsing ATTLIST declaration", source=source)

        name = xml[:name_end.start()]
        xml = xml[name_end.start():]

        # Explicitly check for '>' in name to report accurate errors
        if '>' in name:
            raise XMLError("Missing content spec in ATTLIST declaration", source=source)

        # Expand all entities in name
        if external:
            name = expand_parameter_entity_references(name, dtd, source)

        # Name must conform to xmlspec::Name
        if not RegEx.Name.fullmatch(name):
            raise DisallowedCharacterError(name, "ATTLIST declaration", conforms_to="Name",
                                           source=source)

        return name, xml

    """
        ===========
        ATTRIBUTES
        ===========
    """

    @staticmethod
    def parse_attributes(xml: str,
                         source: str,
                         dtd: DTD,
                         external: bool) -> (Dict[str, AttributeDeclaration], str):
        attributes = {}

        while True:
            # Remove leading whitespace
            whitespace = RegEx.Whitespace.match(xml)
            if whitespace:
                xml = xml[whitespace.end():]

            # End of declaration
            if xml[:1] == ">":
                return attributes, xml[1:]
            elif len(xml) == 0:
                return attributes, xml

            # Leading whitespace is compulsory if there is another attribute
            if not whitespace:
                raise XMLError("Error while parsing ATTLIST attributes list", source)

            # PE references
            if xml.startswith("%"):
                _, expansion_text, xml = parse_parameter_entity_reference(xml, dtd, source)
                new_attributes, _ = AttributeDeclFactory.parse_attributes(expansion_text, source,
                                                                          dtd, external)
                for attribute in new_attributes.values():
                    if attribute.name in attributes.keys():
                        raise XMLError(f"Repeated attribute name in ATTLIST "
                                       f"declaration ({attribute.name})", source)
                    attributes[attribute.name] = attribute
                continue

            # Otherwise parse attribute
            attribute, xml = AttributeDeclFactory.parse_attribute(xml, source, dtd, external)

            # Attribute names must be unique
            if attribute.name in attributes.keys():
                raise XMLError(f"Repeated attribute name in ATTLIST declaration ({attribute.name})",
                               source)

            attributes[attribute.name] = attribute

    @staticmethod
    def parse_attribute(xml: str,
                        source: str,
                        dtd: DTD,
                        external: bool) -> (AttributeDeclaration, str):
        """
            AttDef ::== S Name S AttType S DefaultDeclaration
        """
        attr = AttributeDeclaration()
        attr.name, xml = AttributeDeclFactory.parse_attribute_name(xml, source, dtd, external)

        *attr_info, xml = AttributeDeclFactory.parse_attribute_type(xml, source, dtd, external)
        attr.value_type, attr.options = attr_info

        *attr_defaults, xml = AttributeDeclFactory.parse_default_declaration(xml, source,
                                                                             dtd, external)
        attr.default_declaration, attr.default_value = attr_defaults

        return attr, xml

    @staticmethod
    def parse_attribute_name(xml: str,
                             source: str,
                             dtd: DTD,
                             external: bool) -> (str, str):
        # Name is everything up to following whitespace
        name_end = RegEx.Whitespace.search(xml)
        if not name_end:
            raise XMLError("Error parsing ATTLIST attribute name", source=source)

        name = xml[:name_end.start()]
        xml = xml[name_end.start():]

        # Expand all entities in name
        if external:
            name = expand_parameter_entity_references(name, dtd, source)

        # Name must conform to xmlspec::Name
        if not RegEx.Name.fullmatch(name):
            raise DisallowedCharacterError(name, "attribute name", conforms_to="Name",
                                           source=source)

        # Strip trailing whitespace
        whitespace = RegEx.Whitespace.match(xml)
        if not whitespace:
            raise XMLError("Missing whitespace after attribute name in ATTLIST declaration", source)
        xml = xml[whitespace.end():]

        return name, xml

    """
        ===============
        ATTRIBUTE TYPE
        ===============
    """

    @staticmethod
    def parse_attribute_type(xml: str,
                             source: str,
                             dtd: DTD,
                             external: bool) -> (str, List[str], str):
        # If attribute type is a PE reference
        if xml.startswith("%") and external:
            xml = expand_parameter_entity_reference(xml, dtd, source)
            whitespace = RegEx.OptionalWhitespace.match(xml)
            xml = xml[whitespace.end():]

        # Basic Types
        if xml[:5] == "CDATA":
            return "CDATA", [], xml[5:]
        if xml[:6] == "IDREFS":
            return "IDREFS", [], xml[6:]
        if xml[:5] == "IDREF":
            return "IDREF", [], xml[5:]
        if xml[:2] == "ID":
            return "ID", [], xml[2:]
        if xml[:6] == "ENTITY":
            return "ENTITY", [], xml[6:]
        if xml[:8] == "ENTITIES":
            return "ENTITIES", [], xml[8:]
        if xml[:8] == "NMTOKENS":
            return "NMTOKENS", [], xml[8:]
        if xml[:7] == "NMTOKEN":
            return "NMTOKEN", [], xml[7:]

        # Check whether this is a notation
        default_type = "enumeration"
        if xml[:8] == "NOTATION":
            default_type = "notation"

            whitespace = RegEx.Whitespace.match(xml, pos=8)
            if not whitespace:
                raise XMLError("Missing whitespace after NOTATION keyword", source)
            xml = xml[whitespace.end():]

        # Parse
        return (default_type.upper(),
                *AttributeDeclFactory.parse_enumeration(xml, source, default_type, dtd, external))

    @staticmethod
    def parse_enumeration(xml: str,
                          source: str,
                          default_type: str,
                          dtd: DTD,
                          external: bool) -> (List[str], str):
        """
            Enumeration ::=	'(' S? Nmtoken (S? '|' S? Nmtoken)* S? ')'
            Notations   ::=	'(' S? Name (S? '|' S? Name)* S? ')'
        """
        # Enumeration must begin with '('
        if xml[:1] != "(":
            raise XMLError("Error while parsing ATTLIST enumeration", source)
        xml = xml[1:]

        options = []
        while True:
            # Strip optional whitespace
            whitespace = RegEx.Whitespace.match(xml)
            if whitespace:
                xml = xml[whitespace.end():]

            # Parse PEs independently from current enum
            if xml.startswith("%") and external:
                entity, entity_text, xml = parse_parameter_entity_reference(xml, dtd, source)
                new_options, _xml = AttributeDeclFactory.parse_enumeration(f"({entity_text})",
                                                                           source, default_type,
                                                                           dtd, external)
                options += new_options
                # If there is any remaining unparsed xml, PE must be ill-formed
                if _xml:
                    raise XMLError(f"Parameter entity {entity.name} is ill-formed for use in an "
                                   f"ATTLIST declaration {default_type}", source)
                continue

            # Enum option is everything up to '|' or ')'
            option_end = re.search(f"(?:{RegEx.whitespace})?[|)]", xml)
            if not option_end:
                raise XMLError("Error while parsing AttList enumeration option", source)

            option = xml[:option_end.start()]
            options.append(option)
            xml = xml[option_end.end():]

            # Enum option must conform to xmlspec::Name if NOTATION type or xmlspec::Name
            if default_type == "notation" and not RegEx.Name.fullmatch(option):
                raise DisallowedCharacterError(option, "notation", conforms_to="NmToken",
                                               source=source)
            elif not RegEx.NmToken.fullmatch(option):
                raise DisallowedCharacterError(option, "enumeration option", conforms_to="NmToken",
                                               source=source)

            # If this is the end of the enumeration
            if ")" in option_end.group():
                break

        return options, xml

    """
        ==============================    
        ATTRIBUTE DEFAULT DECLARATION
        ==============================    
    """

    @staticmethod
    def parse_default_declaration(xml: str,
                                  source: str,
                                  dtd: DTD,
                                  external: bool) -> (str, str, str):
        """
        DefaultDecl	::=	'#REQUIRED' | '#IMPLIED' | (('#FIXED' S)? AttValue)
        """
        # Expand entity
        if re.match(f"{RegEx.optional_whitespace}%", xml) and external:
            xml = expand_parameter_entity_reference(xml, dtd, source)

        # Strip leading whitespace
        whitespace = RegEx.Whitespace.match(xml)
        if not whitespace:
            raise XMLError("Error while parsing AttList attribute default declaration", source)
        xml = xml[whitespace.end():]

        # Basic default types
        if xml[:9] == "#REQUIRED":
            return "REQUIRED", None, xml[9:]

        elif xml[:8] == "#IMPLIED":
            return "IMPLIED", None, xml[8:]

        # Fixed value
        elif xml[:6] == "#FIXED":
            xml = xml[6:]

            # Expand entity
            if re.match(f"{RegEx.optional_whitespace}%", xml) and external:
                xml = expand_parameter_entity_reference(xml, dtd, source)

            whitespace = RegEx.Whitespace.match(xml)
            if not whitespace:
                raise XMLError("Missing whitespace after '#FIXED' in attribute default declaration",
                               source)
            xml = xml[whitespace.end():]

            return ("FIXED", *AttributeDeclFactory.parse_default_value(xml, source, dtd, external))

        # Default value
        else:
            return ("DEFAULT", *AttributeDeclFactory.parse_default_value(xml, source, dtd, external))

    @staticmethod
    def parse_default_value(xml: str,
                            source: str,
                            dtd: DTD,
                            external: bool) -> (str, str):
        # Import here to avoid circular import loop
        from xml_parser.content.Element import ElementFactory

        # If default value is a PE reference
        if xml.startswith("%") and external:
            xml = expand_parameter_entity_reference(xml, dtd, source)
            whitespace = RegEx.OptionalWhitespace.match(xml)
            xml = xml[whitespace.end():]

        # Default value must be delimited by quotations
        delimiter = xml[:1]
        if delimiter not in "\'\"":
            raise XMLError("ATTLIST default values must be delimited with \' or \"", source)

        value_end = xml.find(delimiter, 1)

        # Normalise default value
        default_value = ElementFactory.normalise_attribute_value(xml[1: value_end], source, dtd)

        # Default value must conform to xmlspec::Char*
        if not RegEx.CharSequence.fullmatch(default_value):
            raise DisallowedCharacterError(default_value, "ATTLIST attribute default value",
                                           conforms_to="Char", source=source)

        return default_value, xml[value_end + 1:]
