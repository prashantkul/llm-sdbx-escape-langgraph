"""
Quick test of baseline MCP server on port 8002
"""

import requests
import json

BASE_URL = "http://localhost:8002"

def test_health():
    """Test health endpoint"""
    print("\n" + "="*80)
    print("TEST 1: Health Check")
    print("="*80)
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    assert response.status_code == 200
    print("✅ PASS")

def test_read_etc_passwd():
    """Test reading /etc/passwd (should work - exploitable gap!)"""
    print("\n" + "="*80)
    print("TEST 2: Read /etc/passwd (Baseline Gap)")
    print("="*80)
    print("This should work because /etc/passwd is not in the blocklist")
    print("(Unlike secure server which blocks ALL /etc access)")

    # Note: Would need proper MCP client to test
    # For now just demonstrate the concept
    print("✅ Server is ready for MCP client testing")

def test_path_traversal():
    """Test path traversal vulnerability"""
    print("\n" + "="*80)
    print("TEST 3: Path Traversal (Baseline Gap)")
    print("="*80)
    print("Path traversal with ../ should work (no validation)")
    print("✅ Server is ready for MCP client testing")

def test_command_injection():
    """Test command injection with encoding"""
    print("\n" + "="*80)
    print("TEST 4: Command Injection via Encoding (Baseline Gap)")
    print("="*80)
    print("Base64 encoded commands should bypass basic filters")
    print("✅ Server is ready for MCP client testing")

def test_ssrf():
    """Test SSRF to cloud metadata"""
    print("\n" + "="*80)
    print("TEST 5: SSRF to Cloud Metadata (Baseline Gap)")
    print("="*80)
    print("Access to 169.254.169.254 should work (no IP filtering)")
    print("✅ Server is ready for MCP client testing")

if __name__ == "__main__":
    print("\n" + "="*80)
    print("BASELINE MCP SERVER TEST SUITE")
    print("Port: 8002")
    print("="*80)

    test_health()
    test_read_etc_passwd()
    test_path_traversal()
    test_command_injection()
    test_ssrf()

    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print("✅ Server is running on port 8002")
    print("✅ Health check passed")
    print("✅ Ready for agent testing")
    print("")
    print("To test with agent:")
    print("  1. Update .env: TARGET_SERVER=baseline")
    print("  2. Run: python llm_attacker_framework/run_attack.py")
    print("="*80)
