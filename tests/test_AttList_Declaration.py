import unittest

from xml_parser.dtd.AttListDeclaration import AttributeDeclFactory
from xml_parser.errors import XMLError, DisallowedCharacterError
from tests.mocks.MockDTD import MockDTD


class AttListTests(unittest.TestCase):
    def test_attlist_parsing(self):
        xml = "<!ATTLIST Name Att1 ID #REQUIRED Att2 NMTOKEN #IMPLIED Att3 CDATA #FIXED 'Default'>MORE XML"
        element, attributes, remaining_xml = AttributeDeclFactory.parse_from_xml(xml, MockDTD(), False)

        self.assertEqual("Name", element)
        
        self.assertEqual("Att1", attributes["Att1"].name)
        self.assertEqual("ID", attributes["Att1"].value_type)
        self.assertEqual("REQUIRED", attributes["Att1"].default_declaration)
        
        self.assertEqual("Att2", attributes["Att2"].name)
        self.assertEqual("NMTOKEN", attributes["Att2"].value_type)
        self.assertEqual("IMPLIED", attributes["Att2"].default_declaration)
        
        self.assertEqual("Att3", attributes["Att3"].name)
        self.assertEqual("CDATA", attributes["Att3"].value_type)
        self.assertEqual("FIXED", attributes["Att3"].default_declaration)
        self.assertEqual("Default", attributes["Att3"].default_value)
        
        self.assertEqual("MORE XML", remaining_xml)

    def test_no_repeated_attributes(self):
        xml = "<!ATTLIST Name Att ID #REQUIRED Att NMTOKEN #IMPLIED>MORE XML"
        
        with self.assertRaises(XMLError):
            AttributeDeclFactory.parse_from_xml(xml, MockDTD(), False)

    """
        ===================
        MISSING WHITESPACE
        ===================
    """
    def test_missing_whitespace_before_name(self):
        xml = "<!ATTLISTName Att1 ID #REQUIRED>MOREXML"
        with self.assertRaises(XMLError):
            AttributeDeclFactory.parse_from_xml(xml, MockDTD(), False)

    def test_missing_whitespace_after_name(self):
        xml = "<!ATTLIST NameAtt1 ID #REQUIRED>MOREXML"
        with self.assertRaises(XMLError):
            AttributeDeclFactory.parse_from_xml(xml, MockDTD(), False)

    def test_missing_whitespace_between_attributes(self):
        xml = "<!ATTLIST Name Att1 ID #REQUIREDAtt2 NMTOKEN #IMPLIED>MOREXML"
        with self.assertRaises(XMLError):
            AttributeDeclFactory.parse_from_xml(xml, MockDTD(), False)

    """
        =============
        NAME PARSING
        =============
    """
    
    def test_name_parsing(self):
        with self.subTest("Whitespace"):
            xml = " Name MOREXML"
            element, remaining_xml = AttributeDeclFactory.parse_element_name(xml, "", MockDTD(), False)
            
            self.assertEqual("Name", element)
            self.assertEqual(" MOREXML", remaining_xml)
        with self.subTest(">"):
            xml = " Name>MOREXML"
            element, remaining_xml = AttributeDeclFactory.parse_element_name(xml, "", MockDTD(), False)

            self.assertEqual("Name", element)
            self.assertEqual(">MOREXML", remaining_xml)

    def test_disallowed_name_start_characters(self):
        for char in ["-", ".", "0", "7", "\u0305"]:
            with self.subTest(char):
                xml = f" {char}Name MOREXML"
                with self.assertRaises(DisallowedCharacterError):
                    AttributeDeclFactory.parse_element_name(xml, "", MockDTD(), False)

    def test_disallowed_name_characters(self):
        for char in ["\u0001", "\u0003", "\u0010", "\ufffe", "\uffff"]:
            with self.subTest(char):
                xml = f" {char}Name MOREXML"
                with self.assertRaises(DisallowedCharacterError):
                    AttributeDeclFactory.parse_element_name(xml, "", MockDTD(), False)


