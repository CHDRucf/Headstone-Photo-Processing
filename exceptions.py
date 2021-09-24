import enum

class ProcessingError(Exception):
    pass

class RotationError(ProcessingError):
    pass

class CropError(ProcessingError):
    pass

class OCRError(Exception):
    pass

class LabelError(Exception):
    class Situations(enum.Enum):
        Perfect = 0
        Multiple_Perfect = 1
        Fuzzy = 2
        Fuzzy_Tie = 3
        No_Matches = 4
        Too_Close_To_Call = 5
        Manual = 6

    def __init__(self, situation=None, error_string=None):
        if error_string is None:
            super().__init__()
        else:
            super().__init__(error_string)
        self.error_string = error_string
        self.situation = situation

    def __str__(self):
        ret_str = ''
        if self.error_string is not None:
            ret_str += self.error_string + ': '
        ret_str += self.situation.name
        return ret_str

class AbortError(Exception):
    pass