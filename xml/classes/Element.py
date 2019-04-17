from typing import List, Dict, Optional, Union
import Helpers
from RegularExpressions import RegEx
from .ProcessingInstruction import ProcessingInstruction
from .Text import Text
from .XMLMarkup import XMLMarkup
from .Entity import Entity
from .Error import XMLError, DisallowedCharacterError


class Element(XMLMarkup):
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
    def __init__(self, remaining_xml: str):
        self.__raw_declaration = remaining_xml
        self.__current_text = None  # type: Optional[Text]

        self.name = ""  # type: str
        self.attributes = {}  # type: Dict[str, str]
        self.__is_self_closing_element = False  # type: bool

        self.content = []  # type: List[Union[Element, Text, ProcessingInstruction]]
        self.children = []  # type: List[Element]
        self.text = []  # type: List[Text]
        self.processing_instructions = []  # type: List[ProcessingInstruction]

    def parse_to_end(self, general_entities: Dict[str, Entity]) -> str:
        # Parse start tag
        remaining_xml = self.parse_opening_tag(self.__raw_declaration, general_entities)

        # If the element is self-closing, there is nothing else to parse
        if self.__is_self_closing_element:
            return remaining_xml

        # Parse content
        remaining_xml = self.parse_xml_block(remaining_xml, general_entities)

        # Sort content objects into convenience lists
        self.children = [child for child in self.content if isinstance(child, Element)]
        self.text = [child for child in self.content if isinstance(child, Text)]
        self.processing_instructions = [child for child in self.content if isinstance(child, ProcessingInstruction)]

        # Parse end tag
        remaining_xml = self.parse_end_tag(remaining_xml)

        # Pass unparsed xml (after end tag) back for parent to handle
        return remaining_xml

    """
        ==========
        START TAG
        ==========
        These functions are responsible for parsing the start tag of the element
        e.g. <Name attr1="blah" attr2="blah">
    """

    def parse_opening_tag(self, xml, general_entities: Dict[str, Entity]) -> str:
        """
            Parses the element tag found at the beginning of the provided xml string.
            Note: `xml` is guaranteed to have the element's `<` at position 0
        :param xml: The xml string describing the element
        :param general_entities: A dictionary of general entities for the current document
        :return: Unparsed xml after the opening tag
        """
        # Strip opening fluff
        remaining_xml = xml[1:]

        # Collect tag data
        remaining_xml = self.parse_name(remaining_xml)
        remaining_xml = self.parse_attributes(remaining_xml, general_entities)

        # Parse end of the tag
        if remaining_xml[:2] == "/>":
            self.__is_self_closing_element = True

        # Strip closing fluff & return remaining xml to be parsed as content
        if remaining_xml[:1] == ">":
            return remaining_xml[1:]
        elif remaining_xml[:2] == "/>":
            return remaining_xml[2:]
        else:
            raise XMLError("Unable to find end of start-tag for element", source=self.__raw_declaration)

    def parse_name(self, xml) -> str:
        """
            Parses the element's name from the opening tag
        :param xml:
        :return: All xml after the element's name
        """
        # The name will end on either whitespace (if attributes) or tag close (>, />)
        name_end = RegEx.Whitespace_Or_TagClose.search(xml)

        if not name_end:
            raise XMLError("Unable to find end of start-tag for element", source=self.__raw_declaration)

        self.name = xml[:name_end.start()]

        # Names must conform to xmlspec::Name
        if not RegEx.Name.fullmatch(self.name):
            raise DisallowedCharacterError(self.name, "element name", conforms_to="Name", source=self.__raw_declaration)

        # Return remaining xml for processing
        return xml[name_end.start():]

    def parse_attributes(self, xml, general_entities: Dict[str, Entity]) -> str:
        while True:
            # Strip leading whitespace
            whitespace = RegEx.Whitespace.match(xml)
            if whitespace:
                xml = xml[whitespace.end():]

            # Whitespace is compulsory if this is not the end of the tag
            if xml[:1] not in ["/", ">"]:
                if not whitespace:
                    raise XMLError("Missing whitespace before element attribute", source=self.__raw_declaration)

            # If this is the end of the tag, return remaining xml
            else:
                return xml

            # Parse the attribute
            attribute_name, xml = self.parse_attribute_name(xml)
            attribute_value, xml = self.parse_attribute_value(xml, general_entities)

            # Ensure attribute name is unique
            if attribute_name in self.attributes.keys():
                raise XMLError(f"Repeated attribute '{attribute_name}' in element", source=self.__raw_declaration)

            self.attributes[attribute_name] = attribute_value

    def parse_attribute_name(self, xml) -> (str, str):
        """
            Parses an attribute's name & returns both the name and remaining unparsed xml
        """
        # The attribute name will end with an equality
        name_end = RegEx.Eq.search(xml)
        if not name_end:
            raise XMLError(f"Element '{self.name}' contains an attribute without a value",
                           source=self.__raw_declaration)

        # Parse the attribute name
        attribute_name = xml[:name_end.start()]

        # To ensure we report the correct error, explicitly check for '>' in the attribute name
        if '>' in attribute_name:
            raise XMLError(f"Element '{self.name}' contains an attribute without a value",
                           source=self.__raw_declaration)

        # Attribute name must conform to xmlspec::Name
        if not RegEx.Name.fullmatch(attribute_name):
            raise DisallowedCharacterError(attribute_name, "attribute name",
                                           conforms_to="Name",
                                           source=self.__raw_declaration)

        return attribute_name, xml[name_end.end():]

    def parse_attribute_value(self, xml, general_entities: Dict[str, Entity]) -> (str, str):
        # The attribute value will be delimited by the same type of quotation on each end
        delimiter = xml[:1]
        if delimiter not in "\'\"":
            raise XMLError(f"Invalid delimiter `{delimiter}` for attribute value", source=self.__raw_declaration)

        # Find the end of the string literal & parse value
        end_index = xml.find(delimiter, 1)
        attribute_value = xml[1:end_index]

        # Attribute values may not contain '<'
        if "<" in attribute_value:
            raise DisallowedCharacterError(attribute_value, "attribute value",
                                           conforms_to="<",
                                           source=self.__raw_declaration)

        # Expand attribute value references & normalise whitespace
        attribute_value = Helpers.parse_string_literal(attribute_value,
                                                       general_entities=general_entities,
                                                       expand_parameter_entities=False,
                                                       normalise_whitespace=True)

        # Attribute values must conform to xmlspec::Char
        if not RegEx.CharSequence.fullmatch(attribute_value):
            raise DisallowedCharacterError(attribute_value, "attribute value", conforms_to="Char",
                                           source=self.__raw_declaration)

        return attribute_value, xml[end_index + 1:]

    """
        ========
        END TAG
        ========
        This function is responsible for parsing the end tag of the element
        e.g. </Name>
    """

    def parse_end_tag(self, xml) -> str:
        """
            Parses the xml element's end tag.

            Parses the name from the given end tag and ensures it matches the name in the start tag.
        """
        # Ensure the remaining xml is an end tag
        if xml[:2] != "</":
            raise XMLError(f"Unable to find end-tag for element '{self.name}'", source=self.__raw_declaration)

        # Isolate the end-tag name
        end_index = xml.find(">")
        if end_index == -1:
            raise XMLError(f"Unable to find end of end-tag for element '{self.name}'", source=xml)
        end_name = xml[2:end_index]
        xml = xml[end_index + 1:]

        # Remove trailing whitespace from name
        whitespace = RegEx.Whitespace_End.search(end_name)
        if whitespace:
            end_name = end_name[:whitespace.start()]

        # Ensure end name matches start name
        if end_name != self.name:
            raise XMLError(f"Mismatched start ('{self.name}') and end ('{end_name}') tags for element",
                           source=self.__raw_declaration)

        # Return remaining unparsed xml
        return xml

    """
        ========
        CONTENT
        ========
        This function is responsible for parsing the xml element's content.
        todo - write more about me :)
    """

    def parse_xml_block(self, xml, general_entities: Dict[str, Entity], seen_entities: [str] = []) -> str:
        """
            todo - write me :(
        :param xml:
        :param general_entities:
        :param seen_entities:
        :return:
        """
        while True:
            # If the xml block has been exhausted, return
            if len(xml) == 0:
                return xml

            # If we've reached an end-tag, close the current text block and return
            if xml[:2] == "</":
                self.__close_current_text_block()
                return xml

            # Pass child elements on to XMLMarkup class for processing
            if xml[:1] == "<" and xml[:9] != "<![CDATA[":
                child = XMLMarkup(xml)
                xml = child.parse_to_end(general_entities)

                # Discard comments
                from .Comment import Comment
                if not isinstance(child, Comment):
                    self.__close_current_text_block()
                    self.content.append(child)

                continue

            # Expand general entities & parse in isolation from current xml block
            if xml[:1] == "&" and xml[:2] != "&#":
                # Isolate the reference
                reference_end = xml.find(";")
                if reference_end == -1:
                    raise XMLError(f"Unable to find end of entity reference", source=xml)
                reference = xml[:reference_end + 1]

                # Check for recursion
                if reference in seen_entities:
                    raise XMLError(f"Infinite recursion within entity {reference}", source=xml)

                # Expand reference and parse as xml
                expansion_text = Helpers.parse_reference(reference,
                                                         general_entities=general_entities,
                                                         expand_parameter_entities=False)
                unparsed_xml = self.parse_xml_block(expansion_text, general_entities, seen_entities + [reference])

                # If there is any remaining unparsed xml, expansion text contains an unpaired end-tag so is ill-formed
                if len(unparsed_xml) > 0:
                    raise XMLError(f"Ill-formed expansion text for entity {reference}", source=xml)

                # Continue parsing
                xml = xml[reference_end + 1:]
                continue

            # Everything else is text
            xml = self.__parse_text(xml)

    """
        ==============
        TEXT HANDLING
        ==============
        These functions handle non-markup text within the element.
        
        To enable comments & entities to be handled by the `parse_xml_block` function without unnecessarily splitting
        text chunks into multiple Text objects, a single Text object is kept open and added to as more text is 
        parsed, instead of a newe object being created for each text chunk.
        This shared Text object is then closed and a new one created every time text in interrupted by a significant 
        piece of markup (processing instructions or child elements).
        
        For more details see the usage within the `parse_xml_block` function
    """

    def __parse_text(self, remaining_xml: str) -> str:
        """
            Adds the given text to the currently open Text block if there is one, or opens a new one if not.
            The Text class parses the text until it reaches some markup, and all xml after this markup is returned to
            the `parse_xml_block` function for handling
        """
        if not self.__current_text:
            self.__current_text = Text()

        remaining_xml = self.__current_text.add_text(remaining_xml)
        return remaining_xml

    def __close_current_text_block(self):
        """
            Closes the current text block, checks it for well-formedness issues & adds it to the list of this
            element's content.

            Called by `parse_xml_block` whenever it encounters a significant piece of markup which should punctuate
            two text blocks.
        """
        if self.__current_text:
            self.__current_text.check_wellformedness()
            self.content.append(self.__current_text)
            self.__current_text = None
