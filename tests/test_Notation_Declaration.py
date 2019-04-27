import unittest
from xml_parser.dtd.Notation import NotationFactory
from xml_parser.errors import XMLError, DisallowedCharacterError
from tests.mocks.MockDTD import MockDTD


class NotationTests(unittest.TestCase):
    def test_overall_parsing(self):
        with self.subTest("System reference"):
            xml = "<!NOTATION Name SYSTEM 'some uri'>XML CONTINUES"
            notation, _ = NotationFactory.parse_from_xml(xml, MockDTD(), False)

            self.assertEqual("Name", notation.name)
            self.assertEqual("some uri", notation.system_uri)
            self.assertEqual(None, notation.public_uri)

        with self.subTest("Public reference"):
            xml = "<!NOTATION Name PUBLIC 'some uri' >XML CONTINUES"
            notation, _ = NotationFactory.parse_from_xml(xml, MockDTD(), False)

            self.assertEqual("Name", notation.name)
            self.assertEqual(None, notation.system_uri)
            self.assertEqual("some uri", notation.public_uri)

        with self.subTest("Double reference"):
            xml = "<!NOTATION Name PUBLIC 'some uri' 'some other uri' >XML CONTINUES"
            notation, _ = NotationFactory.parse_from_xml(xml, MockDTD(), False)

            self.assertEqual("Name", notation.name)
            self.assertEqual("some other uri", notation.system_uri)
            self.assertEqual("some uri", notation.public_uri)

    def test_ends_parse_on_close(self):
        with self.subTest("System reference"):
            xml = "<!NOTATION Name SYSTEM 'some uri'>XML CONTINUES"
            _, remaining_xml = NotationFactory.parse_from_xml(xml, MockDTD(), False)

            self.assertEqual("XML CONTINUES", remaining_xml)

        with self.subTest("Public reference"):
            xml = "<!NOTATION Name PUBLIC 'some uri' >XML CONTINUES"
            _, remaining_xml = NotationFactory.parse_from_xml(xml, MockDTD(), False)

            self.assertEqual("XML CONTINUES", remaining_xml)

        with self.subTest("Double reference"):
            xml = "<!NOTATION Name PUBLIC 'some uri' 'some other uri' >XML CONTINUES"
            _, remaining_xml = NotationFactory.parse_from_xml(xml, MockDTD(), False)

            self.assertEqual("XML CONTINUES", remaining_xml)

    """
        ===================
        MISSING WHITESPACE
        ===================
    """

    def test_missing_whitespace_before_name(self):
        xml = "<!NOTATIONName SYSTEM 'some uri'>XML CONTINUES"

        with self.assertRaises(XMLError):
            NotationFactory.parse_from_xml(xml, MockDTD(), False)

    def test_missing_whitespace_after_name(self):
        xml = "<!NOTATION NameSYSTEM 'some uri'>XML CONTINUES"

        with self.assertRaises(XMLError):
            NotationFactory.parse_from_xml(xml, MockDTD(), False)

    def test_missing_whitespace_after_system(self):
        xml = "<!NOTATION Name SYSTEM'some uri'>XML CONTINUES"

        with self.assertRaises(XMLError):
            NotationFactory.parse_from_xml(xml, MockDTD(), False)

    def test_missing_whitespace_after_public(self):
        xml = "<!NOTATION Name PUBLIC'some uri'>XML CONTINUES"

        with self.assertRaises(XMLError):
            NotationFactory.parse_from_xml(xml, MockDTD(), False)

    def test_missing_whitespace_betweeen_public_uris(self):
        xml = "<!NOTATION Name PUBLIC 'some uri''some other uri'>XML CONTINUES"

        with self.assertRaises(XMLError):
            NotationFactory.parse_from_xml(xml, MockDTD(), False)

    """
        ================
        WELL-FORMEDNESS
        ================
    """
    def test_notation_not_closed(self):
        with self.subTest("No >"):
            xml = f"<!NOTATION Name SYSTEM 'some uri'"

            with self.assertRaises(XMLError):
                NotationFactory.parse_from_xml(xml, MockDTD(), False)

        with self.subTest("> from following element"):
            xml = f"<NOTATION Name SYSTEM 'some uri' <end/>"

            with self.assertRaises(XMLError):
                NotationFactory.parse_from_xml(xml, MockDTD(), False)


