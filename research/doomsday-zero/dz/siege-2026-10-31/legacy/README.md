# Superseded audit reports

These reports were generated during development by the first auditor, which
checked completed escape/recover/return cycles but could omit a fatal withdrawal
with no Return event. Their passed fields are NOT acceptance of general withdrawal
safety. Older bot traces also lack an explicit Done marker, so later normal-farming
deaths cannot always be separated. The current auditor rejects those trace versions.

Use ../STRICT_FIXTURE_AUDIT.json with the corrected auditor and frozen run
dz-siege-access-fixtures-09. Raw run capsules remain unchanged.
