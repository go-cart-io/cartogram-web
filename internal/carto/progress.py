import json

import redis
import settings


class CartoProgress:
    def __init__(self, key: str):
        self.redis_conn = redis.Redis(
            host=settings.CARTOGRAM_REDIS_HOST, port=settings.CARTOGRAM_REDIS_PORT, db=0
        )
        self.key = key
        self.setData([])

    def setData(self, data_cols: list[str]) -> None:
        self.data_cols = data_cols
        self.data_len = len(data_cols)
        self.data_number = 0

    def start(self, name: str = ""):
        self.data_number = self.data_number + 1
        self.set(0, "", name, progress=0)

    def set(self, order: int, stderr: str, name: str, progress: float) -> None:
        # Calculate overall progress across multiple datasets
        if progress == 1 and self.data_number >= self.data_len:
            # Handle edge case: ensure final progress reaches exactly 1.0
            overall_progress = 1
        else:
            overall_progress = (progress - 1 + self.data_number) / float(self.data_len)

        progress_db = self.redis_conn.get("cartprogress-{}".format(self.key))

        if progress_db is None:
            progress_db = {
                "order": order,
                "stderr": stderr,
                "name": name,
                "progress": overall_progress,
            }
        else:
            progress_db = json.loads(progress_db.decode())

            if progress_db["order"] < order:
                progress_db = {
                    "order": order,
                    "stderr": stderr,
                    "name": name,
                    "progress": overall_progress,
                }

        self.redis_conn.set("cartprogress-{}".format(self.key), json.dumps(progress_db))
        self.redis_conn.expire("cartprogress-{}".format(self.key), 300)

        if self.key == "batch":
            print(name)
            print(stderr)
            print("-" * 30)

    def get(self) -> dict:
        current_progress = self.redis_conn.get("cartprogress-{}".format(self.key))

        if current_progress is None:
            return {"progress": None, "stderr": ""}
        else:
            current_progress = json.loads(current_progress.decode())
            return {
                "name": current_progress["name"],
                "progress": current_progress["progress"],
                "stderr": current_progress["stderr"],
            }
