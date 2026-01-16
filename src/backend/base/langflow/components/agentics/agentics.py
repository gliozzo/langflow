from lfx.custom.custom_component.component import Component
from lfx.io import DataInput, MessageTextInput, Output, TableInput, IntInput
from agentics.core.utils import import_pydantic_from_code
from agentics.core.transducible_functions import make_transducible_function
from agentics.core.atype import get_pydantic_fields, pydantic_model_from_dict, create_pydantic_model
from agentics import AG
from agentics.core.transducible_functions import With
import pandas as pd
from lfx.schema.table import EditMode


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

class Agentics(Component):
    display_name = "AG"
    name = "AG"
    description = "The langflow component for the AG class"
    
    
    inputs = [
        DataInput(
            name="source",
            display_name="Source",
            info="Accepts JSON (list of dicts or {json:[...]}) or DataFrame.",
            required=True,
        ),
        
        MessageTextInput(
            name="atype_name",
            display_name="Atype Name",
            info="Provide a name for the type of the target states.",
            value=""
            # advanced=True,
        ),
        TableInput(
            name="schema",
            display_name="Schema",
            info="Define the structure and data types for the model's output.",
            required=True,
            # TODO: remove deault value
            table_schema=[
                {
                    "name": "name",
                    "display_name": "Name",
                    "type": "str",
                    "description": "Specify the name of the output field.",
                    "default": "field",
                    "edit_mode": EditMode.INLINE,
                },
                {
                    "name": "description",
                    "display_name": "Description",
                    "type": "str",
                    "description": "Describe the purpose of the output field.",
                    "default": "description of field",
                    "edit_mode": EditMode.POPOVER,
                },
                {
                    "name": "type",
                    "display_name": "Type",
                    "type": "str",
                    "edit_mode": EditMode.INLINE,
                    "description": ("Indicate the data type of the output field (e.g., str, int, float, bool, dict)."),
                    "options": ["str", "int", "float", "bool", "dict"],
                    "default": "str",
                },
                {
                    "name": "multiple",
                    "display_name": "As List",
                    "type": "boolean",
                    "description": "Set to True if this output field should be a list of the specified type.",
                    "default": "False",
                    "edit_mode": EditMode.INLINE,
                },
            ],
            value=[
                {
                    "name": "field",
                    "description": "description of field",
                    "type": "str",
                    "multiple": "False",
                }
            ],
        ),
        DropdownInput(
            name="transduction_type",
            display_name="transduction_type",
            options=["amap", "areduce"],
            value="amap"

        ),
        MessageTextInput(
            name="instructions",
            display_name="instructions",
            value="",
        ),
        IntInput(
            name="batch_size",
            display_name="Number of states that will be executed in parallel (optional)",
            value=10,
            required=True,
        ),
        MessageTextInput(
            name="atype",
            display_name="atype",
            value="",
        ),
    ]

    outputs = [
        Output(
            name="states",
            display_name="states",
            method="transduce",
            tool_mode=True
        ),
        Output(
            name="atypeout",
            display_name="atype",
            method="get_atype",
            tool_mode=True
        ),
    ]
    
    
    

    # --------------------------------------------------------

    async def get_atype(self) -> str:
        return self.atype
        
    
    async def transduce(self) -> Data:
        # 1. Normalize input → pandas
        df = ensure_dataframe(self.source)
        source = AG.from_dataframe(df)
        if self.atype_name != "":
            schema_fields = [(field["name"] , field["description"], field["type"], False) for field in self.schema]
            atype = create_pydantic_model(schema_fields, name=self.atype_name)
            self.atype= str(get_pydantic_fields(atype))
        elif self.atype:
            atype = import_pydantic_from_code(self.atype)
        else: return {"json": []}
        target = AG(atype=atype, 
                instructions=self.instructions, 
                transduction_type=self.transduction_type,
                amap_batch_size=self.batch_size)
        output=await (target << source)
        json_rows = [m.dict() for m in output.states]
        return {"json": json_rows}
        