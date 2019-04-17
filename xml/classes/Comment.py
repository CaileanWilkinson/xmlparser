from typing import Dict

from RegularExpressions import RegEx
from .Entity import Entity
from .XMLMarkup import XMLMarkup
from .Error import XMLError, DisallowedCharacterError


class Comment(XMLMarkup):
    """
        Represents a Comment embedded in the xml file. See xml spec ch2.5.
        General format:
        <!--TEXT-->

        This is a placeholder class to enable Comments to be handled by the XMLMarkup superclass and element content
        parsing in the same way as other xml markup and so avoid boilerplate code.

        Ensures Comments are well-formed but does not extract any information. Comment instances are discarded by the
        containing class immediately and are never passed to the client application.
    """

    def __init__(self, remaining_xml: str):
        """
        :param remaining_xml:A block of xml code with a comment beginning at index 0.
        """
        self.__raw_declaration = remaining_xml

    def parse_to_end(self, general_entities: Dict[str, Entity]):
        """
            Removes the comment from the beginning of the given xml and returns the rest for future processing.

            Does not extract any information about the comment, but ensures:
            - Comment is well-formed (starts with <!--, ends with -->)
            - Comment text conforms to xmlspec::Char
            - Comment doesn't contain disallowed sequence '--' or end with '-->'

        :param general_entities: Not used. Parameter exists for compatibility with other XMLMarkup subclasses
        :return: Unparsed xml occurring after the end of the comment
        """
        remaining_xml = self.__raw_declaration

        # Find the closing tag
        end_index = remaining_xml.find("-->")
        if end_index == -1:
            raise XMLError("Unable to find end of comment", source=remaining_xml)

        # Check comment conforms to xmlspec::Char
        if not RegEx.CharSequence.fullmatch(remaining_xml[:end_index]):
            raise DisallowedCharacterError(remaining_xml[:end_index + 3], "comment", conforms_to="Char", source=None)

        # Check comment doesn't contain --
        if "--" in remaining_xml[4: end_index]:
            raise DisallowedCharacterError(remaining_xml[:end_index + 3], "comment", conforms_to="--", source=None)

        # Check comment doesn't end on --->
        if remaining_xml[end_index - 1] == "-":
            raise XMLError("Comments may not end with '--->'", source=remaining_xml[:end_index + 3])

        return remaining_xml[end_index + 3:]
