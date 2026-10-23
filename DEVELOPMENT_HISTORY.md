# ARGUS-RECON Conversation History

This record captures decisions and reasoning from the available development conversation that would not be apparent from reading the source alone. The local session history contained no indexed ARGUS-recon sessions; the record below is based on the repository conversation available in this workspace.

## Bugs And Errors

### Initial watch cycle reported every device as new

- **Root cause:** The watch loop starts with an empty previous-scan dictionary. The generic diff logic therefore interpreted every device in the first scan as a newly discovered device.
- **Fix:** The first watch cycle was changed to establish the in-memory baseline and print the required timestamped no-change message, without emitting `[NEW]` records. Later cycles compare against that baseline.
- **Validation:** Editor diagnostics reported no errors in `main.py` after the fix.

No runtime bug, failed test, or external error was recorded in the available conversation. The only validation explicitly performed was a diagnostics check showing no errors.

## Design Decisions

### Keep watch mode separate from rescan mode

The existing `--rescan` path was deliberately left intact because its screen-clearing and full-table behavior must not change. Watch mode was added as a separate branch with its own loop and output behavior.

### Share scanning and database-upsert work

The existing scan/enrichment/probing/upsert sequence was extracted into a helper so both normal rescan output and watch diffing use the same scan result. This avoids duplicating the behavior while preserving the existing full-table path.

### Compare devices by MAC address

The requested diff identity is the MAC address, so each scan is stored in memory as a dictionary keyed by a lowercased MAC. Lowercasing makes matching stable if scan results vary in MAC letter casing.

### Store only the previous scan in memory

The watch feature intentionally compares the current cycle with the immediately preceding cycle. No historical snapshots or new persistence layer were introduced.

### Report only the requested change types

Watch output is limited to new devices, status changes, and disappeared devices. It does not reprint the full device table, clear the terminal, or report unrelated field changes such as hostname or IP changes when the MAC remains present.

### Use a baseline before reporting changes

The first scan is treated as the starting point rather than as a set of changes. This prevents a noisy initial output and makes subsequent output represent changes observed after watch mode began.

### Enforce mutually exclusive modes explicitly

`--watch` and `--rescan` are rejected together with the exact requested error message and exit status, instead of choosing one mode implicitly.

### Avoid new dependencies and files for the implementation

The feature was implemented with the existing standard-library and project imports, and all runtime changes were kept in `main.py` as requested.

## Conventions And Rules

- Existing `--rescan` behavior is a compatibility constraint: it clears the screen, prints the full table, and sleeps 60 seconds between cycles.
- Watch mode sleeps 60 seconds between scans, does not clear the screen, and does not print the full table.
- Each watch cycle begins with a short divider and a timestamp.
- The exact change prefixes and spacing are part of the output contract: `[NEW]`, `[CHANGED]`, and `[GONE]`.
- Status comparisons use `UNKNOWN` when a status value is empty.
- Changes are held in memory only; the database continues to receive the normal upserts, but it is not used as the previous-watch snapshot.
- The implementation follows the existing `main.py` error-handling style and exits with status 1 for invalid mode combinations.

## College Network Limitations

No limitations or observed behaviors from testing on the college network were recorded in the available conversation. There is no evidence here about campus VLAN visibility, ARP filtering, client isolation, ICMP blocking, randomized MAC churn, permissions, scan duration, or network-specific false positives.

## Considered And Rejected Features

No feature alternatives were explicitly considered and rejected in the available conversation. In particular, there is no recorded discussion of persistence across process restarts, configurable polling intervals, a full initial snapshot, hostname-change reporting, or additional watch filters. These should not be treated as intentionally rejected; they are simply undocumented in the available history.
