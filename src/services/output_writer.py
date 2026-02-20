from __future__ import annotations
from dataclasses import dataclass
import json, os
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from ..common.io import atomic_write

@dataclass
class OutputPaths:
    json_path: str
    parquet_path: str

class FileOutputWriter:
    def __init__(self, root: str = "outputs"):
        self.root = root

    def write(self, document_id: str, payload: dict) -> dict:
        json_path = os.path.join(self.root, "json", f"{document_id}.json")
        parquet_path = os.path.join(self.root, "parquet", f"{document_id}.parquet")

        atomic_write(json_path, json.dumps(payload, default=str, indent=2).encode("utf-8"))

        flat = dict(payload)
        for k, v in list(flat.items()):
            if isinstance(v, (dict, list)):
                flat[k] = json.dumps(v, default=str)
        table = pa.Table.from_pandas(pd.DataFrame([flat]))
        os.makedirs(os.path.dirname(parquet_path), exist_ok=True)
        tmp = f"{parquet_path}.tmp"
        pq.write_table(table, tmp)
        os.replace(tmp, parquet_path)

        return {"json_path": json_path, "parquet_path": parquet_path}
