import re
import os
import glob

components_dir = "entelechy-control-plane/src/components"

files = glob.glob(f"{components_dir}/**/*.tsx", recursive=True)

for path in files:
    with open(path, "r") as f:
        content = f.read()

        button_starts = [m.start() for m in re.finditer(r'<(Button|button)\b', content)]

        for start in button_starts:
            end = content.find('>', start)
            if end == -1:
                continue
            button_tag = content[start:end+1]

            # Check if it has a closing tag to get the full element content
            close_tag_idx = content.find('</' + button_tag[1:7], end)
            if close_tag_idx != -1:
                full_button = content[start:close_tag_idx]

                # Check for "ChevronLeft" or "ChevronRight" or "ChevronsLeft" or "ChevronsRight"
                if re.search(r'<(Chevrons?Left|Chevrons?Right)', full_button):
                    if "aria-label" not in button_tag and "title" not in button_tag:
                         print(f"File: {path}")
                         print(full_button)
                         print("-" * 40)
