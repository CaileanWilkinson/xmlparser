from typing import Dict, Optional
from .Entity import Entity
from .XMLMarkup import XMLMarkup
from RegularExpressions import RegEx
from .Error import XMLError, DisallowedCharacterError


class ProcessingInstruction(XMLMarkup):
    """
        Represents a Processing Instruction embedded in the xml file. See xml spec ch2.6.
        General format:
        <?TARGET DATA?>
        TARGET represents the application this processing instruction is aimed at - see `target` property.
        DATA is an optional series of characters which are passed on to the application as-is - see `data` property.

        Processing Instructions are unique in that they can exist in both the DTD and the main xml content.
        I've elected to make this class a subclass of `XMLMarkup` and not `DTDMarkup` as the xml content is the
        primary, most significant portion of the document.

        My interpretation of the xml spec is that processing instruction data is not to be parsed by xml interpreters
        and so general / parameter / character references are not expanded within processing instructions.

        Arguments:
            target  The processing instruction's target, usually an indicator of who should respond to this PI
            data    The data associated with this processing instruction
    """
    def __init__(self, remaining_xml: str):
        """
        :param remaining_xml:   A block of xml code with a processing instruction beginning at index 0.
        """
        self.__raw_declaration = remaining_xml

        self.target = ""  # type: str
        self.data = None  # type: Optional[str]

    def parse_to_end(self, general_entities: Dict[str, Entity]) -> str:
        """
            Extracts the processing instruction from the beginning of the given xml (`self.__raw_declaration`)
            Returns the remaining xml after the end of the processing instruction unparsed

            Extracts PI target and data, and ensures:
            - PI is well-formed (starts with <?, ends with ?>)
            - Target conforms to xmlspec::Name
            - Data conforms to xmlspec::Char

        :param general_entities: Not used. Parameter exists for compatibility with other XMLMarkup subclasses
        :return: Unparsed xml occurring after the end of the processing instruction
        """
        remaining_xml = self.__raw_declaration[2:]

        # Find the end of the target
        target_end = RegEx.ProcessingInstruction_TargetEnd.search(remaining_xml)
        if not target_end:
            raise XMLError("Unable to find end of processing instruction", source=self.__raw_declaration)

        self.target = remaining_xml[:target_end.start()]
        remaining_xml = remaining_xml[target_end.end():]

        # Ensure target conforms to xmlspec::Name
        if not RegEx.Name.fullmatch(self.target):
            raise DisallowedCharacterError(self.target,
                                           "processing instruction target",
                                           conforms_to="Name",
                                           source=self.__raw_declaration)

        # Special case: no attached data
        if target_end.group() == "?>":
            return remaining_xml

        # Otherwise search for end
        end_index = remaining_xml.find("?>")
        if end_index == -1:
            raise XMLError("Unable to find end of processing instruction", source=self.__raw_declaration)

        # Remove leading whitespace
        whitespace = RegEx.Whitespace.match(remaining_xml)
        if whitespace:
            remaining_xml = remaining_xml[whitespace.end():]

        # Update the data
        self.data = remaining_xml[:end_index]
        remaining_xml = remaining_xml[end_index + 2:]

        # Check data conforms to xmlspec::CharSequence
        if not RegEx.CharSequence.fullmatch(self.data):
            raise DisallowedCharacterError(self.data,
                                           "processing instruction data",
                                           conforms_to="Name",
                                           source=self.__raw_declaration)

        # Return the remaining xml for future processing
        return remaining_xml
