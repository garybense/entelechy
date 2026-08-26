import re
import os

components_dir = "entelechy-control-plane/src/components"

files = [
    "entities-view.tsx",
    "documents-view.tsx",
    "data-view.tsx",
    "mental-model-detail-modal.tsx",
    "mental-models-view.tsx",
    "observation-history-view.tsx",
    "bank-profile-view.tsx"
]

missing_aria = 0

for file in files:
    path = os.path.join(components_dir, file)
    if not os.path.exists(path):
        continue
    with open(path, "r") as f:
        content = f.read()
        # Find buttons with class "h-7 w-7 p-0" (icon buttons)
        pattern = r'<Button[^>]*className="[^"]*h-7 w-7 p-0[^"]*"[^>]*>(.*?)</Button>'
        matches = re.finditer(pattern, content, re.DOTALL)
        for match in matches:
            button_html = match.group(0)
            if "aria-label" not in button_html and "title" not in button_html:
                print(f"Missing aria-label in {file}:")
                # print(button_html)
                missing_aria += 1

print(f"Total missing aria-labels: {missing_aria}")
