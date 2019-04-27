import unittest
from xml_parser.dtd.ElementDeclaration import ElementDeclFactory
from xml_parser.errors import XMLError, DisallowedCharacterError
from tests.mocks.MockDTD import MockDTD


class ElementTests(unittest.TestCase):
    """
        ================
        OVERALL PARSING
        ================
    """

    def test_element_declaration_parsing(self):
        with self.subTest("ANY"):
            xml = "<!ELEMENT Name ANY >"
            element, _ = ElementDeclFactory.parse_from_xml(xml, MockDTD(), False)

            self.assertEqual("Name", element.name)
            self.assertEqual("ANY", element.content_type)

        with self.subTest("EMPTY"):
            xml = "<!ELEMENT Name EMPTY >"
            element, _ = ElementDeclFactory.parse_from_xml(xml, MockDTD(), False)

            self.assertEqual("Name", element.name)
            self.assertEqual("EMPTY", element.content_type)

        with self.subTest("CHILDREN: choice"):
            xml = "<!ELEMENT Name (Name2 | Name3) >"
            element, _ = ElementDeclFactory.parse_from_xml(xml, MockDTD(), False)

            self.assertEqual("Name", element.name)
            self.assertEqual("CHILDREN", element.content_type)
            self.assertEqual("((Name2#)|(Name3#))", element.children_regex)

        with self.subTest("CHILDREN: sequence"):
            xml = "<!ELEMENT Name (Name2, Name3) >"
            element, _ = ElementDeclFactory.parse_from_xml(xml, MockDTD(), False)

            self.assertEqual("Name", element.name)
            self.assertEqual("CHILDREN", element.content_type)
            self.assertEqual("((Name2#)(Name3#))", element.children_regex)

        with self.subTest("MIXED"):
            xml = "<!ELEMENT Name (#PCDATA | Name2 | Name3)* >"
            element, _ = ElementDeclFactory.parse_from_xml(xml, MockDTD(), False)

            self.assertEqual("Name", element.name)
            self.assertEqual("MIXED", element.content_type)
            self.assertEqual("((Name2#)|(Name3#))*", element.children_regex)

    """
        ===================
        MISSING WHITESPACE
        ===================
    """

    def test_missing_whitespace_before_name(self):
        xml = "<!ELEMENTName ANY >"
        with self.assertRaises(XMLError):
            ElementDeclFactory.parse_from_xml(xml, MockDTD(), False)

    def test_missing_whitespace_after_name(self):
        with self.subTest("ANY"):
            xml = "<!ELEMENT NameANY >"
            with self.assertRaises(XMLError):
                ElementDeclFactory.parse_from_xml(xml, MockDTD(), False)

        with self.subTest("CHILDREN"):
            xml = "<!ELEMENT Name(Name2|Name3) >"
            with self.assertRaises(XMLError):
                ElementDeclFactory.parse_from_xml(xml, MockDTD(), False)

    """
        =============
        NAME PARSING
        =============
    """

    def test_name_parsing(self):
        xml = " Name XML CONTINUES>"
        name, unparsed_xml = ElementDeclFactory.parse_name(xml, "", MockDTD(), False)

        self.assertEqual("Name", name)
        self.assertEqual("XML CONTINUES>", unparsed_xml)

    def test_forbidden_name_start_characters(self):
        for char in ["-", ".", "0", "7", "\u0305"]:
            with self.subTest(char):
                xml = f" {char}Name XML CONTINUES>"
                with self.assertRaises(DisallowedCharacterError):
                    ElementDeclFactory.parse_name(xml, "", MockDTD(), False)

    def test_forbidden_name_characters(self):
        for char in ["\u00d7", "\u00f7", "\u037e", "\u2030"]:
            with self.subTest(char):
                xml = f" Na{char}me XML CONTINUES>"
                with self.assertRaises(DisallowedCharacterError):
                    ElementDeclFactory.parse_name(xml, "", MockDTD(), False)