class AttributeDeclarationTest(unittest.TestCase):
    def test_attribute_parsing(self):
        xml = "Name ID #IMPLIED MORE XML"
        attribute, remaining_xml = AttributeDeclFactory.parse_attribute(xml, "", MockDTD(), False)

        self.assertEqual("Name", attribute.name)
        self.assertEqual("ID", attribute.value_type)
        self.assertEqual("IMPLIED", attribute.default_declaration)
        self.assertEqual(" MORE XML", remaining_xml)

    """
        ===================
        MISSING WHITESPACE
        ===================
    """

    def test_missing_whitespace_after_name(self):
        xml = "NameID #IMPLIED MORE XML"
        with self.assertRaises(XMLError):
            AttributeDeclFactory.parse_attribute(xml, "", MockDTD(), False)

    def test_missing_whitespace_after_atttype(self):
        xml = "Name ID#IMPLIED MORE XML"
        with self.assertRaises(XMLError):
            AttributeDeclFactory.parse_attribute(xml, "", MockDTD(), False)

    """
        =============
        NAME PARSING
        =============
    """

    def test_name_parsing(self):
        xml = "Name MOREXML"
        name, remaining_xml = AttributeDeclFactory.parse_attribute_name(xml, "", MockDTD(), False)
        self.assertEqual("Name", name)
        self.assertEqual("MOREXML", remaining_xml)

    def test_disallowed_name_start_characters(self):
        for char in ["-", ".", "0", "7", "\u0305"]:
            with self.subTest(char):
                xml = f" {char}Name MOREXML"
                with self.assertRaises(DisallowedCharacterError):
                    AttributeDeclFactory.parse_attribute_name(xml, "", MockDTD(), False)

    def test_disallowed_name_characters(self):
        for char in ["\u0001", "\u0003", "\u0010", "\ufffe", "\uffff"]:
            with self.subTest(char):
                xml = f" {char}Name MOREXML"
                with self.assertRaises(DisallowedCharacterError):
                    AttributeDeclFactory.parse_attribute_name(xml, "", MockDTD(), False)


