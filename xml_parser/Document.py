import re
import string
from typing import List, Dict, Optional

from xml_parser.regular_expressions import RegEx
from xml_parser.dtd.DTD import DTD, DTDFactory
from xml_parser.content.Comment import CommentFactory
from xml_parser.dtd.Entity import Entity
from xml_parser.errors import XMLError, DisallowedCharacterError
from xml_parser.content.ProcessingInstruction import ProcessingInstruction, ProcessingInstructionFactory
from xml_parser.content.Element import Element, ElementFactory
from xml_parser.dtd.Notation import Notation


class Document:
    def __init__(self, xml):
        self.xml = xml

        self.version = None  # type: Optional[str]
        self.encoding = None  # type: Optional[str]
        self.standalone = None  # type: Optional[bool]

        self.__dtd = None  # type: Optional[DTD]
        self.entities = {}  # type: Dict[str, Entity]
        self.notations = {}  # type: Dict[str, Notation]

        self.dtd_processing_instructions = []  # type: List[ProcessingInstruction]
        self.leading_processing_instructions = []  # type: List[ProcessingInstruction]
        self.trailing_processing_instructions = []  # type: List[ProcessingInstruction]

        self.file = None  # type: Element

    def _set_dtd(self, dtd: DTD):
        """
            Allows me to keep the DTD private in Document but settable from the DocumentFactory
        """
        # Store dtd for future validation
        self.__dtd = dtd

        # Copy data below into Document instance for client app to reference
        self.notations = dtd.notations
        self.entities = dtd.general_entities
        self.dtd_processing_instructions = dtd.processing_instructions


