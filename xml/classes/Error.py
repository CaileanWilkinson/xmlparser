from typing import Optional

from ..RegularExpressions import RegEx


class XMLError(Exception):
    """
        The base error to throw for fatal XML issues - mostly well-formedness complaints
    """
    def __init__(self, message: str, source: Optional[str]):
        self.message = message
        self.source = source
        if source and len(source) > 20:
            Exception.__init__(self, f"{message}\nSource: {source[:20] + '...'}")
        elif source:
            Exception.__init__(self, f"{message}\nSource: {source}")
        else:
            Exception.__init__(self, message)


class DisallowedCharacterError(XMLError):
    """
        A specialised subclass of XMLError to throw when text contains disallowed characters.

        Reiterates through the provided text to find the invalid character for a more detailed report.
        This allows me to pattern match in the xml parser for efficiency, while still being able to provide an exact
        error when the pattern does not match.
    """
    def __init__(self, sequence: str, where: str, conforms_to: str, source: Optional[str]):
        self.sequence = sequence
        self.conforms_to = conforms_to

        char = self.__get_disallowed_char(sequence, conforms_to)

        message = f"Disallowed character '{char}' in {where} ('{sequence}')"
        XMLError.__init__(self, message, source)

    def __get_disallowed_char(self, sequence, conforms_to) -> str:
        if conforms_to.lower() == "name":
            if not RegEx.NameStartChar.match(sequence[:1]):
                return sequence[:1]
            for char in sequence[1:]:
                if not RegEx.NameChar.match(char):
                    return char
        elif conforms_to.lower() == "char":
            for char in sequence:
                if not RegEx.Char.match(char):
                    return char
        else:
            return conforms_to
