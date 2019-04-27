"""
    Regex here adapted from the Extended Backus-Naur Form found in the xml specification at
    http://www.w3.org/TR/xml/
"""
import re


# todo - precompile ALL regex used everywhere!!

class RegEx:
    # todo - docstring?
    # todo - remove unused regexes

    # Basic character sets
    char = "\u0009|\u000A|\u000D|[\u0020-\uD7FF]|[\uE000-\uFFFD]|[\U00010000-\U0010FFFF]"  # Allowed characters in xml
    char_without_hyphen = "\u0009|\u000A|\u000D|[\u0020-\u002C]|[\u002E-\uD7FF]|[\uE000-\uFFFD]|[\U00010000-\U0010FFFF]"  # Allowed characters in xml without the hyphen (?:for use in comments)

    # Note: using '\s' would match characters not considered whitespace by the xml spec
    whitespace = "[\u0020\u0009\u000D\u000A]+"  # Whitespace
    optional_whitespace = "[\u0020\u0009\u000D\u000A]*"  # Whitespace

    xml = "(?:X|x)(?:M|m)(?:L|l)"  # The word 'xml' is often restricted
    eq = f"{optional_whitespace}={optional_whitespace}"
    qt = "\"|\'"

    # Constructs
    charsequence = f"(?:{char})*"
    encoding = f"(?:[A-Za-z][A-Za-z0-9._-]*)"
    namestartchar = '(?:[A-Z]|:|_|[a-z]|[\u00C0-\u00D6]|[\u00D8-\u00F6]|[\u00F8-\u02FF]|[\u0370-\u037D]|[\u037F-\u1FFF]|[\u200C-\u200D]|[\u2070-\u218F]|[\u2C00-\u2FEF]|[\u3001-\uD7FF]|[\uF900-\uFDCF]|[\uFDF0-\uFFFD]|[\U00010000-\U000EFFFF])'
    namechar = f'(?:{namestartchar})|-|\\.|[0-9]|\u00B7|[\u0300-\u036F]|[\u203F-\u2040]'
    name = f"(?!{xml})(?:{namestartchar})(?:{namechar})*"  # Names must start with a StartChar and follow with allowed NameChars and cannot start with xml
    names = f"(?:{name})(?:{whitespace}{name})*"
    nmtoken = f"(?:{namechar})+"  # Name Tokens can start with any allowed NameChar
    nmtokens = f"(?:{nmtoken})(?:{whitespace}{nmtoken})*"  # A series of Name Tokens separated by spaces
    pubid = "[\u0020\u000D\u000Aa-zA-Z0-9'()+,./:=?;!*#@$_%-]*"

    # Useful reg exs
    reference = "[&%].*?;"

    """
        ==================
        COMPILED VERSIONS 
        ==================   
    """
    Whitespace = re.compile(whitespace)
    OptionalWhitespace = re.compile(optional_whitespace)
    Whitespace_Or_TagEnd = re.compile(f"(?:{whitespace}|/>|>)")
    Whitespace_Or_GT = re.compile(f"(?:{whitespace}|>)")

    Element_StartTagEnd = re.compile(f"(?:{whitespace})?/?>")
    Element_EndTagEnd = re.compile(f"(?:{whitespace})?>")

    ElementDeclaration_ContentSpecNameEnd = re.compile(f"(?:{whitespace}|[|,)])")
    DTD_NameEnd = re.compile(f"(?:(?:(?:{whitespace})?>)|(?:(?:{whitespace})?\\[)|{whitespace})")
    ProcessingInstruction_TargetEnd = re.compile(f"(?:({whitespace})|\\?>)")
    Eq = re.compile(eq)

    Char = re.compile(char)
    CharSequence = re.compile(charsequence)
    Encoding = re.compile(encoding)

    NameStartChar = re.compile(namestartchar)
    NameChar = re.compile(namechar)
    Name = re.compile(name)
    Names = re.compile(names)
    NmToken = re.compile(nmtoken)
    NmTokens = re.compile(nmtokens)
    PubId = re.compile(pubid)
    Reference = re.compile(reference)
