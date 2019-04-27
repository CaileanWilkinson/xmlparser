from xml_parser.dtd.Entity import Entity, EntityFactory
from tests.mocks.MockDTD import MockDTD
from tests.mocks.MockEntity import MockEntity
from xml_parser.errors import XMLError, DisallowedCharacterError
import unittest


class EntityTests(unittest.TestCase):
    """
        ======================
        BASIC PARSING TESTS
        ======================
    """
    def test_internal_general(self):
        xml = "<!ENTITY Name 'SomeValue' >"
        entity, _ = EntityFactory.parse_from_xml(xml, MockDTD())

        self.assertEqual(entity.type, Entity.Type.GENERAL)
        self.assertEqual(entity.external, False)
        self.assertEqual(entity.parsed, True)
        self.assertEqual(entity.name, "Name")
        self.assertEqual(entity.system_uri, None)
        self.assertEqual(entity.public_uri, None)
        self.assertEqual(entity.notation, None)
        self.assertEqual(entity.expansion_text, "SomeValue")

    def test_internal_parameter(self):
        xml = "<!ENTITY % Name 'SomeValue' >"
        entity, _ = EntityFactory.parse_from_xml(xml, MockDTD())

        self.assertEqual(entity.type, Entity.Type.PARAMETER)
        self.assertEqual(entity.external, False)
        self.assertEqual(entity.parsed, True)
        self.assertEqual(entity.name, "Name")
        self.assertEqual(entity.system_uri, None)
        self.assertEqual(entity.public_uri, None)
        self.assertEqual(entity.notation, None)
        self.assertEqual(entity.expansion_text, "SomeValue")

    def test_external_general(self):
        with self.subTest("SYSTEM"):
            xml = "<!ENTITY Name SYSTEM 'some_uri' >"
            entity, _ = EntityFactory.parse_from_xml(xml, MockDTD())

            self.assertEqual(entity.type, Entity.Type.GENERAL)
            self.assertEqual(entity.external, True)
            self.assertEqual(entity.parsed, True)
            self.assertEqual(entity.name, "Name")
            self.assertEqual(entity.system_uri, 'some_uri')
            self.assertEqual(entity.public_uri, None)
            self.assertEqual(entity.notation, None)
            self.assertEqual(entity.expansion_text, None)

        with self.subTest("PUBLIC"):
            xml = "<!ENTITY Name PUBLIC 'some_uri' 'some_other_uri' >"
            entity, _ = EntityFactory.parse_from_xml(xml, MockDTD())

            self.assertEqual(entity.type, Entity.Type.GENERAL)
            self.assertEqual(entity.external, True)
            self.assertEqual(entity.parsed, True)
            self.assertEqual(entity.name, "Name")
            self.assertEqual(entity.system_uri, 'some_other_uri')
            self.assertEqual(entity.public_uri, 'some_uri')
            self.assertEqual(entity.notation, None)
            self.assertEqual(entity.expansion_text, None)

    def test_external_parameter(self):
        with self.subTest("SYSTEM"):
            xml = "<!ENTITY % Name SYSTEM 'some_uri' >"
            entity, _ = EntityFactory.parse_from_xml(xml, MockDTD())

            self.assertEqual(entity.type, Entity.Type.PARAMETER)
            self.assertEqual(entity.external, True)
            self.assertEqual(entity.parsed, True)
            self.assertEqual(entity.name, "Name")
            self.assertEqual(entity.system_uri, 'some_uri')
            self.assertEqual(entity.public_uri, None)
            self.assertEqual(entity.notation, None)
            self.assertEqual(entity.expansion_text, None)

        with self.subTest("PUBLIC"):
            xml = "<!ENTITY % Name PUBLIC 'some_uri' 'some_other_uri' >"
            entity, _ = EntityFactory.parse_from_xml(xml, MockDTD())

            self.assertEqual(entity.type, Entity.Type.PARAMETER)
            self.assertEqual(entity.external, True)
            self.assertEqual(entity.parsed, True)
            self.assertEqual(entity.name, "Name")
            self.assertEqual(entity.system_uri, 'some_other_uri')
            self.assertEqual(entity.public_uri, 'some_uri')
            self.assertEqual(entity.notation, None)
            self.assertEqual(entity.expansion_text, None)

    def test_unparsed(self):
        with self.subTest("SYSTEM"):
            xml = "<!ENTITY Name SYSTEM 'some_uri' NDATA notation>"
            entity, _ = EntityFactory.parse_from_xml(xml, MockDTD())

            self.assertEqual(entity.type, Entity.Type.GENERAL)
            self.assertEqual(entity.external, True)
            self.assertEqual(entity.parsed, False)
            self.assertEqual(entity.name, "Name")
            self.assertEqual(entity.system_uri, 'some_uri')
            self.assertEqual(entity.public_uri, None)
            self.assertEqual(entity.notation, 'notation')
            self.assertEqual(entity.expansion_text, None)

        with self.subTest("PUBLIC"):
            xml = "<!ENTITY Name PUBLIC 'some_uri' 'some_other_uri' NDATA notation>"
            entity, _ = EntityFactory.parse_from_xml(xml, MockDTD())

            self.assertEqual(entity.type, Entity.Type.GENERAL)
            self.assertEqual(entity.external, True)
            self.assertEqual(entity.parsed, False)
            self.assertEqual(entity.name, "Name")
            self.assertEqual(entity.system_uri, 'some_other_uri')
            self.assertEqual(entity.public_uri, 'some_uri')
            self.assertEqual(entity.notation, 'notation')
            self.assertEqual(entity.expansion_text, None)

    """
        ================
        PARSE-END TESTS
        ================
    """

    def test_ends_parse_on_close(self):
        xml = "<!ENTITY name 'value'>Some text"
        entity, unparsed_xml = EntityFactory.parse_from_xml(xml, MockDTD())

        self.assertEqual("Some text", unparsed_xml)

    """
        ======================
        WELL-FORMEDNESS TESTS
        ======================
    """

    def test_no_unparsed_parameter_entities(self):
        with self.subTest("SYSTEM"):
            xml = "<!ENTITY % Name SYSTEM 'some_uri' NDATA notation>"

            with self.assertRaises(XMLError):
                EntityFactory.parse_from_xml(xml, MockDTD())

        with self.subTest("PUBLIC"):
            xml = "<!ENTITY % Name PUBLIC 'some_uri' 'some_other_uri' NDATA notation>"

            with self.assertRaises(XMLError):
                EntityFactory.parse_from_xml(xml, MockDTD())

    def test_external_entity_declaration_conformance(self):
        with self.subTest("SYSEM"):
            xml = "<!ENTITY Name SYSEM 'some_uri' >"

            with self.assertRaises(XMLError):
                EntityFactory.parse_from_xml(xml, MockDTD())

        with self.subTest("PUB"):
            xml = "<!ENTITY Name PUB 'some_uri' 'some_other_uri' >"

            with self.assertRaises(XMLError):
                EntityFactory.parse_from_xml(xml, MockDTD())


