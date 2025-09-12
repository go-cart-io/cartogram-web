import json

import redis
import settings


def setprogress(params):
    redis_conn = redis.Redis(
        host=settings.CARTOGRAM_REDIS_HOST, port=settings.CARTOGRAM_REDIS_PORT, db=0
    )
    current_progress = redis_conn.get("cartprogress-{}".format(params["key"]))

    if current_progress is None:
        current_progress = {
            "order": params["order"],
            "stderr": params["stderr"],
            "name": params["name"],
            "progress": params["progress"],
        }
    else:
        current_progress = json.loads(current_progress.decode())

        if current_progress["order"] < params["order"]:
            current_progress = {
                "order": params["order"],
                "stderr": params["stderr"],
                "name": params["name"],
                "progress": params["progress"],
            }

    redis_conn.set(
        "cartprogress-{}".format(params["key"]), json.dumps(current_progress)
    )
    redis_conn.expire("cartprogress-{}".format(params["key"]), 300)


def getprogress(key):
    redis_conn = redis.Redis(
        host=settings.CARTOGRAM_REDIS_HOST, port=settings.CARTOGRAM_REDIS_PORT, db=0
    )
    current_progress = redis_conn.get("cartprogress-{}".format(key))

    if current_progress is None:
        return {"progress": None, "stderr": ""}
    else:
        current_progress = json.loads(current_progress.decode())
        return {
            "name": current_progress["name"],
            "progress": current_progress["progress"],
            "stderr": current_progress["stderr"],
        }
