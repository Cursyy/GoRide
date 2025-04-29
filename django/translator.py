import polib
from googletrans import Translator
import time

translator = Translator()

po_file = polib.pofile('locale/uk/LC_MESSAGES/djangojs.po')

for entry in po_file:
    if entry.msgid and not entry.msgstr and not entry.obsolete:
        try:
            translated = translator.translate(entry.msgid, src='en', dest='uk').text
            entry.msgstr = translated
            print(f"Перекладено: {entry.msgid} -> {entry.msgstr}")
            time.sleep(0.5)
        except Exception as e:
            print(f"Помилка перекладу для {entry.msgid}: {e}")
            entry.msgstr = entry.msgid  
            if 'fuzzy' not in entry.flags:
                entry.flags.append('fuzzy') 

po_file.save()