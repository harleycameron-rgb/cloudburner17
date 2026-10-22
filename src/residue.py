from collections.abc import Mapping, Sequence

if __package__:
    from .harmony import smooth_residue
else:
    from harmony import smooth_residue


def Residue(data, tag):
    r = sum(data)
    s = f"{tag}-{int(r)}"
    return smooth_residue((r, s))


_RESIDUE_KINDS = ("syntactic", "semantic", "epistemic")


def typed_residue(residuals):
    """Group model residuals by type without changing the legacy Residue API."""
    if not isinstance(residuals, Sequence) or isinstance(
        residuals, (str, bytes, bytearray)
    ):
        raise TypeError("residuals must be a sequence")

    grouped = {kind: [] for kind in _RESIDUE_KINDS}
    seen = set()
    for entry in residuals:
        if not isinstance(entry, Mapping):
            raise TypeError("each residual must be a mapping")
        if set(entry) != {"model", "kind", "residual"}:
            raise ValueError("each residual must contain model, kind, and residual")

        model = entry["model"]
        kind = entry["kind"]
        residual = entry["residual"]
        if not isinstance(model, str) or not model.strip():
            raise ValueError("residual model must be a non-empty string")
        if kind not in _RESIDUE_KINDS:
            raise ValueError(f"residual kind must be one of {_RESIDUE_KINDS}")
        if not isinstance(residual, str):
            raise TypeError("residual value must be a string")
        key = (model, kind)
        if key in seen:
            raise ValueError("a model may provide only one residual of each kind")
        seen.add(key)
        grouped[kind].append({"model": model, "residual": residual})

    for kind in _RESIDUE_KINDS:
        grouped[kind].sort(key=lambda item: item["model"])
    return grouped
