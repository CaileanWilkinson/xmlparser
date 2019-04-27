from tests.generate_canonical_xml import canonical_form
from xml_parser.errors import XMLError
import unittest
from xml_parser import parse_file
import os


class test_XMLTest(unittest.TestCase):
    root = os.path.dirname(__file__)

    """
        SETUP
    """
    # def test_load_tests(self):
    #     path = os.path.join(test_XMLTest.root,
    #                         f"official_suite/xmltest/xmltest.xml")
    #     tests = parse_file(path)
    #
    #     for test in tests.root.children:
    #         if "EDITION" in test.attributes:
    #             print(f"{test.attributes['ID']} editions {test.attributes['EDITION']}")

    """
        ======================
        ILL-FORMED XML TESTS
        ======================
    """
    def test_illformed_internal_standalone_xml(self):
        for i in range(1, 187):
            if i in [140, 141]: continue  # Tests 140, 141 made obsolete in xml 1.0 spec v5

            num = "{0:0=3d}".format(i)
            with self.subTest(num):
                with self.assertRaises((XMLError, UnicodeError)):
                    path = os.path.join(test_XMLTest.root,
                                        f"official_suite/xmltest/not-wf/sa/{num}.xml")
                    parse_file(path)

    def test_illformed_external_standalone_xml(self):
        for i in range(1, 4):
            num = "{0:0=3d}".format(i)
            with self.subTest(num):
                with self.assertRaises((XMLError, UnicodeError)):
                    path = os.path.join(test_XMLTest.root,
                                        f"official_suite/xmltest/not-wf/ext-sa/{num}.xml")
                    parse_file(path)

    def test_illformed_not_standalone_xml(self):
        for i in range(1, 12):
            num = "{0:0=3d}".format(i)
            with self.subTest(num):
                with self.assertRaises((XMLError, UnicodeError)):
                    path = os.path.join(test_XMLTest.root,
                                        f"official_suite/xmltest/not-wf/not-sa/{num}.xml")
                    parse_file(path)

    """
        ================
        VALID XML TESTS
        ================
    """
    def test_valid_internal_xml(self):
        for i in range(1, 120):
            num = "{0:0=3d}".format(i)
            with self.subTest(num):
                # Parse file & convert to canonical form
                path = os.path.join(test_XMLTest.root,
                                    f"official_suite/xmltest/valid/sa/{num}.xml")
                document = parse_file(path)
                parsed_xml = canonical_form(document)

                # Load the test required canonical form
                canonical_path = os.path.join(test_XMLTest.root,
                                    f"official_suite/xmltest/valid/sa/out/{num}.xml")
                with open(canonical_path) as file:
                    expected_xml = file.read()
                    self.assertEqual(expected_xml, parsed_xml)

    def test_valid_external_standalone_xml(self):
        for i in range(1, 15):
            num = "{0:0=3d}".format(i)
            with self.subTest(num):
                # Parse file & convert to canonical form
                path = os.path.join(test_XMLTest.root,
                                    f"official_suite/xmltest/valid/ext-sa/{num}.xml")
                document = parse_file(path)
                parsed_xml = canonical_form(document)

                # Load the test required canonical form
                canonical_path = os.path.join(test_XMLTest.root,
                                    f"official_suite/xmltest/valid/ext-sa/out/{num}.xml")
                with open(canonical_path) as file:
                    expected_xml = file.read()
                    self.assertEqual(expected_xml, parsed_xml)

    def test_valid_not_standalone_xml(self):
        for i in range(1, 32):
            if i == 22: continue  # There is no test 22
            num = "{0:0=3d}".format(i)
            with self.subTest(num):
                # Parse file & convert to canonical form
                path = os.path.join(test_XMLTest.root,
                                    f"official_suite/xmltest/valid/not-sa/{num}.xml")
                document = parse_file(path)
                parsed_xml = canonical_form(document)

                # Load the test required canonical form
                canonical_path = os.path.join(test_XMLTest.root,
                                    f"official_suite/xmltest/valid/not-sa/out/{num}.xml")
                with open(canonical_path) as file:
                    expected_xml = file.read()
                    self.assertEqual(expected_xml, parsed_xml)


    # def test_valid(self):
    #     num = "081"
    #     # Parse file & convert to canonical form
    #     path = os.path.join(test_XMLTest.root,
    #                         f"official_suite/xmltest/valid/sa/{num}.xml")
    #     document = parse_file(path)
    #     parsed_xml = canonical_form(document)
    #     # print(parsed_xml)
    #
    #     # Load the test required canonical form
    #     canonical_path = os.path.join(test_XMLTest.root,
    #                                   f"official_suite/xmltest/valid/sa/out/{num}.xml")
    #     with open(canonical_path) as file:
    #         expected_xml = file.read()
    #         self.assertEqual(expected_xml, parsed_xml)

    # def test_illformed(self):
    #     num = "081"
    #
    #     # with self.assertRaises(XMLError):
    #     path = os.path.join(test_XMLTest.root,
    #                         f"official_suite/xmltest/not-wf/sa/{num}.xml")
    #     parse_file(path)
