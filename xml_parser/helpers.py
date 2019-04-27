# todo - Module docstring
import os
import re
from typing import List, Optional, Any

from xml_parser.dtd.DTD import DTD
from .regular_expressions import RegEx
from .errors import XMLError, DisallowedCharacterError

"""
    =============
    TEXT PARSING    
    =============
"""


def parse_character_reference(xml: str) -> (str, str):
    reference_end = xml.find(";") + 1
    if reference_end == 0:
        raise XMLError("Unable to find end of character reference", source=xml)

    reference = xml[:reference_end]
    xml = xml[reference_end:]

    try:
        # Isolate the character code
        if reference[2:3] == "x":
            character_code = int(reference[3:-1], 16)
        else:
            character_code = int(reference[2:-1])

        # Convert the character code to a character
        return chr(character_code), xml

    # If unable to convert character code to a char
    except ValueError:
        raise XMLError(f"Invalid character reference {reference}", source=xml)


def expand_parameter_entity_references(text: str,
                                       dtd: DTD,
                                       source: str,
                                       entity_chain: List[str] = []) -> str:
    """
        Expands all parameter entities in the given text.
        For use parsing external subsets
    """
    expanded_text = ""

    # Iterate through all parameter entity references
    last_index = 0
    for match in re.finditer("%.*?;", text):
        reference = match.group()

        # Append skipped text
        expanded_text += text[last_index: match.start()]
        last_index = match.end()

        # Check for parameter entity recursion
        if reference in entity_chain:
            raise XMLError(f"Recursion within entities is prohibited "
                           f"(reference loop in {reference})")

        entity = dtd.parameter_entities.get(reference[1:-1], None)
        if not entity:
            raise XMLError(f"Reference to undeclared entity {reference}", source)

        # Expand PEs recursively before appending
        expanded_text += expand_parameter_entity_references(f" {entity.expansion_text} ", dtd,
                                                            source, entity_chain)

    # Append final text (after last reference) unless it contains unescaped '&' or '%'
    expanded_text += text[last_index:]

    return expanded_text


def expand_parameter_entity_reference(text: str,
                                      dtd: DTD,
                                      source: str,
                                      entity_chain: List[str] = []) -> str:
    """
        Expands a single parameter entity at the start of the given text.
        For use parsing external subsets
    """
    match = re.match(f"{RegEx.optional_whitespace}(%.*?;)", text)
    if not match:
        raise XMLError("Unable to find end of parameter entity reference", source=text)
    reference = match.group(1)

    # Check for parameter entity recursion
    if reference in entity_chain:
        raise XMLError(f"Recursion within entities is prohibited "
                       f"(reference loop in {reference})")

    entity = dtd.parameter_entities.get(reference[1:-1], None)
    if not entity:
        raise XMLError(f"Reference to undeclared entity {reference}", source)

    # Expand all PEs recursively
    expansion_text = expand_parameter_entity_references(entity.expansion_text, dtd, source,
                                                        entity_chain + [reference])
    xml = " " + expansion_text + " " + text[match.end():]

    return xml


def parse_parameter_entity_reference(text: str,
                                     dtd: DTD,
                                     source: str) -> (Any, str, str):  # Any = Entity
    """
        Parses a single parameter entity at the start of the given text.
        Returns the PE name, unparsed expansion text and remaining xml
    """
    match = re.match("%.*?;", text)
    if not match:
        raise XMLError("Unable to find end of parameter entity reference", source=text)
    reference = match.group()

    entity = dtd.parameter_entities.get(reference[1:-1], None)
    if not entity:
        raise XMLError(f"Reference to undeclared entity {reference}", source)

    return entity, f" {entity.expansion_text} ", text[match.end():]

"""
    ============
    URI PARSING    
    ============
"""


