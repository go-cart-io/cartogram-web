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

def get_data_string(data):    
    datasets = []
    is_area_as_base = False

    # Find the position of spacial fields
    col_region = 0
    col_color = 2
    col_area = 3

    for index, header in enumerate(data['values']['fields']):
        if header['label'] == 'Region':
            col_region = index
        elif header['label'] == 'Color':
            col_color = index
        elif header['label'].startswith('Land Area'):
            col_area = index
            is_area_as_base = True
        elif header['label'] != 'Abbreviation':
            m = re.match(r'(.+)\s?\((.+)\)$', header['label'])
            if m:
                name = m.group(1).strip()      
            else:
                name = header['label'].strip()
            
            datasets.append({'label': sanitize_filename(name), 'index': index, 'datastring': 'name,Data,Color\n'})

    for rowId, row in data['values']['items'].items():
        for col in datasets:
            # Validate values
            if row[col['index']] is not None:
                float(row[col['index']])
            else:
                row[col['index']] = 'NA',
            
            if row[col_color] != '' and not re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', row[col_color]):
                raise ValueError('The color data was invaild.')
                    
            col['datastring'] = col['datastring'] + '{0},{1},{2}\n'.format(row[col_region], row[col['index']], row[col_color])   

    return datasets, is_area_as_base