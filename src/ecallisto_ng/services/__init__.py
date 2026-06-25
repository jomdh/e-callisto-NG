# SPDX-License-Identifier: AGPL-3.0-or-later
"""Services -- acquisition, scheduler, uploader, jobs.

Orchestration that drives drivers, writers and transports. Services depend on
``core`` contracts and on concrete drivers/writers only at their edges.
"""
