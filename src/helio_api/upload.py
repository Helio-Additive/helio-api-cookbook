"""
G-code upload and registration functions for the Helio Additive API.

Handles the three-step upload workflow:
  1. Get a presigned S3 upload URL
  2. Upload the file via HTTP PUT
  3. Register the G-code and poll until READY
"""

from __future__ import annotations

import time

import requests

from helio_api.client import (
    GCODE_POLL_INTERVAL_S,
    GCODE_POLL_MAX,
    HelioClient,
    print_progress_bar,
)
from helio_api.queries import MUTATION_CREATE_GCODE, QUERY_POLL_GCODE, QUERY_PRESIGNED_URL


def get_presigned_url(client: HelioClient) -> tuple[str, str]:
    """Get a presigned S3 upload URL.

    Always uses ``fileName="test.gcode"`` (matching BambuStudio behavior).

    Returns:
        ``(key, upload_url)`` tuple.

    Raises:
        RuntimeError: On API error.
    """
    data, errors, trace_id = client.query(
        QUERY_PRESIGNED_URL, {"fileName": "test.gcode"}
    )
    if errors:
        raise RuntimeError(f"Presigned URL error: {'; '.join(errors)} (trace: {trace_id})")
    result = data["getPresignedUrl"]
    return result["key"], result["url"]


def upload_file(file_path: str, presigned_url: str) -> None:
    """Upload a file to the presigned S3 URL via HTTP PUT.

    Args:
        file_path: Local path to the G-code file.
        presigned_url: The presigned S3 URL to upload to.

    Raises:
        RuntimeError: If the upload returns a non-200 status.
    """
    with open(file_path, "rb") as f:
        file_data = f.read()

    resp = requests.put(
        presigned_url,
        data=file_data,
        headers={"Content-Type": "application/octet-stream"},
        timeout=300,
    )
    if resp.status_code != 200:
        raise RuntimeError(f"Upload failed: HTTP {resp.status_code} - {resp.text[:300]}")


def register_gcode(
    client: HelioClient, gcode_key: str, printer_id: str, material_id: str
) -> str:
    """Register uploaded G-code via createGcodeV2 mutation, then poll until READY.

    Args:
        client: Helio API client.
        gcode_key: The S3 key returned by ``get_presigned_url()``.
        printer_id: Printer ID to associate with the G-code.
        material_id: Material ID to associate with the G-code.

    Returns:
        The gcode ID.

    Raises:
        RuntimeError: On API error, processing error, or timeout.
    """
    gcode_name = gcode_key.split("/")[-1] if "/" in gcode_key else gcode_key

    variables = {
        "input": {
            "name": gcode_name,
            "printerId": printer_id,
            "materialId": material_id,
            "gcodeKey": gcode_key,
            "isSingleShell": True,
        }
    }

    data, errors, trace_id = client.query(MUTATION_CREATE_GCODE, variables)
    if errors:
        raise RuntimeError(f"CreateGcode error: {'; '.join(errors)} (trace: {trace_id})")

    gcode = data["createGcodeV2"]
    if gcode is None:
        raise RuntimeError("CreateGcode returned null.")

    gcode_id = gcode["id"]
    status_str = gcode.get("status", "")

    # Poll until READY
    poll_count = 0
    while status_str not in ("READY", "ERROR", "RESTRICTED") and poll_count < GCODE_POLL_MAX:
        time.sleep(GCODE_POLL_INTERVAL_S)
        poll_count += 1

        poll_data, poll_errors, poll_trace = client.query(QUERY_POLL_GCODE, {"id": gcode_id})
        if poll_errors:
            print(f"  Poll warning: {poll_errors}")
            continue

        gv2 = poll_data.get("gcodeV2")
        if gv2 is None:
            continue

        status_str = gv2.get("status", "")
        progress = gv2.get("progress", 0)
        print_progress_bar(progress)

        # Check for processing errors
        gcode_errors = gv2.get("errors") or []
        errors_v2 = gv2.get("errorsV2") or []
        all_errors: list[str] = []
        if isinstance(gcode_errors, list):
            all_errors.extend(gcode_errors)
        for ev2 in errors_v2:
            detail = ev2.get("type", "")
            line = ev2.get("line")
            if line is not None:
                detail += f" (line {line})"
            if detail:
                all_errors.append(detail)
        if all_errors:
            print()
            raise RuntimeError(f"GCode processing errors: {'; '.join(all_errors)}")

    print()  # newline after progress bar

    if status_str in ("ERROR", "RESTRICTED"):
        raise RuntimeError(f"GCode creation failed with status: {status_str}")

    if status_str != "READY":
        raise RuntimeError(f"GCode polling timed out. Last status: {status_str}")

    print(f"  GCode registered: id={gcode_id}, status={status_str}")
    return gcode_id


def upload_and_register_gcode(
    client: HelioClient, file_path: str, printer_id: str, material_id: str
) -> str:
    """Full upload workflow: presigned URL -> upload -> register -> poll until READY.

    Args:
        client: Helio API client.
        file_path: Local path to the G-code file.
        printer_id: Printer ID.
        material_id: Material ID.

    Returns:
        The registered gcode ID.
    """
    print("  Step 1/3: Getting presigned URL...")
    key, url = get_presigned_url(client)
    print(f"  Got key: {key}")

    print("  Step 2/3: Uploading file...")
    upload_file(file_path, url)
    print("  Upload complete.")

    print("  Step 3/3: Registering G-code and waiting for processing...")
    gcode_id = register_gcode(client, key, printer_id, material_id)
    return gcode_id
