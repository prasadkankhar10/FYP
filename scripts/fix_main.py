with open('backend/app/main.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('@app.get("/", tags=["Health"])', '@app.get("/api/status", tags=["Health"])')

with open('backend/app/main.py', 'w', encoding='utf-8') as f:
    f.write(text)

print('Updated main.py successfully!')
