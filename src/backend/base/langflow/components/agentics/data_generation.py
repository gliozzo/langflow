from lfx.custom.custom_component.component import Component
from lfx.io import DataInput, MessageTextInput, Output, IntInput
from agentics.core.utils import import_pydantic_from_code
from agentics.core.transducible_functions import make_transducible_function
from agentics import AG
import pandas as pd
from agentics.core.transducible_functions import generate_prototypical_instances

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

class DataGeneration(Component):
    display_name = "Data Generation"
    name = "generation"
    description = "Generate a random sample of entifies for the given type"

    inputs = [
        MessageTextInput(
            name="type",
            display_name="type",
            value="""from pydantic import BaseModel
class Person(BaseModel):
    name: str | None = None
    age: int | None = None
""",
        ),
        IntInput(
        name="number_of_states",
        display_name="number of states",
        info="The number of states that will be generated for the given type",
        value=10,
        required=False,
        ),
    ]

    outputs = [
        Output(
            name="output_states",
            display_name="output_states",
            method="generate_samples",
            tool_mode=True
        ),
    ]

    # --------------------------------------------------------
    async def generate_samples(self) -> Data:
        # 1. Normalize input → pandas
        # df = ensure_dataframe(self.source_states)

        # 2. Dynamic Pydantic types
        SelectedType = import_pydantic_from_code(self.type)
        #Target = import_pydantic_from_code(self.target_type)

        # 3. Convert to AG typed container
        results = await generate_prototypical_instances(SelectedType,n_instances=self.number_of_states)
        
        json_rows = [m.dict() for m in results]

        # 7. Return JSON (NOT DataFrame)
        return {"json": json_rows}