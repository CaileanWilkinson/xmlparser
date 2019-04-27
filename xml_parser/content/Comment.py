from xml_parser.dtd.DTD import DTD
from xml_parser.regular_expressions import RegEx
from ..errors import XMLError, DisallowedCharacterError


class CommentFactory:
    @staticmethod
    def parse_from_xml(xml, dtd: DTD) -> str:
        del dtd

        # Parse to the end of the comment
        comment_end = xml.find("-->")
        if comment_end == -1:
            raise XMLError("Unable to find end of comment", source=xml)

        # Comments must conform to xmlspec::Char
        if not RegEx.CharSequence.fullmatch(xml[:comment_end]):
            raise DisallowedCharacterError(xml[:comment_end + 3],
                                           "comment",
                                           conforms_to="Char",
                                           source=xml)

        # Comments may not contain '--'
        if "--" in xml[4: comment_end]:
            raise DisallowedCharacterError(xml[:comment_end + 3],
                                           "comment",
                                           conforms_to="--",
                                           source=xml[:comment_end + 3])

        # Comments may not end on '--->'
        if xml[comment_end - 1] == "-":
            raise XMLError("Comments may not end with '--->'", source=xml[:comment_end + 3])

        return xml[comment_end + 3:]
