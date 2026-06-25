"""Vulture whitelist -- intentional 'unused' names, not dead code.

Run vulture as: ``vulture src/ vulture_whitelist.py``.

Parameters of ``Protocol`` methods in ``core/contracts.py`` have no body
(they are interface declarations), so vulture reports them as unused. They
are part of the public contract and must keep their names. Listing them here
marks them as used.
"""

# OutputWriter.write parameters
unit
out_dir
# UploadTransport.put / verify parameters
local
remote
# Connection.read parameter (kept for interface conformance; some backends,
# like the simulator, do not need it)
timeout
protocol.FORMAT_MV  # C2: bench output-format select (hardware wire path)
protocol.FORMAT_MHZ_MV
