"""
Represents and manages one Spec in the XML. It has a list of active nodes.
"""

import base64
from copy import deepcopy
import re

from PoB.constants import bad_text, empty_spec_dict, starting_scion_node, tree_versions, PlayerClasses, _VERSION, _VERSION_str
from dialogs.popup_dialogs import ok_dialog


class Spec:
    def __init__(self, build, new_spec=None, version=_VERSION_str) -> None:  # Circular reference on Build()
        """
        Represents one Spec in the build. Most simple settings are properties.

        :param new_spec: the spec from the XML, dict from json, or None for a new Spec
        """
        self.internal_version = 6
        self.build = build
        self.tr = self.build.settings._app.tr

        self.spec = type(new_spec) is dict and new_spec or deepcopy(empty_spec_dict)
        self.nodes = set()
        self.ascendancy_nodes = []
        self.extended_hashes = []
        self.masteryEffects = {}
        self.sockets = {}
        self.active_hidden_skills = {}

        self.set_nodes_from_string(self.spec.get("nodes", f"{starting_scion_node}"))
        self.set_mastery_effects_from_string(self.spec["masteryEffects"])
        self.set_sockets_from_string(self.spec.get("Sockets", ""))

    @property
    def classId(self) -> int:
        return PlayerClasses(int(self.spec.get("classId", PlayerClasses.SCION.value)))

    @classId.setter
    def classId(self, new_class_id):
        """
        :param new_class_id: PlayerClasses or int or str if sourced from xml
        :return: N/A
        """
        if type(new_class_id) is PlayerClasses:
            new_class_id = PlayerClasses(new_class_id).value
        self.spec["classId"] = int(new_class_id)

    def classId_str(self) -> str:
        """Return a string of the current Class"""
        return self.classId.name.title()

    @property
    def ascendClassId(self) -> int:
        return self.spec.get("ascendClassId", 0)

    @ascendClassId.setter
    def ascendClassId(self, new_ascend_class_id):
        """
        :param new_ascend_class_id: int or str if sourced from xml
        :return: N/A
        """
        self.spec["ascendClassId"] = int(new_ascend_class_id)

    def ascendClassId_str(self):
        """Return a string of the current Ascendancy"""
        # get a list of ascendancies from the current tree's json
        class_json = self.build.current_tree.classes[self.classId]
        ascendancies = [_ascendancy["name"] for _ascendancy in class_json["ascendancies"]]
        # insert the class name for when ascendClassId == 0
        ascendancies.insert(0, "None")
        # Return the current ascendancy's name
        return ascendancies[self.ascendClassId]

    @property
    def treeVersion(self):
        return self.spec.get("treeVersion", _VERSION_str)

    @treeVersion.setter
    def treeVersion(self, new_version):
        """
        Set the tree version string in the dict
        :param new_version: str
        :return:
        """
        # ensure it is formatted correctly (n_nn). Remove dots and a trailing sub-version
        # Do not remove the leading \. despite what python grammar checkers might say.
        tmp_list = re.split(r"[._/]", new_version)
        self.spec["treeVersion"] = f"{tmp_list[0]}_{tmp_list[1]}"
        self.get_hidden_skills_from_nodes()

    @property
    def title(self):
        return self.spec.get("title", "")

    @title.setter
    def title(self, new_value):
        self.spec["title"] = new_value

    @property
    def URL(self):
        url = self.spec.get("URL", bad_text)
        return url == bad_text and "" or url

    @URL.setter
    def URL(self, new_url):
        """
        :param new_url: str
        :return: N/A
        """
        self.spec["URL"] = new_url

    def b_to_i(self, byte_array, begin, end, endian, length=0) -> int:
        """Grabs end->begin bytes and returns an int
        :param byte_array: byte_array:
        :param begin: int:
        :param end: int:
        :param endian: int:
        :param length: int:
        :return: int:
        """
        if length == 0:
            return int.from_bytes(byte_array[begin:end], endian)
        else:
            return int.from_bytes(byte_array[begin : begin + length], endian)

    def import_regular_nodes(self, decoded_data, start, count, endian):
        """
        Import all the regular nodes from an URl
        :param decoded_data:
        :param start: int:
        :param count: This needs to be passed in as it's one byte in ggg url and two in poeplanner
        :param endian: big (ggg) or little (poeplanner)
        :return: new index
        """
        end = start + (count * 2)

        print("nodes: start, end, count", start, end, count)
        decoded_nodes = decoded_data[start:end]

        # now decode the nodes structure to numbers
        # self.nodes = []
        self.nodes = set()
        for i in range(0, len(decoded_nodes), 2):
            print(i, int.from_bytes(decoded_nodes[i : i + 2], endian))
            self.nodes.add(int.from_bytes(decoded_nodes[i : i + 2], endian))
        if len(self.nodes) == 0:
            self.nodes.add(starting_scion_node)
        return end

    def import_cluster_nodes(self, decoded_data, start, count, endian):
        """
        Import the cluster nodes from an URL
        :param decoded_data:
        :param start:
        :param count: This needs to be passed in as it's one byte in ggg url and two in poeplanner
        :param endian: big (ggg) or little (poeplanner)
        :return: new index
        """

        end = start + (count * 2)
        print("cluster: start, end", start, end, count)
        if count > 0:
            decoded_cluster_nodes = decoded_data[start:end]
            # now decode the cluster nodes structure to numbers
            for i in range(0, len(decoded_cluster_nodes), 2):
                # print(''.join('{:02x} '.format(x) for x in cluster_nodes[i:i + 2]))
                # print(i, int.from_bytes(decoded_cluster_nodes[i : i + 2], endian) + 65536)
                self.nodes.add(int.from_bytes(decoded_cluster_nodes[i : i + 2], endian) + 65536)
        return end

    def import_mastery_nodes(self, decoded_data, start, count, endian):
        """
        Import the mastery nodes from an URL
        :param decoded_data:
        :param start:
        :param count: This needs to be passed in as it's one byte in ggg url and two in poeplanner
        :param endian: big (ggg) or little (poeplanner)
        :return: new index
        """

        end = start + (count * 4)
        print("mastery: start, end, count", start, end, count)
        if count > 0:
            self.masteryEffects = {}
            decoded_mastery_nodes = decoded_data[start:end]
            # now decode the mastery nodes structure to numbers
            for i in range(0, len(decoded_mastery_nodes), 4):
                # print(''.join('{:02x} '.format(x) for x in decoded_mastery_nodes[i:i + 2]))
                # print(''.join('{:02x} '.format(x) for x in decoded_mastery_nodes[i + 2:i + 4]))
                if endian == "little":
                    # poeplanner has these two round the other way too
                    m_id = int.from_bytes(decoded_mastery_nodes[i : i + 2], endian)
                    m_effect = int.from_bytes(decoded_mastery_nodes[i + 2 : i + 4], endian)
                else:
                    m_id = int.from_bytes(decoded_mastery_nodes[i + 2 : i + 4], endian)
                    m_effect = int.from_bytes(decoded_mastery_nodes[i : i + 2], endian)
                print("id", m_id, "effect", m_effect)
                self.masteryEffects[m_id] = m_effect
                self.nodes.add(m_id)

    def import_ascendancy_nodes(self, decoded_data, start, count, endian):
        """
        Import the ascendancy nodes from an URL from poeplpanner
        :param decoded_data:
        :param start:
        :param count: This needs to be passed in as it's one byte in ggg url and two in poeplanner
        :param endian: big (ggg) or little (poeplanner)
        :return: new index
        """
        end = start + (count * 2)
        print("ascendancy: start, end, count", start, end, count)
        if count > 0:
            decoded_ascendancy_nodes = decoded_data[start:end]
            # print(f"ascendancy_nodes: {len(decoded_ascendancy_nodes)},", "".join("{:02x} ".format(x) for x in decoded_ascendancy_nodes))
            for i in range(0, len(decoded_ascendancy_nodes), 2):
                # print("".join("{:02x} ".format(x) for x in decoded_ascendancy_nodes[i : i + 2]))
                print(i, self.b_to_i(decoded_ascendancy_nodes, i, i + 2, endian))
                self.nodes.add(self.b_to_i(decoded_ascendancy_nodes, i, i + 2, endian))
        return end

    def import_tree(self, new_url):
        """
        Import a passive tree URL.

        :return: N/A
        """
        print("Spec.import_tree", new_url)
        if new_url is None or new_url == "":
            return
        ggg = re.search(r"http.*passive-skill-tree/(.*/)?(.*)", new_url)
        poep = re.search(r"http.*poeplanner.com/(.*)", new_url)
        if ggg is not None:
            self.set_nodes_from_ggg_url(new_url)
        if poep is not None:
            self.set_nodes_from_poeplanner_url(new_url)
        if len(self.nodes) == 0:
            self.nodes.add(starting_scion_node)

    def set_nodes_from_ggg_url(self, ggg_url):
        """
        This function sets the nodes from GGG url.

        :param ggg_url: str: incoming url.
        :return: N/A
        """
        endian = "big"

        if ggg_url is None or ggg_url == "":
            return
        m = re.search(r"http.*passive-skill-tree/(.*/)?(.*)", ggg_url)

        # check the validity of what was passed in
        # group(1) is None or a version
        # group(2) is always the encoded string, with any variables
        if m is not None:
            self.URL = ggg_url
            self.treeVersion = m.group(1) is None and _VERSION_str or m.group(1)
            if self.treeVersion not in tree_versions.keys():
                v = re.sub("_", ".", self.treeVersion)
                ok_dialog(
                    self.build.win,
                    f"{self.tr('Invalid tree version')}: {v}",
                    f"{self.tr('Valid tree versions are')}:\n{str(list(tree_versions.values()))[1:-1]}\n\n"
                    + f"{self.tr('This will be converted to ')}{_VERSION}\n",
                )
                self.title = f"{self.title} ({self.tr('was')} v{v})"
                self.treeVersion = _VERSION_str

            tmp_output = m.group(2).split("?")
            encoded_str = tmp_output[0]
            del tmp_output[0]
            # a list of variable=value (accountName=xyllywyt&characterName=PrettyXylly) found on the url or an empty list
            variables = tmp_output
            decoded_data = base64.urlsafe_b64decode(encoded_str)

            # # output[0] will be the encoded string and the rest will variable=value, which we don't care about (here)
            # output = m.group(2).split("?")
            # decoded_data = base64.urlsafe_b64decode(output[0])

            # the decoded_data is 0 based, so every index will be one smaller than the equivalent in lua
            if decoded_data and len(decoded_data) > 7:
                version = self.b_to_i(decoded_data, 0, 4, endian)
                print(self.tr(f"Valid tree found, version: {version}"))

                self.classId = decoded_data[4]
                self.ascendClassId = version >= 4 and decoded_data[5] or 0

                # Nodes. Ascendancy nodes are in here also
                idx = 6
                nodes_count = self.b_to_i(decoded_data, idx, idx + 1, endian)
                idx = self.import_regular_nodes(decoded_data, idx + 1, nodes_count, endian)

                # Clusters
                cluster_count = decoded_data[idx]
                idx = self.import_cluster_nodes(decoded_data, idx + 1, cluster_count, endian)

                # Mastery
                mastery_count = decoded_data[idx]
                mastery_start = idx + 1
                self.import_mastery_nodes(decoded_data, mastery_start, mastery_count, endian)

    def set_nodes_from_poeplanner_url(self, poep_url):
        """
        This function sets the nodes from poeplanner url.

        :param poep_url: str: incoming url.
        :return: N/A
        """
        endian = "little"

        def get_tree_version(minor):
            """Translates poeplanner internal tree version to GGG version"""
            # fmt: off
            peop_tree_versions = { # poeplanner id: ggg version
                31: 24, 29: 23, 27: 22, 26: 21, 25: 20, 24: 19, 23: 18, 22: 17, 21: 16, 19: 15, 18: 14, 17: 13, 16: 12, 15: 11, 14: 10,
            }
            # fmt: on
            return peop_tree_versions.get(minor, -1)

        if poep_url is None or poep_url == "":
            return
        m = re.search(r"http.*poeplanner.com/(.*)?(.*)", poep_url)
        # group(1) is always the encoded string
        if m is not None:
            # print("M", m.groups())
            # Remove any variables at the end (probably not required for poeplanner)
            tmp_output = m.group(1).split("?")
            encoded_str = tmp_output[0]
            del tmp_output[0]
            variables = tmp_output  # a list of variable=value found on the url or an empty list

            decoded_data = base64.urlsafe_b64decode(encoded_str)
            # print(f"decoded_data: {len(decoded_data)},", "".join("{:02x} ".format(x) for x in decoded_data))
            if decoded_data and len(decoded_data) > 10:
                # 0-1 is version ?
                version = self.b_to_i(decoded_data, 0, 2, endian)

                # 2 is ??

                # 3-6 is tree version_version
                major_version = self.b_to_i(decoded_data, 3, 4, endian)
                minor_version = get_tree_version(self.b_to_i(decoded_data, 5, 6, endian))
                self.treeVersion = minor_version < 0 and _VERSION_str or f"{major_version}_{minor_version}"
                if self.treeVersion not in tree_versions.keys():
                    v = re.sub("_", ".", self.treeVersion)
                    ok_dialog(
                        self.build.win,
                        f"{self.tr('Invalid tree version')}: {v}",
                        f"{self.tr('Valid tree versions are')}:\n{str(list(tree_versions.values()))[1:-1]}\n\n"
                        f"{self.tr('This will be converted to ')}{_VERSION}\n",
                    )
                    self.title = f"{self.title} ({self.tr('was')} v{v})"
                    self.treeVersion = _VERSION_str

                # 7 is Class, 8 is Ascendancy
                self.classId = decoded_data[7]
                self.ascendClassId = decoded_data[8]

                # 9 is Bandit
                self.build.set_bandit_by_number(decoded_data[9])

                # Nodes
                idx = 10
                nodes_count = self.b_to_i(decoded_data, idx, idx + 1, endian)
                idx = self.import_regular_nodes(decoded_data, idx + 2, nodes_count, endian)

                # Clusters
                cluster_count = self.b_to_i(decoded_data, idx, idx + 1, endian)
                idx = self.import_cluster_nodes(decoded_data, idx + 2, cluster_count, endian)

                # Ascendancy Nodes
                ascendancy_count = self.b_to_i(decoded_data, idx, idx + 1, endian)
                idx = self.import_ascendancy_nodes(decoded_data, idx + 2, ascendancy_count, endian)

                # Masteries
                mastery_count = self.b_to_i(decoded_data, idx, idx + 1, endian)
                self.import_mastery_nodes(decoded_data, idx + 2, mastery_count, endian)

    def export_nodes_to_url(self):
        endian = "big"
        byte_stream = bytearray()
        byte_stream.extend(self.internal_version.to_bytes(4, endian))
        byte_stream.append(self.classId)
        byte_stream.append(self.ascendClassId)

        # print(''.join('{:02x} '.format(x) for x in byte_stream))

        # separate the cluster nodes from the real nodes
        nodes = []
        cluster_nodes = []
        for node in sorted(self.nodes):
            if node >= 65536:
                cluster_nodes.append(node)
            else:
                nodes.append(node)

        byte_stream.append(len(nodes))
        for node in self.nodes:
            byte_stream.extend(node.to_bytes(2, endian))
        # print(''.join('{:02x} '.format(x) for x in byte_stream))

        byte_stream.append(len(cluster_nodes))
        for cluster_node in cluster_nodes:
            cluster_node -= 65536
            byte_stream.extend(cluster_node.to_bytes(2, endian))
        # print(''.join('{:02x} '.format(x) for x in byte_stream))

        byte_stream.append(len(self.masteryEffects))
        for mastery_node in self.masteryEffects:
            byte_stream.extend(self.masteryEffects[mastery_node].to_bytes(2, endian))
            byte_stream.extend(mastery_node.to_bytes(2, endian))

        # string = " ".join('{:02x}'.format(x) for x in byte_stream)
        # print(string)

        encoded_string = base64.urlsafe_b64encode(byte_stream).decode("utf-8")
        self.URL = f"https://www.pathofexile.com/passive-skill-tree/{encoded_string}"
        return self.URL

    def set_mastery_effects_from_string(self, new_effects):
        """
        masteryEffects is a string of {paired numbers}. Turn it into a dictionary [int1] = int2

        :param new_effects: str
        :return:
        """
        if new_effects != "":
            # get a list of matches
            effects = re.findall(r"{(\d+),(\d+)}", new_effects)
            for effect in effects:
                self.masteryEffects[int(effect[0])] = int(effect[1])

    def set_sockets_from_string(self, new_sockets):
        """
        masteryEffects is a string of {paired numbers}. Turn it into a dictionary [int1] = int2

        :param new_sockets: str
        :return:
        """
        if new_sockets != "":
            self.sockets.clear()
            # get a list of matches
            sockets = re.findall(r"{(\d+),(\d+)}", new_sockets)
            for socket in sockets:
                self.sockets[int(socket[0])] = int(socket[1])

    def get_mastery_effect(self, node_id):
        """return one node id from mastery effects"""
        return self.masteryEffects.get(node_id, -1)

    def set_mastery_effect(self, node_id, effect_id):
        """add one node id from mastery effects"""
        print("set_mastery_effect", node_id, effect_id)
        self.masteryEffects[node_id] = int(effect_id)

    def remove_mastery_effect(self, node_id):
        """remove one node id from mastery effects"""
        try:
            del self.masteryEffects[node_id]
        except KeyError:
            pass

    def list_assigned_effects_for_mastery_type(self, node_list):
        """
        Get a list of effects assigned for a given mastery type (eg: "Life Mastery").

        :param node_list: list: A list of node id's
        :return: list of effects already assigned.
        """
        pass

    def add_node(self, node):
        """Things to do when adding a node"""
        self.nodes.add(node.id)
        if node.grants_skill:
            self.active_hidden_skills[f"Tree:{node.id}"] = node.grants_skill

    def remove_node(self, node):
        """Things to do when removing a node"""
        self.nodes.remove(node.id)
        if node.grants_skill:
            # self.win.remove_item_or_node_with_skills(f"Tree:{node.id}")
            self.active_hidden_skills.pop(f"Tree:{node.id}", 0)

    def get_hidden_skills_from_nodes(self):
        """Search selected node, from the current tree's nodes for hidden skills.
        Called when changing tree versions or setting nodes (eg import)"""
        ctree_nodes = self.build.current_tree.nodes
        for n_id in [n_id for n_id in self.nodes if ctree_nodes[n_id].grants_skill != ("", 0)]:
            self.add_node(ctree_nodes[n_id])
        # self.active_hidden_skills = [ctree_nodes[n_id].grants_skill for n_id in self.nodes if ctree_nodes[n_id].grants_skill != ("", 0)]
        # print(f"get_hidden_skills_from_nodes: {self.active_hidden_skills}")

    def set_nodes_from_string(self, new_nodes):
        """
        Turn the string list of numbers into a list of numbers
        :param new_nodes: str
        :return: N/A
        """
        if new_nodes:
            self.nodes = set([int(s_node) for s_node in new_nodes.split(",")])
            self.get_hidden_skills_from_nodes()

    def set_extended_hashes_from_string(self, new_nodes):
        """
        Turn the string list of numbers into a list of numbers
        :param new_nodes: str
        :return: N/A
        """
        print("set_extended_hashes_from_string", new_nodes)
        if new_nodes:
            self.nodes = set(new_nodes.split(","))

    def set_item_to_socket(self, node_id, item_id):
        """
        Add or delete an entry to self.sockets
        :param node_id: a node on the tree (currently assuming this has been checked to be a socket)
        :param item_id: an Item's id, or 0 to'empty' a socket
        :return: N/A
        """
        if node_id in self.nodes:
            if node_id == 0:
                self.sockets.pop(node_id, None)
            else:
                self.sockets[node_id] = item_id

    def save(self, xml=False):
        """
        Save anything that can't be a property, like Nodes, sockets
        :param xml: bool: Return a XML snippet
        :return: Title,dict or Title,xml snippet
        """
        if len(self.nodes) > 0:
            self.spec["nodes"] = ",".join(f"{node}" for node in sorted(self.nodes))
        self.export_nodes_to_url()

        # put masteryEffects back into a string of {number,number},{number,number}
        str_mastery_effects = ""
        for effect in self.masteryEffects.keys():
            str_mastery_effects += f"{{{effect},{self.masteryEffects[effect]}}},"
        self.spec["masteryEffects"] = str_mastery_effects.rstrip(",")

        # same for sockets
        str_sockets = ""
        for socket in self.sockets.keys():
            str_sockets += f"{{{socket},{self.sockets[socket]}}},"
        self.spec["Sockets"] = str_sockets.rstrip(",")
        return self.spec

    # def save(self):
    #     """Save things to the internal dict() and return it"""
    #     if len(self.nodes) > 0:
    #         self.spec["nodes"] = ",".join(f"{node}" for node in sorted(self.nodes))
    #     self.export_nodes_to_url()
    #
    #     str_mastery_effects = ""
    #     for effect in self.masteryEffects.keys():
    #         str_mastery_effects += f"{{{effect},{self.masteryEffects[effect]}}},"
    #     self.spec["masteryEffects"] = str_mastery_effects.rstrip(",")
    #
    #     return self.spec

    def load_from_ggg_json(self, json_tree, json_character):
        """
        Import the tree (and later the jewels)

        :param json_tree: json import of tree and jewel data
        :param json_character: json import of the character items
        :return: N/A
        """
        # print("load_from_ggg_json", json_character)
        # print("load_from_ggg_json", json_tree)
        self.nodes = set(json_tree.get("hashes", "0"))
        # print(self.nodes)
        self.extended_hashes = json_tree.get("hashes_ex", [])
        # for the json import, this is a list of large ints (https://www.pathofexile.com/developer/docs/reference)
        #   with the modulo remainder being "the string value of the mastery node skill hash"
        #   with the quotient being "the value is the selected effect hash"
        for effect in json_tree.get("mastery_effects", []):
            self.masteryEffects[int(effect) % 65536] = int(effect) // 65536
        self.classId = json_tree.get("character", 0)
        self.ascendClassId = json_tree.get("ascendancy", 0)
        # ToDo: investigate jewel_data
        # self.jewel_data = json_tree.get("jewel_data", 0)

        # write nodes and stuff to xml
        self.save()

    def import_from_poep_json(self, json_tree):
        """
        Import the tree (and later the jewels)

        :param json_tree: json import of tree and jewel data
        :return: N/A
        """
        self.nodes = set(json_tree.get("selectedNodeHashes", starting_scion_node))
        self.extended_hashes = json_tree.get("selectedExtendedNodeHashes", [])
        # for the json import, this is a list of:
        # { "effectHash": 28638, "masteryHash": 64128 }
        for mastery_effect in json_tree.get("selectedMasteryEffects", []):
            mastery_node = int(mastery_effect["masteryHash"])
            self.nodes.add(mastery_node)
            self.masteryEffects[mastery_node] = int(mastery_effect["effectHash"])
        self.classId = json_tree.get("classIndex", 0)
        self.ascendClassId = json_tree.get("ascendancyIndex", 0)
        # write nodes and stuff to xml
        self.save()
