from xml_parser.content.ProcessingInstruction import ProcessingInstructionFactory
from tests.mocks.MockDTD import MockDTD
from xml_parser.errors import XMLError, DisallowedCharacterError
import unittest


class ProcessingInstructionTests(unittest.TestCase):
    """
        ====================
        BASIC PARSING TESTS
        ====================
    """

    def test_parsing(self):
        with self.subTest("No data"):
            xml = "<?Target?>"
            pi, _ = ProcessingInstructionFactory.parse_from_xml(xml, MockDTD())

            self.assertEqual("Target", pi.target)
            self.assertEqual(None, pi.data)
        with self.subTest("Empta daty"):
            xml = "<?Target ?>"
            pi, _ = ProcessingInstructionFactory.parse_from_xml(xml, MockDTD())

            self.assertEqual("Target", pi.target)
            self.assertEqual("", pi.data)
        with self.subTest("Basic data"):
            xml = "<?Target Data?>"
            pi, _ = ProcessingInstructionFactory.parse_from_xml(xml, MockDTD())

            self.assertEqual("Target", pi.target)
            self.assertEqual("Data", pi.data)
        with self.subTest("Complex data"):
            xml = "<?Target Some complex data involving spaces?>"
            pi, remaining_xml = ProcessingInstructionFactory.parse_from_xml(xml, MockDTD())

            self.assertEqual("Target", pi.target)
            self.assertEqual("Some complex data involving spaces", pi.data)

    def test_ends_parse_on_close(self):
        with self.subTest("Without space"):
            xml = "<?Target Data?>Some text <end/>"
            _, unparsed_xml = ProcessingInstructionFactory.parse_from_xml(xml, MockDTD())

            self.assertEqual("Some text <end/>", unparsed_xml)

        with self.subTest("With space"):
            xml = "<?Target Data ?>Some text <end/>"
            _, unparsed_xml = ProcessingInstructionFactory.parse_from_xml(xml, MockDTD())

            self.assertEqual("Some text <end/>", unparsed_xml)

    """
        ================
        WELL-FORMEDNESS
        ================
    """

    def test_processing_instruction_not_closed(self):
        with self.subTest("No >"):
            xml = f"<?Target data "

            with self.assertRaises(XMLError):
                ProcessingInstructionFactory.parse_from_xml(xml, MockDTD())

        with self.subTest("> from following element"):
            xml = f"<?Target data Text <end/>"

            with self.assertRaises(XMLError):
                ProcessingInstructionFactory.parse_from_xml(xml, MockDTD())

    def test_whitespace_before_target(self):
        xml = f"<? Target data?>"

        with self.assertRaises(XMLError):
            ProcessingInstructionFactory.parse_from_xml(xml, MockDTD())


class TargetTests(unittest.TestCase):
    """
        ===============
        TARGET PARSING
        ===============
    """

    def test_target_parsing(self):
        with self.subTest("Without data"):
            xml = "Target?>"
            target, remaining_xml = ProcessingInstructionFactory.parse_target(xml, "")

            self.assertEqual("Target", target)
            self.assertEqual("?>", remaining_xml)

        with self.subTest("With whitespace"):
            xml = "Target "
            target, remaining_xml = ProcessingInstructionFactory.parse_target(xml, "")

            self.assertEqual("Target", target)
            self.assertEqual(" ", remaining_xml)

        with self.subTest("With data"):
            xml = "Target Data?>"
            target, remaining_xml = ProcessingInstructionFactory.parse_target(xml, "")

            self.assertEqual("Target", target)
            self.assertEqual(" Data?>", remaining_xml)

    """
        =====================
        FORBIDDEN CHARACTERS
        =====================
    """

    def test_forbidden_name_start_characters(self):
        for char in ["-", ".", "0", "7", "\u0305"]:
            with self.subTest(char):
                xml = f"{char}Target?>"

                with self.assertRaises(XMLError):
                    ProcessingInstructionFactory.parse_target(xml, "")

    def test_forbidden_name_characters(self):
        for char in ["\u00d7", "\u00f7", "\u037e", "\u2030"]:
            with self.subTest(char):
                xml = f"Tar{char}get?>"

                with self.assertRaises(XMLError):
                    ProcessingInstructionFactory.parse_target(xml, "")

    def test_forbidden_xml_name(self):
        with self.subTest("xml"):
            xml = f"xml?>"

            with self.assertRaises(XMLError):
                ProcessingInstructionFactory.parse_target(xml, "")

        with self.subTest("XmL"):
            xml = f"XmL?>"

            with self.assertRaises(XMLError):
                ProcessingInstructionFactory.parse_target(xml, "")

        with self.subTest("xmlBlah"):
            xml = f"xmlBlah?>"

            with self.assertRaises(XMLError):
                ProcessingInstructionFactory.parse_target(xml, "")

        with self.subTest("XmLBlah"):
            xml = f"XmLBlah?>"

            with self.assertRaises(XMLError):
                ProcessingInstructionFactory.parse_target(xml, "")


