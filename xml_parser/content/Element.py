import re
from typing import List, Dict, Union

from xml_parser.dtd.DTD import DTD
from xml_parser.helpers import parse_character_reference
from xml_parser.regular_expressions import RegEx
from .ProcessingInstruction import ProcessingInstruction, ProcessingInstructionFactory
from .Comment import CommentFactory
from .Text import Text, TextFactory
from ..errors import XMLError, DisallowedCharacterError

__all__ = ['Element']


class Element:
    """
        Represents a single xml element.

        Attributes:
            name                    The element's name, as specified in the start and end tags
            attributes              A key-value dictionary of the element's attributes, as specified in the start tag
            content                 A list of all the content within the element including text, processing
                                    instructions and child elements.
            children                A list of all the child elements within this element
                                    (i.e. `content` without the text and processing instructions)
            text                    A list of all the text within this element
                                    (i.e. `content` without the elements and processing instructions)
            processing_instructions A list of all the processing instructions within this element
                                    (i.e. `content` without the text and elements)
    """

    def __init__(self, dtd: DTD):
        self.__dtd = dtd

        self.name = ""  # type: str
        self.attributes = {}  # type: Dict[str, str]

        self.content = []  # type: List[Union[Element, Text, ProcessingInstruction]]
        self.children = []  # type: List[Element]
        self.text = []  # type: List[Text]
        self.processing_instructions = []  # type: List[ProcessingInstruction]


