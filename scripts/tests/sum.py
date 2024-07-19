n = int(input())

D = {}

for i in range(0, n):
    name, m1, m2, m3 = input().split(" ")
    D[name] += [int(m1), int(m2), int(m3)]

query = input()

val = D.get(query)

soom = sun(val) / 3

print(soom)
