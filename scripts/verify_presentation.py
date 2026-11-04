import os
import re

with open('presentation/index.html', encoding='utf-8') as f:
    content = f.read()

imgs = re.findall(r'src=["\']([^"\']+)["\']', content)
print(f'Found {len(imgs)} image references:')
all_exist = True
for img in imgs:
    path = os.path.normpath(os.path.join('presentation', img))
    exists = os.path.exists(path)
    print(f'  {img} -> {path} : {"EXISTS" if exists else "MISSING"}')
    if not exists:
        all_exist = False

print('All images exist:', all_exist)
