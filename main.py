"""MatEIS - Materials Engineering Interactive Suite (NiceGUI entry point)."""
import os

from nicegui import app, ui

import config
from ui.pages import corrosion, data, guide, history, home, phase, selection  # noqa: F401  (importing registers the pages)

app.add_static_files("/static", str(config.ROOT / "ui" / "static"))

if __name__ in {"__main__", "__mp_main__"}:
    ui.run(title="MatEIS - Materials Engineering Interactive Suite", favicon="⚙️", host="0.0.0.0",
           port=int(os.environ.get("PORT", 8080)), storage_secret=config.STORAGE_SECRET, reload=False, show=False)
