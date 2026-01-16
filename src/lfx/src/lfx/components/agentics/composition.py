from lfx.custom.custom_component.component import Component
from lfx.io import DataInput, Output, DropdownInput
from agentics import AG
import pandas as pd
from lfx.schema.data import Data



# ============================================================
# Helper: normalize JSON / Data / DataFrame into pandas DataFrame
# ============================================================

def ensure_dataframe(obj):
    """Convert Langflow Data or raw JSON into a pandas DataFrame."""
    # Case 1 — Langflow Data wrapper
    if hasattr(obj, "data"):
        obj = obj.data

    # Case 2 — JSON reader: {"json": [...]}
    if isinstance(obj, dict) and "json" in obj:
        return pd.DataFrame(obj["json"])

    # Case 3 — {"states": [...]}
    if isinstance(obj, dict) and "states" in obj:
        return pd.DataFrame(obj["states"])

    # Case 4 — list of dicts
    if isinstance(obj, list) and all(isinstance(x, dict) for x in obj):
        return pd.DataFrame(obj)

    # Case 5 — already DF
    if isinstance(obj, pd.DataFrame):
        return obj

    raise ValueError(f"Cannot convert to DataFrame: {obj}")


# ============================================================
# TRANSDUCTION COMPONENT — RETURNS JSON
# ============================================================

class Composition(Component):
    display_name = "Composition"
    name = "composition"
    description = "Perform various operations to combine states in workflows"
    
    inputs = [
         DropdownInput(
            name="composition_type",
            display_name="Composition Type",
            options=["merge", "compose", "add"],
            value="merge",
            info="Select the an operation to combine input states.",
            real_time_refresh=True,
        ),
        
        DataInput(
            name="left_source",
            display_name="Left Source",
            info="Accepts JSON (list of dicts or {json:[...]}) or DataFrame.",
            required=True,
        ),
        DataInput(
            name="right_source",
            display_name="Right Source",
            info="Accepts JSON (list of dicts or {json:[...]}) or DataFrame.",
            required=True,
        ),
    ]

    outputs = [
        Output(
            name="merged_states",
            display_name="merged_states",
            method="merge_states",
            tool_mode=True
        ),
    ]
    

        
    
    async def merge_states(self) -> Data:
        # 1. Normalize input → pandas
        left_source= AG.from_dataframe(ensure_dataframe(self.left_source))
        right_source = AG.from_dataframe(ensure_dataframe(self.right_source))
        if self.composition_type == "merge":
            output_states = left_source.merge_states(right_source)
        elif self.composition_type == "compose":
            output_states = left_source.compose_states(right_source)
        elif self.composition_type == "add":
            output_states = AG()
            output_states.states = left_source.states + right_source.states 
            
        else: output_states = AG()
            
            
        json_rows = [m.model_dump() for m in output_states.states]
        return {"json": json_rows}
        