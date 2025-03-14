import re
import sys
from pathlib import Path

def wrap_text_in_trans_tags(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = r">(?!\s*{%\s*trans\s*%})([^<>{}%]+?)<"

    new_content = re.sub(pattern, r">{% trans '\1' %}<", content)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)

def main():
    for file in sys.argv[1:]:
        wrap_text_in_trans_tags(file)

if __name__ == "__main__":
    main()