class ContentSpecTests(unittest.TestCase):
    """
        ============
        BASIC TYPES
        ============
    """
    def test_empty_content(self):
        with self.subTest("With whitespace"):
            xml = "EMPTY >XMLCONTINUES"
            content_type, condition, unparsed_xml = ElementDeclFactory.parse_content_spec(xml, "", MockDTD(), False)

            self.assertEqual("EMPTY", content_type)
            self.assertEqual(None, condition)
            self.assertEqual(" >XMLCONTINUES", unparsed_xml)

        with self.subTest("Without whitespace"):
            xml = "EMPTY>XMLCONTINUES"
            content_type, condition, unparsed_xml = ElementDeclFactory.parse_content_spec(xml, "", MockDTD(), False)

            self.assertEqual("EMPTY", content_type)
            self.assertEqual(None, condition)
            self.assertEqual(">XMLCONTINUES", unparsed_xml)

    def test_any_content(self):
        with self.subTest("With whitespace"):
            xml = "ANY >XMLCONTINUES"
            content_type, condition, unparsed_xml = ElementDeclFactory.parse_content_spec(xml, "", MockDTD(), False)

            self.assertEqual("ANY", content_type)
            self.assertEqual(None, condition)
            self.assertEqual(" >XMLCONTINUES", unparsed_xml)

        with self.subTest("Without whitespace"):
            xml = "ANY>XMLCONTINUES"
            content_type, condition, unparsed_xml = ElementDeclFactory.parse_content_spec(xml, "", MockDTD(), False)

            self.assertEqual("ANY", content_type)
            self.assertEqual(None, condition)
            self.assertEqual(">XMLCONTINUES", unparsed_xml)

    def test_invalid_content(self):
        for content in ["SOMETHING", "DISALLOWED"]:
            with self.subTest(content):
                xml = f"{content}>XMLCONTINUES"
                with self.assertRaises(XMLError):
                    ElementDeclFactory.parse_content_spec(xml, "", MockDTD(), False)

    """
        ==============
        MIXED CONTENT
        ==============
        Mixed ::== '(' S? '#PCDATA' (S? '|' S? Name)* S? ')*' | '(' S? '#PCDATA' S? ')'
    """
    def test_mixed_only_pcdata(self):
        with self.subTest("With whitespace"):
            xml = "( #PCDATA )REMAININGXML"
            content_type, condition, unparsed_xml = ElementDeclFactory.parse_content_spec(xml, "", MockDTD(), False)

            self.assertEqual("", condition)
            self.assertEqual("REMAININGXML", unparsed_xml)

        with self.subTest("Without whitespace"):
            xml = "(#PCDATA)REMAININGXML"
            content_type, condition, unparsed_xml = ElementDeclFactory.parse_content_spec(xml, "", MockDTD(), False)

            self.assertEqual("", condition)
            self.assertEqual("REMAININGXML", unparsed_xml)

        with self.subTest("With *"):
            xml = "(#PCDATA)*REMAININGXML"
            content_type, condition, unparsed_xml = ElementDeclFactory.parse_content_spec(xml, "", MockDTD(), False)

            self.assertEqual("", condition)
            self.assertEqual("REMAININGXML", unparsed_xml)

    def test_mixed_with_elements(self):
        with self.subTest("1 element"):
            xml = "(#PCDATA | Name)*REMAININGXML"
            content_type, condition, unparsed_xml = ElementDeclFactory.parse_content_spec(xml, "", MockDTD(), False)

            self.assertEqual(condition, "((Name#))*")
            self.assertEqual("REMAININGXML", unparsed_xml)

        with self.subTest("2 elements"):
            xml = "(#PCDATA | Name | Name2)*REMAININGXML"
            content_type, condition, unparsed_xml = ElementDeclFactory.parse_content_spec(xml, "", MockDTD(), False)

            self.assertEqual(condition, "((Name#)|(Name2#))*")
            self.assertEqual("REMAININGXML", unparsed_xml)

    def test_mixed_must_end_asterisk(self):
        with self.assertRaises(XMLError):
            xml = "(#PCDATA | Name)REMAININGXML"
            ElementDeclFactory.parse_content_spec(xml, "", MockDTD(), False)

    def test_mixed_names_must_be_unique(self):
        with self.assertRaises(XMLError):
            xml = "(#PCDATA | Name | Name2 | Name)*REMAININGXMLxml, "
            ElementDeclFactory.parse_content_spec(xml, "", MockDTD(), False)

    def test_mixed_invalid_delimiter(self):
        for delimiter in [",", " ", "*", "^"]:
            with self.assertRaises(XMLError):
                xml = f"(#PCDATA | Name | Name2 {delimiter} Name3)*MOREXMLxml, "
                ElementDeclFactory.parse_content_spec(xml, "", MockDTD(), False)

    def test_mixed_forbidden_name_characters(self):
        for char in ["\u00d7", "\u00f7", "\u037e", "\u2030"]:
            with self.subTest(char):
                with self.assertRaises(DisallowedCharacterError):
                    xml = f"(#PCDATA | Na{char}me)*XMLCONTINUES>xml, "
                    ElementDeclFactory.parse_content_spec(xml, "", MockDTD(), False)

    def test_mixed_forbidden_name_start_characters(self):
        for char in ["-", ".", "0", "7", "\u0305"]:
            with self.subTest(char):
                with self.assertRaises(DisallowedCharacterError):
                    xml = f"(#PCDATA | {char}Name)*XMLCONTINUES>xml, "
                    ElementDeclFactory.parse_content_spec(xml, "", MockDTD(), False)

    """
        =================
        CHILDREN CONTENT
        =================
        children ::== ( choice | seq ) ('?' | '*' | '+')
    """
    def test_children_choice_parsing(self):
        xml = "(Name | Name2 | Name3)MOREXML"
        content_type, condition, unparsed_xml = ElementDeclFactory.parse_content_spec(xml, "", MockDTD(), False)

        self.assertEqual("CHILDREN", content_type)
        self.assertEqual("((Name#)|(Name2#)|(Name3#))", condition)
        self.assertEqual("MOREXML", unparsed_xml)

    def test_children_sequence_parsing(self):
        xml = "(Name, Name2, Name3)MOREXML"
        content_type, condition, unparsed_xml = ElementDeclFactory.parse_content_spec(xml, "", MockDTD(), False)

        self.assertEqual("CHILDREN", content_type)
        self.assertEqual("((Name#)(Name2#)(Name3#))", condition)
        self.assertEqual("MOREXML", unparsed_xml)

    def test_children_modifier_parsing(self):
            for modifier in "?*+":
                with self.subTest(f"Choice: {modifier}"):
                    xml = f"(Name | Name2 | Name3){modifier}MOREXML"
                    content_type, condition, unparsed_xml = ElementDeclFactory.parse_content_spec(xml, "", MockDTD(), False)

                    self.assertEqual("CHILDREN", content_type)
                    self.assertEqual(f"((Name#)|(Name2#)|(Name3#)){modifier}", condition)
                    self.assertEqual("MOREXML", unparsed_xml)

                with self.subTest(f"Sequence: {modifier}"):
                    xml = f"(Name, Name2, Name3){modifier}MOREXML"
                    content_type, condition, unparsed_xml = ElementDeclFactory.parse_content_spec(xml, "", MockDTD(), False)

                    self.assertEqual("CHILDREN", content_type)
                    self.assertEqual(f"((Name#)(Name2#)(Name3#)){modifier}", condition)
                    self.assertEqual("MOREXML", unparsed_xml)


