import re
from typing import Optional
from xml_parser.dtd.DTD import DTD
from xml_parser.regular_expressions import RegEx
from ..errors import XMLError, DisallowedCharacterError


class ProcessingInstruction:
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
    def __init__(self, dtd: DTD):
        self.__dtd = dtd

        self.target = ""  # type: str
        self.data = None  # type: Optional[str]


class ProcessingInstructionFactory:
    @staticmethod
    def parse_from_xml(xml: str, dtd: DTD) -> (ProcessingInstruction, str):
        """
            PI	::=	'<?' PITarget (S (Char* - (Char* '?>' Char*)))? '?>'
        """
        processing_instruction = ProcessingInstruction(dtd)

        # Strip leading fluff
        source = xml
        xml = xml[2:]

        # Parse the processing instruction
        processing_instruction.target, xml = ProcessingInstructionFactory.parse_target(xml, source)
        processing_instruction.data, xml = ProcessingInstructionFactory.parse_data(xml, source)

        return processing_instruction, xml

    @staticmethod
    def parse_target(xml: str, source: str) -> (str, str):
        # PI Target ends with either whitespace or '?>'
        target_end = re.search(f"({RegEx.whitespace})|\\?>", xml)
        if not target_end:
            raise XMLError("Unable to find end of processing instruction", source=source)

        target = xml[:target_end.start()]
        xml = xml[target_end.start():]

        # Target must conform to xmlspec::Name
        if not RegEx.Name.fullmatch(target):
            raise DisallowedCharacterError(target, "processing instruction target",
                                           conforms_to="Name",
                                           source=source)

        return target, xml

    @staticmethod
    def parse_data(xml: str, source: str) -> (Optional[str], str):
        # If PI immediately closes, there is no data
        if xml[:2] == "?>":
            return None, xml[2:]

        # Strip whitespace
        whitespace = RegEx.Whitespace.match(xml)
        xml = xml[whitespace.end():]

        # Data is everything up to close of the PI
        end_index = xml.find("?>")
        if end_index == -1:
            raise XMLError("Unable to find end of processing instruction", source=source)

        data = xml[:end_index]
        xml = xml[end_index + 2:]

        # Data must conforms to xmlspec::Char*
        if not RegEx.CharSequence.fullmatch(data):
            raise DisallowedCharacterError(data, "processing instruction data",
                                           conforms_to="Name",
                                           source=source)

        return data, xml