class ElementFactory:
    @staticmethod
    def parse_from_xml(xml: str, dtd: DTD):
        """
        element      ::== EmptyElemTag | STag content ETag
        STag	     ::== '<' Name (S Attribute)* S? '>'
        content	     ::== (element | CharData | Reference | CDSect | PI | Comment)*
        ETag	     ::== '</' Name S? '>'
        EmptyElemTag ::== '<' Name (S Attribute)* S? '/>'
        """
        element = Element(dtd)

        xml, is_self_closing = ElementFactory.parse_start_tag_into_element(xml, element, dtd)
        ElementFactory.append_default_attributes_to_element(element, dtd)

        if not is_self_closing:
            xml = ElementFactory.parse_content_into_element(xml, element, dtd)
            xml = ElementFactory.parse_end_tag(xml, element.name)

        return element, xml

    """
        ==========
        START & END TAG
        ==========
    """

    @staticmethod
    def parse_start_tag_into_element(xml: str, element: Element, dtd: DTD) -> (str, bool):
        """
        STag	     ::= '<' Name (S Attribute)* S? '>'
        EmptyElemTag ::= '<' Name (S Attribute)* S? '/>'
        Attribute	 ::= Name Eq AttValue
        """
        source = xml
        xml = xml[1:]

        element.name, xml = ElementFactory.parse_name(xml, source)
        element.attributes, xml = ElementFactory.parse_attributes(xml, source, element.name, dtd)

        whitespace = RegEx.OptionalWhitespace.match(xml)
        xml = xml[whitespace.end():]

        # Element is self-closing if it ends with '/>' instead of '>'
        if xml.startswith("/>"):
            return xml[2:], True
        elif xml.startswith(">"):
            return xml[1:], False

        # Any remaining content before '>' is illegal
        else:
            raise XMLError("Illegal extra content at end of element", source)

    @staticmethod
    def parse_name(xml: str, source: str) -> (str, str):
        name_end = RegEx.Whitespace_Or_TagEnd.search(xml)
        if not name_end:
            raise XMLError("Unable to find end of xml element", source)

        name = xml[:name_end.start()]
        xml = xml[name_end.start():]

        # Element name must conform to xmlspec::Name
        if not RegEx.Name.fullmatch(name):
            raise DisallowedCharacterError(name, "element name", conforms_to="Name", source=source)

        return name, xml

    """
        ===========
        ATTRIBUTES
        ===========
    """

    @staticmethod
    def parse_attributes(xml: str, source: str, element: str, dtd: DTD) -> (str, Dict[str, str]):
        attributes = {}

        while not RegEx.Element_StartTagEnd.match(xml):
            # Strip leading whitespace
            whitespace = RegEx.Whitespace.match(xml)
            if not whitespace:
                raise XMLError("Missing whitespace before attribute", source)
            xml = xml[whitespace.end():]

            # Parse attribute
            att_name, xml = ElementFactory.parse_attribute_name(xml, source)
            att_value, xml = ElementFactory.parse_attribute_value(xml, source,
                                                                  element, att_name, dtd)

            # Attribute names must be unique
            if att_name in attributes.keys():
                raise XMLError(f"Attribute '{att_name}' repeated in element", source)

            attributes[att_name] = att_value

        return attributes, xml

    @staticmethod
    def parse_attribute_name(xml: str, source: str) -> (str, str):
        name_end = RegEx.Eq.search(xml)
        if not name_end:
            raise XMLError(f"Element contains an attribute without a value", source)

        name = xml[:name_end.start()]
        xml = xml[name_end.end():]

        # Explicitly check for '>' in attribute name to report accurate errors
        if '>' in name:
            raise XMLError(f"Element contains an attribute without a value", source)

        # Attribute names must conform to xmlspec::Name
        if not RegEx.Name.fullmatch(name):
            raise DisallowedCharacterError(name, "attribute name",
                                           conforms_to="Name", source=source)

        return name, xml

    @staticmethod
    def parse_attribute_value(xml: str,
                              source: str,
                              element: str,
                              attribute: str,
                              dtd: DTD) -> (str, str):
        delimiter = xml[0]
        if delimiter not in "\'\"":
            raise XMLError(f"Invalid delimiter `{delimiter}` for attribute value", source=source)
        value_end = xml.find(delimiter, 1)

        value = xml[1: value_end]
        xml = xml[value_end + 1:]

        # If the attribute is of type != 'CDATA' it requires extra normalisation
        attr = dtd.element_attributes.get(element, {}).get(attribute, None)
        is_cdata = not (attr and attr.value_type != "CDATA")

        normalised_value = ElementFactory.normalise_attribute_value(value, source, dtd,
                                                                    is_cdata=is_cdata)

        # Attribute values must conform to xmlspec::Char*
        if not RegEx.CharSequence.fullmatch(normalised_value):
            raise DisallowedCharacterError(normalised_value, "attribute value",
                                           conforms_to="Char", source=source)

        return normalised_value, xml

    @staticmethod
    def normalise_attribute_value(value: str,
                                  source: str,
                                  dtd: DTD,
                                  entity_chain: List[str] = [],
                                  is_cdata: bool = True) -> str:
        """
            An implementation of the attribute normalisation algorithm as described in
            ch 3.3.3 of the xml spec

            Normalises all whitespace characters (#x20, #xD, #xA, #x9) to #x20,
            Expands character and general entities
            If this attribute is declared with a type other than 'CDATA', further normalises by:
                - Stripping all leading & trailing whitespace
                - Replacing whitespace sequences of length >1 with a single space
        """
        normalised_value = ""

        # Normalise pre-existing whitespace
        value = value.replace("\u000a", "\u0020")
        value = value.replace("\u000d", "\u0020")
        value = value.replace("\u0009", "\u0020")

        # Iterate through all general and character references
        last_index = 0
        for match in re.finditer("&.*?;", value):
            reference = match.group()

            # Append skipped text
            skipped_text = value[last_index: match.start()]
            normalised_value += skipped_text
            last_index = match.end()

            # Attribute value may not contain unescaped & or >
            if "&" in skipped_text:
                raise DisallowedCharacterError(value, "attribute value",
                                               conforms_to="&", source=value)
            if "<" in skipped_text:
                raise DisallowedCharacterError(value, "attribute value",
                                               conforms_to="<", source=value)

            # Append character references & continue
            if reference.startswith("&#"):
                character, _ = parse_character_reference(reference)
                normalised_value += character
                continue

            # Check for general entity recursion
            if match.group() in entity_chain:
                raise XMLError(f"Recursion within entities is prohibited "
                               f"(reference loop in {reference})", source)

            # Normalise entity expansion text before appending
            entity = dtd.general_entities.get(reference[1:-1], None)
            if not entity:
                raise XMLError(f"Reference to undeclared entity {reference}", source)
            if not entity.parsed:
                raise XMLError("Illegal reference to unparsed entity in attribute value", source)
            if entity.expansion_text is None:
                raise XMLError(f"Reference to parsed external entity {reference} which could not "
                               f"be found at public uri {entity.public_uri} "
                               f"or system uri {entity.system_uri}", source)
            normalised_value += ElementFactory.normalise_attribute_value(entity.expansion_text,
                                                                         source, dtd,
                                                                         entity_chain + [reference])

        # Append final text (after last reference) unless it contains unescaped '&' or '>'
        if "&" in value[last_index:]:
            raise DisallowedCharacterError(value, "attribute value",
                                           conforms_to="&", source=source)
        if "<" in value[last_index:]:
            raise DisallowedCharacterError(value, "attribute value",
                                           conforms_to="<", source=source)
        normalised_value += value[last_index:]

        # If this is not a CDATA section, normalise value further
        if not is_cdata:
            # Remove whitespace at start and end
            while normalised_value.startswith("\u0020"):
                normalised_value = normalised_value[1:]
            while normalised_value.endswith("\u0020"):
                normalised_value = normalised_value[:-1]
            # Remove double-spaces
            while "\u0020\u0020" in normalised_value:
                normalised_value = normalised_value.replace("\u0020\u0020", "\u0020")

        return normalised_value

    @staticmethod
    def append_default_attributes_to_element(element: Element, dtd: DTD):
        """
            Adds any attributes with declared default values to this element
        """
        for key, attribute in dtd.element_default_attributes.get(element.name, {}).items():
            if key not in element.attributes:
                value = attribute.default_value

                # Normalise whitespace for non-CDATA attributes
                if attribute.value_type != "CDATA":
                    # Remove whitespace at start and end
                    while value.startswith(" "):
                        value = value[1:]
                    while value.endswith(" "):
                        value = value[:-1]
                    # Remove double-spaces
                    while "  " in value:
                        value = value.replace("  ", " ")

                element.attributes[key] = value

    """
        ========
        CONTENT
        ========
    """

    @staticmethod
    def parse_content_into_element(xml: str, element: Element, dtd: DTD) -> str:
        """
            content ::=	(element | CharData | Reference | CDSect | PI | Comment)*
        """
        text_factory = TextFactory(dtd)

        # Parse the element content
        element.content, xml = ElementFactory.parse_xml_block(xml, text_factory, dtd)

        # Append final text block if there is one
        text = text_factory.pop_text_object()
        if text:
            element.content.append(text)

        # Sort elements into convenience-lists by type
        element.children = [child for child in element.content if isinstance(child, Element)]
        element.text = [child for child in element.content if isinstance(child, Text)]
        element.processing_instructions = [child for child in element.content
                                           if isinstance(child, ProcessingInstruction)]

        return xml

    @staticmethod
    def parse_xml_block(xml,
                        text_factory: TextFactory,
                        dtd: DTD,
                        entity_chain: List[str] = []
                        ) -> (List[Union[Element, Text, ProcessingInstruction]], str):
        """
            content ::=	(element | CharData | Reference | CDSect | PI | Comment)*
        """
        content = []

        # Stop parsing this block upon an end-tag or when the block is exhausted
        while len(xml) > 0 and not xml.startswith("</"):
            # General entities
            if xml.startswith("&") and not xml.startswith("&#"):
                entity_content, xml = ElementFactory.parse_general_entity(xml, text_factory,
                                                                          dtd, entity_chain)
                content += entity_content
                continue

            # Processing Instructions
            if xml.startswith("<?"):
                content.append(text_factory.pop_text_object())
                processing_instruction, xml = ProcessingInstructionFactory.parse_from_xml(xml, dtd)
                content.append(processing_instruction)
                continue

            # Comments
            if xml.startswith("<!--"):
                xml = CommentFactory.parse_from_xml(xml, dtd)
                continue

            # Elements
            if xml.startswith("<") and not xml.startswith("<![CDATA["):
                content.append(text_factory.pop_text_object())
                element, xml = ElementFactory.parse_from_xml(xml, dtd)
                content.append(element)
                continue

            # Anything else is character data
            xml = text_factory.add_text(xml)

        # Filter content to remove empty text blocks before returning
        return [child for child in content if child], xml

    @staticmethod
    def parse_general_entity(xml,
                             text_factory: TextFactory,
                             dtd: DTD,
                             entity_chain: List[str]
                             ) -> (List[Union[Element, Text, ProcessingInstruction]], str):

        # Isolate the entity reference from remaining xml
        reference_end = xml.find(";")
        if reference_end == -1:
            raise XMLError("Unable to find end of entity reference", source=xml)

        reference = xml[:reference_end + 1]
        xml = xml[reference_end + 1:]

        # Check for recursion
        if reference in entity_chain:
            raise XMLError(
                f"Recursion within entities is prohibited (reference loop in {reference})")

        # Fetch the entity & parse as markup in isolated from current xml block
        entity = dtd.general_entities.get(reference[1:-1], None)
        if not entity:
            raise XMLError(f"Reference to undeclared entity {reference}", source=xml)
        if not entity.parsed:
            raise XMLError("Illegal reference to unparsed entity in element content value",
                           source=xml)
        if entity.expansion_text is None:
            raise XMLError(f"Reference to parsed external entity {reference} which could not "
                           f"be found at public uri {entity.public_uri} "
                           f"or system uri {entity.system_uri}", source=xml)

        content, unparsed_xml = ElementFactory.parse_xml_block(entity.expansion_text, text_factory,
                                                               dtd, entity_chain + [reference])

        # If there is any remaining xml, entity contains mismatched end-tag so is ill-formed
        if unparsed_xml:
            raise XMLError(f"Ill-formed expansion text for entity {reference}", source=xml)

        return content, xml

    """
        ========
        END TAG
        ========
    """

    @staticmethod
    def parse_end_tag(xml: str, start_tag_name: str) -> str:
        """
        ETag ::= '</' Name S? '>'
        """
        source = xml

        # End tags must begin with '</'
        if not xml.startswith("</"):
            raise XMLError(f"Unable to find end-tag for element '{start_tag_name}'", source=source)
        xml = xml[2:]

        # End tags consist only of name
        tag_end = RegEx.Element_EndTagEnd.search(xml)
        if not tag_end:
            raise XMLError(f"Error parsing end-tag for element '{start_tag_name}'", source=source)

        end_tag_name = xml[:tag_end.start()]
        xml = xml[tag_end.end():]

        # Name must match start-tag
        if end_tag_name != start_tag_name:
            raise XMLError(f"Mismatched start ('{start_tag_name}') "
                           f"and end ('{end_tag_name}') tags for element", source=source)

        return xml