class ContentParticleTests(unittest.TestCase):
    # todo - Test choice / sequence parsing
    def test_name_parsing(self):
        for delimiter in ",|)":
            with self.subTest(f"Delimiter: {delimiter}"):
                xml = f"Name{delimiter}MOREXML"
                name, _, unparsed_xml = ElementDeclFactory.parse_content_particle(xml, "",  MockDTD(), False)

                self.assertEqual("(Name#)", name)
                self.assertEqual(f"{delimiter}MOREXML", unparsed_xml)

    def test_modifier_parsing(self):
        for modifier in "?*+":
            with self.subTest(f"Delimiter: {modifier}"):
                xml = f"Name{modifier})>MOREXML"
                name, _, unparsed_xml = ElementDeclFactory.parse_content_particle(xml, "",  MockDTD(), False)

                self.assertEqual(f"(Name#){modifier}", name)
                self.assertEqual(")>MOREXML", unparsed_xml)

    def test_forbidden_name_start_characters(self):
        for char in ["-", ".", "0", "7", "\u0305"]:
            with self.subTest(char):
                xml = f"{char}Name)>"
                with self.assertRaises(DisallowedCharacterError):
                    ElementDeclFactory.parse_content_particle(xml, "",  MockDTD(), False)

    def test_forbidden_name_characters(self):
        for char in ["\u00d7", "\u00f7", "\u037e", "\u2030"]:
            with self.subTest(char):
                xml = f"Na{char}me)>"
                with self.assertRaises(DisallowedCharacterError):
                    ElementDeclFactory.parse_content_particle(xml, "",  MockDTD(), False)


