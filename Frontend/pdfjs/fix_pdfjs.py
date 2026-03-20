import re
import sys

with open('web/viewer.mjs', 'r', encoding='utf-8') as f:
    text = f.read()

# Just replace the entire if block or the throw statement.
# Let's replace `const ex = new Error("file origin does not match viewer's");`
# with `const ex = null; // bypassed origin check`
# We can also just replace the throw or the Error creation.

new_text = text.replace('const ex = new Error("file origin does not match viewer\'s");\n    throw ex;', '/* bypassed origin check */')
if new_text == text:
    new_text = text.replace('const ex = new Error("file origin does not match viewer\'s");', '/* bypassed origin check */')

if new_text != text:
    with open('web/viewer.mjs', 'w', encoding='utf-8') as f2:
        f2.write(new_text)
    print("Replaced successfully!")
else:
    print("Still failed. Let's find exactly how it looks:")
    m = re.search(r'.{0,100}file origin does not match.{0,100}', text)
    if m: print(repr(m.group(0)))
