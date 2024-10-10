import re

def sanitize_filename(filename):    
    invalid_chars = r'[\\/:*?"<>|]'
    sanitized_filename = re.sub(invalid_chars, '_', filename)
    return sanitized_filename

def get_csv(data):
    fields = data['values']['fields']
    items = data['values']['items']
    
    header = ','.join([field['label'] for field in fields])

    rows = []
    for key, item in items.items():
        row = ','.join(str(value) for value in item)
        rows.append(row)

    return f'{header}\n' + '\n'.join(rows)
