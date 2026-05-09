# COMSOL Authentication on WSL

## Problem
mph client-server mode fails when the client runs on WSL/Linux but COMSOL runs on Windows:
```
com.comsol.util.exceptions.FlException: No user name and password could be obtained
```

## Root Cause
`ModelUtil.connect(host, port)` requires OS-level authentication (NTLM/Kerberos on Windows). When the JVM runs on Linux (WSL), it cannot obtain Windows credentials, even though the machine is physically the same.

## Failed Approaches
1. **Starting server with `-login auto`**: Server allows auto-login, but the *client* still needs credentials to send. The client-side `ModelUtil.connect()` always requires them.
2. **Starting server with `-login never`**: Same issue — client-side auth is mandatory.
3. **Symlinking COMSOL into `~/.local/`**: mph discovery works, but the JVM starts on Linux and can't use Windows JVM DLL or Windows auth.
4. **Using `mph.start()` from WSL**: Calls `mph.Server` (starts Windows exe, works) then `mph.Client` (starts Linux JVM, auth fails).

## Working Solution
Run the **entire mph script via Windows Python**:
```bash
/mnt/c/Users/Admin/PyCharmMiscProject/.venv/Scripts/python.exe script.py
```
This ensures:
- The JVM starts as a Windows process
- Windows authentication works natively
- mph uses stand-alone mode by default (fast, no server needed)
- All COMSOL API features available

## Alternative (untested): use mph.start() with explicit credentials
If `ModelUtil.connect(host, port, user, password)` is available, could patch mph's Client.connect(). But the Windows Python approach is simpler and officially supported.
