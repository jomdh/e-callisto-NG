"""Output writers -- one per output mode (legacy / standard / custom).

Each implements :class:`ecallisto_ng.core.OutputWriter`. Standard mode lands
first; legacy (byte-compatible) and custom (templated) follow behind the same
contract (DESIGN 6a).
"""
