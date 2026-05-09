# mph API Pitfalls (COMSOL 6.4)

## Study Creation
### Problem
```python
(model/'studies').create('std1')
# TypeError: StudyListClient.create(String, String) — no matching overload
```
mph's `Node.create()` forwards the argument as a *type* string, calling `container.create(tag, type_string)`. `StudyListClient.create()` only accepts one string (the tag).

### Fix
```python
std = model.java.study().create("std1")
std.run()
```

## Client-Side Physics Object Limitations
In client-server mode (and possibly stand-alone), the physics client proxy object may not expose all server-side methods.

### Problem
```python
model.java.component("comp1").physics("es").intTotalEnergy()
# AttributeError: 'PhysicsClient' object has no attribute 'intTotalEnergy'
```

### Workaround
Use mph's `model.evaluate()` or global evaluation nodes:
```python
# Global evaluation
eval_node = (model/'evaluations').create('EvalGlobal')
eval_node.set('expr', 'es.intWe')
value = model.evaluate('es.intWe', 'J')
```

Or use mph's high-level evaluate:
```python
value = model.evaluate('es.intWe')
```

## Stand-Alone vs Client-Server Mode
- **Windows**: mph defaults to stand-alone mode (faster, no server process)
- **Linux/macOS**: mph uses client-server mode (requires server process)
- In client-server mode, some API methods may be thin proxies to the server

## mph Discovery on Non-Standard Paths
mph discovers COMSOL via:
1. Windows Registry (Windows)
2. `/usr/local/` and `~/.local/` (Linux/macOS)
3. `which comsol` / `where comsol`

On WSL, none of these find the Windows installation. Symlinks don't help because the architecture detection returns `glnxa64` but COMSOL has `win64` binaries.
