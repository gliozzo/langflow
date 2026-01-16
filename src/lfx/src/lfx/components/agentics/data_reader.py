from lfx.custom.custom_component.component import Component
from lfx.io import FileInput, DataInput, Output, IntInput
from lfx.schema.data import Data
from lfx.schema.dataframe import DataFrame
import json
import pandas as pd


class DataReader(Component):
    display_name = "Data Reader"
    name = "DataReader"
    description = (
        "Reads JSONL, JSON, CSV files, or DataFrame input and outputs unified JSON "
        "(list of objects)."
    )

    inputs = [
        FileInput(
            name="file",
            display_name="JSON / JSONL / CSV File",
            file_types=["jsonl", "json", "csv"],
            required=False,
            tool_mode=True,
        ),
        DataInput(
            name="dataframe",
            display_name="DataFrame or JSON Input (optional)",
            info="If provided, this input overrides file loading.",
            required=False,
        ),
        IntInput(
            name="max_number_of_rows",
            display_name="Max Number of rows to be imported (optional)",
            value=None,
            required=False,
        ),
    ]

    outputs = [
        Output(
            name="states",
            display_name="states",
            method="read_any",
        )
    ]

    # ---------------------------------------------------------
    # Main loader
    # ---------------------------------------------------------
    def read_any(self) -> Data:
        """Normalize file input OR DataFrame/JSON input into a list[dict]."""

        # ======================================================
        # 1. If DataFrame input exists → convert it
        # ======================================================
        if self.dataframe is not None:
            df = self._convert_dataframe_like(self.dataframe)
            if self.max_number_of_rows:
                df = df.head(max_number_of_rows)
            rows = df.to_dict(orient="records")
            result = Data(data={"states": rows})
            self.status = result
            return result

        # ======================================================
        # 2. Otherwise, load from file
        # ======================================================
        file_info = self.file
        if not file_info:
            raise ValueError("No file or DataFrame/JSON input provided.")

        # Normalize Langflow file input
        if isinstance(file_info, dict) and "file_path" in file_info:
            path = file_info["file_path"]
        elif isinstance(file_info, str):
            path = file_info
        else:
            raise ValueError(f"Cannot interpret file input: {file_info}")

        # -------------------------
        # JSONL 
        # -------------------------
        if path.endswith(".jsonl"):
            rows = []
            with open(path, "r", encoding="utf-8") as f:

                for line in f:

                    line = line.strip()
                    if line:
                        rows.append(json.loads(line))
                    
                            

        # -------------------------
        # JSON
        # -------------------------
        elif path.endswith(".json"):
            with open(path, "r", encoding="utf-8") as f:
                loaded = json.load(f)

            if isinstance(loaded, list):
                rows = loaded
            elif isinstance(loaded, dict):
                rows = [loaded]
            else:
                raise ValueError("JSON must contain an object or a list of objects.")

        # -------------------------
        # CSV
        # -------------------------
        elif path.endswith(".csv"):
            df = pd.read_csv(path)
            rows = df.to_dict(orient="records")

        else:
            raise ValueError("Unsupported file extension.")

        # ======================================================
        # 3. Return normalized JSON
        # ======================================================
        result = Data(data={"states": rows[:self.max_number_of_rows]})
        self.status = result
        return result

    # ---------------------------------------------------------
    # Helper: turn Data / DataFrame / dict into pandas DF
    # ---------------------------------------------------------
    def _convert_dataframe_like(self, obj):
        """Normalize DataframeInput OR JSON DataInput into pandas DataFrame."""
        # Langflow DataFrame (wrapper)
        if isinstance(obj, DataFrame):
            return obj.to_pandas()

        # Langflow Data wrapper: {"json": [...]}
        if hasattr(obj, "data"):
            data = obj.data

            if isinstance(data, dict) and "json" in data:
                return pd.DataFrame(data["json"])

            if isinstance(data, list):
                return pd.DataFrame(data)

        # Already a pandas DataFrame
        if isinstance(obj, pd.DataFrame):
            return obj

        raise ValueError(f"Cannot convert to dataframe: {obj}")