class EntityTypeTests(unittest.TestCase):
    def test_general(self):
        xml = "Name 'Value'>"
        entity_type, _ = EntityFactory.parse_entity_type(xml, "")

        self.assertEqual(Entity.Type.GENERAL, entity_type)

    def test_parameter(self):
        xml = "% Name 'Value'>"
        entity_type, _ = EntityFactory.parse_entity_type(xml, "")

        self.assertEqual(Entity.Type.PARAMETER, entity_type)

    """
        ================
        PARSE-END TESTS
        ================
    """

    def test_ends_parse_general(self):
        xml = "Name 'Value'>"
        _, remaining_xml = EntityFactory.parse_entity_type(xml, "")

        self.assertEqual("Name 'Value'>", remaining_xml)

    def test_ends_parse_parameter(self):
        xml = "% Name 'Value'>"
        _, remaining_xml = EntityFactory.parse_entity_type(xml, "")

        self.assertEqual("Name 'Value'>", remaining_xml)


class NameTests(unittest.TestCase):
    """
        =============
        NAME PARSING
        =============
    """

    def test_name_parsing(self):
        name, _ = EntityFactory.parse_name("Name ", "", MockDTD(), False)

        self.assertEqual("Name", name)

    def test_parse_ends_after_name(self):
        _, unparsed_xml = EntityFactory.parse_name("Name MOREXML", "", MockDTD(), False)

        self.assertEqual("MOREXML", unparsed_xml)

    """
        =====================
        FORBIDDEN CHARACTERS
        =====================
    """

    def test_forbidden_name_start_characters(self):
        for char in ["-", ".", "0", "7", "\u0305"]:
            with self.subTest(char):
                xml = f"{char}Name "
                with self.assertRaises(DisallowedCharacterError):
                    EntityFactory.parse_name(xml, "", MockDTD(), False)

    def test_forbidden_name_characters(self):
        for char in ["\u00d7", "\u00f7", "\u037e", "\u2030"]:
            with self.subTest(char):
                xml = f"Na{char}me "
                with self.assertRaises(DisallowedCharacterError):
                    EntityFactory.parse_name(xml, "", MockDTD(), False)

    def test_forbidden_xml_name(self):
        with self.subTest("xml"):
            xml = f"xml "

            with self.assertRaises(XMLError):
                EntityFactory.parse_name(xml, "", MockDTD(), False)

        with self.subTest("XmL"):
            xml = f"XmL "

            with self.assertRaises(XMLError):
                EntityFactory.parse_name(xml, "", MockDTD(), False)

        with self.subTest("xmlBlah"):
            xml = f"xmlBlah "

            with self.assertRaises(XMLError):
                EntityFactory.parse_name(xml, "", MockDTD(), False)

        with self.subTest("XmLBlah"):
            xml = f"XmLBlah "

            with self.assertRaises(XMLError):
                EntityFactory.parse_name(xml, "", MockDTD(), False)


