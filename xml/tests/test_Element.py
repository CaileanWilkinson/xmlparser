from classes.Element import Element
from tests.mocks.MockEntity import MockEntity
from classes.Error import XMLError
import unittest


class ElementTests(unittest.TestCase):
    """
        ===========
        NAME TESTS
        ===========
    """

    def test_name_parsing(self):
        with self.subTest("Self-closing"):
            element = Element("<Element/> some text")
            element.parse_to_end({})
            self.assertEqual("Element", element.name)
        with self.subTest("Open"):
            element = Element("<Element>some text</Element> some more text")
            element.parse_to_end({})
            self.assertEqual("Element", element.name)

    def test_disallowed_xml_name(self):
        with self.subTest("xml"):
            element = Element("<xmlElement/>")
            with self.assertRaises(XMLError):
                element.parse_to_end({})
        with self.subTest("XmL"):
            element = Element("<XmLElement/>")
            with self.assertRaises(XMLError):
                element.parse_to_end({})

    def test_disallowed_name_start_characters(self):
        for char in ["-", ".", "0", "7", "\u0305"]:
            with self.subTest(char):
                element = Element(f"<{char}xmlElement/>")
                with self.assertRaises(XMLError):
                        element.parse_to_end({})

    def test_disallowed_name_characters(self):
        for char in ["\u0001", "\u0003", "\u0010", "\ufffe", "\uffff"]:
            with self.subTest(char):
                element = Element(f"<{char}xmlElement/>")
                with self.assertRaises(XMLError):
                    element.parse_to_end({})

    """
        ================
        ATTRIBUTE TESTS
        ================
    """

    def test_attribute_parsing(self):
        with self.subTest("Self-closing - \' delimiters"):
            element = Element("<Element attr='Value'/> some text")
            element.parse_to_end({})
            self.assertEqual({"attr": "Value"}, element.attributes)
        with self.subTest("Self-closing - \" delimiters"):
            element = Element("<Element attr=\"Value\"/> some text")
            element.parse_to_end({})
            self.assertEqual({"attr": "Value"}, element.attributes)
        with self.subTest("Self-closing - with whitespace"):
            element = Element("<Element attr = \"Value\"/> some text")
            element.parse_to_end({})
            self.assertEqual({"attr": "Value"}, element.attributes)
        with self.subTest("Open"):
            element = Element("<Element attr='Value'>some text</Element> some more text")
            element.parse_to_end({})
            self.assertEqual({"attr": "Value"}, element.attributes)

    def test_multiple_attribute_parsing(self):
        element = Element("<Element attr1='Value1' attr2='Value2'/> some text")
        element.parse_to_end({})
        self.assertEqual({"attr1": "Value1", "attr2": "Value2"}, element.attributes)

    def test_attribute_general_entity_replacement(self):
        entity = MockEntity("entity", expansion_text="ENTITY TEXT")
        element = Element("<Element attr='Entity &entity; text'/>")
        element.parse_to_end({"entity": entity})
        self.assertEqual("Entity ENTITY TEXT text", element.attributes["attr"])

    def test_attribute_missing_general_entity(self):
        element = Element("<Element attr='Entity &entity; text'/>")
        with self.assertRaises(XMLError):
            element.parse_to_end({})

    def test_attribute_ignores_parameter_entity(self):
        element = Element("<Element attr='Entity %entity; text'/>")
        element.parse_to_end({})
        self.assertEqual("Entity %entity; text", element.attributes["attr"])

    def test_attribute_decimal_character_reference_replacement(self):
        for num, char in [(118, "v"), (279, "ė"), (632, "ɸ"), (986, "Ϛ"), (1948, "ޜ")]:
            with self.subTest(f"&#{num}; -> {char}"):
                element = Element(f"<Element attr='Entity &#{num}; text'/>")
                element.parse_to_end({})
                self.assertEqual(f"Entity {char} text", element.attributes["attr"])

    def test_attribute_hexadecimal_character_reference_replacement(self):
        for num, char in [("76", "v"), ("117", "ė"), ("278", "ɸ"), ("3da", "Ϛ"), ("79c", "ޜ")]:
            with self.subTest(f"&#{num}; -> {char}"):
                element = Element(f"<Element attr='Entity &#x{num}; text'/>")
                element.parse_to_end({})
                self.assertEqual(f"Entity {char} text", element.attributes["attr"])

    def test_repeated_attribute(self):
        element = Element("<Element attr='value' attr='value'/>")
        with self.assertRaises(XMLError):
            element.parse_to_end({})

    def test_disallowed_attribute_characters(self):
        for char in ["<", "&", "\u0001", "\u0003", "\u0010", "\ufffe", "\uffff"]:
            with self.subTest(char):
                element = Element(f"<Element attr='Blah{char}'/>")
                with self.assertRaises(XMLError):
                    element.parse_to_end({})

    def test_disallowed_attribute_entity_replacement_character(self):
        with self.subTest("Disallow <"):
            entity = MockEntity("entity", expansion_text="<")
            element = Element("<Element attr='blah&entity;blah'/>")
            with self.assertRaises(XMLError):
                element.parse_to_end({"entity": entity})
        with self.subTest("Allow &lt;"):
            lt = MockEntity("lt", "&#60;")
            element = Element("<Element attr='blah&lt;blah'/>")
            element.parse_to_end({"lt": lt})

    """
        ================
        PARSE-END TESTS
        ================
        These tests ensure that the Text class only parses the provided xml as far as it is character data,
        and that occurrences of markup are returned to the parent class for proper processing
    """

    def test_ends_parse_on_close(self):
        with self.subTest("Self-closing"):
            element = Element("<Element/> some text")
            unparsed_xml = element.parse_to_end({})
            self.assertEqual(" some text", unparsed_xml)
        with self.subTest("Open"):
            element = Element("<Element>some text</Element> some more text")
            unparsed_xml = element.parse_to_end({})
            self.assertEqual(" some more text", unparsed_xml)

    """ 
        ======================
        WELL-FORMEDNESS TESTS
        ======================
    """

    def test_mismatched_tags(self):
        element = Element("<Element1>some text</Element2> some more text")
        with self.assertRaises(XMLError):
            element.parse_to_end({})


