a = 10


class Counter:
    counter = (
        0  # Class attribute shared by all, since there is no static variable in python
    )

    def __init__(self, name):
        self.name = name
        self.__name_private = name
        self._name_protected = name

    @classmethod
    def total(cls):
        return cls.count

    @staticmethod
    def is_valid(name):
        return bool(name.strip())
