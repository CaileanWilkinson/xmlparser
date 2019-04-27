from typing import List, Dict
from xml_parser.dtd.DTD import DTD
from xml_parser.dtd.Entity import Entity


class MockDTD(DTD):
    def __init__(self, general: Dict[str, Entity] = {}, parameter: Dict[str, Entity] = {}):
        DTD.__init__(self, "", "")

        self.root_name = None

        self.general_entities.update(general)
        self.parameter_entities.update(parameter)

        self.element_declarations = {}  # type: Dict
        self.element_attributes = {}  # type: Dict[str, Dict]
        self.element_default_attributes = {}  # type: Dict[str, Dict]
        self.notations = {}  # type: Dict

        self.processing_instructions = []  # type: List
