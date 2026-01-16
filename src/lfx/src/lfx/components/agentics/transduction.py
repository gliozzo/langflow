from lfx.custom.custom_component.component import Component
from lfx.io import DataInput, MessageTextInput, Output
from agentics.core.utils import import_pydantic_from_code
from agentics.core.transducible_functions import make_transducible_function
from agentics import AG
from agentics.core.transducible_functions import With
import pandas as pd


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

class Transduction(Component):
    display_name = "Transduction"
    name = "Transduction"
    description = "Transduces JSON or DataFrame rows into new typed states using Agentics."

    inputs = [
        DropdownInput(
            name="transduction_type",
            display_name="transduction_type",
            options=["MAP", "REDUCE"],

        ),
        DataInput(
            name="source_states",
            display_name="source_states",
            info="Accepts JSON (list of dicts or {json:[...]}) or DataFrame.",
            required=True,
        ),
        
        MessageTextInput(
            name="source_type",
            display_name="source_type",
            value="""from pydantic import BaseModel
class Source(BaseModel):
    value: str | None = None
""",
        ),
        MessageTextInput(
            name="target_type",
            display_name="target_type",
            value="""from pydantic import BaseModel
class Target(BaseModel):
    result: str | None = None
""",
        ),
        MessageTextInput(
            name="instructions",
            display_name="instructions",
            value="Summarize the input.",
        ),
    ]

    outputs = [
        Output(
            name="output_states",
            display_name="output_states",
            method="transduce",
            tool_mode=True
        ),
    ]

    # --------------------------------------------------------
    async def transduce(self) -> Data:
        # 1. Normalize input → pandas
        df = ensure_dataframe(self.source_states)

        # 2. Dynamic Pydantic types
        Source = import_pydantic_from_code(self.source_type)
        Target = import_pydantic_from_code(self.target_type)

        # 3. Convert to AG typed container
        ag = AG.from_dataframe(df, atype=Source)
        
        if self.transduction_type=="MAP":
        # 4. Build transduction function
            fn = make_transducible_function(
                InputModel=Source,
                OutputModel=Target,
                instructions=self.instructions,
            )
    
            # 5. Apply fn
            results = await fn(ag.states)
    
            # 6. Convert to JSON serializable output
            json_rows = [m.dict() for m in results]
    
            # 7. Return JSON (NOT DataFrame)
            return {"json": json_rows}
            
        elif self.transduction_type=="REDUCE":
            fn = Target << With(Source, 
            areduce=True,
            instructions=self.instructions)
            
            result = await fn(ag.states)
            return result.model_dump()
            
            