class AttributeTypeDeclarationTest(unittest.TestCase):
    """
        ==========
        TEXT TYPE
        ==========
    """
    def test_cdata_type(self):
        xml = "CDATA XMLCONTINUES"
        value_type, options, unparsed_xml = AttributeDeclFactory.parse_attribute_type(xml, "", MockDTD(), False)

        self.assertEqual("CDATA", value_type)
        self.assertEqual(" XMLCONTINUES", unparsed_xml)

    """
        ================
        TOKENIZED TYPES
        ================
    """
    def test_id_type(self):
        xml = "ID XMLCONTINUES"
        value_type, options, unparsed_xml = AttributeDeclFactory.parse_attribute_type(xml, "", MockDTD(), False)

        self.assertEqual("ID", value_type)
        self.assertEqual(" XMLCONTINUES", unparsed_xml)

    def test_idref_type(self):
        xml = "IDREF XMLCONTINUES"
        value_type, options, unparsed_xml = AttributeDeclFactory.parse_attribute_type(xml, "", MockDTD(), False)

        self.assertEqual("IDREF", value_type)
        self.assertEqual(" XMLCONTINUES", unparsed_xml)

    def test_idrefs_type(self):
        xml = "IDREFS XMLCONTINUES"
        value_type, options, unparsed_xml = AttributeDeclFactory.parse_attribute_type(xml, "", MockDTD(), False)

        self.assertEqual("IDREFS", value_type)
        self.assertEqual(" XMLCONTINUES", unparsed_xml)

    def test_entity_type(self):
        xml = "ENTITY XMLCONTINUES"
        value_type, options, unparsed_xml = AttributeDeclFactory.parse_attribute_type(xml, "", MockDTD(), False)

        self.assertEqual("ENTITY", value_type)
        self.assertEqual(" XMLCONTINUES", unparsed_xml)

    def test_entities_type(self):
        xml = "ENTITIES XMLCONTINUES"
        value_type, options, unparsed_xml = AttributeDeclFactory.parse_attribute_type(xml, "", MockDTD(), False)

        self.assertEqual("ENTITIES", value_type)
        self.assertEqual(" XMLCONTINUES", unparsed_xml)

    def test_nmtoken_type(self):
        xml = "NMTOKEN XMLCONTINUES"
        value_type, options, unparsed_xml = AttributeDeclFactory.parse_attribute_type(xml, "", MockDTD(), False)

        self.assertEqual("NMTOKEN", value_type)
        self.assertEqual(" XMLCONTINUES", unparsed_xml)

    def test_nmtokens_type(self):
        xml = "NMTOKENS XMLCONTINUES"
        value_type, options, unparsed_xml = AttributeDeclFactory.parse_attribute_type(xml, "", MockDTD(), False)

        self.assertEqual("NMTOKENS", value_type)
        self.assertEqual(" XMLCONTINUES", unparsed_xml)

    def test_invalid_type(self):
        with self.assertRaises(XMLError):
            xml = "SOMETYPE XMLCONTINUES"
            AttributeDeclFactory.parse_attribute_type(xml, "", MockDTD(), False)

    """
        ============
        ENUMERATION
        ============
    """
    def test_enumeration_single_option(self):
        xml = "(Name) XMLCONTINUES"
        value_type, options, unparsed_xml = AttributeDeclFactory.parse_attribute_type(xml, "", MockDTD(), False)

        self.assertEqual("ENUMERATION", value_type)
        self.assertEqual(["Name"], options)
        self.assertEqual(" XMLCONTINUES", unparsed_xml)

    def test_enumeration_multiple_options(self):
        with self.subTest("2 options; no whitespace"):
            xml = "(Name1|Name2) XMLCONTINUES"
            value_type, options, unparsed_xml = AttributeDeclFactory.parse_attribute_type(xml, "", MockDTD(), False)

            self.assertEqual("ENUMERATION", value_type)
            self.assertEqual(["Name1", "Name2"], options)
            self.assertEqual(" XMLCONTINUES", unparsed_xml)

        with self.subTest("3 options; whitespace"):
            xml = "( Name1 | Name2 | Name3) XMLCONTINUES"
            value_type, options, unparsed_xml = AttributeDeclFactory.parse_attribute_type(xml, "", MockDTD(), False)

            self.assertEqual("ENUMERATION", value_type)
            self.assertEqual(["Name1", "Name2", "Name3"], options)
            self.assertEqual(" XMLCONTINUES", unparsed_xml)

    def test_enumeration_allowed_name_start_characters(self):
        for char in ["-", ".", "0", "7", "\u0305"]:
            with self.subTest(char):
                xml = f"(Name1|{char}Name2) XMLCONTINUES"
                value_type, options, unparsed_xml = AttributeDeclFactory.parse_attribute_type(xml, "", MockDTD(), False)

                self.assertEqual("ENUMERATION", value_type)
                self.assertEqual(["Name1", f"{char}Name2"], options)
                self.assertEqual(" XMLCONTINUES", unparsed_xml)

    def test_enumeration_disallowed_name_characters(self):
        for char in ["\u0001", "\u0003", "\u0010", "\ufffe", "\uffff"]:
            with self.subTest(char):
                xml = f"(Name1|Na{char}me2) XMLCONTINUES"
                with self.assertRaises(DisallowedCharacterError):
                    AttributeDeclFactory.parse_attribute_type(xml, "", MockDTD(), False)


    """
        =========
        NOTATION
        =========
    """

    def test_notation_single_option(self):
        xml = "NOTATION (Name) XMLCONTINUES"
        value_type, options, unparsed_xml = AttributeDeclFactory.parse_attribute_type(xml, "", MockDTD(), False)

        self.assertEqual("NOTATION", value_type)
        self.assertEqual(["Name"], options)
        self.assertEqual(" XMLCONTINUES", unparsed_xml)

    def test_notation_multiple_options(self):
        with self.subTest("2 options; no whitespace"):
            xml = "NOTATION (Name1|Name2) XMLCONTINUES"
            value_type, options, unparsed_xml = AttributeDeclFactory.parse_attribute_type(xml, "", MockDTD(), False)

            self.assertEqual("NOTATION", value_type)
            self.assertEqual(["Name1", "Name2"], options)
            self.assertEqual(" XMLCONTINUES", unparsed_xml)

        with self.subTest("3 options; whitespace"):
            xml = "( Name1 | Name2 | Name3) XMLCONTINUES"
            value_type, options, unparsed_xml = AttributeDeclFactory.parse_attribute_type(xml, "", MockDTD(), False)

            self.assertEqual("ENUMERATION", value_type)
            self.assertEqual(["Name1", "Name2", "Name3"], options)
            self.assertEqual(" XMLCONTINUES", unparsed_xml)

    def test_notation_disallowed_name_start_characters(self):
        for char in ["-", ".", "0", "7", "\u0305"]:
            with self.subTest(char):
                xml = f"NOTATION (Name1|{char}Name2) XMLCONTINUES"
                with self.assertRaises(DisallowedCharacterError):
                    AttributeDeclFactory.parse_attribute_type(xml, "", MockDTD(), False)

    def test_notation_disallowed_name_characters(self):
        for char in ["\u0001", "\u0003", "\u0010", "\ufffe", "\uffff"]:
            with self.subTest(char):
                xml = f"NOTATION (Name1|Na{char}me2) XMLCONTINUES"
                with self.assertRaises(DisallowedCharacterError):
                    AttributeDeclFactory.parse_attribute_type(xml, "", MockDTD(), False)


