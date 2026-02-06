
#!/usr/bin/env python3
"""
Load `document_history.json` 30,000,000 times into the `history` collection.

Usage example:
  python load_history.py --uri "<your Atlas URI>" --db your_db --file ./document_history.json
"""
import sys
from bulk_loader_common import main as _common_main  # type: ignore

if __name__ == "__main__":
    # Defaults for this script
    sys.argv += ["--collection", "history", "--count", "400000"]
    _common_main()