class NameTests(unittest.TestCase):
    """
        =============
        NAME PARSING
        =============
    """

    def test_name_parsing(self):
        xml = "Name XML-CONTINUES"
        name, unparsed_xml = NotationFactory.parse_name(xml, "", MockDTD(), False)

        self.assertEqual("Name", name)
        self.assertEqual("XML-CONTINUES", unparsed_xml)

    def test_parse_ends_after_name(self):
        xml = "Name MOREXML"
        _, unparsed_xml = NotationFactory.parse_name(xml, "", MockDTD(), False)

        self.assertEqual("MOREXML", unparsed_xml)

    """
        =====================
        FORBIDDEN CHARACTERS
        =====================
    """

    def test_forbidden_name_start_characters(self):
        for char in ["-", ".", "0", "7", "\u0305"]:
            with self.subTest(char):
                with self.assertRaises(DisallowedCharacterError):
                    xml = f"{char}Name >"
                    NotationFactory.parse_name(xml, "", MockDTD(), False)

    def test_forbidden_name_characters(self):
        for char in ["\u00d7", "\u00f7", "\u037e", "\u2030"]:
            with self.subTest(char):
                xml = f"Na{char}me >"
                with self.assertRaises(DisallowedCharacterError):
                    NotationFactory.parse_name(xml, "", MockDTD(), False)

    def test_forbidden_xml_name(self):
        with self.subTest("xml"):
            xml = f"xml "

            with self.assertRaises(XMLError):
                NotationFactory.parse_name(xml, "", MockDTD(), False)

        with self.subTest("XmL"):
            xml = f"XmL "

            with self.assertRaises(XMLError):
                NotationFactory.parse_name(xml, "", MockDTD(), False)

        with self.subTest("xmlBlah"):
            xml = f"xmlBlah "

            with self.assertRaises(XMLError):
                NotationFactory.parse_name(xml, "", MockDTD(), False)

        with self.subTest("XmLBlah"):
            xml = f"XmLBlah "

            with self.assertRaises(XMLError):
                NotationFactory.parse_name(xml, "", MockDTD(), False)


class ExternalReferenceTests(unittest.TestCase):
    """
        ===========================
        EXTERNAL REFERENCE PARSING
        ===========================
    """

    def test_system_reference_parsing(self):
        with self.subTest("With whitespace"):
            xml = "SYSTEM 'some uri' >MORE XML"
            system, public, unparsed_xml = NotationFactory.parse_external_ref(xml, MockDTD(), False)

            self.assertEqual("some uri", system)
            self.assertEqual(None, public)
            self.assertEqual(" >MORE XML", unparsed_xml)

        with self.subTest("Without whitespace"):
            xml = "SYSTEM 'some uri'>MORE XML"
            system, public, unparsed_xml = NotationFactory.parse_external_ref(xml, MockDTD(), False)

            self.assertEqual("some uri", system)
            self.assertEqual(None, public)
            self.assertEqual(">MORE XML", unparsed_xml)

    def test_public_reference_parsing(self):
        with self.subTest("With whitespace"):
            xml = "PUBLIC 'some uri' >MORE XML"
            system, public, unparsed_xml = NotationFactory.parse_external_ref(xml, MockDTD(), False)

            self.assertEqual(None, system)
            self.assertEqual("some uri", public)
            self.assertEqual(" >MORE XML", unparsed_xml)

        with self.subTest("Without whitespace"):
            xml = "PUBLIC 'some uri'>MORE XML"
            system, public, unparsed_xml = NotationFactory.parse_external_ref(xml, MockDTD(), False)

            self.assertEqual(None, system)
            self.assertEqual("some uri", public)
            self.assertEqual(">MORE XML", unparsed_xml)

    def test_system_and_public_reference_parsing(self):
        with self.subTest("With whitespace"):
            xml = "PUBLIC 'uri1' 'uri2' >MORE XML"
            system, public, unparsed_xml = NotationFactory.parse_external_ref(xml, MockDTD(), False)

            self.assertEqual("uri2", system)
            self.assertEqual("uri1", public)
            self.assertEqual(" >MORE XML", unparsed_xml)

        with self.subTest("Without whitespace"):
            xml = "PUBLIC 'uri1' 'uri2'>MORE XML"
            system, public, unparsed_xml = NotationFactory.parse_external_ref(xml, MockDTD(), False)

            self.assertEqual("uri2", system)
            self.assertEqual("uri1", public)
            self.assertEqual(">MORE XML", unparsed_xml)

    """
        =====================
        FORBIDDEN CHARACTERS
        =====================
    """

    def test_forbidden_characters_system_reference(self):
        for char in ["\u0001", "\u0003", "\u0010", "\ufffe", "\uffff"]:
            with self.subTest(f"Char: {char}"):
                xml = f"SYSTEM 'some {char}uri'>"
                with self.assertRaises(DisallowedCharacterError):
                    NotationFactory.parse_external_ref(xml, MockDTD(), False)

    def test_forbidden_characters_public_reference(self):
        for char in ["^", "&", "|", "\u0001", "\u0003", "\u0010", "\ufffe", "\uffff"]:
            with self.subTest(f"Char: {char}"):
                xml = f"PUBLIC 'some {char}uri'>"
                with self.assertRaises(DisallowedCharacterError):
                    NotationFactory.parse_external_ref(xml, MockDTD(), False)
