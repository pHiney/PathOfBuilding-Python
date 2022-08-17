"""
Node Class

This class represents one node of the Passive Tree.

It is referenced by the Tree class
"""
from constants import _VERSION


class Node:
    def __init__(self, _node, _version: str = _VERSION) -> None:
        """
        init
        :param _node: a copy of the dictionary for this node only
        :param _version:
        """
        # declare variables that are set in functions
        self.version = _version
        self._active = False

        # calculated values
        self.conquered = False
        self.linkedId = {}
        self.modKey = ""
        self.modList = {}
        self.mods = {}
        self.overlay = {}
        self.size = {}
        self.sprites = {}
        self.x = 0
        self.y = 0
        self._type = ""
        self.startArt = ""
        self._reminderText = ""  # Do not use None
        self.masterySprites = {}
        self.group = {}
        self.isBlighted = False

        """values from the passed in dictionary"""
        self.name = _node.get("name", "")
        self.dn = _node.get("name", "")
        self._id = _node.get("skill", 0)
        self.skill = _node.get("skill", 0)
        self.group_id = _node.get("group", -1)
        self.g = _node.get("group", -1)
        self.orbit = _node.get("orbit", 0)
        self.o = _node.get("orbit", 0)
        self.orbitIndex = _node.get("orbitIndex", 0)
        self.oidx = _node.get("orbitIndex", 0)
        self.passivePointsGranted = _node.get("passivePointsGranted", 0)
        self.stats = _node.get("stats", [])
        self.sd = _node.get("stats", [])
        self.reminderText = _node.get("reminderText", "")
        self.ascendancyName = _node.get("ascendancyName", "")
        self.nodes_in = _node.get("in", [])
        self.nodes_out = _node.get("out", [])
        self.recipe = _node.get("recipe", [])
        self.classStartIndex = _node.get("classStartIndex", -1)
        self.masteryEffects = _node.get("masteryEffects", {})
        self.isNotable = _node.get("isNotable", False)
        self.isAscendancyStart = _node.get("isAscendancyStart", False)
        self.isMastery = _node.get("isMastery", False)
        self.isJewelSocket = _node.get("isJewelSocket", False)
        self.expansionJewel = _node.get("expansionJewel", {})
        self.isProxy = _node.get("isProxy", False)
        self.isKeystone = _node.get("isKeystone", False)
        self.flavourText = _node.get("flavourText", "")

        """ These value are text items indicating the name of a file. 
            We will overwrite them with a handle to an image"""
        self.icon = _node.get("icon", "")
        self.inactiveIcon = _node.get("inactiveIcon", "")
        self.activeIcon = _node.get("activeIcon", "")
        self.activeEffectImage = _node.get("activeEffectImage", "")

    @property
    def id(self):
        return self._id

    # @id.setter
    # def id(self, new_id):
    #     self._id = new_id

    @property
    def active(self):
        """
        Used for determining the right icon to display ?? The build should have a separate list managing that
        :return:
        """
        if self._active:
            return "Active"
        else:
            return "Inactive"

    @active.setter
    def active(self, new_state: bool):
        self._active = new_state

    @active.setter
    def active(self, new_state: str):
        self._active = new_state == "Active"

    @property
    def reminderText(self):
        return self._reminderText

    @reminderText.setter
    def reminderText(self, new_text):
        self._reminderText = ""
        if new_text is None:
            return
        for line in new_text:
            self._reminderText = f"{self._reminderText}{line}\n"
        self._reminderText = self._reminderText.strip()

    @property
    def type(self):
        return self._type

    @type.setter
    def type(self, new_type):
        self._type = new_type