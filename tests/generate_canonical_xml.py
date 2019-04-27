"""
    Generates canonical xml from the given document to test against given xmltest
"""
from typing import Dict

from xml_parser.content.Element import Element
from xml_parser.Document import Document
from xml_parser.content.Text import Text
from xml_parser.content.ProcessingInstruction import ProcessingInstruction
from xml_parser.dtd.Notation import Notation


def canonical_form(document: Document) -> str:
    xml = ""

    # DTD
    xml += __dtd(document.file.name, document.notations)

    # Leading PIs
    for pi in document.leading_processing_instructions:
        xml += f"<?{pi.target} {pi.data or ''}?>"

    # Root element
    xml += __element(document.file)

    # Trailing PIs
    for pi in document.trailing_processing_instructions:
        xml += f"<?{pi.target} {pi.data or ''}?>"

    # Return xml
    return xml


def __element(element: Element) -> str:
    # Start tag
    xml = f"<{element.name}"
    attributes = list(element.attributes.keys())
    attributes.sort()
    for attribute in attributes:
        value = element.attributes[attribute]
        value = value.replace("&", "&amp;")
        value = value.replace("<", "&lt;")
        value = value.replace(">", "&gt;")
        value = value.replace("\"", "&quot;")
        value = value.replace("\u0009", "&#9;")
        value = value.replace("\u000a", "&#10;")
        value = value.replace("\u000d", "&#13;")
        xml += f" {attribute}=\"{value}\""
    xml += ">"

    # Content
    for child in element.content:
        if isinstance(child, Text):
            text = child.text
            text = text.replace("&", "&amp;")
            text = text.replace("<", "&lt;")
            text = text.replace(">", "&gt;")
            text = text.replace("\"", "&quot;")
            text = text.replace("\u0009", "&#9;")
            text = text.replace("\u000a", "&#10;")
            text = text.replace("\u000d", "&#13;")
            xml += text
        elif isinstance(child, ProcessingInstruction):
            xml += f"<?{child.target} {child.data or ''}?>"
        elif isinstance(child, Element):
            xml += __element(child)

    # End tag
    xml += f"</{element.name}>"

    return xml


def __dtd(root: str, notations: Dict[str, Notation]) -> str:
    # Do not include DTD if no notations
    if not notations:
        return ""

    dtd = f"<!DOCTYPE {root} ["

    for notation in notations.values():
        if notation.public_uri and notation.system_uri:
            dtd += f"\n<!NOTATION {notation.name} PUBLIC '{notation.public_uri}' '{notation.system_uri}'>"
        elif notation.public_uri:
            dtd += f"\n<!NOTATION {notation.name} PUBLIC '{notation.public_uri}'>"
        elif notation.system_uri:
            dtd += f"\n<!NOTATION {notation.name} SYSTEM '{notation.system_uri}'>"

    dtd += "\n]>\n"

    return dtd
