from handler_metadata import cartogram_handlers


def has_handler(handler):
    return handler in cartogram_handlers


def get_sorted_handler_names():
    sub_cartogram_handlers = {}
    for key, value in cartogram_handlers.items():
        if "hidden" in value:
            continue

        sub_cartogram_handlers[key] = {
            "name": value["name"],
        }

    sorted_data = [
        {
            "key": key,
            "name": value["name"],
        }
        for key, value in sorted(
            sub_cartogram_handlers.items(), key=lambda item: item[1]["name"]
        )
    ]

    return sorted_data


def get_handler(handler):
    return cartogram_handlers[handler]


def get_name(handler):
    return cartogram_handlers[handler]["name"]


def get_gen_file(handler, string_key=""):
    if handler == "custom":
        return f"./static/userdata/{string_key}/Input.json"
    else:
        return f"./static/cartdata/{handler}/Input.json"
