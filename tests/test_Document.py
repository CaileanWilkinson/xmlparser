import unittest

from xml_parser.dtd.Entity import Entity
from xml_parser.content.Element import Element
from xml_parser.errors import XMLError
from xml_parser.Document import Document


class DocumentTests(unittest.TestCase):
    """
        ====================
        BASIC PARSING TESTS
        ====================
    """

    def test_with_xmldeclaration(self):
        document = Document("<?xml version='1.0' encoding='utf-8' standalone='yes'?>  <root></root>")
        document.parse()

        self.assertEqual("1.0", document.version)
        self.assertEqual("utf-8", document.encoding)
        self.assertEqual(True, document.standalone)

        self.assertIsInstance(document.file, Element)
        self.assertEqual(document.file.name, "root")

    def test_without_xmldeclaration(self):
        with self.subTest("Open tag"):
            document = Document("<root></root>")
            document.parse()

            self.assertIsInstance(document.file, Element)
            self.assertEqual(document.file.name, "root")
        with self.subTest("Closed tag"):
            document = Document("<root/>")
            document.parse()

            self.assertIsInstance(document.file, Element)
            self.assertEqual(document.file.name, "root")

    def test_with_empty_dtd(self):
        document = Document("""
        <?xml version='1.0' encoding='utf-8' standalone='yes'?>  
        <!DOCTYPE root []>
        
        <root></root>
        """)
        document.parse()

        self.assertEqual("1.0", document.version)
        self.assertEqual("utf-8", document.encoding)
        self.assertEqual(True, document.standalone)

        self.assertIsInstance(document.file, Element)
        self.assertEqual(document.file.name, "root")

    def test_with_fluff(self):
        document = Document("""
        <?xml version='1.0' encoding='utf-8' standalone='yes'?>  
        <!DOCTYPE root []>
        
        <?Target A rogue processing instruction?>
        <!-- And even a comment! -->
        <root></root>
        <!-- Another comment -->
        <?Target And more PIs?>
        <?Target?>
        """)
        document.parse()

        self.assertEqual("1.0", document.version)
        self.assertEqual("utf-8", document.encoding)
        self.assertEqual(True, document.standalone)

        self.assertIsInstance(document.file, Element)
        self.assertEqual(document.file.name, "root")
        self.assertEqual(3, len(document.leading_processing_instructions))

    """
        ======================
        WELL-FORMEDNESS TESTS
        ======================
    """

    def test_missing_root_element(self):
        self.fail()

    def test_only_one_root_element(self):
        document = Document("<?xml version='1.0' encoding='utf-8' standalone='yes'?>  <root1></root1> <root2></root2>")
        with self.assertRaises(XMLError):
            document.parse()

    def test_no_superfluous_characters(self):
        with self.subTest("Before xml declaration"):
            document = Document("some text<?xml version='1.0'?><root></root>")
            with self.assertRaises(XMLError):
                document.parse()
        with self.subTest("Between xml declaration and dtd"):
            document = Document("<?xml version='1.0'?>some text<!DOCTYPE root []><root></root>")
            with self.assertRaises(XMLError):
                document.parse()
        with self.subTest("Between dtd and root element"):
            document = Document("<?xml version='1.0'?><!DOCTYPE root []>some text<root></root>")
            with self.assertRaises(XMLError):
                document.parse()
        with self.subTest("After root element"):
            document = Document("<?xml version='1.0'?><!DOCTYPE root []><root></root>some text")
            with self.assertRaises(XMLError):
                document.parse()


