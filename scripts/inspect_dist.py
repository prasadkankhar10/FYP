import re

with open('frontend/dist/assets/index-2cmq4gn9.js', 'r', encoding='utf-8') as f:
    text = f.read()

matches = set(re.findall(r'https?://[a-zA-Z0-9\.\-_]+', text))
print('Found domains in frontend bundle:')
for m in matches:
    print(' ', m)