class DocumentFactory:
    """
        Builds a Document instance from the provided xml
    """
    @staticmethod
    def parse_from_xml(xml: str, file: str, encoding: str) -> Document:
        # Start building document
        document = Document(xml)
        document.file = file
        document.encoding = encoding

        # Parse the XML Declaration
        whitespace = RegEx.Whitespace.match(xml)
        if xml[:5] == "<?xml":
            xml = DocumentFactory.parse_xml_declaration_into_document(xml, document)
        elif whitespace and xml[whitespace.end(): whitespace.end() + 5] == "<?xml":
            raise XMLError("Illegal whitespace before xml declaration", source=xml)

        # Parse misc items
        document.leading_processing_instructions, xml = DocumentFactory.parse_misc(xml, None)

        # Parse the DTD
        if xml[:9] == "<!DOCTYPE":
            dtd, xml = DTDFactory.parse_from_xml(xml, document.file, document.encoding)
            document._set_dtd(dtd)
        else:
            dtd = DTDFactory.empty(document.file, document.encoding)

        # Parse misc items
        processing_instructions, xml = DocumentFactory.parse_misc(xml, dtd)
        document.leading_processing_instructions += processing_instructions

        # Parse the root element
        if xml[:1] == "<":
            document.file, xml = ElementFactory.parse_from_xml(xml, dtd)
        else:
            raise XMLError("Unable to find root element in xml document", source=document.xml)

        # Parse misc items
        document.trailing_processing_instructions, xml = DocumentFactory.parse_misc(xml, dtd)

        # If there is any remaining xml, throw error
        if len(xml) != 0:
            raise XMLError("Illegal extra content after root element", source=xml)

        return document

    @staticmethod
    def parse_misc(xml: str, dtd: Optional[DTD]) -> (List[ProcessingInstruction], str):
        processing_instructions = []

        while True:
            # Strip whitespace
            whitespace = RegEx.Whitespace.match(xml)
            if whitespace:
                xml = xml[whitespace.end():]

            # Processing instructions
            if xml[:2] == "<?":
                processing_instruction, xml = ProcessingInstructionFactory.parse_from_xml(xml, dtd)
                processing_instructions.append(processing_instruction)
                continue

            # Comments
            if xml[:4] == "<!--":
                xml = CommentFactory.parse_from_xml(xml, dtd)
                continue

            # Otherwise return non-misc xml
            return processing_instructions, xml

    """
        ================
        XML DECLARATION
        ================
    """

    @staticmethod
    def parse_xml_declaration_into_document(xml: str, document: Document) -> str:
        """
            XMLDecl ::== '<?xml' VersionInfo EncodingDecl? SDDecl? S? '?>'
            VersionInfo ::== S 'version' Eq Qt ('1.' [0-9]+) Qt
            EncodingDecl ::== S 'encoding' Eq Qt EncName Qt
            SDDecl ::== S 'standalone' Eq Qt ('yes' | 'no') Qt
        """
        source = xml
        xml = xml[5:]

        # Parse version info
        document.version, xml = DocumentFactory.parse_version_info(xml, source=source)

        # Parse encoding info (accept whitespace as optional to enable more descriptive errors)
        is_encoding_declaration = re.match(f"({RegEx.whitespace})?encoding", xml)
        if is_encoding_declaration:
            document.encoding, xml = DocumentFactory.parse_encoding_info(xml, source=source)

        # Parse standalone info
        is_standalone_declaration = re.match(f"({RegEx.whitespace})?standalone", xml)
        if is_standalone_declaration:
            document.standalone, xml = DocumentFactory.parse_standalone_info(xml, source=source)

        # Strip optional whitespace
        whitespace = RegEx.Whitespace.match(xml)
        if whitespace:
            xml = xml[whitespace.end():]

        # XML declaration must end on '?>'
        if xml[:2] != "?>":
            raise XMLError("Illegal extra content at end of xml declaration", source=xml)

        return xml[2:]

    @staticmethod
    def parse_version_info(xml: str, source: str) -> (str, str):
        """
            VersionInfo ::== S 'version' Eq Qt ('1.' [0-9]+) Qt
        """
        # Version info must begin with whitespace
        whitespace = RegEx.Whitespace.match(xml)
        if not whitespace:
            raise XMLError("Missing whitespace before xml version declaration", source=xml)
        xml = xml[whitespace.end():]

        # Must have keyword 'version'
        if xml[:7] != "version":
            raise XMLError("XML declaration must declare xml version", source=source)
        xml = xml[7:]

        # Remove the equality
        equality = RegEx.Eq.match(xml)
        if not equality:
            raise XMLError("Illegal content before '=' in version declaration", source=xml)
        xml = xml[equality.end():]

        # Parse the version
        delimiter = xml[:1]
        if delimiter not in "\'\"":
            raise XMLError("XML version declaration must be delimited by \' or \"", source=source)
        version_end = xml.find(delimiter, 1)
        version = xml[1: version_end]
        xml = xml[version_end + 1:]

        # Version must be 1.x
        if version[:2] != "1.":
            raise XMLError("Invalid XML Version: must be 1.x", source=source)
        for char in version[2:]:
            if char not in string.digits:
                raise XMLError("Invalid XML Version: must be 1.x", source=source)

        return version, xml

    @staticmethod
    def parse_encoding_info(xml: str, source: str) -> (str, str):
        """
            EncodingDecl ::== S 'encoding' Eq Qt EncName Qt
        """
        # Encoding declaration must begin with whitespace
        whitespace = RegEx.Whitespace.match(xml)
        if not whitespace:
            raise XMLError("Missing whitespace before xml encoding declaration", source=xml)
        xml = xml[whitespace.end():]

        # Remove the equality
        equality = RegEx.Eq.search(xml)
        if not equality:
            raise XMLError("Illegal content before '=' in encoding declaration", source=xml)
        xml = xml[equality.end():]

        # Parse the encoding
        delimiter = xml[:1]
        if delimiter not in "\'\"":
            raise XMLError("XML encoding declaration must be delimited by \' or \"", source=source)
        encoding_end = xml.find(delimiter, 1)
        encoding = xml[1: encoding_end]
        xml = xml[encoding_end + 1:]

        # Encoding must match xmlspec::EncName
        if not RegEx.Encoding.fullmatch(encoding):
            raise DisallowedCharacterError(encoding,
                                           "document encoding declaration",
                                           conforms_to="Encoding",
                                           source=source)

        return encoding, xml

    @staticmethod
    def parse_standalone_info(xml: str, source: str) -> (Optional[bool], str):
        """
            SDDecl ::== S 'standalone' Eq Qt ('yes' | 'no') Qt
        """
        # Standalone declaration must begin with whitespace
        whitespace = RegEx.Whitespace.match(xml)
        if not whitespace:
            raise XMLError("Missing whitespace before xml standalone declaration", source=xml)
        xml = xml[whitespace.end():]

        # Remove the equality
        equality = RegEx.Eq.search(xml)
        if not equality:
            raise XMLError("Illegal content before '=' in standalone declaration", source=xml)
        xml = xml[equality.end():]

        # Parse the standalone declaration
        delimiter = xml[:1]
        if delimiter not in "\'\"":
            raise XMLError("XML standalone declaration must be delimited by \' or \"", source=source)
        sd_end = xml.find(delimiter, 1)
        standalone = xml[1: sd_end]
        xml = xml[sd_end + 1:]

        # Standalone must be 'yes' or 'no'
        if standalone not in ["yes", "no"]:
            raise XMLError("Invalid value for standalone declaration. Must be 'yes' or 'no'", source=source)

        return (standalone == "yes"), xml