class ChoiceTests(unittest.TestCase):
    """
        =======
        CHOICE 
        =======
        choice ::== '(' S? cp (S? '|' S? cp)+ S? ')'
    """

    def test_single_choice_parsing(self):
        with self.subTest("With whitespace"):
            xml = "( Name )MOREXML"
            choice, _, remaining_xml = ElementDeclFactory.parse_content_particle(xml, "", MockDTD(), False)

            self.assertEqual("((Name#))", choice)
            self.assertEqual("MOREXML", remaining_xml)
        with self.subTest("Without whitespace"):
            xml = "(Name)MOREXML"
            choice, _, remaining_xml = ElementDeclFactory.parse_content_particle(xml, "", MockDTD(), False)

            self.assertEqual("((Name#))", choice)
            self.assertEqual("MOREXML", remaining_xml)

    def test_multiple_choice_parsing(self):
        with self.subTest("2 choices"):
            xml = "( Name | Name2 )MOREXML"
            choice, _, remaining_xml = ElementDeclFactory.parse_content_particle(xml, "", MockDTD(), False)

            self.assertEqual("((Name#)|(Name2#))", choice)
            self.assertEqual("MOREXML", remaining_xml)
        with self.subTest("3 choices"):
            xml = "(Name|Name2|Name3)MOREXML"
            choice, _, remaining_xml = ElementDeclFactory.parse_content_particle(xml, "", MockDTD(), False)

            self.assertEqual("((Name#)|(Name2#)|(Name3#))", choice)
            self.assertEqual("MOREXML", remaining_xml)

    def test_modifier_parsing(self):
        for modifier in "?*+":
            with self.subTest(f"Modifier: {modifier}"):
                xml = f"(Name|Name2){modifier}MOREXML"
                choice, _, remaining_xml = ElementDeclFactory.parse_content_particle(xml, "", MockDTD(), False)

                self.assertEqual(f"((Name#)|(Name2#)){modifier}", choice)
                self.assertEqual("MOREXML", remaining_xml)

    def test_nested_modifier_parsing(self):
        for modifier in "?*+":
            with self.subTest(f"Modifier: {modifier}"):
                xml = f"(Name{modifier}|Name2)MOREXML"
                choice, _, remaining_xml = ElementDeclFactory.parse_content_particle(xml, "", MockDTD(), False)

                self.assertEqual(f"((Name#){modifier}|(Name2#))", choice)
                self.assertEqual("MOREXML", remaining_xml)

    def test_nested_choice(self):
        xml = "( Name | (Name2 | Name3 ))MOREXML"
        choice, _, remaining_xml = ElementDeclFactory.parse_content_particle(xml, "", MockDTD(), False)

        self.assertEqual("((Name#)|((Name2#)|(Name3#)))", choice)
        self.assertEqual("MOREXML", remaining_xml)

    def test_nested_sequence(self):
        xml = "( Name | (Name2, Name3 ))MOREXML"
        choice, _, remaining_xml = ElementDeclFactory.parse_content_particle(xml, "", MockDTD(), False)

        self.assertEqual("((Name#)|((Name2#)(Name3#)))", choice)
        self.assertEqual("MOREXML", remaining_xml)

    def test_invalid_delimiter(self):
        for delimiter in [",", " ", "*", "^"]:
            with self.subTest(delimiter):
                with self.assertRaises(XMLError):
                    xml = f"( Name | Name2 {delimiter} Name3 )MOREXML"
                    ElementDeclFactory.parse_content_particle(xml, "", MockDTD(), False)

    def test_allowed_repeated_names(self):
        xml = "( Name | Name2 | Name )MOREXML"
        choice, _, remaining_xml = ElementDeclFactory.parse_content_particle(xml, "", MockDTD(), False)

        self.assertEqual("((Name#)|(Name2#)|(Name#))", choice)
        self.assertEqual("MOREXML", remaining_xml)


