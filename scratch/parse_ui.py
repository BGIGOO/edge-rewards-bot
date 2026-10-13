# -*- coding: utf-8 -*-
import sys
import xml.etree.ElementTree as ET

try:
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

tree = ET.parse("scratch/ui.xml")
for node in tree.iter():
    text = node.attrib.get("text", "")
    desc = node.attrib.get("content-desc", "")
    res_id = node.attrib.get("resource-id", "")
    bounds = node.attrib.get("bounds", "")
    clickable = node.attrib.get("clickable", "")
    if text or desc:
        print(f"[{bounds}] clickable={clickable} | id={res_id} | text='{text}' | desc='{desc}'")