class DataTests(unittest.TestCase):
    """
        =============
        DATA PARSING
        =============
    """

    def test_data_parsing(self):
        with self.subTest("Empty"):
            xml = " ?>MOREXML"
            data, remaining_xml = ProcessingInstructionFactory.parse_data(xml, "")

            self.assertEqual("", data)
            self.assertEqual("MOREXML", remaining_xml)

        with self.subTest("Basic"):
            xml = " Data?>MOREXML"
            data, remaining_xml = ProcessingInstructionFactory.parse_data(xml, "")

            self.assertEqual("Data", data)
            self.assertEqual("MOREXML", remaining_xml)

        with self.subTest("Complex"):
            xml = " Some complex data involving spaces?>MOREXML"
            data, remaining_xml = ProcessingInstructionFactory.parse_data(xml, "")

            self.assertEqual("Some complex data involving spaces", data)
            self.assertEqual("MOREXML", remaining_xml)

    """
        =====================
        FORBIDDEN CHARACTERS
        =====================
    """

    def test_allowed_characters(self):
        """
            Explicitly check for allowed characters which may accidentally throw errors
        """
        for char in ["<", ">", "&", "%", "?", "]]>"]:
            with self.subTest(char):
                xml = f" some text {char} some more text?>"
                data, _ = ProcessingInstructionFactory.parse_data(xml, "")

                self.assertEqual(f"some text {char} some more text", data)

    def test_forbidden_characters(self):
        for char in ["\u0001", "\u0003", "\u0010", "\ufffe", "\uffff"]:
            with self.subTest(f"Char: {char}"):
                xml = f" data with {char}?>"

                with self.assertRaises(DisallowedCharacterError):
                    ProcessingInstructionFactory.parse_data(xml, "")

    """
        =================
        ENTITY EXPANSION
        =================
    """

    def test_ignores_decimal_char_references(self):
        for num, char in [(118, "v"), (279, "ė"), (632, "ɸ"), (986, "Ϛ"), (1948, "ޜ")]:
            with self.subTest(f"&#{num}; -/> {char}"):
                xml = f" char&#{num};?>"
                data, _ = ProcessingInstructionFactory.parse_data(xml, "")

                self.assertEqual(f"char&#{num};", data)

    def test_ignores_hexadecimal_char_references(self):
        for num, char in [("76", "v"), ("117", "ė"), ("278", "ɸ"), ("3da", "Ϛ"), ("79c", "ޜ")]:
            with self.subTest(f"&#{num}; -/> {char}"):
                xml = f" Char&#x{num};?>"
                data, _ = ProcessingInstructionFactory.parse_data(xml, "")

                self.assertEqual(f"Char&#x{num};", data)

    def test_ignores_general_entities(self):
        xml = " Some data with &entity;?>"
        data, _ = ProcessingInstructionFactory.parse_data(xml, "")

        self.assertEqual("Some data with &entity;", data)

    def test_ignores_parameter_entities(self):
        xml = " Some data with %entity;?>"
        data, _ = ProcessingInstructionFactory.parse_data(xml, "")

        self.assertEqual("Some data with %entity;", data)