class SequenceTests(unittest.TestCase):
    """
        =========
        SEQUENCE
        =========
        seq ::== '(' S? cd (S? ',' S? cp)* S? ')'
    """

    def test_single_item_parsing(self):
        with self.subTest("With whitespace"):
            xml = "( Name )MOREXML"
            sequence, _, remaining_xml = ElementDeclFactory.parse_content_particle(xml, "", MockDTD(), False)

            self.assertEqual("((Name#))", sequence)
            self.assertEqual("MOREXML", remaining_xml)
        with self.subTest("Without whitespace"):
            xml = "(Name)MOREXML"
            sequence, _, remaining_xml = ElementDeclFactory.parse_content_particle(xml, "", MockDTD(), False)

            self.assertEqual("((Name#))", sequence)
            self.assertEqual("MOREXML", remaining_xml)

    def test_multiple_item_parsing(self):
        with self.subTest("2 items"):
            xml = "( Name, Name2 )MOREXML"
            sequence, _, remaining_xml = ElementDeclFactory.parse_content_particle(xml, "", MockDTD(), False)

            self.assertEqual("((Name#)(Name2#))", sequence)
            self.assertEqual("MOREXML", remaining_xml)
        with self.subTest("3 items"):
            xml = "(Name,Name2,Name3)MOREXML"
            sequence, _, remaining_xml = ElementDeclFactory.parse_content_particle(xml, "", MockDTD(), False)

            self.assertEqual("((Name#)(Name2#)(Name3#))", sequence)
            self.assertEqual("MOREXML", remaining_xml)

    def test_modifier_parsing(self):
        for modifier in "?*+":
            with self.subTest(f"Modifier: {modifier}"):
                xml = f"(Name,Name2){modifier}MOREXML"
                sequence, _, remaining_xml = ElementDeclFactory.parse_content_particle(xml, "", MockDTD(), False)

                self.assertEqual(f"((Name#)(Name2#)){modifier}", sequence)
                self.assertEqual("MOREXML", remaining_xml)

    def test_nested_modifier_parsing(self):
        for modifier in "?*+":
            with self.subTest(f"Modifier: {modifier}"):
                xml = f"(Name{modifier}, Name2)MOREXML"
                sequence, _, remaining_xml = ElementDeclFactory.parse_content_particle(xml, "", MockDTD(), False)

                self.assertEqual(f"((Name#){modifier}(Name2#))", sequence)
                self.assertEqual("MOREXML", remaining_xml)

    def test_nested_choice(self):
        xml = "( Name, (Name2 | Name3 ))MOREXML"
        sequence, _, remaining_xml = ElementDeclFactory.parse_content_particle(xml, "", MockDTD(), False)

        self.assertEqual("((Name#)((Name2#)|(Name3#)))", sequence)
        self.assertEqual("MOREXML", remaining_xml)

    def test_nested_sequence(self):
        xml = "( Name, (Name2, Name3 ))MOREXML"
        sequence, _, remaining_xml = ElementDeclFactory.parse_content_particle(xml, "", MockDTD(), False)

        self.assertEqual("((Name#)((Name2#)(Name3#)))", sequence)
        self.assertEqual("MOREXML", remaining_xml)

    def test_invalid_delimiter(self):
        for delimiter in ["|", " ", "*", "^"]:
            with self.assertRaises(XMLError):
                xml = f"( Name , Name2 {delimiter} Name3 )MOREXML"
                ElementDeclFactory.parse_content_particle(xml, "", MockDTD(), False)

    def test_allowed_repeated_names(self):
        xml = "( Name, Name2, Name )MOREXML"
        sequence, _, remaining_xml = ElementDeclFactory.parse_content_particle(xml, "", MockDTD(), False)

        self.assertEqual("((Name#)(Name2#)(Name#))", sequence)
        self.assertEqual("MOREXML", remaining_xml)
