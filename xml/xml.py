from .classes.document.Document import Document


def parse(xml: str) -> Document:
    # Normalise whitespace
    xml = xml.replace("\u000d\u000a", "\u000a")
    xml = xml.replace("\u000d", "\u000a")

    # Parse document
    document = Document(xml)
    document.parse()
    return document


def parse_file(path: str) -> Document:
    """
        A convenience function to parse the xml from a file at the given path
    :param path:
    :return:
    """
    with open(path) as file:
        xml = file.read()
        return parse(xml)
