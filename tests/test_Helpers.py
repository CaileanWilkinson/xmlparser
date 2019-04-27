from xml_parser import helpers
from tests.mocks.MockEntity import MockEntity
from xml_parser.errors import XMLError
import unittest


class Parse_Reference_Tests(unittest.TestCase):
    """
        ================
        parse_reference
        ================
    """

    def test_expands_decimal_char_references(self):
        for num, char in [(118, "v"), (279, "ė"), (632, "ɸ"), (986, "Ϛ"), (1948, "ޜ")]:
            with self.subTest(f"&#{num}; -> {char}"):
                expansion_text = Helpers.parse_reference(f"&#{num};")
                self.assertEqual(char, expansion_text)

    def test_expands_hexadecimal_char_references(self):
        for num, char in [("76", "v"), ("117", "ė"), ("278", "ɸ"), ("3da", "Ϛ"), ("79c", "ޜ")]:
            with self.subTest(f"&#{num}; -> {char}"):
                expansion_text = Helpers.parse_reference(f"&#x{num};")
                self.assertEqual(char, expansion_text)

    def test_general_entity(self):
        entity = MockEntity("entity", expansion_text="SOMEVALUE")

        expansion_text = Helpers.parse_reference(f"&entity;", general_entities={"entity": entity})
        self.assertEqual("SOMEVALUE", expansion_text)

    def test_parameter_entity(self):
        entity = MockEntity("entity", expansion_text="SOMEVALUE", entity_type=MockEntity.Type.PARAMETER)

        expansion_text = Helpers.parse_reference(f"%entity;", parameter_entities={"entity": entity})
        self.assertEqual("SOMEVALUE", expansion_text)

    def test_ignores_general_entity(self):
        expansion_text = Helpers.parse_reference(f"&entity;", expand_general_entities=False)
        self.assertEqual("&entity;", expansion_text)

    def test_ignores_parameter_entity(self):
        expansion_text = Helpers.parse_reference(f"%entity;", expand_parameter_entities=False)
        self.assertEqual("%entity;", expansion_text)


class Expand_References_Tests(unittest.TestCase):
    """
        ==================
        expand_references
        ==================
    """

    def test_no_recursion(self):
        with self.subTest("Direct recursion"):
            entity = MockEntity("entity", expansion_text="Some Text &entity;")
            with self.assertRaises(XMLError):
                Helpers.parse_string_literal("Text &entity;", general_entities={"entity": entity})
        with self.subTest("Indirect recursion"):
            entity1 = MockEntity("entity1", expansion_text="Some Text &entity2;")
            entity2 = MockEntity("entity2", expansion_text="Some Text &entity1;")
            with self.assertRaises(XMLError):
                Helpers.parse_string_literal("Text &entity;", general_entities={"entity1": entity1, "entity2": entity2})

    def test_ampersand_expansion(self):
        with self.subTest("&amp;"):
            amp = MockEntity('amp', expansion_text="&#38;")
            text = Helpers.parse_string_literal("Text &amp; an entity", general_entities={"amp": amp})
            self.assertEqual("Text & an entity", text)
        with self.subTest("Entity containing &"):
            entity = MockEntity('entity', expansion_text="Some text &")
            with self.assertRaises(XMLError):
                Helpers.parse_string_literal("Text &entity; an entity", general_entities={"entity": entity})
        with self.subTest("Entity containing &amp;"):
            amp = MockEntity('amp', expansion_text="&#38;")
            entity = MockEntity('entity', expansion_text="and Some text &amp;")
            text = Helpers.parse_string_literal("Text &entity; an entity", general_entities={"amp": amp, "entity": entity})
            self.assertEqual("Text and Some text & an entity", text)

    def test_basic_entity_expansion(self):
        with self.subTest("General"):
            entity = MockEntity("entity", expansion_text="SOMEVALUE")
            text = Helpers.parse_string_literal(f"Some text and an entity: &entity;", general_entities={"entity": entity})
            self.assertEqual("Some text and an entity: SOMEVALUE", text)
        with self.subTest("Parameter"):
            entity = MockEntity("entity", expansion_text="SOMEVALUE")
            text = Helpers.parse_string_literal(f"Some text and an entity: %entity;",
                                                parameter_entities={"entity": entity})
            self.assertEqual("Some text and an entity: SOMEVALUE", text)

    def test_respects_ignore_flags(self):
        with self.subTest("General"):
            entity = MockEntity("entity", expansion_text="SOMEVALUE")
            text = Helpers.parse_string_literal(f"Some text and an entity: &entity;", general_entities={"entity": entity})
            self.assertEqual("Some text and an entity: SOMEVALUE", text)
        with self.subTest("Parameter"):
            entity = MockEntity("entity", expansion_text="SOMEVALUE")
            text = Helpers.parse_string_literal(f"Some text and an entity: %entity;",
                                                parameter_entities={"entity": entity})
            self.assertEqual("Some text and an entity: SOMEVALUE", text)

    def test_fails_invalid_entity(self):
        with self.subTest("General"):
            with self.assertRaises(XMLError):
                Helpers.parse_string_literal(f"Some text and an entity: &entity;")
        with self.subTest("Parameter"):
            with self.assertRaises(XMLError):
                Helpers.parse_string_literal(f"Some text and an entity: %entity;")