class XMLDeclarationTests(unittest.TestCase):
    """
        ====================
        BASIC PARSING TESTS
        ====================
    """

    def test_version_parsing(self):
        with self.subTest("With space"):
            document = Document("")
            document._Document__parse_xml_declaration("<?xml version = '1.0' ?>")
            self.assertEqual("1.0", document.version)
        with self.subTest("Without space"):
            document = Document("")
            document._Document__parse_xml_declaration("<?xml version='1.0'?>")
            self.assertEqual("1.0", document.version)
        with self.subTest("Invalid version 2.0"):
            document = Document("")
            with self.assertRaises(XMLError):
                document._Document__parse_xml_declaration("<?xml version='2.0'?>")
        with self.subTest("Valid version 1.1"):
            document = Document("")
            document._Document__parse_xml_declaration("<?xml version='1.1'?>")
            self.assertEqual("1.1", document.version)

    def test_encoding_parsing(self):
        document = Document("")
        document._Document__parse_xml_declaration("<?xml version='1.0' encoding='utf-8'?>")
        self.assertEqual("1.0", document.version)
        self.assertEqual("utf-8", document.encoding)

    def test_standalone_parsing(self):
        with self.subTest("With encoding"):
            document = Document("")
            document._Document__parse_xml_declaration("<?xml version='1.0' encoding='utf-8' standalone='no'?>")
            self.assertEqual("1.0", document.version)
            self.assertEqual("utf-8", document.encoding)
            self.assertEqual(False, document.standalone)
        with self.subTest("Without encoding"):
            document = Document("")
            document._Document__parse_xml_declaration("<?xml version='1.0' standalone='yes'?>")
            self.assertEqual("1.0", document.version)
            self.assertEqual(True, document.standalone)
        with self.subTest("Invalid value"):
            document = Document("")
            with self.assertRaises(XMLError):
                document._Document__parse_xml_declaration("<?xml version='1.0' standalone='maybe'?>")

    """ 
        ======================
        WELL-FORMEDNESS TESTS    
        ======================
    """

    def test_missing_whitespace(self):
        with self.subTest("Before version"):
            document = Document("")
            with self.assertRaises(XMLError):
                document._Document__parse_xml_declaration("<?xmlversion='1.0'?>")
        with self.subTest("After version -> encoding"):
            document = Document("")
            with self.assertRaises(XMLError):
                document._Document__parse_xml_declaration("<?xml version='1.0'encoding='utf-8'?>")
        with self.subTest("After version -> standalone"):
            document = Document("")
            with self.assertRaises(XMLError):
                document._Document__parse_xml_declaration("<?xml version='1.0'standalone='no'?>")
        with self.subTest("After encoding -> standalone"):
            document = Document("")
            with self.assertRaises(XMLError):
                document._Document__parse_xml_declaration("<?xml version='1.0' encoding='utf-8'standalone='no'?>")

    def test_invalid_keyword(self):
        with self.subTest("Versionn"):
            document = Document("")
            with self.assertRaises(XMLError):
                document._Document__parse_xml_declaration("<?xml versionn='1.0'?>")
        with self.subTest("Versio"):
            document = Document("")
            with self.assertRaises(XMLError):
                document._Document__parse_xml_declaration("<?xml versio='1.0'?>")
        with self.subTest("encodin"):
            document = Document("")
            with self.assertRaises(XMLError):
                document._Document__parse_xml_declaration("<?xml version='1.0' encodin='utf-8?>")
        with self.subTest("standalne"):
            document = Document("")
            with self.assertRaises(XMLError):
                document._Document__parse_xml_declaration("<?xml version='1.0' standalne='no'?>")

    def test_misordered_xml_declaration(self):
        with self.subTest("Encoding -> Version"):
            document = Document("")
            with self.assertRaises(XMLError):
                document._Document__parse_xml_declaration("<?xml encoding='utf-8' version='1.0'?>")
        with self.subTest("Version -> Standalone -> Encoding"):
            document = Document("")
            with self.assertRaises(XMLError):
                document._Document__parse_xml_declaration("<?xml version='1.0' standalone='no' encoding='utf-8'?>")
        with self.subTest("Standalone -> Version"):
            document = Document("")
            with self.assertRaises(XMLError):
                document._Document__parse_xml_declaration("<?xml standalone='no' version='1.0'?>")

    def test_missing_version(self):
        with self.subTest("Encoding"):
            document = Document("")
            with self.assertRaises(XMLError):
                document._Document__parse_xml_declaration("<?xml encoding='utf-8'?>")
        with self.subTest("Standalone"):
            document = Document("")
            with self.assertRaises(XMLError):
                document._Document__parse_xml_declaration("<?xml standalone='no'?>")
        with self.subTest("Both"):
            document = Document("")
            with self.assertRaises(XMLError):
                document._Document__parse_xml_declaration("<?xml encoding='utf-8' standalone='yes'?>")


