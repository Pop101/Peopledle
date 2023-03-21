from itertools import product

# From https://stackoverflow.com/questions/2460177/edit-distance-in-python
# I'd use python-Levenshtein, but it doesn't seem to work on the pi


def edit_distance(s1, s2, processor=lambda x: x):
    s1, s2 = processor(s1), processor(s2)
    d = {**{(i, 0): i for i in range(len(s1) + 1)}, **{(0, j): j for j in range(len(s2) + 1)}}
    for i, j in product(range(1, len(s1) + 1), range(1, len(s2) + 1)):
        d[i, j] = min((s1[i - 1] != s2[j - 1]) + d[i - 1, j - 1], d[i - 1, j] + 1, d[i, j - 1] + 1)
    return d[i, j]
