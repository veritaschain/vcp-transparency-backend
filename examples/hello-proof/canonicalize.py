#!/usr/bin/env python3
"""
Legacy local example serializer (not fully RFC 8785 conformant).

Changed 2026-11-01: reject non-finite numbers and non-string object keys.
Existing finite-number formatting and key ordering are preserved.

Usage:
    python3 canonicalize.py sample_event.json > canonical.json
    python3 canonicalize.py sample_event.json --bytes > canonical.bin
"""

import json
import math
import sys
from typing import Any

def canonicalize(obj: Any) -> str:
    """
    Serialize with this example's existing byte format.

    This differs from JCS for some numbers and supplementary Unicode keys.
    Do not use it as a general RFC 8785 implementation.
    """
    if obj is None:
        return "null"
    elif isinstance(obj, bool):
        return "true" if obj else "false"
    elif isinstance(obj, int):
        return str(obj)
    elif isinstance(obj, float):
        if not math.isfinite(obj):
            raise ValueError("Non-finite numbers cannot be serialized")
        # Handle special cases per RFC 8785
        if obj == 0:
            return "0"
        # Use repr to get shortest form, then clean up
        s = repr(obj)
        # Remove trailing .0 for whole numbers represented as float
        if '.' in s and s.endswith('0') and 'e' not in s.lower():
            s = s.rstrip('0').rstrip('.')
        return s
    elif isinstance(obj, str):
        # Escape only required characters
        result = '"'
        for char in obj:
            code = ord(char)
            if char == '"':
                result += '\\"'
            elif char == '\\':
                result += '\\\\'
            elif code < 0x20:
                # Control characters
                if char == '\b':
                    result += '\\b'
                elif char == '\f':
                    result += '\\f'
                elif char == '\n':
                    result += '\\n'
                elif char == '\r':
                    result += '\\r'
                elif char == '\t':
                    result += '\\t'
                else:
                    result += f'\\u{code:04x}'
            else:
                result += char
        result += '"'
        return result
    elif isinstance(obj, list):
        elements = [canonicalize(item) for item in obj]
        return "[" + ",".join(elements) + "]"
    elif isinstance(obj, dict):
        if not all(isinstance(key, str) for key in obj):
            raise TypeError("JSON object keys must be strings")
        # Sort keys by UTF-16 code units (Python's default sort works for BMP)
        sorted_keys = sorted(obj.keys(), key=lambda k: [ord(c) for c in k])
        pairs = [f'{canonicalize(k)}:{canonicalize(obj[k])}' for k in sorted_keys]
        return "{" + ",".join(pairs) + "}"
    else:
        raise TypeError(f"Cannot canonicalize type: {type(obj)}")


def main():
    if len(sys.argv) < 2:
        print("Usage: canonicalize.py <input.json> [--bytes]", file=sys.stderr)
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_bytes = "--bytes" in sys.argv
    
    with open(input_file, 'r', encoding='utf-8') as f:
        obj = json.load(f)
    
    canonical = canonicalize(obj)
    
    if output_bytes:
        sys.stdout.buffer.write(canonical.encode('utf-8'))
    else:
        print(canonical)


if __name__ == "__main__":
    main()
