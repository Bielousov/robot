class Enum:
    def __init__(self, **kwds):
        self.__dict__.update(kwds)
    
    def get(self, key):
        return self.__dict__.__getitem__(key)
    
    def has(self, key):
        return self.__dict__.__contains__(key)

    def set(self, key, value):
        self.__dict__.__setitem__(key,value)
