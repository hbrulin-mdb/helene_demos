
#!/usr/bin/env python3
"""
Load `document_jdb_events.json` 15,000,000 times into the `jdb` collection.

Usage example:
  python load_jdb_events.py --uri "<your Atlas URI>" --db your_db --file ./document_jdb_events.json
"""
import sys
from bulk_loader_common import main as _common_main  # type: ignore

if __name__ == "__main__":
    # Defaults for this script
    sys.argv += ["--collection", "jdb", "--count", "65000"]
    _common_main()
