"""
Carbon-footprint calculation tool.

Implements the linear LCA formula described in
``agent/tools/carbon_footprint_calculating.docx``::

    f(cf) = sum_k ( m_k * Cef_k )

where ``m_k`` is the mass ratio (or mass) of component ``k`` of the mixture and
``Cef_k`` is the corresponding carbon emission factor (kg CO2-eq per kg of
material).  Default emission factors:

    Cement      735
    Slag         83
    FA           20
    SF           70
    Biochar   -2300
    Fiber      4980
    Water       0.168
    Sand        2.51
    Gravel      2.18
    BDA         0
    Admixture  1670
    Other      1670

The keys used in the lookup match the question identifiers from the existing
extraction pipeline (2.1 - 2.12) and friendly names (case-insensitive).
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Mapping, Optional


DEFAULT_EMISSION_FACTORS: Dict[str, float] = {
    "cement": 735.0,
    "slag": 83.0,
    "fa": 20.0,
    "fly ash": 20.0,
    "sf": 70.0,
    "silica fume": 70.0,
    "biochar": -2300.0,
    "fiber": 4980.0,
    "water": 0.168,
    "sand": 2.51,
    "fine aggregate": 2.51,
    "gravel": 2.18,
    "coarse aggregate": 2.18,
    "bda": 0.0,
    "biochar developed aggregate": 0.0,
    "admixture": 1670.0,
    "other": 1670.0,
}


QUESTION_KEY_TO_COMPONENT: Dict[str, str] = {
    "2.1": "cement",
    "2.2": "slag",
    "2.3": "fa",
    "2.4": "sf",
    "2.5": "biochar",
    "2.6": "fiber",
    "2.7": "water",
    "2.8": "sand",
    "2.9": "gravel",
    "2.10": "bda",
    "2.11": "admixture",
    "2.12": "other",
}


def _coerce_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip()
    if not s or s.lower() in {"nan", "na", "none", "null", "-"}:
        return None
    s = s.split("±")[0].strip()
    s = s.replace("%", "").replace(",", "").strip()
    try:
        return float(s)
    except ValueError:
        return None


def carbon_footprint_calculating(
    mixture: Mapping[str, Any],
    *,
    emission_factors: Optional[Mapping[str, float]] = None,
    custom_factors: Optional[Mapping[str, float]] = None,
) -> Dict[str, Any]:
    """
    Compute the LCA carbon footprint of a single mixture.

    Parameters
    ----------
    mixture : mapping
        Mapping of component -> mass / mass-ratio. Keys may be question
        identifiers (e.g. ``"2.5"``) or component names (e.g. ``"biochar"``).
    emission_factors : mapping, optional
        Override the whole emission factor table. Keys are component names
        (case-insensitive).
    custom_factors : mapping, optional
        Merge-style override on top of the defaults (component name -> factor).

    Returns
    -------
    dict
        ``{"success": True, "data": {"f_cf": float, "breakdown": [{"component", "mass", "factor", "contribution"}], "unit": "kg CO2-eq / unit mass"}}``
    """
    if not isinstance(mixture, Mapping):
        return {"success": False, "error": "`mixture` must be a mapping of component -> mass value."}

    factors: Dict[str, float] = dict(emission_factors or DEFAULT_EMISSION_FACTORS)
    if custom_factors:
        for k, v in custom_factors.items():
            factors[str(k).lower().strip()] = float(v)

    breakdown = []
    total = 0.0
    missing_factor: list[str] = []

    for raw_key, raw_value in mixture.items():
        component = QUESTION_KEY_TO_COMPONENT.get(str(raw_key).strip(), str(raw_key).strip().lower())
        mass = _coerce_float(raw_value)
        if mass is None:
            continue

        factor = factors.get(component)
        if factor is None:
            missing_factor.append(component)
            continue

        contribution = mass * factor
        total += contribution
        breakdown.append({
            "key": raw_key,
            "component": component,
            "mass": mass,
            "factor": factor,
            "contribution": contribution,
        })

    return {
        "success": True,
        "data": {
            "f_cf": total,
            "breakdown": breakdown,
            "unit": "kg CO2-eq per unit mass of mixture",
            "missing_factor": missing_factor,
        },
    }


def carbon_footprint_batch(
    mixtures: Iterable[Mapping[str, Any]],
    **kwargs: Any,
) -> Dict[str, Any]:
    """Convenience wrapper to score a batch of mixtures."""
    results = [carbon_footprint_calculating(m, **kwargs) for m in mixtures]
    return {"success": True, "data": {"results": results, "count": len(results)}}
