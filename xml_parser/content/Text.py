import re
from typing import Optional

from xml_parser.dtd.DTD import DTD
from xml_parser.regular_expressions import RegEx
from xml_parser.helpers import parse_character_reference
from ..errors import XMLError, DisallowedCharacterError


class Text:
    """
        Represents a chunk of character data in an xml element's content

        See xml spec ch 2.4 for specific details.
    """

    def __init__(self, text: str):
        self.text = text


class TextFactory:
    def __init__(self, dtd: DTD):
        self.__text = ""
        self.dtd = dtd

    def pop_text_object(self) -> Optional[Text]:
        """
            Removes the current Text object from the stack and returns it.

            todo - write me :(
        """
        if not self.__text:
            return None

        # Text must conform to xmlspec::Char*
        if not RegEx.CharSequence.fullmatch(self.__text):
            raise DisallowedCharacterError(self.__text, "text", conforms_to="Char", source=None)

        text_object = Text(self.__text)
        self.__text = ""

        return text_object

    def add_text(self, xml) -> str:
        """
            todo - rewrite this :/
            Parses the given xml until it reaches a markup, and adds the text to this class.

            Parses up until an element tag, comment, processing instruction or general entity,
            then returns the markup and following xml unparsed to be handled by the parent element.

            Appends all the text before the markup to this class's text property, and:
                - removes & skips past CDATA tags
                - expands character references
                - ensures no ']]>' in character data
                - todo - Ensure each piecewise chunk of text conforms to xmlspec::Char?
        """
        source = xml

        # Keep parsing text until we reach a non-text element
        while True:
            # Jump to the next interesting character (markup chars: &, ], <)
            match = re.search(r"[<&\]]", xml)

            # If there are no more interesting characters, add all remaining text
            if not match:
                self.__text += xml
                return ""

            # Add jumped text
            self.__text += xml[:match.start()]
            xml = xml[match.start():]

            # Skip cdata sections
            if xml[:9] == "<![CDATA[":
                text, xml = TextFactory.parse_cdata_section(xml)
                self.__text += text
                continue

            # Expand character references
            if xml[:2] == "&#":
                character, xml = parse_character_reference(xml)
                self.__text += character
                continue

            # Disallow cdata end tags in normal text
            if xml[:3] == "]]>":
                raise XMLError("Disallowed sequence ']]>' in text", source=source)

            # Allow ']' if it is not part of above pattern
            if xml[:1] == "]":
                self.__text += "]"
                xml = xml[1:]
                continue

            # Otherwise pass control back up to parent element to handle xml markup
            return xml

    @staticmethod
    def parse_cdata_section(xml: str) -> (str, str):
        cdata_end = xml.find("]]>")
        if cdata_end == -1:
            raise XMLError("Unable to find end of CDATA section", source=xml)

        text = xml[9: cdata_end]
        xml = xml[cdata_end + 3:]

        return text, xml
