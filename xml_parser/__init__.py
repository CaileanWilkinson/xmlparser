import os
from typing import Optional

from xml_parser.Document import Document, DocumentFactory
from .content.Element import Element
from .content.ProcessingInstruction import ProcessingInstruction
from .content.Text import Text
from xml_parser.dtd.Entity import Entity
from .dtd.Notation import Notation

__all__ = ["parse_string", "parse_file"]


def parse_string(xml: str, root: Optional[str] = None, encoding: str = "utf-8") -> Document:
    root = root or os.getcwd()

    # Normalise whitespace
    xml = xml.replace("\u000d\u000a", "\u000a")
    xml = xml.replace("\u000d", "\u000a")

    # Parse document
    return DocumentFactory.parse_from_xml(xml, root, encoding)


def parse_file(path: str, encoding: Optional[str] = None) -> Document:
    """
        A convenience function to parse the xml from a file at the given path
    :param path:
    :return:
    """
    # If the user has specified an encoding for this file
    if encoding:
        with open(path, encoding=encoding) as file:
            xml = file.read()
            return parse_string(xml, path, encoding)

    else:
        # First try to open using utf-8 and fall back on utf-16
        try:
            with open(path, encoding="utf-8") as file:
                xml = file.read()
        except UnicodeError:
            return parse_file(path, encoding="utf-16")
        return parse_string(xml, path, encoding)
