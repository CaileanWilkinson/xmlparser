from .generate_canonical_xml import canonical_form
from xml.classes.Error import XMLError
import unittest
from xml.xml import parse_file


class test_XMLTest(unittest.TestCase):
    def test_illformed_xml(self):
        with self.subTest("Standalone"):
            for i in range(1, 187):
                num = "{0:0=3d}".format(i)
                with self.subTest(num):
                    with self.assertRaises(XMLError):
                        parse_file(f"official_suite/xmltest/not-wf/sa/{num}.xml")

    def test_valid_xml(self):
        with self.subTest("Standalone"):
            for i in range(1, 120):
                num = "{0:0=3d}".format(i)
                with self.subTest(num):
                    # Parse file & convert to canonical form
                    document = parse_file(f"official_suite/xmltest/valid/sa/{num}.xml")
                    parsed_xml = canonical_form(document)

                    # Load the test required canonical form
                    with open(f"official_suite/xmltest/valid/sa/out/{num}.xml") as file:
                        expected_xml = file.read()
                        self.assertEqual(expected_xml, parsed_xml)

    def test_invalid_xml(self):
        with self.subTest("Standalone"):
            for num in ["002", "005", "006"]:
                with self.subTest(num):
                    parse_file(f"official_suite/xmltest/invalid/{num}.xml")

    def test_test(self):
        num = "018"
        # Parse file & convert to canonical form
        document = parse_file(f"official_suite/xmltest/valid/sa/{num}.xml")
        parsed_xml = canonical_form(document)

        # Load the test required canonical form
        with open(f"official_suite/xmltest/valid/sa/out/{num}.xml") as file:
            expected_xml = file.read()
            self.assertEqual(expected_xml, parsed_xml)
