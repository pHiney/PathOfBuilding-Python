# Defining custom names for lists
# pull in live code so fixes/updates affect the main app
import sys

sys.path.insert(1, "../src/")
from PoB.pob_file import read_json, read_xml_as_dict, write_json
from PoB.pob_xml import load_from_xml, read_xml


file = "stats"
# file = "t"
# file = "XyllySRS"
# file = "Phys Trapper Saboteur"
# file = "_LittleXyllyBleeder_ggg_import_with_crucible_from_lua"
# file = "t1"

build = read_xml_as_dict(f"{file}.xml")
write_json(f"{file}_xml.json", build)

build = load_from_xml(f"{file}.xml")
write_json(f"{file}.json", build)