def parse_external_reference(xml: str,
                             dtd: Optional[DTD] = None,
                             look_for_notation: bool = True,
                             require_full_public_exp: bool = True,
                             allow_parameter_entities: bool = True
                             ) -> (Optional[str], Optional[str], Optional[str], str):
    """
       Returns (remaining_xml, public, system, notation)

       todo - TESTS!! And this is also a mess :(
    """
    # The URI type (system or public) runs up to the next whitespace
    whitespace = RegEx.Whitespace.search(xml)
    if not whitespace:
        raise XMLError("Unable to parse type of external resource reference", source=xml)
    uri_type = xml[:whitespace.start()]

    # Expand PEs in URI type
    if allow_parameter_entities:
        uri_type = expand_parameter_entity_references(uri_type, dtd, xml)

    # URI type must be either system or public
    if uri_type not in ["SYSTEM", "PUBLIC"]:
        raise XMLError(f"Invalid external resource reference type '{uri_type}'. "
                       f"Must be 'SYSTEM' or 'PUBLIC'",
                       source=xml)

    # Parse the first uri
    uri1, xml = parse_uri(xml[whitespace.start():],dtd, uri_type == "PUBLIC",
                          allow_parameter_entities=allow_parameter_entities)

    # If this is a PUBLIC reference there may be another uri
    uri2 = None
    whitespace = RegEx.OptionalWhitespace.match(xml)
    if uri_type == "PUBLIC":
        if require_full_public_exp or xml[whitespace.end()] in "\'\"":
            uri2, xml = parse_uri(xml, dtd, False,
                                  allow_parameter_entities=allow_parameter_entities)

    # Expand PEs
    if xml.startswith("%") and allow_parameter_entities:
        xml = expand_parameter_entity_reference(xml, dtd, xml)
        whitespace = RegEx.OptionalWhitespace.match(xml)
        xml = xml[whitespace.end():]

    # Check for a notation
    ndata = re.match(f"{RegEx.whitespace}NDATA{RegEx.whitespace}", xml)
    if ndata and look_for_notation:
        # Notation is up to next whitespace or `>`
        notation_end = RegEx.Whitespace_Or_GT.search(xml, pos=ndata.end())
        if not notation_end:
            raise XMLError("Error parsing notation reference", source=xml)

        notation = xml[ndata.end():notation_end.start()]
        xml = xml[notation_end.start():]

        # Expand PEs in notation
        if allow_parameter_entities:
            notation = expand_parameter_entity_references(notation, dtd, notation)

        # Notation must conform to xmlspec::Name
        if not RegEx.Name.fullmatch(notation):
            raise DisallowedCharacterError(notation, "external reference notation",
                                           conforms_to="Name", source=None)

        if uri_type == "PUBLIC":
            return uri2, uri1, notation, xml
        else:
            return uri1, None, notation, xml
    # If there is no notation, just return the public & system URIs
    if uri_type == "PUBLIC":
        return uri2, uri1, None, xml
    else:
        return uri1, None, None, xml


def parse_uri(xml: str,
              dtd: DTD,
              public: bool,
              allow_parameter_entities: bool = True) -> (str, str):
    # Expand PEs
    if re.match(f"{RegEx.optional_whitespace}%", xml) and external:
        xml = expand_parameter_entity_reference(xml, dtd, source)

    # Strip whitespace
    whitespace = RegEx.Whitespace.match(xml)
    if not whitespace:
        raise XMLError("Missing whitespace before URI", source=xml)
    xml = xml[whitespace.end():]

    # Get the URI delimiter
    delimiter = xml[0]
    if delimiter not in "\"\'":
        raise XMLError("Unable to parse URI", source=xml)

    # Parse the URI
    end_index = xml.find(delimiter, 1)
    uri = xml[1: end_index]

    # Expand PEs in URI
    if allow_parameter_entities:
        uri = expand_parameter_entity_references(uri, dtd, uri)

    # URI must conform to xmlspec::char if system or xmlspec::pubid if public
    if public and not RegEx.PubId.fullmatch(uri):
        raise DisallowedCharacterError(uri, "URI", conforms_to="Pubid", source=None)
    elif not RegEx.CharSequence.fullmatch(uri):
        raise DisallowedCharacterError(uri, "URI", conforms_to="Char", source=None)

    # Return uri and unparsed xml
    return uri, xml[end_index + 1:]


"""
    =============
    URI HANDLING
    =============
"""


def fetch_content_at_uri(uri: str,
                         current_path: str,
                         encoding: str) -> (Optional[str], Optional[str], str):
    # Try opening uri as a relative path
    path = os.path.join(current_path, uri)
    root = os.path.dirname(path)
    contents = read_file(path, encoding)
    if contents[0] is not None:
        return (*contents, root)

    # Try opening uri as an absolute path
    root = os.path.dirname(uri)
    return (*read_file(uri, encoding), root)


def read_file(path: str, encoding: str) -> (Optional[str], Optional[str]):
    # Try in requested encoding first
    try:
        with open(path, encoding=encoding) as f:
            return f.read(), encoding

    # Then fall back on utf-8, utf-16
    except UnicodeDecodeError:
        try:
            with open(path, encoding="utf-8") as f:
                return f.read(), "utf-8"
        except UnicodeDecodeError:
            try:
                with open(path, encoding="utf-16") as f:
                    return f.read(), "utf-16"
            except UnicodeDecodeError:
                return None, None

    # If the uri doesn't reference a file
    except FileNotFoundError:
        return None, None


""" 
    ===================
    EXTERNAL RESOURCES
    ===================
"""


def parse_text_declaration(xml: str, encoding: str) -> (str, str):
    # Import here to avoid import loop
    from xml_parser.Document import DocumentFactory

    # Strip text declaration
    if xml.startswith("<?xml"):
        source = xml
        xml = xml[5:]

        # XML Version is not important as long as it is valid
        is_version_declaration = re.match(f"({RegEx.whitespace})?version", xml)
        if is_version_declaration:
            _, xml = DocumentFactory.parse_version_info(xml, source)

        is_encoding_declaration = re.match(f"({RegEx.whitespace})?encoding", xml)
        if is_encoding_declaration:
            encoding, xml = DocumentFactory.parse_encoding_info(xml, source)

        # Strip optional whitespace
        whitespace = RegEx.Whitespace.match(xml)
        if whitespace:
            xml = xml[whitespace.end():]

        # XML declaration must end on '?>'
        if xml[:2] != "?>":
            raise XMLError("Illegal extra content at end of xml declaration", source=xml)

        return xml[2:], encoding

    return xml, encoding
