#!/usr/bin/env python3
"""
Build endpoint matrix script for BakeMate backend.
Parses OpenAPI spec to generate a CSV of all API endpoints.
"""

import json
import csv
import sys
import os


def parse_openapi_spec(openapi_file):
    """Parse OpenAPI spec file and extract endpoints."""
    with open(openapi_file, "r") as f:
        spec = json.load(f)

    endpoints = []

    # Extract paths and methods
    for path, path_item in spec.get("paths", {}).items():
        # Skip /docs and /redoc paths
        if path.startswith("/docs") or path.startswith("/redoc"):
            continue

        for method, operation in path_item.items():
            if method.lower() in ["get", "post", "put", "delete", "patch"]:
                # Determine if the endpoint requires a request body
                requires_body = False
                if "requestBody" in operation:
                    requires_body = True

                # Add to endpoints list
                endpoints.append(
                    {
                        "method": method.upper(),
                        "path": path,
                        "requires_body": requires_body,
                        "operation_id": operation.get("operationId", ""),
                        "summary": operation.get("summary", ""),
                    }
                )

    return endpoints


def write_csv(endpoints, output_file):
    """Write endpoints to CSV file."""
    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)
        # Write header
        writer.writerow(["method", "path", "requires_body", "operation_id", "summary"])

        # Write data
        for endpoint in endpoints:
            writer.writerow(
                [
                    endpoint["method"],
                    endpoint["path"],
                    "true" if endpoint["requires_body"] else "false",
                    endpoint["operation_id"],
                    endpoint["summary"],
                ]
            )


def main():
    """Main function to build endpoint matrix."""
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <openapi_json_file> <output_csv_file>")
        return 1

    openapi_file = sys.argv[1]
    output_file = sys.argv[2]

    if not os.path.exists(openapi_file):
        print(f"Error: OpenAPI file {openapi_file} not found")
        return 1

    try:
        endpoints = parse_openapi_spec(openapi_file)
        write_csv(endpoints, output_file)
        print(f"Successfully wrote {len(endpoints)} endpoints to {output_file}")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
