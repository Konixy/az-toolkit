# Security

Do not open an issue containing an encryption key, firmware image, dump,
credential, or personal data. Treat an exposed key as compromised; deleting it
from a commit does not remove it from Git history.

The 1.30 runtime refuses a non-RAM root, a separate `/root/pdj` mount, a
64-bit player binary when only an ARM32 table exists, and any unlisted `rbp`
hash before a guarded write. The default image registers no hashes and no
words. Changes to these checks require validation against the exact target
binary and hardware.

Do not flash a `.UPD`. AZ updates are LUKS; this repository will not decrypt
them.

## Reporting

Report a vulnerability through GitHub's private security advisory form on this
repository, under Security, Report a vulnerability. Do not open a public issue.

No response or disclosure timeline is committed to yet.
