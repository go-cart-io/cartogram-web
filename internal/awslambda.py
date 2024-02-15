import requests
import json
from lambda_package import lambda_function
def generate_cartogram(area_data, gen_file, lambda_url, lambda_api_key, cartogram_key, flags=''):

    headers = {
        'x-api-key': lambda_api_key
    }

    with open(gen_file, 'r') as gen_fp:
        gen_file_contents = gen_fp.read()

    lambda_event = {
        'gen_file': gen_file_contents,
        'area_data': area_data,
        'key': cartogram_key,
        'flags': flags
    }

    if lambda_url is not None and lambda_url is not '':
        r = requests.post(lambda_url, headers=headers, json=lambda_event)
        return r.json()
    
    else:        
        r = lambda_function.lambda_handler({'body': json.dumps(lambda_event)}, {})
        return json.loads(r['body'])