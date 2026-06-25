# SPDX-License-Identifier: AGPL-3.0-or-later
"""Device-connection backends implementing ``core.connection.Connection``.

The medium varies by instrument class (DESIGN 5a): serial-over-USB (class 1),
USB bulk (class 2), TCP/Ethernet (class 3). Backends are imported lazily so a
station that never touches a given medium need not install its library.
"""
