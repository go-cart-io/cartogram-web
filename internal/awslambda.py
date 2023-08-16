import requests
import json

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

    r = requests.post(lambda_url, headers=headers, json=lambda_event)

    return r.json()