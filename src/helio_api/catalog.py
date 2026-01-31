"""
Catalog and account functions for the Helio Additive API.

Provides access to supported printers, materials, print priority options,
user quota information, default optimization settings, and recent runs.
"""

from __future__ import annotations

from helio_api.client import HelioClient
from helio_api.queries import (
    QUERY_DEFAULT_OPT_SETTINGS,
    QUERY_MATERIALS,
    QUERY_PRINT_PRIORITY_OPTIONS,
    QUERY_PRINTERS,
    QUERY_RECENT_RUNS,
    QUERY_USER_QUOTA,
)


def list_printers(client: HelioClient) -> list[dict]:
    """Fetch all supported printers (paginated).

    Returns:
        List of dicts with keys: ``id``, ``name``, ``bambustudio_name``.
    """
    all_printers: list[dict] = []
    page = 1
    while True:
        data, errors, trace_id = client.query(QUERY_PRINTERS, {"page": page})
        if errors:
            print(f"  Error fetching printers (page {page}): {errors}")
            break
        if not data or "printers" not in data:
            break
        printers_data = data["printers"]
        for obj in printers_data.get("objects", []):
            alt = obj.get("alternativeNames") or {}
            all_printers.append({
                "id": obj.get("id", ""),
                "name": obj.get("name", ""),
                "bambustudio_name": alt.get("bambustudio", ""),
            })
        if not printers_data.get("pageInfo", {}).get("hasNextPage", False):
            break
        page += 1
    return all_printers


def list_materials(client: HelioClient) -> list[dict]:
    """Fetch all supported materials (paginated), filtered to FILAMENT feedstock.

    Returns:
        List of dicts with keys: ``id``, ``name``, ``feedstock``, ``bambustudio_name``.
    """
    all_materials: list[dict] = []
    page = 1
    while True:
        data, errors, trace_id = client.query(QUERY_MATERIALS, {"page": page})
        if errors:
            print(f"  Error fetching materials (page {page}): {errors}")
            break
        if not data or "materials" not in data:
            break
        materials_data = data["materials"]
        for obj in materials_data.get("objects", []):
            feedstock = obj.get("feedstock", "")
            if feedstock != "FILAMENT":
                continue
            alt = obj.get("alternativeNames") or {}
            all_materials.append({
                "id": obj.get("id", ""),
                "name": obj.get("name", ""),
                "feedstock": feedstock,
                "bambustudio_name": alt.get("bambustudio", ""),
            })
        if not materials_data.get("pageInfo", {}).get("hasNextPage", False):
            break
        page += 1
    return all_materials


def get_print_priority_options(client: HelioClient, material_id: str) -> list[dict]:
    """Fetch print priority options for a given material.

    Returns:
        List of dicts with keys: ``value``, ``label``, ``isAvailable``, ``description``.
    """
    data, errors, trace_id = client.query(
        QUERY_PRINT_PRIORITY_OPTIONS, {"materialId": material_id}
    )
    if errors:
        print(f"  Error fetching print priority options: {errors}")
        return []
    if not data or "printPriorityOptions" not in data:
        return []
    options = []
    for opt in data["printPriorityOptions"]:
        options.append({
            "value": opt.get("value", ""),
            "label": opt.get("label", ""),
            "isAvailable": opt.get("isAvailable", True),
            "description": opt.get("description", ""),
        })
    return options


def check_user_quota(client: HelioClient) -> dict:
    """Check user's remaining optimizations and subscription info.

    Returns:
        Dict with quota/subscription fields, or ``{"error": [...]}`` on failure.
    """
    data, errors, trace_id = client.query(QUERY_USER_QUOTA)
    if errors:
        return {"error": errors}
    if not data or "user" not in data:
        return {"error": ["No user data in response"]}
    user = data["user"]
    sub = user.get("subscription") or {}
    return {
        "remaining_opts_this_month": user.get("remainingOptsThisMonth", 0),
        "add_on_optimizations": user.get("addOnOptimizations", 0),
        "subscription_name": sub.get("name", ""),
        "is_free_trial_active": user.get("isFreeTrialActive", False),
        "is_free_trial_claimed": user.get("isFreeTrialClaimed", False),
        "free_trial_eligible": data.get("freeTrialEligibility", False),
    }


def get_default_optimization_settings(client: HelioClient, gcode_id: str) -> dict | None:
    """Fetch server-recommended default optimization settings for a G-code.

    Returns:
        The defaultOptimizationSettings dict, or ``None`` on error.
    """
    data, errors, trace_id = client.query(
        QUERY_DEFAULT_OPT_SETTINGS, {"gcodeId": gcode_id}
    )
    if errors:
        print(f"  Error fetching defaults: {errors}")
        return None
    if not data or "defaultOptimizationSettings" not in data:
        return None
    return data["defaultOptimizationSettings"]


def get_recent_runs(client: HelioClient) -> tuple[list[dict], list[dict]]:
    """Fetch recent optimizations and simulations from user history.

    Returns:
        ``(optimizations, simulations)`` tuple of lists.
    """
    data, errors, trace_id = client.query(QUERY_RECENT_RUNS)
    if errors:
        raise RuntimeError(f"Recent runs error: {'; '.join(errors)} (trace: {trace_id})")
    if not data:
        return [], []
    opts = data.get("optimizations", {}).get("objects", [])
    sims = data.get("simulations", {}).get("objects", [])
    return opts, sims
