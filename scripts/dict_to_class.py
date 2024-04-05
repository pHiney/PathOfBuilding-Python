import sys
sys.path.insert(1, "../src/")
sys.path.insert(1, "../src/PoB")
from PoB.pob_file import read_json, write_json

class PoBDict(object):
    """
    Turns a dictionary into a class
    """

    def __init__(self, dictionary):
        """PoBDict. Constructor"""
        self.load(dictionary)
        self._internal_var1 = "one"
        self._internal_var2 = "two"

    def __repr__(self):
        """return: str:"""
        return "%s" % self.__dict__

    def load(self, dictionary=None):
        """Reset internal dictionary attr's"""
        # Only need to delete the top level as GC should dispose of the rest.
        # On first run through, keys() is empty.
        keys = [key for key in self.__dict__.keys() if not key.startswith("_")]
        print(f"PoBdict: load: {keys=}")
        for key in keys:
            delattr(self, key)

        if dictionary:
            for key, value in dictionary.items():
                if type(value) is dict:
                    setattr(self, key, PoBDict(value))
                else:
                    setattr(self, key, value)

    def save(self):
        """return: dict: the python type dictionary representation of the class"""
        _dict = {}
        for key, value in self.__dict__.items():
            if not key.startswith("_"):
                if type(value) is PoBDict:
                    _dict[key] = value.save()
                else:
                    _dict[key] = value
        return _dict

    def exists(self, key):
        """"""
        return getattr(self, key, None) is not None

#----------------------------------------------------------------------
sub_dict = {"color":"red",
             "size":9,
             "material":"rubber"}
ball_dict = {"color":"blue",
             "size":8,
             "material":"rubber",
             "sub": sub_dict
             }

#----------------------------------------------------------------------
ball = PoBDict(ball_dict)

print(f"1 {ball_dict=}")
print(f"1 {     ball=}")
print(f"1 {ball.size=}")
print(f"1 {ball.sub=}")
print(f"1 {ball.sub.size=}")

#----------------------------------------------------------------------
ball.sub.material="wood"
if not ball.sub.exists("extra"):
    ball.sub.extra = PoBDict({})
ball.sub.extra.something="something"
print(f"\n2 {ball.sub.material=}")

print(f"2 {type(ball.save())=}")
print(f"2        {ball=}")
print(f"2 {ball.save()=}")

write_json("test.json", ball.save())

#----------------------------------------------------------------------
ball.load(sub_dict)
print(f"\n3        {ball=}")
