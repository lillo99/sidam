C82 = "!\"%&'()*+,-./0123456789:;<=>?ABCDEFGHIJKLMNOPQRSTUVWXYZ_abcdefghijklmnopqrstuvwxyz"
C32 = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
P = [2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83]
def check(part):
    n = len(part); s = sum(C82.index(c) * P[n-1-i] for i, c in enumerate(part)) % 1021
    return C32[s >> 5] + C32[s & 31]
def ok(b): return check(b[:-2]) == b[-2:]