class ParseUriTests(unittest.TestCase):
    def test_uri_parsing(self):
        with self.subTest("SYSTEM with \'"):
            xml = " 'some uri'"
            uri, _ = helpers.parse_uri(xml, False)

            self.assertEqual("some uri", uri)
        with self.subTest("SYSTEM with \""):
            xml = ' "some uri"'
            uri, _ = helpers.parse_uri(xml, False)

            self.assertEqual("some uri", uri)
        with self.subTest("SYSTEM with \'"):
            xml = " 'some uri'"
            uri, _ = helpers.parse_uri(xml, True)

            self.assertEqual("some uri", uri)
        with self.subTest("SYSTEM with \""):
            xml = ' "some uri"'
            uri, _ = helpers.parse_uri(xml, True)

            self.assertEqual("some uri", uri)

    def test_parse_ends_after_uri(self):
        with self.subTest("SYSTEM"):
            xml = " 'some uri' BLAH"
            _, remaining_xml = helpers.parse_uri(xml, False)

            self.assertEqual(" BLAH", remaining_xml)
        with self.subTest("PUBLIC"):
            xml = " 'some uri' BLAH"
            _, remaining_xml = helpers.parse_uri(xml, True)

            self.assertEqual(" BLAH", remaining_xml)

    """
        ==========================
        FORBIDDEN CHARACTER TESTS
        ==========================
    """

    def test_system_forbidden_characters(self):
        for char in ["\u0001", "\u0003", "\u0010", "\ufffe", "\uffff"]:
            with self.subTest(char):
                xml = f" 'Blah{char}'"
                with self.assertRaises(XMLError):
                    helpers.parse_uri(xml, public=False)

    def test_system_allowed_characters(self):
        for char in [">", "<", "^", "|", "&"]:
            with self.subTest(char):
                xml = f" 'Blah{char}'"
                uri, _ = helpers.parse_uri(xml, public=False)

                self.assertEqual(f"Blah{char}", uri)

    def test_public_forbidden_characters(self):
        for char in [">", "<", "^", "|", "&", "\u0001", "\u0003", "\u0010", "\ufffe", "\uffff"]:
            with self.subTest(char):
                xml = f" 'Blah{char}'"
                with self.assertRaises(XMLError):
                    helpers.parse_uri(xml, public=True)

    def test_public_allowed_characters(self):
        for char in ["-", ":", "=", "!", "\u0020", "\u000d", "%"]:
            with self.subTest(char):
                xml = f" 'Blah{char}'"
                uri, _ = helpers.parse_uri(xml, public=True)

                self.assertEqual(f"Blah{char}", uri)


class ParseExternalReferenceTests(unittest.TestCase):
    def test_system_reference(self):
        xml = "SYSTEM 'some uri'"
        system, public, notation, _ = helpers.parse_external_reference(xml)

        self.assertEqual("some uri", system)
        self.assertEqual(None, public)
        self.assertEqual(None, notation)

    def test_double_public_reference(self):
        with self.subTest("Disallowing single uri"):
            xml = "PUBLIC 'uri1' 'uri2'"
            system, public, notation, _ = helpers.parse_external_reference(xml)

            self.assertEqual("uri2", system)
            self.assertEqual("uri1", public)
            self.assertEqual(None, notation)

        with self.subTest("Allowing single uri"):
            xml = "PUBLIC 'uri1' 'uri2'"
            system, public, notation, _ = helpers.parse_external_reference(xml,
                                                                           require_full_public_exp=False)

            self.assertEqual("uri2", system)
            self.assertEqual("uri1", public)
            self.assertEqual(None, notation)

    def test_single_public_reference(self):
        with self.subTest("Disallowing single uri"):
            xml = "PUBLIC 'uri'"
            with self.assertRaises(XMLError):
                helpers.parse_external_reference(xml, require_full_public_exp=True)

        with self.subTest("Allowing single uri"):
            xml = "PUBLIC 'uri1'>"
            system, public, notation, _ = helpers.parse_external_reference(xml,
                                                                           require_full_public_exp=False)
            self.assertEqual(None, system)
            self.assertEqual("uri1", public)
            self.assertEqual(None, notation)

    def test_notation_parsing(self):
        with self.subTest("SYSTEM"):
            xml = "SYSTEM 'uri1' NDATA notation"
            system, public, notation, _ = helpers.parse_external_reference(xml,
                                                                           require_full_public_exp=False)
            self.assertEqual("uri1", system)
            self.assertEqual(None, public)
            self.assertEqual("notation", notation)

        with self.subTest("PUBLIC"):
            xml = "PUBLIC 'uri1' 'uri2' NDATA notation"
            system, public, notation, _ = helpers.parse_external_reference(xml,
                                                                           require_full_public_exp=False)
            self.assertEqual("uri2", system)
            self.assertEqual("uri1", public)
            self.assertEqual("notation", notation)

        with self.subTest("Disallowing notations"):
            xml = "PUBLIC 'uri1' NDATA notation"
            system, public, notation, _ = helpers.parse_external_reference(xml,
                                                                           require_full_public_exp=False)
            self.assertEqual(None, system)
            self.assertEqual("uri1", public)
            self.assertEqual("notation", notation)

    """
        ================
        WELL-FORMEDNESS
        ================
    """
    def test_missing_delimiter(self):
        self.fail()
