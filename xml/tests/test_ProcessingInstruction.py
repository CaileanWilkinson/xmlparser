from xml.classes.content.ProcessingInstruction import ProcessingInstruction
from xml.tests.mocks.MockEntity import MockEntity
from xml.classes.Error import XMLError
import unittest


class ProcessingInstructionTests(unittest.TestCase):
    """
        ====================
        BASIC PARSING TESTS
        ====================
    """

    def test_target_parsing(self):
        with self.subTest("Without data"):
            pi = ProcessingInstruction("<?Target?>Some text <end/>")
            pi.parse_to_end({})
            self.assertEqual("Target", pi.target)
        with self.subTest("With data"):
            pi = ProcessingInstruction("<?Target Data?>Some text <end/>")
            pi.parse_to_end({})
            self.assertEqual("Target", pi.target)

    def test_data_parsing(self):
        with self.subTest("None"):
            pi = ProcessingInstruction("<?Target?>Some text <end/>")
            pi.parse_to_end({})
            self.assertEqual(None, pi.data)
        with self.subTest("Empty"):
            pi = ProcessingInstruction("<?Target ?>Some text <end/>")
            pi.parse_to_end({})
            self.assertEqual("", pi.data)
        with self.subTest("Basic"):
            pi = ProcessingInstruction("<?Target Data?>Some text <end/>")
            pi.parse_to_end({})
            self.assertEqual("Data", pi.data)
        with self.subTest("Complex"):
            pi = ProcessingInstruction("<?Target Some complex data involving spaces?>Some text <end/>")
            pi.parse_to_end({})
            self.assertEqual("Some complex data involving spaces", pi.data)

    """
        ================
        PARSE-END TESTS
        ================
        These tests ensure that the Text class only parses the provided xml as far as it is character data,
        and that occurrences of markup are returned to the parent class for proper processing
    """

    def test_ends_parse_on_close(self):
        with self.subTest("Without space"):
            pi = ProcessingInstruction("<?Target Data?>Some text <end/>")
            unparsed_xml = pi.parse_to_end({})
            self.assertEqual("Some text <end/>", unparsed_xml)

        with self.subTest("With space"):
            pi = ProcessingInstruction("<?Target Data ?>Some text <end/>")
            unparsed_xml = pi.parse_to_end({})
            self.assertEqual("Some text <end/>", unparsed_xml)

    """
        =================================
        ENTITY REFERENCE EXPANSION TESTS
        =================================
    """

    def test_ignores_decimal_char_references(self):
        for num, char in [(118, "v"), (279, "ė"), (632, "ɸ"), (986, "Ϛ"), (1948, "ޜ")]:
            with self.subTest(f"&#{num}; -/> {char}"):
                pi = ProcessingInstruction(f"<?Target char&#{num};?><end/>")
                pi.parse_to_end({})
                self.assertEqual(f"char&#{num};", pi.data)

    def test_ignores_hexadecimal_char_references(self):
        for num, char in [("76", "v"), ("117", "ė"), ("278", "ɸ"), ("3da", "Ϛ"), ("79c", "ޜ")]:
            with self.subTest(f"&#{num}; -/> {char}"):
                pi = ProcessingInstruction(f"<?Target Char&#x{num};?><end/>")
                pi.parse_to_end({})
                self.assertEqual(f"Char&#x{num};", pi.data)

    def test_ignores_general_entities(self):
        entity = MockEntity("entity", expansion_text="SOMEVALUE")

        pi = ProcessingInstruction("<?Target Some data with &entity;?> and some text<end/>")
        pi.parse_to_end({"entity": entity})

        self.assertEqual("Some data with &entity;", pi.data)

    def test_ignores_parameter_entities(self):
        pi = ProcessingInstruction("<?Target Some data with %entity;?> and some text<end/>")
        pi.parse_to_end({})

        self.assertEqual("Some data with %entity;", pi.data)

    """
        ======================
        WELL-FORMEDNESS TESTS
        ======================
    """
    def test_allowed_characters(self):
        """
            Explicitly check for allowed characters which may accidentally throw errors
        """
        for char in ["<", ">", "&", "%", "?", "]]>"]:
            with self.subTest(char):
                processing_instruction = ProcessingInstruction(f"<?TARGET some text {char} some more text?> some final text")
                processing_instruction.parse_to_end({})
                self.assertEqual(f"some text {char} some more text", processing_instruction.data)

    def test_forbidden_characters(self):
        for char in ["\u0001", "\u0003", "\u0010", "\ufffe", "\uffff"]:
            with self.subTest(f"Char: {char}"):
                pi = ProcessingInstruction(f"<?Target data with {char}?> Text <end/>")
                with self.assertRaises(XMLError):
                    pi.parse_to_end({})

    def test_forbidden_name_start_characters(self):
        for char in ["-", ".", "0", "7", "\u0305"]:
            with self.subTest(char):
                pi = ProcessingInstruction(f"<?{char}Target?>")
                with self.assertRaises(XMLError):
                    pi.parse_to_end({})

    def test_forbidden_name_characters(self):
        for char in ["\u00d7", "\u00f7", "\u037e", "\u2030"]:
            with self.subTest(char):
                pi = ProcessingInstruction(f"<?Tar{char}get?>")
                with self.assertRaises(XMLError):
                    pi.parse_to_end({})

    def test_forbidden_xml_name(self):
        with self.subTest("xml"):
            pi = ProcessingInstruction(f"<?xml data?> Text <end/>")
            with self.assertRaises(XMLError):
                pi.parse_to_end({})
        with self.subTest("XmL"):
            pi = ProcessingInstruction(f"<?XmL data?> Text <end/>")
            with self.assertRaises(XMLError):
                pi.parse_to_end({})

    def test_pi_not_closed(self):
        pi = ProcessingInstruction(f"<?Target data Text <end/>")
        with self.assertRaises(XMLError):
            pi.parse_to_end({})

    def test_whitespace_before_target(self):
        pi = ProcessingInstruction(f"<? Target data?> Text <end/>")
        with self.assertRaises(XMLError):
            pi.parse_to_end({})
