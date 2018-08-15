from collections import defaultdict
from pprint import pprint
from random import choice


def reverse_elmap():
    from element import load_elmap
    elmap = load_elmap()
    ret = defaultdict(list)
    for (a, b), c in elmap.items():
        ret[c].append((a, b))
    return ret


def bfs(known, end='dragon', pamle=None):
    """
        return list of steps (a,b)->c
    """
    assert isinstance(known, set)
    if not pamle:
        pamle = reverse_elmap()
        known = known.copy()

    variants = pamle[end]
    if not variants:
        return []

    retcands = []
    for substrates in variants:
        a, b = substrates
        retcand = [(a, b)]
        
        if a not in known or b not in known:
            for e in (a, b):
                steps = bfs(known.copy(), e, pamle=pamle)
                retcand = steps + retcand

        retcands.append(retcand)

    retcands.sort(key=lambda x: len(x))

    return retcands[0]


if __name__ == '__main__':
    # import timeit
    # print(timeit.timeit(lambda: bfs({'water', 'fire', 'air', 'earth'}, 'dragon'), number=1000))
    pprint(bfs({'water', 'fire', 'air', 'earth'}, 'dragon'))
