# todo - Module docstring
import re
from typing import List, Dict, Optional

from .RegularExpressions import RegEx
from .classes.document.Entity import Entity
from .classes.Error import XMLError, DisallowedCharacterError

"""
    =============
    TEXT PARSING    
    =============
"""


def parse_reference(reference: str,
                    general_entities: Dict[str, Entity] = None,
                    parameter_entities: Dict[str, Entity] = None,
                    expand_general_entities: bool = True,
                    expand_parameter_entities: bool = True):
    """
        Returns the replacement text for the given entity, if the entity is enabled. Otherwise returns the given text.

        Entity must be of format &BLAH; or %BLAH; with BLAH either a character code or an entity reference.
        Leading [&%] and trailing ; are required.

        :param reference The full entity reference, including leading and trailing fluff
        :param document A reference to the current document containing allowed entities
        :param expand_general_entities Whether to expand general entities. If false, ignores general entities. Defaults to True
        :param expand_parameter_entities Whether to expand parameter entities. Defaults to False
    """
    # Fix parameters
    if general_entities is None:
        general_entities = {}  # type: Dict[str, Entity]
    if parameter_entities is None:
        parameter_entities = {}  # type: Dict[str, Entity]

    # Character entities
    if reference[:2] == "&#":
        # Isolate the character code
        try:
            if reference[2:3] == "x":
                character_code = int(reference[3:-1], 16)
            else:
                character_code = int(reference[2:-1])
        except ValueError:
            raise XMLError(f"Invalid character reference {reference}", None)

        # Attempt to convert to a unicode string & return
        try:
            return chr(character_code)
        except (ValueError, OverflowError):
            raise XMLError(f"Invalid character reference {reference}", None)

    # General entities
    elif reference[:1] == "&" and expand_general_entities:
        # Isolate the entity id & fetch the entity
        id = reference[1:-1]
        entity = general_entities.get(id, None)
        if entity is None:
            raise XMLError(f"Reference to undeclared entity {reference}", None)

        # Return the entity's replacement text
        return entity.expansion_text

    # Parameter entities
    elif reference[:1] == "%" and expand_parameter_entities:
        # Isolate the entity id & fetch the entity
        id = reference[1:-1]
        entity = parameter_entities.get(id, None)
        if entity is None:
            raise XMLError(f"Reference to undeclared entity {reference}", None)

        # Return the entity's replacement text
        return entity.expansion_text

    # Otherwise (if entity is not recognised or entity type expansion is disabled)
    return reference


def parse_string_literal(text: str,
                         general_entities: Dict[str, Entity] = None,
                         parameter_entities: Dict[str, Entity] = None,
                         expand_general_entities: bool = True,
                         expand_parameter_entities: bool = True,
                         normalise_whitespace: bool = False,
                         previous_entities: List[str] = None):
    """
        Expands all entity references found within the given text. Ignores other markup
    :param text:
    :param expand_general_entities:
    :param expand_parameter_entities:
    :param general_entities:
    :param parameter_entities:
    :param previous_entities
    :return:
    """
    # Fix parameters
    general_entities = general_entities or {}
    parameter_entities = parameter_entities or {}
    previous_entities = previous_entities or []

    # Normalise existing whitespace
    if normalise_whitespace:
        text = text.replace("\u000a", "\u0020")
        text = text.replace("\u000d", "\u0020")
        text = text.replace("\u0009", "\u0020")

    # The final text after parsing
    parsed_text = ""
    last_index = 0

    # Iterate through every reference in the text
    for reference in RegEx.Reference.finditer(text):
        # Append skipped text
        skipped_text = text[last_index: reference.start()]
        parsed_text += skipped_text

        # Ensure skipped text doesn't contain &
        if "&" in skipped_text:
            raise XMLError("Invalid character ('&') in text", source=text)

        # Check for recursion (if we are referencing an entity from higher up the chain
        if reference.group() in previous_entities:
            raise XMLError(f"Infinite recursion within entity {reference}", source=text)

        # Get the reference expansion text
        expansion_text = parse_reference(reference.group(),
                                         general_entities,
                                         parameter_entities,
                                         expand_general_entities,
                                         expand_parameter_entities)

        # Normalise whitespace
        if normalise_whitespace and reference.group()[1] != "#":
            expansion_text = expansion_text.replace("\u000a", "\u0020")
            expansion_text = expansion_text.replace("\u000d", "\u0020")
            expansion_text = expansion_text.replace("\u0009", "\u0020")

        # Ensure expansion text doesn't contain "<" unless it is &#60;
        if "<" in expansion_text and reference.group() not in ["&#60;", "&#x3c;", "&lt;"]:
            raise XMLError("Invalid character ('<') in entity expansion text", source=reference.group())

        # If the reference was recognised, reparse it
        if expansion_text != reference.group() and reference.group() != "&#38;":
            parsed_text += parse_string_literal(expansion_text,
                                                general_entities,
                                                parameter_entities,
                                                expand_general_entities,
                                                expand_parameter_entities,
                                                previous_entities=previous_entities + [reference.group()])
        else:
            parsed_text += expansion_text

        # Update the index
        last_index = reference.end()

    # Append any final text
    parsed_text += text[last_index:]

    # Ensure final text doesn't contain &
    if "&" in text[last_index:]:
        raise XMLError("Invalid character ('&') in text", source=text)

    # Return the expanded text
    return parsed_text