class DefaultDeclarationTests(unittest.TestCase):
    """
        ============
        BASIC CASES
        ============
    """
    def test_required(self):
        with self.subTest("Whitespace"):
            xml = " #REQUIRED MOREXML"
            default_type, value, unparsed_xml = AttributeDeclFactory.parse_default_declaration(xml, "", MockDTD, False)
            self.assertEqual("REQUIRED", default_type)
            self.assertEqual(" MOREXML", unparsed_xml)
        with self.subTest(">"):
            xml = " #REQUIRED>MOREXML"
            default_type, value, unparsed_xml = AttributeDeclFactory.parse_default_declaration(xml, "", MockDTD, False)

            self.assertEqual("REQUIRED", default_type)
            self.assertEqual(">MOREXML", unparsed_xml)

    def test_implied(self):
        with self.subTest("Whitespace"):
            xml = " #IMPLIED MOREXML"
            default_type, value, unparsed_xml = AttributeDeclFactory.parse_default_declaration(xml, "", MockDTD, False)

            self.assertEqual("IMPLIED", default_type)
            self.assertEqual(" MOREXML", unparsed_xml)
        with self.subTest(">"):
            xml = " #IMPLIED>MOREXML"
            default_type, value, unparsed_xml = AttributeDeclFactory.parse_default_declaration(xml, "", MockDTD, False)

            self.assertEqual("IMPLIED", default_type)
            self.assertEqual(">MOREXML", unparsed_xml)

    """
        ====================
        DEFAULT VALUE CASES
        ====================
    """
    def test_default_value_parsing(self):
        with self.subTest("Not fixed"):
            xml = " 'Value'>MOREXML"
            default_type, value, unparsed_xml = AttributeDeclFactory.parse_default_declaration(xml, "", MockDTD, False)

            self.assertEqual("DEFAULT", default_type)
            self.assertEqual("Value", value)
            self.assertEqual(">MOREXML", unparsed_xml)

        with self.subTest("Fixed"):
            xml = " #FIXED 'Value'>MOREXML"
            default_type, value, unparsed_xml = AttributeDeclFactory.parse_default_declaration(xml, "", MockDTD, False)

            self.assertEqual("FIXED", default_type)
            self.assertEqual("Value", value)
            self.assertEqual(">MOREXML", unparsed_xml)

    def test_missing_whitespace_after_fixed(self):
        with self.assertRaises(XMLError):
            xml = " #FIXED'Value'>MOREXML"
            AttributeDeclFactory.parse_default_declaration(xml, "", MockDTD(), False)

    def test_disallowed_characters(self):
        for char in ["<", "&", "\u0001", "\u0003", "\u0010", "\ufffe", "\uffff"]:
            with self.subTest(char):
                xml = f" #FIXED 'Val{char}ue'>MOREXML"
                with self.assertRaises(DisallowedCharacterError):
                    AttributeDeclFactory.parse_default_declaration(xml, "", MockDTD(), False)