class ValueTests(unittest.TestCase):
    def test_parsing(self):
        with self.subTest('"'):
            name, _ = EntityFactory.parse_internal_entity_value('"Value"', "", MockDTD(), False)
            self.assertEqual("Value", name)

        with self.subTest("'"):
            name, _ = EntityFactory.parse_internal_entity_value("'Value'", "", MockDTD(), False)
            self.assertEqual("Value", name)

    def test_parse_ends_after_value(self):
        with self.subTest('"'):
            xml = '"Value">MOREXML'
            _, remaining_xml = EntityFactory.parse_internal_entity_value(xml, "", MockDTD(), False)

            self.assertEqual(">MOREXML", remaining_xml)

        with self.subTest("'"):
            xml = "'Value'>MOREXML"

            _, remaining_xml = EntityFactory.parse_internal_entity_value(xml, "", MockDTD(), False)
            self.assertEqual(">MOREXML", remaining_xml)

    """
        =====================
        FORBIDDEN CHARACTERS
        =====================
    """
    def test_forbidden_characters(self):
        for char in ["&", "%", "\u0001", "\u0003", "\u0010", "\ufffe", "\uffff"]:
            with self.subTest(f"Char: {char}"):
                xml = f"'Value {char}'"

                with self.assertRaises(XMLError):
                    EntityFactory.parse_internal_entity_value(xml, "", MockDTD(), False)

    """
        =================
        ENTITY EXPANSION
        =================
    """

    def test_ignores_general_entites(self):
        entity = MockEntity("entity", "SomeValue")
        dtd = MockDTD(general={"entity": entity})

        xml = "'SomeValue &entity;'"
        value, _ = EntityFactory.parse_internal_entity_value(xml, "", dtd, False)

        self.assertEqual(value, "SomeValue &entity;")

    def test_expands_external_parameter_entities(self):
        param_entity = MockEntity("entity", "ENTITY TEXT", entity_type=Entity.Type.PARAMETER)
        dtd = MockDTD(parameter={"entity": param_entity})

        xml = "'SomeValue %entity;'"
        value, _ = EntityFactory.parse_internal_entity_value(xml, "", dtd, True)

        self.assertEqual("SomeValue ENTITY TEXT", value)

    def test_disallows_internal_parameter_entities(self):
        param_entity = MockEntity("entity", "ENTITY TEXT", entity_type=Entity.Type.PARAMETER)
        dtd = MockDTD(parameter={"entity": param_entity})

        xml = "'SomeValue %entity;'"

        with self.assertRaises(XMLError):
            value, _ = EntityFactory.parse_internal_entity_value(xml, "", dtd, False)

    def test_expands_decimal_character_reference(self):
        for num, char in [(118, "v"), (279, "ė"), (632, "ɸ"), (986, "Ϛ"), (1948, "ޜ")]:
            with self.subTest(f"&#{num}; -> {char}"):
                xml = f"'SomeValue &#{num};'"
                value, _ = EntityFactory.parse_internal_entity_value(xml, "", MockDTD(), False)

                self.assertEqual(value, f"SomeValue {char}")

    def test_expands_hexadecimal_character_reference(self):
        for num, char in [("76", "v"), ("117", "ė"), ("278", "ɸ"), ("3da", "Ϛ"), ("79c", "ޜ")]:
            with self.subTest(f"&#x{num}; -> {char}"):
                xml = f"'SomeValue &#x{num};'"
                value, _ = EntityFactory.parse_internal_entity_value(xml, "", MockDTD(), False)

                self.assertEqual(value, f"SomeValue {char}")


# todo - External entity tests
