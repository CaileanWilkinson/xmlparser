from xml.classes.document.Entity import Entity
from xml.tests.mocks.MockEntity import MockEntity
from xml.classes.Error import XMLError
import unittest


class EntityTests(unittest.TestCase):
    """
        ======================
        BASIC PARSING TESTS
        ======================
    """
    def test_internal_general(self):
        entity = Entity("<!ENTITY Name 'SomeValue' >")
        entity.parse_to_end({})

        self.assertEqual(entity.type, Entity.Type.GENERAL)
        self.assertEqual(entity.external, False)
        self.assertEqual(entity.parsed, True)
        self.assertEqual(entity.name, "Name")
        self.assertEqual(entity.system_URI, None)
        self.assertEqual(entity.public_URI, None)
        self.assertEqual(entity.notation, None)
        self.assertEqual(entity.expansion_text, "SomeValue")

    def test_internal_parameter(self):
        entity = Entity("<!ENTITY % Name 'SomeValue' >")
        entity.parse_to_end({})

        self.assertEqual(entity.type, Entity.Type.PARAMETER)
        self.assertEqual(entity.external, False)
        self.assertEqual(entity.parsed, True)
        self.assertEqual(entity.name, "Name")
        self.assertEqual(entity.system_URI, None)
        self.assertEqual(entity.public_URI, None)
        self.assertEqual(entity.notation, None)
        self.assertEqual(entity.expansion_text, "SomeValue")

    def test_external_general(self):
        with self.subTest("SYSTEM"):
            entity = Entity("<!ENTITY Name SYSTEM 'some_uri' >")
            entity.parse_to_end({})

            self.assertEqual(entity.type, Entity.Type.GENERAL)
            self.assertEqual(entity.external, True)
            self.assertEqual(entity.parsed, True)
            self.assertEqual(entity.name, "Name")
            self.assertEqual(entity.system_URI, 'some_uri')
            self.assertEqual(entity.public_URI, None)
            self.assertEqual(entity.notation, None)
            self.assertEqual(entity.expansion_text, None)

        with self.subTest("PUBLIC"):
            entity = Entity("<!ENTITY Name PUBLIC 'some_uri' 'some_other_uri' >")
            entity.parse_to_end({})

            self.assertEqual(entity.type, Entity.Type.GENERAL)
            self.assertEqual(entity.external, True)
            self.assertEqual(entity.parsed, True)
            self.assertEqual(entity.name, "Name")
            self.assertEqual(entity.system_URI, 'some_other_uri')
            self.assertEqual(entity.public_URI, 'some_uri')
            self.assertEqual(entity.notation, None)
            self.assertEqual(entity.expansion_text, None)

    def test_external_parameter(self):
        with self.subTest("SYSTEM"):
            entity = Entity("<!ENTITY % Name SYSTEM 'some_uri' >")
            entity.parse_to_end({})

            self.assertEqual(entity.type, Entity.Type.PARAMETER)
            self.assertEqual(entity.external, True)
            self.assertEqual(entity.parsed, True)
            self.assertEqual(entity.name, "Name")
            self.assertEqual(entity.system_URI, 'some_uri')
            self.assertEqual(entity.public_URI, None)
            self.assertEqual(entity.notation, None)
            self.assertEqual(entity.expansion_text, None)

        with self.subTest("PUBLIC"):
            entity = Entity("<!ENTITY % Name PUBLIC 'some_uri' 'some_other_uri' >")
            entity.parse_to_end({})

            self.assertEqual(entity.type, Entity.Type.PARAMETER)
            self.assertEqual(entity.external, True)
            self.assertEqual(entity.parsed, True)
            self.assertEqual(entity.name, "Name")
            self.assertEqual(entity.system_URI, 'some_other_uri')
            self.assertEqual(entity.public_URI, 'some_uri')
            self.assertEqual(entity.notation, None)
            self.assertEqual(entity.expansion_text, None)

    def test_unparsed(self):
        with self.subTest("SYSTEM"):
            entity = Entity("<!ENTITY Name SYSTEM 'some_uri' NDATA notation>")
            entity.parse_to_end({})

            self.assertEqual(entity.type, Entity.Type.GENERAL)
            self.assertEqual(entity.external, True)
            self.assertEqual(entity.parsed, False)
            self.assertEqual(entity.name, "Name")
            self.assertEqual(entity.system_URI, 'some_uri')
            self.assertEqual(entity.public_URI, None)
            self.assertEqual(entity.notation, 'notation')
            self.assertEqual(entity.expansion_text, None)

        with self.subTest("PUBLIC"):
            entity = Entity("<!ENTITY Name PUBLIC 'some_uri' 'some_other_uri' NDATA notation>")
            entity.parse_to_end({})

            self.assertEqual(entity.type, Entity.Type.GENERAL)
            self.assertEqual(entity.external, True)
            self.assertEqual(entity.parsed, False)
            self.assertEqual(entity.name, "Name")
            self.assertEqual(entity.system_URI, 'some_other_uri')
            self.assertEqual(entity.public_URI, 'some_uri')
            self.assertEqual(entity.notation, 'notation')
            self.assertEqual(entity.expansion_text, None)

    """
        ================
        PARSE-END TESTS
        ================
        These tests ensure that the Text class only parses the provided xml as far as it is character data,
        and that occurrences of markup are returned to the parent class for proper processing
    """

    def test_ends_parse_on_close(self):
        with self.subTest("Internal"):
            entity = Entity("<!ENTITY name 'value'>Some text")
            unparsed_xml = entity.parse_to_end({})
            self.assertEqual("Some text", unparsed_xml)

        with self.subTest("External"):
            entity = Entity("<!ENTITY name SYSTEM 'uri' >Some text")
            unparsed_xml = entity.parse_to_end({})
            self.assertEqual("Some text", unparsed_xml)

    """
        ==================
        ENTITY EXPANSIONS
        ==================
    """
    def test_ignores_general_entites(self):
        entity = Entity("<!ENTITY Name 'SomeValue &entity;' >")
        entity.parse_to_end({})
        self.assertEqual(entity.expansion_text, "SomeValue &entity;")

    def test_expands_parameter_entities(self):
        param_entity = MockEntity("entity", expansion_text="ENTITY TEXT")

        entity = Entity("<!ENTITY Name 'SomeValue %entity;' >")
        entity.parse_to_end({"entity": param_entity})
        self.assertEqual(entity.expansion_text, "SomeValue ENTITY TEXT")

    def test_expands_decimal_character_reference(self):
        for num, char in [(118, "v"), (279, "ė"), (632, "ɸ"), (986, "Ϛ"), (1948, "ޜ")]:
            with self.subTest(f"&#{num}; -> {char}"):
                entity = Entity(f"<!ENTITY Name 'SomeValue &#{num};' >")
                entity.parse_to_end({})
                self.assertEqual(entity.expansion_text, f"SomeValue {char}")

    def test_expands_hexadecimal_character_reference(self):
        for num, char in [("76", "v"), ("117", "ė"), ("278", "ɸ"), ("3da", "Ϛ"), ("79c", "ޜ")]:
            with self.subTest(f"&#x{num}; -> {char}"):
                entity = Entity(f"<!ENTITY Name 'SomeValue &#x{num};' >")
                entity.parse_to_end({})
                self.assertEqual(entity.expansion_text, f"SomeValue {char}")

    """
        ======================
        WELL-FORMEDNESS TESTS
        ======================
    """
    def test_forbidden_characters(self):
        for char in ["\u0001", "\u0003", "\u0010", "\ufffe", "\uffff"]:
            with self.subTest(f"Char: {char}"):
                pi = Entity(f"<!ENTITY Name 'Value {char}'>")
                with self.assertRaises(XMLError):
                    pi.parse_to_end({})

    def test_forbidden_name_start_characters(self):
        for char in ["-", ".", "0", "7", "\u0305"]:
            with self.subTest(char):
                pi = Entity(f"<!ENTITY {char}Name 'Value'>")
                with self.assertRaises(XMLError):
                    pi.parse_to_end({})

    def test_forbidden_name_characters(self):
        for char in ["\u00d7", "\u00f7", "\u037e", "\u2030"]:
            with self.subTest(char):
                pi = Entity(f"<!ENTITY Name{char} 'Value'>")
                with self.assertRaises(XMLError):
                    pi.parse_to_end({})

    def test_no_unparsed_parameter_entities(self):
        with self.subTest("SYSTEM"):
            entity = Entity("<!ENTITY % Name SYSTEM 'some_uri' NDATA notation>")
            with self.assertRaises(XMLError):
                entity.parse_to_end({})

        with self.subTest("PUBLIC"):
            entity = Entity("<!ENTITY % Name PUBLIC 'some_uri' 'some_other_uri' NDATA notation>")
            with self.assertRaises(XMLError):
                entity.parse_to_end({})

    def test_external_entity_declaration_conformance(self):
        with self.subTest("SYSEM"):
            entity = Entity("<!ENTITY Name SYSEM 'some_uri' >")
            with self.assertRaises(XMLError):
                entity.parse_to_end({})

        with self.subTest("PUB"):
            entity = Entity("<!ENTITY Name PUB 'some_uri' 'some_other_uri' >")
            with self.assertRaises(XMLError):
                entity.parse_to_end({})

    # todo - test fetching of external entities?
