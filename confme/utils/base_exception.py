

class ConfmeException(Exception):

    def __init__(self, msg: str):
        super(ConfmeException, self).__init__(msg)