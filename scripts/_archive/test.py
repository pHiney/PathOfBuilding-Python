import re
import timeit
import locale

# print(timeit.timeit("[(a, b) for a in (1, 3, 5) for b in (2, 4, 6)]"))

# print(timeit.timeit('import re; re.sub(r"MaelstrÃ¶m|Maelstrom", "Maelstr\u00f6m", "Maelström Staff")', number=10000))

# print(timeit.timeit('"Maelström Staff".replace("Maelstrom", "Maelstr\u00f6m").replace("MaelstrÃ¶m", "Maelstr\u00f6m")', number=10000))

# s = "Test String"
# lvl = 68
# c = "Guardian"
# l = 25 - len(s) + len(c)
# ss=locale.format_string(f"%{l}s", c)
# print(f"{s}{ss} lvl:{lvl}")
# s = "Test String1"
# l = 25 - len(s) + len(c)
# ss=locale.format_string(f"%{l}s", c)
# print(f"{s}{ss} lvl:{lvl}")
# s = "12345678901234567890123"
# l = 25 - len(s) + len(c)
# ss=locale.format_string(f"%{l}s", c)
# print(f"{s}{ss} lvl:{lvl}")
# print(f"{s}{ss.ljust(l)} lvl:{lvl}")
# s = "Test String111"
# l = 25 - len(s) + len(c)
# ss=locale.format_string(f"%{l}s", c)
# print(f"{s}{ss} lvl:{lvl}")


_line = "{tags:jewellery_attribute}{variant:1}{range:0.5}+(10-20) to all Attributes"
m = re.search(r"({tags:[\w,]+})", _line)
print(f"{m=}")
m = re.search(r"({.*})", _line)
print(f"{m=}")

print(locale.format_string("%0.3f",0.5))
print(locale.format_string("%0.3g",0.5))

r= "fred"
print(re.sub(r"{range:([0-9.]+)}", rf"{{range:{r}}}", _line))
