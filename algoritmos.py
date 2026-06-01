import math


def dist(a, b):
    return math.hypot(a[0]-b[0], a[1]-b[1])


def median_of_medians(a, k):
    if not a:
        return None
    if len(a) <= 5:
        return sorted(a)[k]
    chunks = [a[i:i+5] for i in range(0, len(a), 5)]
    medians = [sorted(chunk)[len(chunk)//2] for chunk in chunks]
    pivot = median_of_medians(medians, len(medians)//2)
    lows = [x for x in a if x < pivot]
    highs = [x for x in a if x > pivot]
    pivots = [x for x in a if x == pivot]
    if k < len(lows):
        return median_of_medians(lows, k)
    elif k < len(lows) + len(pivots):
        return pivot
    else:
        return median_of_medians(highs, k - len(lows) - len(pivots))


def closest_pair(points):
    px = sorted(points, key=lambda p: p[0])
    py = sorted(points, key=lambda p: p[1])

    def _rec(px, py):
        n = len(px)
        if n <= 3:
            best = (1e9, None, None)
            for i in range(n):
                for j in range(i+1, n):
                    d = dist(px[i], px[j])
                    if d < best[0]:
                        best = (d, px[i], px[j])
            return best
        mid = n//2
        midx = px[mid][0]
        Lx = px[:mid]
        Rx = px[mid:]
        Ly = [p for p in py if p[0] <= midx]
        Ry = [p for p in py if p[0] > midx]
        dl, a1, b1 = _rec(Lx, Ly)
        dr, a2, b2 = _rec(Rx, Ry)
        best = (dl, a1, b1) if dl < dr else (dr, a2, b2)
        strip = [p for p in py if abs(p[0]-midx) < best[0]]
        for i in range(len(strip)):
            for j in range(i+1, min(i+7, len(strip))):
                d = dist(strip[i], strip[j])
                if d < best[0]:
                    best = (d, strip[i], strip[j])
        return best

    return _rec(px, py)


def merge_groups_by_closest(zombies, groups, threshold):
    points = [(z.pos[0], z.pos[1], idx) for idx, z in enumerate(zombies)]
    if len(points) < 2:
        return groups
    changed = False
    while True:
        d, p1, p2 = closest_pair(points)
        if d is None or d >= threshold:
            break
        i = p1[2]; j = p2[2]
        gi = None; gj = None
        for gid, s in list(groups.items()):
            if i in s: gi = gid
            if j in s: gj = gid
        if gi is None: gi = max(groups.keys(), default=-1)+1; groups[gi] = set([i])
        if gj is None: gj = max(groups.keys(), default=-1)+1; groups[gj] = set([j])
        if gi != gj:
            groups[gi].update(groups[gj])
            del groups[gj]
            changed = True
        points = [(x,y,idx) for (x,y,idx) in points if idx not in [i,j]]
        if len(points) < 2:
            break
    merged = True
    while merged:
        merged = False
        gids = list(groups.keys())
        for a in gids:
            for b in gids:
                if a>=b or a not in groups or b not in groups: continue
                close = False
                for i in groups[a]:
                    for j in groups[b]:
                        if dist(zombies[i].pos, zombies[j].pos) < threshold*1.1:
                            close = True; break
                    if close: break
                if close:
                    groups[a].update(groups[b]); del groups[b]
                    merged = True
                    break
            if merged: break
    return groups
