from typing import Dict
from .Entity import Entity


class XMLMarkup:
    """
        todo - This needs roundly rewritten :(
        A superclass which all XML classes inherit from.

        Defines the required functions of each class and also acts as a buffer to avoid circular imports between the
        xml implementation classes todo - is this true???

        todo - except PIs are instantiated like that in e.g. the DTD
        No xml element should be instantiated directly (i.e. don't use `ProcessingInstruction(blah)` to create a new
        PI object), rather every xml element should be instantiated using XMLClass(remaining_xml).
        This class will automatically create the correct subclass object during instantiation.
    """
    def __new__(cls, remaining_xml: str):
        """
            Override __new__ method to return an object of the correct subclass for the given xml data instead of a
            generic XMLMarkup object.

            This enables all xml objects to be created using XMLClass(remaining_xml) without having to know the
            object's type.
        """
        # Import subclasses
        from .Element import Element
        from .ProcessingInstruction import ProcessingInstruction
        from .Comment import Comment

        # PROCESSING INSTRUCTIONS
        if remaining_xml[:2] == "<?":
            markup_object = super().__new__(ProcessingInstruction)
            markup_object.__init__(remaining_xml)
            return markup_object

        # COMMENTS
        if remaining_xml[:4] == "<!--":
            markup_object = super().__new__(Comment)
            markup_object.__init__(remaining_xml)
            return markup_object

        # ELEMENTS
        markup_object = super().__new__(Element)
        markup_object.__init__(remaining_xml)
        return markup_object

    def parse_to_end(self, general_entities: Dict[str, Entity]) -> str:
        """
            Parses to the end of this element, and returns a string containing the remaining xml in the sequence.

            Subclasses will extract their content from the beginning of the provided xml string, and return whatever
            xml they do not parse for the parent to handle.

            todo - this requirement has changed :(
            This function should check for well-formedness errors only in the xml structure.
            e.g. if a tag/string is not closed or an essential part of a tag is missing.
            Other errors, including conformance to allowed characters, should be thrown in the check_wellformedness
            method instead
        """
        raise NotImplementedError()
