"""Upload transports -- ship finished files to a destination.

Each implements :class:`ecallisto_ng.core.UploadTransport`. ``local`` (copy to
a directory/mount) lands first and is fully testable; ``ftp`` (stdlib) follows.
SFTP and others are added behind the same contract.
"""