"""
    =====================
    NESTED ELEMENT TESTS
    =====================
"""


class ElementNestingTests(unittest.TestCase):
    def test_nested_elements(self):
        element = Element("<Element><SubElement><SubSubElement></SubSubElement></SubElement></Element>")
        element.parse_to_end({})

        self.assertEqual("SubElement", element.content[0].name)
        self.assertEqual("SubElement", element.children[0].name)

        self.assertEqual("SubSubElement", element.content[0].content[0].name)
        self.assertEqual("SubSubElement", element.children[0].children[0].name)

    def test_nested_processing_instructions(self):
        element = Element("<Element><?Target1?><?Target2 data?></Element>")
        element.parse_to_end({})

        self.assertEqual("Target1", element.content[0].target)
        self.assertEqual("Target1", element.processing_instructions[0].target)

        self.assertEqual("Target2", element.content[1].target)
        self.assertEqual("Target2", element.processing_instructions[1].target)

    def test_nested_text(self):
        element = Element("<Element>Some text here</Element>")
        element.parse_to_end({})

        self.assertEqual("Some text here", element.content[0].text)
        self.assertEqual("Some text here", element.text[0].text)

    def test_nested_mixed(self):
        element = Element(
            "<Element>Some text<SubElement>More text</SubElement>  <!-- comment --><?Target data?></Element>")
        element.parse_to_end({})

        self.assertEqual("Some text", element.content[0].text)
        self.assertEqual("Some text", element.text[0].text)

        self.assertEqual("SubElement", element.content[1].name)
        self.assertEqual("SubElement", element.children[0].name)
        self.assertEqual("More text", element.content[1].text[0].text)

        self.assertEqual("  ", element.content[2].text)
        self.assertEqual("  ", element.text[1].text)

        self.assertEqual("Target", element.content[3].target)
        self.assertEqual("Target", element.processing_instructions[0].target)

        self.assertEqual(4, len(element.content))
