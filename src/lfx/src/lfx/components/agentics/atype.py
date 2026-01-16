from lfx.custom.custom_component.component import Component
from lfx.io import DropdownInput, CodeInput, Output
from lfx.schema.message import Message
import os

DIR = "/Users/gliozzo/Code/langflow/basic_types"

class AType(Component):
    display_name = "AType"
    description = "Choose or write a Pydantic Type."
    icon = "Code"
    name = "AType"

    # Preload models from files
    PREDEFINED_TYPES = {
        name: open(os.path.join(DIR, name)).read()
        for name in os.listdir(DIR)
    }

    inputs = [
        DropdownInput(
            name="template_choice",
            display_name="Choose from Library",
            options=list(PREDEFINED_TYPES.keys()) + ["Custom"],
            value="Custom",
            real_time_refresh=True,
        ),
        CodeInput(
            name="custom_code",
            display_name="Define New Type",
            value="""from pydantic import BaseModel

class GenericInput(BaseModel):
    value: str | None = None
""",
            required=False,
        ),
    ]

    outputs = [
        Output(
            display_name="Pydantic Code",
            name="type_code",
            method="build_output"
        ),
    ]

    def build_output(self) -> Message:
        """Return selected or custom Pydantic code as a message-compatible output."""
        if self.template_choice != "Custom":
            code = self.PREDEFINED_TYPES[self.template_choice]
        else:
            code = self.custom_code

        # Show result in component status UI
        self.status = code

        # The message-compatible output
        return Message(text=code)