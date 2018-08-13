from collections import defaultdict
from pprint import pprint


def reverse_elmap():
    from element import load_elmap
    elmap = load_elmap()
    ret = defaultdict(list)
    for (a, b), c in elmap.items():
        ret[c].append((a, b))
    return ret


def bfs(known, end='dragon', pamle=None):
    """
        return steps to reach and list of steps (a,b)->c
    """
    assert isinstance(known, set)
    if not pamle:
        pamle = reverse_elmap()
        known = known.copy()

    ret = 1
    retsteps = pamle[end]
    for a, b in pamle[end]:
        if b not in known or b not in known:
            for e in (a, b):
                steps, steplist = bfs(known, e, pamle=pamle)
                ret += steps
                retsteps = steplist + retsteps
                
                known.add(e)
    return ret, retsteps


if __name__ == '__main__':
    # import timeit
    # print(timeit.timeit(lambda: bfs({'water', 'fire', 'air', 'earth'}, 'dragon'), number=1000))
    pprint(bfs({'water', 'fire', 'air', 'earth', 'life'}, 'dragon'))
