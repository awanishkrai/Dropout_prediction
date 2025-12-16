
pkgs = ['streamlit','pymongo','pandas','numpy','scikit-learn','joblib','bcrypt','opencv-python','Pillow','plotly','pytest']
try:
    with open('current_versions.txt', 'r', encoding='utf-16') as f:
        lines = f.readlines()
except:
    # Fallback if encoding is different
    with open('current_versions.txt', 'r', encoding='utf-8') as f:
        lines = f.readlines()

found = []
for l in lines:
    l = l.strip()
    for p in pkgs:
        if l.lower().startswith(p.lower() + '=='):
            found.append(l)
            break

with open('pinned_reqs.txt', 'w') as f:
    f.write('\n'.join(sorted(found)))