class DoctypeDeclarationTests(unittest.TestCase):
    """
        ==================
        ROOT NAME PARSING
        ==================
    """

    def test_root_name_parsing(self):
        with self.subTest("With no subset"):
            document = Document("")
            document._Document__parse_doctype_declaration("<!DOCTYPE root>")
            self.assertEqual("root", document.dtd_name)
        with self.subTest("With empty internal subset"):
            document = Document("")
            document._Document__parse_doctype_declaration("<!DOCTYPE root []>")
            self.assertEqual("root", document.dtd_name)

    def test_forbidden_name_start_characters(self):
        for char in ["-", ".", "0", "7", "\u0305"]:
            with self.subTest(char):
                document = Document("")
                with self.assertRaises(XMLError):
                    document._Document__parse_doctype_declaration(f"<!DOCTYPE {char}root>")

    def test_forbidden_name_characters(self):
        for char in ["\u00d7", "\u00f7", "\u037e", "\u2030"]:
            with self.subTest(char):
                document = Document("")
                with self.assertRaises(XMLError):
                    document._Document__parse_doctype_declaration(f"<!DOCTYPE root{char}>")

    """
        =============================
        EXTERNAL DECLARATION PARSING
        =============================
    """

    def test_external_declaration_parsing(self):
        with self.subTest("SYSTEM"):
            document = Document("")
            document._Document__parse_doctype_declaration("<!DOCTYPE root SYSTEM 'uri'>")
            self.assertEqual("root", document.dtd_name)
            self.assertEqual("uri", document.external_system_uri)
        with self.subTest("PUBLIC"):
            document = Document("")
            document._Document__parse_doctype_declaration("<!DOCTYPE root PUBLIC 'uri1' 'uri2'>")
            self.assertEqual("root", document.dtd_name)
            self.assertEqual("uri1", document.external_public_uri)
            self.assertEqual("uri2", document.external_system_uri)
        with self.subTest("SYSTEM with internal subset"):
            document = Document("")
            document._Document__parse_doctype_declaration("<!DOCTYPE root SYSTEM 'uri' []>")
            self.assertEqual("root", document.dtd_name)
            self.assertEqual("uri", document.external_system_uri)

    # todo - invalid uris, keywords, etc

    """
        ====================
        ENTITY DECLARATIONS
        ====================
    """

    def test_internal_general_entity_definition(self):
        document = Document("")
        document._Document__parse_doctype_declaration("<!DOCTYPE root [<!ENTITY entity 'blah'>]>")
        self.assertEqual("blah", document.entities["entity"].expansion_text)
        self.assertEqual(Entity.Type.GENERAL, document.entities["entity"].type)
        self.assertEqual(False, document.entities["entity"].external)

    def test_external_general_entity_definition(self):
        with self.subTest("SYSTEM"):
            document = Document("")
            document._Document__parse_doctype_declaration("<!DOCTYPE root [<!ENTITY entity SYSTEM 'uri'>]>")
            self.assertEqual("uri", document.entities["entity"].system_uri)
            self.assertEqual(Entity.Type.GENERAL, document.entities["entity"].type)
            self.assertEqual(True, document.entities["entity"].external)
            self.assertEqual(True, document.entities["entity"].parsed)
        with self.subTest("PUBLIC"):
            document = Document("")
            document._Document__parse_doctype_declaration("<!DOCTYPE root [<!ENTITY entity PUBLIC 'uri1' 'uri2'>]>")
            self.assertEqual("uri1", document.entities["entity"].public_uri)
            self.assertEqual("uri2", document.entities["entity"].system_uri)
            self.assertEqual(Entity.Type.GENERAL, document.entities["entity"].type)
            self.assertEqual(True, document.entities["entity"].external)
            self.assertEqual(True, document.entities["entity"].parsed)

    def test_internal_parameter_entity_definition(self):
        document = Document("")
        document._Document__parse_doctype_declaration("<!DOCTYPE root [<!ENTITY % entity 'blah'>]>")
        self.assertEqual("blah", document.parameter_entities["entity"].expansion_text)
        self.assertEqual(Entity.Type.PARAMETER, document.parameter_entities["entity"].type)
        self.assertEqual(False, document.parameter_entities["entity"].external)

    def test_external_parameter_entity_definition(self):
        with self.subTest("SYSTEM"):
            document = Document("")
            document._Document__parse_doctype_declaration("<!DOCTYPE root [<!ENTITY % entity SYSTEM 'uri'>]>")
            self.assertEqual("uri", document.parameter_entities["entity"].system_URI)
            self.assertEqual(Entity.Type.PARAMETER, document.parameter_entities["entity"].type)
            self.assertEqual(True, document.parameter_entities["entity"].external)
            self.assertEqual(True, document.parameter_entities["entity"].parsed)
        with self.subTest("PUBLIC"):
            document = Document("")
            document._Document__parse_doctype_declaration("<!DOCTYPE root [<!ENTITY % entity PUBLIC 'uri1' 'uri2'>]>")
            self.assertEqual("uri1", document.parameter_entities["entity"].public_URI)
            self.assertEqual("uri2", document.parameter_entities["entity"].system_URI)
            self.assertEqual(Entity.Type.PARAMETER, document.parameter_entities["entity"].type)
            self.assertEqual(True, document.parameter_entities["entity"].external)
            self.assertEqual(True, document.parameter_entities["entity"].parsed)

    def test_unparsed_entity_definition(self):
        with self.subTest("SYSTEM"):
            document = Document("")
            document._Document__parse_doctype_declaration(
                "<!DOCTYPE root [<!ENTITY entity SYSTEM 'uri' NDATA notation>]>")
            self.assertEqual("uri", document.entities["entity"].system_uri)
            self.assertEqual(Entity.Type.GENERAL, document.entities["entity"].type)
            self.assertEqual(True, document.entities["entity"].external)
            self.assertEqual(False, document.entities["entity"].parsed)
            self.assertEqual("notation", document.entities["entity"].notation)
        with self.subTest("PUBLIC"):
            document = Document("")
            document._Document__parse_doctype_declaration(
                "<!DOCTYPE root [<!ENTITY entity PUBLIC 'uri1' 'uri2' NDATA notation>]>")
            self.assertEqual("uri1", document.entities["entity"].public_uri)
            self.assertEqual("uri2", document.entities["entity"].system_uri)
            self.assertEqual(Entity.Type.GENERAL, document.entities["entity"].type)
            self.assertEqual(True, document.entities["entity"].external)
            self.assertEqual(False, document.entities["entity"].parsed)
            self.assertEqual("notation", document.entities["entity"].notation)

    def test_name_collisions(self):
        with self.subTest("General and parameter entities occupy different namespaces"):
            document = Document("")
            document._Document__parse_doctype_declaration("""<!DOCTYPE root [
            <!ENTITY % entity 'SOME TEXT'>
            <!ENTITY entity 'SOME OTHER TEXT'>
            ]>""")
            self.assertEqual("SOME TEXT", document.parameter_entities["entity"].expansion_text)
            self.assertEqual("SOME OTHER TEXT", document.entities["entity"].expansion_text)
        with self.subTest("General entities"):
            document = Document("")
            document._Document__parse_doctype_declaration("""<!DOCTYPE root [
            <!ENTITY entity 'SOME TEXT'>
            <!ENTITY entity 'SOME OTHER TEXT'>
            ]>""")
            self.assertEqual("SOME TEXT", document.entities["entity"].expansion_text)
        with self.subTest("Parameter entities"):
            document = Document("")
            document._Document__parse_doctype_declaration("""<!DOCTYPE root [
            <!ENTITY % entity 'SOME TEXT'>
            <!ENTITY % entity 'SOME OTHER TEXT'>
            ]>""")
            self.assertEqual("SOME TEXT", document.parameter_entities["entity"].expansion_text)

    """
        ========================
        INTERNAL SUBSET PARSING
        ========================
    """

    def test_parameter_entity_expansion(self):
        with self.subTest("In DTD"):
            document = Document("")
            document._Document__parse_doctype_declaration("""<!DOCTYPE root [
            <!ENTITY % entity '<!ENTITY entity2 "SOME TEXT">'>
            %entity;
            ]>""")
            self.assertEqual("SOME TEXT", document.entities["entity2"].expansion_text)
        with self.subTest("In general entity"):
            document = Document("")
            document._Document__parse_doctype_declaration("""<!DOCTYPE root [
            <!ENTITY % entity 'SOME TEXT'>
            <!ENTITY entity2 'SOME %entity; OTHER TEXT'>
            ]>""")
            self.assertEqual("SOME TEXT", document.parameter_entities["entity"].expansion_text)
            self.assertEqual("SOME SOME TEXT OTHER TEXT", document.entities["entity2"].expansion_text)

    def test_parameter_reference_within_markup(self):
        with self.subTest("ELEMENT declaration"):
            document = Document("")
            with self.assertRaises(XMLError):
                document._Document__parse_doctype_declaration("""<!DOCTYPE root [
                <!ENTITY % entity 'blah, blahblah'>'
                <!ELEMENT root (%entity;)>
                ]>""")
        with self.subTest("NOTATION declaration"):
            document = Document("")
            with self.assertRaises(XMLError):
                document._Document__parse_doctype_declaration("""<!DOCTYPE root [
                <!ENTITY % entity 'SYSTEM \"blahblah\"'>'
                <!NOTATION blah %entity;>
                ]>""")
        with self.subTest("ATTLIST declaration"):
            document = Document("")
            with self.assertRaises(XMLError):
                document._Document__parse_doctype_declaration("""<!DOCTYPE root [
                <!ENTITY % entity 'CDATA #REQUIRED'>'
                <!ATTLIST root %entity;>
                ]>""")

    def test_no_text_in_internal_subset(self):
        document = Document("")
        with self.assertRaises(XMLError):
            document._Document__parse_doctype_declaration("""<!DOCTYPE root [
            <!ENTITY % entity 'blah, blahblah'>'
            some disallowed text
            ]>""")
