"""
Test the sandboxed Python executor directly.

This verifies the security controls work before testing with the agent.
"""

import sys
import os

# Add security module to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'mcp_server_secure'))
from security import get_executor


def test_sandbox():
    """Test various Python code samples against the sandbox."""
    executor = get_executor()

    test_cases = [
        # (code, should_succeed, description)

        # ============ SHOULD BE BLOCKED ============
        ("import os\nprint(os.listdir('/etc'))", False, "Direct os import"),
        ("import urllib.request", False, "urllib import"),
        ("import subprocess", False, "subprocess import"),
        ("__import__('os')", False, "__import__ builtin"),
        ("open('/etc/passwd').read()", False, "open() builtin"),
        ("exec('print(1)')", False, "exec() builtin"),
        ("eval('1+1')", False, "eval() builtin"),
        ("getattr(__builtins__, 'open')", False, "__builtins__ access"),
        ("().__class__.__base__.__subclasses__()", False, "class hierarchy traversal"),
        ("import importlib\nimportlib.import_module('os')", False, "importlib bypass"),

        # String obfuscation attempts
        ("module = 'o' + 's'\n__import__(module)", False, "obfuscated __import__"),
        ("''.join(['o','s'])", True, "string join (harmless)"),  # This is OK, just builds a string

        # Network attempts
        ("import socket", False, "socket import"),
        ("import requests", False, "requests import"),
        ("import httpx", False, "httpx import"),

        # ============ SHOULD BE ALLOWED ============
        ("print('Hello World')", True, "simple print"),
        ("sum([1, 2, 3, 4, 5])", True, "sum builtin"),
        ("math.sqrt(16)", True, "math module (pre-imported)"),
        ("json.dumps({'key': 'value'})", True, "json module (pre-imported)"),
        ("str(datetime.datetime.now())", True, "datetime module (pre-imported)"),
        ("re.findall(r'\\d+', 'abc123')", True, "re module (pre-imported)"),
        ("[x**2 for x in range(10)]", True, "list comprehension"),
        ("sum([x**2 for x in range(100)])", True, "computation"),

        # Legitimate data processing
        ("""
data = {'values': [1, 2, 3], 'sum': sum([1, 2, 3])}
print(json.dumps(data))
        """, True, "JSON data processing"),

        # Complex but safe computation
        ("""
result = sum([math.sqrt(x) for x in range(1, 101)])
print(f"Sum of square roots: {result:.2f}")
        """, True, "mathematical computation"),
    ]

    print("="*80)
    print("TESTING SANDBOXED PYTHON EXECUTOR")
    print("="*80)

    passed = 0
    failed = 0

    for code, should_succeed, description in test_cases:
        success, output = executor.execute(code)

        # Determine if test passed
        test_passed = (success == should_succeed)

        if test_passed:
            status = "✓ PASS"
            passed += 1
        else:
            status = "✗ FAIL"
            failed += 1

        print(f"\n{status} | {description}")
        print(f"  Code: {code[:50]}...")
        print(f"  Expected: {'SUCCESS' if should_succeed else 'BLOCKED'}")
        print(f"  Got: {'SUCCESS' if success else 'BLOCKED'}")
        if not success:
            print(f"  Error: {output[:100]}")
        else:
            print(f"  Output: {output[:100]}")

    print("\n" + "="*80)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(test_cases)} tests")
    print("="*80)

    if failed == 0:
        print("\n✅ All tests passed! Sandbox is working correctly.")
    else:
        print(f"\n⚠️  {failed} tests failed! Security controls may have issues.")

    return failed == 0


if __name__ == "__main__":
    success = test_sandbox()
    sys.exit(0 if success else 1)
