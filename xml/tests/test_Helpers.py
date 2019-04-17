import xml.Helpers as Helpers
from xml.tests.mocks.MockEntity import MockEntity
from xml.classes.Error import XMLError
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
