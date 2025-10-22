# Baseline Security MCP Server - EDUCATIONAL PURPOSES ONLY

⚠️ **WARNING**: This server has **INTENTIONAL SECURITY GAPS** designed for security research and education.

**NEVER deploy this server in production environments.**

---

## Purpose

This server represents a **realistic** MCP server implementation that:
- Follows MCP security best practices (June 2025)
- Implements common Docker security hardening
- Has basic input validation and sanitization
- Blocks obvious attack patterns

**BUT** still has exploitable vulnerabilities due to subtle implementation gaps.

**Goal**: Demonstrate that following "best practices" isn't enough - you need defense-in-depth and expert security review.

---

## Security Posture Summary

### What We DO Right (Following Standards)

✅ **MCP Best Practices**:
- Basic input validation (type checking, format validation)
- Block obvious dangerous patterns (rm -rf, /etc/shadow)
- Human-in-the-Loop logging (simulated)
- Secret management via environment variables
- Python import restrictions

✅ **Docker Security**:
- Non-root user (mcpuser, not root)
- Capability dropping (cap_drop: ALL)
- Resource limits (CPU, memory)
- no-new-privileges flag
- Health checks

### What We MISS (Exploitable Gaps)

❌ **Subtle Vulnerabilities**:
- Path traversal (../../../etc/passwd bypasses blocklist)
- SSRF to cloud metadata (169.254.169.254 not blocked)
- Command injection via encoding (base64 bypasses char filters)
- Python sandbox escape (__import__ not blocked)
- No real Human-in-the-Loop (just logging)
- GET-based exfiltration (data in URL parameters)

❌ **Advanced Docker Security**:
- No custom seccomp profile
- No AppArmor/SELinux profile
- No network egress filtering
- Default bridge network (full external access)
- Host directory mounts

---

## Port

**8002** - Runs alongside:
- Secure server (8001)
- Vulnerable server (8000)

---

## Key Vulnerabilities

### 1. Unrestricted File Access
- ✅ Can read /etc/passwd, /etc/shadow
- ✅ Can read SSH keys from /root/.ssh/
- ✅ Can read environment files (.env)

### 2. Shell Command Injection
- ✅ Uses `subprocess.run(shell=True)`
- ✅ No command validation
- ✅ No input sanitization

### 3. SSRF via HTTP Client
- ✅ Can access cloud metadata (169.254.169.254)
- ✅ Can access localhost services
- ✅ file:// protocol works
- ✅ No URL filtering

### 4. Unrestricted Python Execution
- ✅ Unrestricted `exec()`
- ✅ Can import os, subprocess, socket
- ✅ Full filesystem and network access

### 5. Data Exfiltration
- ✅ Full POST support
- ✅ No method restrictions
- ✅ No data filtering

---

## Critical Attack: Cloud Metadata Theft

**AWS Example**:
```
1. Access http://169.254.169.254/latest/meta-data/iam/security-credentials/
2. Get role name
3. Retrieve credentials
4. Exfiltrate via POST

Result: Full AWS access with instance IAM role
```

**GCP Example**:
```
1. Access http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token
2. Get service account token
3. Exfiltrate

Result: Full GCP access with service account permissions
```

---

## Expected Attack Success Rate

Based on testing plan: **~60-70% (6-7/10 attacks succeed)**

Why lower than vulnerable server?
- Basic validation blocks simple attacks
- Obvious patterns caught and rejected
- Docker non-root user limits some exploits

Why still high despite "best practices"?
- Sophisticated attacks bypass validation
- Encoding/obfuscation techniques work
- Cloud metadata SSRF still possible
- Path traversal via ../ works

Compare to:
- Secure server: 0% (0/54 attacks succeeded)
- **Baseline server: ~65% (subtle gaps exploitable)**
- Vulnerable server: ~80% (designed for research)

---

## Research Value

### Demonstrates

1. **Reality Check**: Most MCP servers won't be as locked down as our secure version
2. **Cloud Risk**: SSRF to cloud metadata is a critical vulnerability
3. **Defense Importance**: Shows impact of proper security controls
4. **Education**: Clear examples for developers

### Use Cases

- Security research
- LLM agent attack testing
- Educational demonstrations
- Security tool validation
- Conference presentations

---

## Files

```
mcp_server_naive/
├── README.md           # This file
├── PLANNING.md         # Detailed design and attack scenarios
├── server.py           # Main MCP server (TO BE IMPLEMENTED)
├── tools/
│   ├── files.py        # Unrestricted file operations
│   ├── shell.py        # Shell execution with shell=True
│   ├── http.py         # HTTP client with SSRF
│   └── python.py       # Unrestricted Python exec()
├── config/
│   └── tools.json      # Tool definitions
├── tests/
│   └── test_naive_exploits.py  # Attack test suite
├── Dockerfile          # Basic Docker (no hardening)
└── docker-compose.yml  # Minimal configuration
```

---

## Integration with Existing Agent

The same LangGraph agent can target this server:

```bash
# .env
TARGET_SERVER=naive

# Agent connects to http://localhost:8002
```

All 54 attack prompts from the attacker framework will be tested against this server.

---

## Comparison Table

| Security Control | Secure Server | Naive Server |
|------------------|---------------|--------------|
| **Path validation** | /app/data and /tmp only | ❌ None - full filesystem |
| **Command whitelist** | 5 commands | ❌ None - any command |
| **Shell injection protection** | Blocks ; \| & $ | ❌ None - shell=True |
| **HTTP POST** | Blocked | ✅ Full support |
| **SSRF protection** | file:// blocked | ❌ None - all protocols |
| **Cloud metadata** | Blocked | ❌ Accessible |
| **Python execution** | Disabled | ✅ Unrestricted exec() |
| **Docker security** | Non-root, read-only | ❌ Root, read-write |

---

## Ethical Use Only

✅ **Acceptable**:
- Security research in controlled environment
- Educational demonstrations
- Testing your own systems
- Security tool development

❌ **Not Acceptable**:
- Deploying in production
- Testing against systems you don't own
- Using for actual attacks
- Sharing without security warnings

---

## Next Steps

See `PLANNING.md` for:
- Detailed vulnerability analysis
- 10 attack test scenarios
- Cloud metadata theft procedures
- Implementation timeline
- Integration guide

---

## Status

📋 **PLANNING PHASE**

Coming soon:
- [ ] Core server implementation
- [ ] Dockerfile and docker-compose
- [ ] Tool implementations
- [ ] Cloud metadata SSRF tests
- [ ] Attack success comparison report

---

## Questions?

This is part of the LLM Sandbox Escape research project. See main README for:
- Overall project goals
- Secure server comparison
- Attack framework documentation
- Research findings
