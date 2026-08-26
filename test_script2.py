import re
import os
import glob

components_dir = "entelechy-control-plane/src/components"

files = glob.glob(f"{components_dir}/**/*.tsx", recursive=True)

missing_aria = 0
found_aria = 0

for path in files:
    with open(path, "r") as f:
        content = f.read()

        # We need to parse correctly to avoid false positives.
        # But a simple heuristic:
        # 1. find all `<Button ` or `<button ` opening tags
        # 2. check if they have text children vs only icon children

        button_starts = [m.start() for m in re.finditer(r'<(Button|button)\b', content)]

        for start in button_starts:
            # simple naive check
            end = content.find('>', start)
            if end == -1:
                continue
            button_tag = content[start:end+1]

            # Check if it has a closing tag to get the full element content
            close_tag_idx = content.find('</' + button_tag[1:7], end)
            if close_tag_idx != -1:
                full_button = content[start:close_tag_idx]

                # if the button contains only a lucide icon and no text
                # an icon is usually `<IconName ` or `<svg `
                if re.search(r'<[A-Z][A-Za-z]+.*?\/>', full_button) and not re.search(r'>\s*[A-Za-z0-9]+\s*<', full_button):
                    if "aria-label" not in button_tag and "title" not in button_tag:
                         missing_aria += 1
                         print(f"File: {path}")
                         # print(full_button)
                    else:
                         found_aria += 1

print(f"Missing aria-labels for icon buttons: {missing_aria}")
print(f"Found aria-labels for icon buttons: {found_aria}")
