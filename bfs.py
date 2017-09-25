from collections import defaultdict


def reverse_elmap():
    from element import load_elmap
    elmap = load_elmap()
    ret = defaultdict(list)
    for (a, b), c in elmap.items():
        ret[c].append(a)
        ret[c].append(b)
    return ret


def bfs(known, end='dragon', pamle=None):
    assert isinstance(known, set)
    if not pamle:
        pamle = reverse_elmap()
        known = known.copy()

    ret = 1
    for e in pamle[end]:
        if e not in known:
            ret += bfs(known, e, pamle=pamle)
            known.add(e)
    return ret


if __name__ == '__main__':
    import timeit
    print(timeit.timeit(lambda: bfs({'water', 'fire', 'air', 'earth'}, 'dragon'), number=1000))
