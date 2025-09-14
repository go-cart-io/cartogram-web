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
        self.num_done = 0

    def done(self):
        self.num_done = self.num_done + 1

    def set(self, order: int, stderr: str, name: str, progress: float) -> None:
        # Calculate overall progress across multiple datasets
        if progress == 1 and self.num_done == self.data_len:
            # Handle edge case: ensure final progress reaches exactly 1.0
            overall_progress = 1
        else:
            # Formula: (individual_progress / total_datasets) + (completed_datasets / total_datasets)
            overall_progress = (progress / self.data_len) + (
                self.num_done / self.data_len
            )

        current_progress = self.redis_conn.get("cartprogress-{}".format(self.key))

        if current_progress is None:
            current_progress = {
                "order": order,
                "stderr": stderr,
                "name": name,
                "progress": overall_progress,
            }
        else:
            current_progress = json.loads(current_progress.decode())

            if current_progress["order"] < order:
                current_progress = {
                    "order": order,
                    "stderr": stderr,
                    "name": name,
                    "progress": overall_progress,
                }

        self.redis_conn.set(
            "cartprogress-{}".format(self.key), json.dumps(current_progress)
        )
        self.redis_conn.expire("cartprogress-{}".format(self.key), 300)

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
