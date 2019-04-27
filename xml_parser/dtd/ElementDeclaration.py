import re
from typing import List, Optional

from xml_parser.dtd.DTD import DTD
from xml_parser.helpers import (expand_parameter_entity_references,
                                expand_parameter_entity_reference, parse_parameter_entity_reference)
from xml_parser.regular_expressions import RegEx
from ..errors import XMLError, DisallowedCharacterError


class ElementDeclaration:
    def __init__(self, dtd: DTD):
        self.__dtd = dtd

        self.name = ""  # type: str
        self.content_type = ""  # type: str
        self.children_regex = None  # type: Optional[str]


class ElementDeclFactory:
    @staticmethod
    def parse_from_xml(xml: str,
                       dtd: DTD,
                       external: bool) -> (ElementDeclaration, str):
        """
            elementdecl ::== '<!ELEMENT' S Name S contentspec S? '>'
        """
        element = ElementDeclaration(dtd)
        source = xml
        xml = xml[9:]

        element.name, xml = ElementDeclFactory.parse_name(xml, source, dtd, external)
        content_type, regex, xml = ElementDeclFactory.parse_content_spec(xml, source, dtd, external)
        element.content_type = content_type
        element.children_regex = regex

        # Strip optional whitespace
        whitespace = RegEx.Whitespace.match(xml)
        if whitespace:
            xml = xml[whitespace.end():]

        # Ensure element declaration ends properly
        if xml[:1] != ">":
            raise XMLError("Illegal extra content at end of xml element declaration", source)

        return element, xml[1:]

    @staticmethod
    def parse_name(xml: str,
                   source: str,
                   dtd: DTD,
                   external: bool) -> (str, str):
        # Strip leading whitespace
        whitespace = RegEx.Whitespace.match(xml)
        if not whitespace:
            raise XMLError("Missing whitespace before name in element declaration", source)
        xml = xml[whitespace.end():]

        # Name is everything up to following whitespace
        name_end = RegEx.Whitespace.search(xml)
        if not name_end:
            raise XMLError("Error parsing element declaration", source=source)

        name = xml[:name_end.start()]
        xml = xml[name_end.end():]

        # Explicitly check for '>' in name to report accurate errors
        if '>' in name:
            raise XMLError("Missing content spec in element declaration", source=source)

        # Expand all entities in name
        if external:
            name = expand_parameter_entity_references(name, dtd, source)

        # Name must conform to xmlspec::Name
        if not RegEx.Name.fullmatch(name):
            raise DisallowedCharacterError(name, "element declaration",
                                           conforms_to="Name", source=source)

        return name, xml

    """
        =============
        CONTENT SPEC
        =============
    """

    @staticmethod
    def parse_content_spec(xml: str,
                           source: str,
                           dtd: DTD,
                           external: bool) -> (str, Optional[str], str):
        """
            contentspec ::== 'EMPTY' | 'ANY' | Mixed | children
            children ::== ( choice | seq ) ('?' | '*' | '+')
            Mixed ::== '(' S? '#PCDATA' (S? '|' S? Name)* S? ')*' | '(' S? '#PCDATA' S? ')'

            :return (Element type, regex condition,
        """
        # Expand parameter entity
        if xml.startswith("%") and external:
            xml = expand_parameter_entity_reference(xml, dtd, source)
            whitespace = RegEx.OptionalWhitespace.match(xml)
            xml = xml[whitespace.end():]

        if xml.startswith("EMPTY"):
            return "EMPTY", None, xml[5:]

        if xml.startswith("ANY"):
            return "ANY", None, xml[3:]

        condition, is_mixed, xml = ElementDeclFactory.parse_content_particle(xml, source,
                                                                             dtd, external)

        if is_mixed:
            return "MIXED", condition, xml
        else:
            return "CHILDREN", condition, xml

    @staticmethod
    def parse_content_particle(xml: str,
                               source: str,
                               dtd: DTD,
                               external: bool,
                               is_mixed: bool = False,
                               structure_type=None) -> (Optional[str], bool, str):
        # Expand and parse PE references separately to current structure
        if xml.startswith("%") and external:
            # Expand entity
            entity, value, xml = parse_parameter_entity_reference(xml, dtd, source)

            # Ignore entities with no content
            if RegEx.Whitespace.sub("", value) == "":
                return None, is_mixed, xml

            # Parse entity content as a list of CPs
            regex, is_mixed, _xml = ElementDeclFactory.parse_structure(f"({value})", source, dtd,
                                                                       external, structure_type)

            # If there is any remaining unparsed xml, PE must be ill-formed
            if _xml:
                raise XMLError(f"Parameter entity {entity.name} is ill-formed for use in an "
                               "element declaration content spec", source)

            return regex, is_mixed, _xml

        # If there is a #PCDATA option, this element must be mixed
        if xml.startswith("#PCDATA") and not is_mixed:
            return "#PCDATA", True, xml[7:]

        # Anything not beginning with "(" is an element name
        if not xml.startswith("("):
            name, xml = ElementDeclFactory.parse_child_name(xml, source, is_mixed)
            return name, is_mixed, xml

        # Anything beginning with '(' is a structure (choice or sequence)
        return ElementDeclFactory.parse_structure(xml, source, dtd, external, is_mixed)

    @staticmethod
    def parse_child_name(xml: str,
                         source: str,
                         is_mixed: bool) -> (str, str):
        # Name must end either on ')', '|' or ','
        name_end = re.search(f"({RegEx.whitespace})?[|,)]", xml)
        if not name_end:
            raise XMLError("Error while parsing content spec in element declaration", source=source)

        name = xml[:name_end.start()]
        xml = xml[name_end.start():]

        if len(name) == 0 or (len(name) == 1 and name[-1] in "?*+"):
            raise XMLError("Error while parsing content spec in element declaration", source=source)

        # Look for a modifier
        modifier = ""
        if name[-1] in "?*+" and not is_mixed:
            modifier = name[-1]
            name = name[:-1]

        # Element name must conform to xmlspec::Name
        if not RegEx.Name.fullmatch(name):
            raise DisallowedCharacterError(name, "element declaration child name",
                                           conforms_to="Name", source=source)

        return f"({name}#){modifier}", xml

    @staticmethod
    def parse_structure(xml: str,
                        source: str,
                        dtd: DTD,
                        external: bool,
                        is_mixed: bool = False,
                        structure_type=None) -> (str, bool, str):
        xml = xml[1:]

        items: List[str] = []
        while True:
            # Strip whitespace
            whitespace = RegEx.Whitespace.match(xml)
            if whitespace:
                xml = xml[whitespace.end():]

            # Parse item
            item, is_mixed, xml = ElementDeclFactory.parse_content_particle(xml, source, dtd,
                                                                            external, is_mixed)
            if item:
                items.append(item)

            # Strip whitespace
            whitespace = RegEx.Whitespace.match(xml)
            if whitespace:
                xml = xml[whitespace.end():]

            # If this is the end of the structure
            if xml[:1] == ")":
                break

            # If there is another item
            if structure_type and xml[:1] == structure_type:
                xml = xml[1:]
                continue
            elif not structure_type and xml[:1] in "|,":
                structure_type = xml[:1]
                xml = xml[1:]
                continue

            # Or a PE reference
            if xml[:1] == "%":
                continue

            # Anything else is an error
            print(xml)
            raise XMLError("Error while parsing content spec in element declaration", source)

        # Structure must not be empty
        if not items:
            raise XMLError("Empty structure () in element declaration content spec", source)

        # '#PCDATA' must be first item
        if items[0] == "#PCDATA":
            items.pop(0)
        if "#PCDATA" in items:
            raise XMLError("'#PCDATA' must be the first option in a mixed content spec", source)

        # Look for a modifier
        modifier = xml[1] if xml[1] in "?*+" else ""

        # Mixed structures must have '*' modifier if any child options
        if is_mixed and len(items) > 0 and modifier != "*":
            raise XMLError("Mixed content spec must end in ')*' when "
                           "child element options are specified", source)
        elif is_mixed and modifier in ["?", "+"]:
            raise XMLError(f"Illegal modifier {modifier} after mixed content spec ", source)

        # Mixed structures must have unique names
        if is_mixed and len(items) != len(set(items)):
            raise XMLError("Mixed content spec may only list each child option once", source)

        # Build regex based on structure type
        regex = ""
        if not structure_type and len(items) > 0:
            regex = f"({items[0]}){modifier}"
        elif structure_type == "|":
            regex = f"({'|'.join(items)}){modifier}"
        elif structure_type == ",":
            regex = f"({''.join(items)}){modifier}"

        return regex, is_mixed, xml[2:] if modifier else xml[1:]