"""
    =====
    URIs    
    =====
"""


def parse_external_reference(xml: str, look_for_notation: bool = True) -> (str, str, Optional[str], Optional[str]):
    """
       Returns (remaining_xml, public, system, notation)

       todo - TESTS!! And this is also a mess :(
    """
    # The URI type (system or public) runs up to the next whitespace
    whitespace = RegEx.Whitespace.search(xml)
    if not whitespace:
        raise XMLError("Unable to parse type of external resource reference", source=xml)
    uri_type = xml[:whitespace.start()]

    # URI type must be either system or public
    if uri_type not in ["SYSTEM", "PUBLIC"]:
        raise XMLError(f"Invalid external resource reference type '{uri_type}'. Must be 'SYSTEM' or 'PUBLIC'",
                       source=xml)

    # Parse the second uri
    uri1, xml = parse_uri(xml[whitespace.start():])

    # If this is a PUBLIC reference there is another uri
    if uri_type == "PUBLIC":
        uri2, xml = parse_uri(xml)

    # Check for a notation
    ndata = re.match(f"{RegEx.whitespace}NDATA{RegEx.whitespace}", xml)
    if ndata and look_for_notation:
        # Notation is up to next whitespace or `>`
        notation_end = RegEx.Whitespace_Or_GT.search(xml, pos=ndata.end())
        if not notation_end:
            raise XMLError()
        notation = xml[ndata.end():notation_end.start()]
        xml = xml[notation_end.start():]

        # Notation must conform to xmlspec::Name
        if not RegEx.Name.fullmatch(notation):
            raise DisallowedCharacterError(notation, "external reference notation", conforms_to="Name", source=None)

        if uri_type == "PUBLIC":
            return xml, uri2, uri1, notation
        else:
            return xml, uri1, None, notation
    # If there is no notation, just return the public & system URIs
    if uri_type == "PUBLIC":
        return xml, uri2, uri1, None
    else:
        return xml, uri1, None, None


def parse_uri(remaining_xml: str) -> (str, str):
    # Strip whitespace
    whitespace = RegEx.Whitespace.match(remaining_xml)
    if not whitespace:
        raise XMLError("Missing whitespace before URI", source=remaining_xml)
    remaining_xml = remaining_xml[whitespace.end():]

    # Get the URI delimiter
    delimiter = remaining_xml[0]
    if delimiter not in "\"\'":
        raise XMLError("Unable to parse URI", source=remaining_xml)

    # Parse the URI
    end_index = remaining_xml.find(delimiter, 1)
    uri = remaining_xml[1: end_index]

    # URI must conform to xmlspec::char
    if not RegEx.CharSequence.fullmatch(uri):
        raise DisallowedCharacterError(uri, "URI", conforms_to="Char", source=None)

    # Return uri and unparsed xml
    return uri, remaining_xml[end_index + 1:]
