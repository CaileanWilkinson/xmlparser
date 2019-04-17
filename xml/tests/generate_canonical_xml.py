"""
    Generates canonical xml from the given document to test against given xmltest
"""
from classes.Element import Element
from classes.Document import Document
from classes.Text import Text
from classes.ProcessingInstruction import ProcessingInstruction


def canonical_form(document: Document) -> str:
    xml = ""

    # Assume all top-level PIs are at beginning todo - change me :/
    for pi in document.processing_instructions:
        xml += f"<?{pi.target} {pi.data or ''}?>"

    # Root element
    xml += __element(document.root)

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
