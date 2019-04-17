import re
from RegularExpressions import RegEx
import Helpers
from .Error import XMLError, DisallowedCharacterError


class Text:
    """
        Represents a chunk of text between xml markup elements. See xml spec ch2.4.

        todo - describe how this class works
    """

    def __init__(self):
        self.text = ""  # type: str

    def add_text(self, xml) -> str:
        """
            Parses the given xml until it reaches a markup, and adds the preceeding text to this class.

            Parses up until an element tag, comment, processing instruction or general entity,
            then returns the markup and following xml unparsed to be handled by the parent element.

            Appends all the text before the markup to this class's text property, and:
                - removes & skips past CDATA tags
                - expands character references
                - ensures no ']]>' in character data
                - todo - Ensure each piecewise chunk of text conforms to xmlspec::Char?
        """
        # Keep parsing text until we reach a non-text element
        while True:
            # Jump to the next interesting character
            match = re.search("[<&\\]]", xml)
            # If there are no more interesting characters, append all
            if not match:
                self.text += xml
                return ""
            index = match.start()

            # Handle jumped text
            self.text += xml[:index]
            xml = xml[index:]

            # CDATA
            if xml[:9] == "<![CDATA[":
                # Skip to the end of the cdata section
                end_index = xml.find("]]>")
                if end_index == -1:
                    raise XMLError("Unable to find end of CDATA section", source=xml)
                self.text += xml[9:end_index]
                xml = xml[end_index + 3:]
                continue

            # Expand character references
            if xml[:2] == "&#":
                # Isolate reference
                end_index = xml.find(";")
                if end_index == -1:
                    raise XMLError("Unable to find end of character reference", source=xml)
                reference = xml[:end_index + 1]

                # Fetch expansion text
                expansion_text = Helpers.parse_reference(reference,
                                                         expand_general_entities=False,
                                                         expand_parameter_entities=False)

                # Append expansion it to text
                self.text += expansion_text
                xml = xml[end_index + 1:]
                continue

            # Disallow CDATA end tags in normal text
            if xml[:3] == "]]>":
                raise XMLError("Disallowed sequence ']]>' in text", source=xml)

            # Allow ']' if it is not part of above pattern
            elif xml[:1] == "]":
                self.text += xml[:1]
                xml = xml[1:]
                continue

            # Otherwise pass control back up to parent element to handle xml markup
            return xml

    def check_wellformedness(self):
        """
            Ensures that the accumulated text conforms to xmlspec::Char
        """
        # Check text conforms to xmlspec::Char
        if not RegEx.CharSequence.fullmatch(self.text):
            raise DisallowedCharacterError(self.text, "text", conforms_to="Char", source=None)
