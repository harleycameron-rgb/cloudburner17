from harmony import smooth_residue


def Residue(data, tag):
    r = sum(data)
    s = f"{tag}-{int(r)}"
    return smooth_residue((r, s))
