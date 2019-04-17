import string
from typing import List, Dict, Optional

from ...Helpers import parse_reference
from ...RegularExpressions import RegEx
from ..content.Comment import Comment
from .Entity import Entity
from ..Error import XMLError
from ..content.ProcessingInstruction import ProcessingInstruction
from ..content.Element import Element


# todo - Rewrite me: I'm a mess.
class Document:
    def __init__(self, raw: str):
        self.__raw = raw

        self.version = None  # type: Optional[str]
        self.encoding = None  # type: Optional[str]
        self.standalone = None  # type: Optional[bool]

        self.dtd_name = None  # type: Optional[str]
        self.external_public_uri = None  # type: Optional[str]
        self.external_system_uri = None  # type: Optional[str]

        self.general_entities = {}  # type: Dict[str, Entity]
        self.parameter_entities = {}  # type: Dict[str, Entity]
        self.__load_initial_entities()

        self.processing_instructions = []  # type: List[ProcessingInstruction]
        self.root = None  # type: Optional[Element]

    def __load_initial_entities(self):
        """
            Loads the initial set of entities (lt, gt, amp, apos, quot)
        """
        lt = Entity('<!ENTITY lt "&#38;#60;">')
        lt.parse_to_end({})
        self.general_entities["lt"] = lt
        gt = Entity('<!ENTITY gt "&#62;">')
        gt.parse_to_end({})
        self.general_entities["gt"] = gt
        amp = Entity('<!ENTITY amp "&#38;#38;">')
        amp.parse_to_end({})
        self.general_entities["amp"] = amp
        apos = Entity('<!ENTITY apos "&#39;">')
        apos.parse_to_end({})
        self.general_entities["apos"] = apos
        quot = Entity('<!ENTITY quot "&#34;"    >')
        quot.parse_to_end({})
        self.general_entities["quot"] = quot

    def parse(self):
        remaining_xml = self.__raw
        # Strip whitespace
        whitespace = RegEx.Whitespace.match(remaining_xml)
        if whitespace:
            remaining_xml = remaining_xml[whitespace.end():]

        # Parse the XML Declaration
        if remaining_xml[:5] == "<?xml":
            remaining_xml = self.__parse_xml_declaration(remaining_xml)

        # Parse misc items
        remaining_xml = self.__parse_misc(remaining_xml)

        # Parse the DTD
        if remaining_xml[:9] == "<!DOCTYPE":
            remaining_xml = self.__parse_doctype_declaration(remaining_xml)

        # Parse misc items
        remaining_xml = self.__parse_misc(remaining_xml)

        # Parse the root element
        if remaining_xml[:1] == "<":
            self.root = Element(remaining_xml)
            remaining_xml = self.root.parse_to_end(self.general_entities)
        else:
            raise XMLError()

        # Parse misc items
        remaining_xml = self.__parse_misc(remaining_xml)

        # If there is any remaining xml, throw error
        if len(remaining_xml) != 0:
            raise XMLError()

    """
        ================
        XML Declaration
        ================
    """

    def __parse_xml_declaration(self, remaining_xml: str) -> str:
        # --- XML DECLARATION OPENING --- #
        # Strip opening fluff
        remaining_xml = remaining_xml[5:]

        # Strip whitespace
        whitespace = RegEx.Whitespace.match(remaining_xml)
        if not whitespace:
            raise XMLError()
        remaining_xml = remaining_xml[whitespace.end():]

        # Parse the version info
        remaining_xml = self.__parse_version_info(remaining_xml)

        # --- ENCODING DECLARATION --- #
        # Strip whitespace
        whitespace = RegEx.Whitespace.match(remaining_xml)
        if whitespace:
            remaining_xml = remaining_xml[whitespace.end():]

        if remaining_xml[:8] == "encoding":
            remaining_xml = remaining_xml[8:]
            # If an encoding string is present, whitespace is mandatory
            if not whitespace:
                raise XMLError()

            # Parse the encoding
            remaining_xml = self.__parse_encoding_declaration(remaining_xml)

            # Strip whitespace
            whitespace = RegEx.Whitespace.match(remaining_xml)
            if whitespace:
                remaining_xml = remaining_xml[whitespace.end():]

        # --- STANDALONE DECLARATION --- #
        if remaining_xml[:10] == "standalone":
            remaining_xml = remaining_xml[10:]
            # If standalone declaration is present whitespace is mandatory
            if not whitespace:
                raise XMLError()

            # Parse standalone declaration
            remaining_xml = self.__parse_standalone_declaration(remaining_xml)

            # Strip whitespace
            whitespace = RegEx.Whitespace.match(remaining_xml)
            if whitespace:
                remaining_xml = remaining_xml[whitespace.end():]

        # --- XML DECLARATION CLOSE -->
        if remaining_xml[:2] != "?>":
            raise XMLError()

        return remaining_xml[2:]

    def __parse_version_info(self, remaining_xml: str) -> str:
        if remaining_xml[:7] != "version":
            raise XMLError()
        remaining_xml = remaining_xml[7:]

        # Remove equality
        equality = RegEx.Eq.match(remaining_xml)
        if not equality:
            raise XMLError()
        remaining_xml = remaining_xml[equality.end():]

        # Parse version
        delimiter = remaining_xml[0]
        if delimiter not in "\'\"":
            raise XMLError()
        end_index = remaining_xml.find(delimiter, 1)
        self.version = remaining_xml[1: end_index]
        remaining_xml = remaining_xml[end_index + 1:]

        # Ensure version is 1.x
        if self.version[:2] != "1.":
            raise XMLError()
        for char in self.version[2:]:
            if char not in string.digits:
                raise XMLError()

        # Return unparsed xml
        return remaining_xml

    def __parse_encoding_declaration(self, remaining_xml: str) -> str:
        # Remove equality
        equality = RegEx.Eq.match(remaining_xml)
        if not equality:
            raise XMLError()
        remaining_xml = remaining_xml[equality.end():]

        # Parse encoding
        delimiter = remaining_xml[0]
        if delimiter not in "\'\"":
            raise XMLError()
        end_index = remaining_xml.find(delimiter, 1)
        self.encoding = remaining_xml[1: end_index]
        remaining_xml = remaining_xml[end_index + 1:]

        # todo - Ensure encoding is valid?

        # Return the unparsed xml
        return remaining_xml

    def __parse_standalone_declaration(self, remaining_xml: str) -> str:
        # Remove equality
        equality = RegEx.Eq.match(remaining_xml)
        if not equality:
            raise XMLError()
        remaining_xml = remaining_xml[equality.end():]

        # Parse standalone
        delimiter = remaining_xml[0]
        if delimiter not in "\'\"":
            raise XMLError()
        end_index = remaining_xml.find(delimiter, 1)
        standalone = remaining_xml[1: end_index]
        remaining_xml = remaining_xml[end_index + 1:]

        # Ensure standalone is valid
        if standalone == "no":
            self.standalone = False
        elif standalone == "yes":
            self.standalone = True
        else:
            raise XMLError()

        # Return the unparsed xml
        return remaining_xml

        # Return the unparsed xml

    """
        ================
        DTD Declaration
        ================
    """

    def __parse_doctype_declaration(self, remaining_xml: str) -> str:
        # todo - this is a complete mess. Refactor me :(

        # --- DTD OPENING --- #
        # Strip opening fluff
        remaining_xml = remaining_xml[9:]

        # Strip whitespace
        whitespace = RegEx.Whitespace.match(remaining_xml)
        if not whitespace:
            raise XMLError()
        remaining_xml = remaining_xml[whitespace.end():]

        # Parse the root name
        name_end = RegEx.DTD_NameEnd.search(remaining_xml)
        if not name_end:
            raise XMLError()
        self.dtd_name = remaining_xml[:name_end.start()]
        remaining_xml = remaining_xml[name_end.end():]

        # Ensure root name is well formed
        if not RegEx.Name.fullmatch(self.dtd_name):
            raise XMLError()

        # For DTDs without an external subset
        if "[" in name_end.group():
            remaining_xml = self.__parse_subset(remaining_xml)
            # Ensure internal subset ends on ']'
            if remaining_xml[:1] != "]":
                raise XMLError()
            remaining_xml = remaining_xml[1:]
            # Strip whitespace
            whitespace = RegEx.Whitespace.match(remaining_xml)
            if whitespace:
                remaining_xml = remaining_xml[whitespace.end():]
            if remaining_xml[0] != ">":
                raise XMLError
            return remaining_xml[1:]

        # For DTDs without any subset
        if ">" in name_end.group():
            return remaining_xml[1:]

        # For DTDs with an external subset
        # Get the external uri type
        whitespace = RegEx.Whitespace.search(remaining_xml)
        if not whitespace:
            raise XMLError
        external_type = remaining_xml[:whitespace.start()]
        if external_type not in ["SYSTEM", "PUBLIC"]:
            raise XMLError
        remaining_xml = remaining_xml[whitespace.end():]

        # Get the first URI delimiter
        delimiter = remaining_xml[0]
        if delimiter not in "\"\'":
            raise XMLError
        # Isolate the first URI
        end_index = remaining_xml.find(delimiter, 1)
        uri = remaining_xml[1: end_index]
        remaining_xml = remaining_xml[end_index + 1:]
        # Ensure uri conforms to xmlspec::Char
        if not RegEx.CharSequence.fullmatch(uri):
            raise XMLError()
        # If this is a PUBLIC external entity, look for another uri
        if external_type == "PUBLIC":
            self.external_public_uri = uri
            # Strip leading whitespace
            whitespace = RegEx.Whitespace.match(remaining_xml)
            if whitespace:
                remaining_xml = remaining_xml[whitespace.end():]
            # Get the second URI delimiter
            delimiter = remaining_xml[0]
            if delimiter not in "\"\'":
                raise XMLError
            # Isolate the second URI
            end_index = remaining_xml.find(delimiter, 1)
            self.external_system_uri = remaining_xml[1: end_index]
            remaining_xml = remaining_xml[end_index + 1:]
            # Ensure uri conforms to xmlspec::Char
            if not RegEx.CharSequence.fullmatch(self.external_system_uri):
                raise XMLError()
        # If this is a SYSTEM external entity, there is no other uri
        elif external_type == "SYSTEM":
            self.external_system_uri = uri

        # todo - fetch and parse the external subset

        # Strip whitespace
        whitespace = RegEx.Whitespace.match(remaining_xml)
        if whitespace:
            remaining_xml = remaining_xml[whitespace.end():]

        # If there is an internal subset parse that
        if remaining_xml[0] == "[":
            remaining_xml = self.__parse_subset(remaining_xml[1:])
            if remaining_xml[:1] != "]":
                raise XMLError()
            remaining_xml = remaining_xml[1:]

        # Strip whitespace & return
        whitespace = RegEx.Whitespace.match(remaining_xml)
        if whitespace:
            remaining_xml = remaining_xml[whitespace.end():]
        if remaining_xml[0] != ">":
            raise XMLError
        return remaining_xml[1:]

    def __parse_subset(self, xml: str, seen_entities: List[str] = None) -> str:
        """
            Parses the given xml block as a subset until it is finished or we reach the end of the subset (])
        """
        # Fix default parameters
        if seen_entities is None:
            seen_entities = []

        # Parse xml block
        while True:
            # Strip whitespace
            whitespace = RegEx.Whitespace.match(xml)
            if whitespace:
                xml = xml[whitespace.end():]

            # If the xml block is exhausted
            if len(xml) == 0:
                return xml

            # If we've reached the end of the internal subset
            if xml[:1] == "]":
                return xml

            # Expand and parse general entities in isolation from existing xml block
            if xml[:1] == "%":
                # Get reference
                reference_end = xml.find(";")
                if reference_end == -1:
                    raise XMLError()
                reference = xml[:reference_end + 1]

                # Check for recursion
                if reference in seen_entities:
                    raise XMLError()

                # Expand and parse reference
                expansion_text = parse_reference(reference,
                                                         parameter_entities=self.parameter_entities,
                                                         expand_general_entities=False)
                unparsed_xml = self.__parse_subset(expansion_text, seen_entities + [reference])

                # If there is any remaining unparsed xml, expansion text must be ill formed so raise error
                if len(unparsed_xml) > 0:
                    raise XMLError()

                # Continue parsing
                xml = xml[reference_end + 1:]
                continue

            # Processing Instructions
            if xml[:2] == "<?":
                processing_instruction = ProcessingInstruction(xml)
                xml = processing_instruction.parse_to_end({})
                self.processing_instructions.append(processing_instruction)
                # todo - maintain PI position somehow
                continue

            # Comments
            if xml[:4] == "<!--":
                comment = Comment(xml)
                xml = comment.parse_to_end({})
                continue

            # Entity declaration
            if xml[:8] == "<!ENTITY":
                xml = self.__parse_entity_declaration(xml)
                continue

            # Element declaration
            if xml[:9] == "<!ELEMENT":
                xml = self.__parse_element_declaration(xml)
                continue

            # Attribute declaration
            if xml[:9] == "<!ATTLIST":
                xml = self.__parse_attributelist_declaration(xml)
                continue

            # Notation declaration
            if xml[:8] == "<!NOTATION":
                xml = self.__parse_notation_declaration(xml)
                continue

            # Anything else is a WF error
            else:
                raise XMLError()

    def __parse_entity_declaration(self, remaining_xml: str) -> str:
        entity = Entity(remaining_xml)
        remaining_xml = entity.parse_to_end(self.parameter_entities)
        if entity.type == Entity.Type.GENERAL and entity.name not in self.general_entities.keys():
            self.general_entities[entity.name] = entity
        if entity.type == Entity.Type.PARAMETER and entity.name not in self.parameter_entities.keys():
            self.parameter_entities[entity.name] = entity
        return remaining_xml

    def __parse_element_declaration(self, remaining_xml: str) -> str:
        # Ignore Element declarations (we are not yet validating)
        end_index = remaining_xml.find(">")
        return remaining_xml[end_index + 1:]

    def __parse_attributelist_declaration(self, remaining_xml: str) -> str:
        # Ignore attlist declarations (we are not yet validating)
        index = 0
        while True:
            if index > len(remaining_xml):
                raise XMLError()
            char = remaining_xml[index]

            # Skip to end of strings
            if char in "\'\"":
                delimiter = char
                index = remaining_xml.find(delimiter, index + 1) + 1
                continue

            # If this is the end of the attribute list
            if char == ">":
                return remaining_xml[index + 1:]

            # Otherwise move on to next char
            index += 1

    def __parse_notation_declaration(self, remaining_xml: str) -> str:
        # Ignore notation declarations (we are not yet validating)
        end_index = remaining_xml.find(">")
        return remaining_xml[end_index + 1:]

    """
        =====
        MISC
        =====
    """

    def __parse_misc(self, remaining_xml: str) -> str:
        while True:
            # Strip whitespace
            whitespace = RegEx.Whitespace.match(remaining_xml)
            if whitespace:
                remaining_xml = remaining_xml[whitespace.end():]

            # Processing instruction
            if remaining_xml[:2] == "<?":
                processing_instruction = ProcessingInstruction(remaining_xml)
                remaining_xml = processing_instruction.parse_to_end({})
                self.processing_instructions.append(processing_instruction)
                continue

            # Comments
            if remaining_xml[:4] == "<!--":
                comment = Comment(remaining_xml)
                remaining_xml = comment.parse_to_end({})
                continue

            # Otherwise return non-misc xml
            return remaining_xml
