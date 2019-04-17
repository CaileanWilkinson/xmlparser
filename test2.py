class CustomException(Exception):
    def __init__(self):
        Exception.__init__(self, "Blah")


raise CustomException()
