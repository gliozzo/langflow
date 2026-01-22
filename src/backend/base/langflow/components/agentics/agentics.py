from lfx.custom.custom_component.component import Component
from lfx.io import  MessageTextInput, Output, TableInput, IntInput, DataFrameInput
from agentics.core.atype import create_pydantic_model
from agentics import AG
from agentics.core.transducible_functions import generate_prototypical_instances


from lfx.schema.table import EditMode

from crewai import LLM


from lfx.base.models.anthropic_constants import ANTHROPIC_MODELS
from lfx.base.models.google_generative_ai_constants import GOOGLE_GENERATIVE_AI_MODELS
from lfx.base.models.openai_constants import OPENAI_CHAT_MODEL_NAMES, OPENAI_REASONING_MODEL_NAMES
from lfx.inputs.inputs import BoolInput, MessageTextInput, StrInput
from lfx.io import DropdownInput, SecretStrInput
from lfx.schema.dataframe import DataFrame



# IBM watsonx.ai constants
IBM_WATSONX_DEFAULT_MODELS = ["meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8", "openai/gpt-oss-120b"]
IBM_WATSONX_URLS = [
    "https://us-south.ml.cloud.ibm.com",
    "https://eu-de.ml.cloud.ibm.com",
    "https://eu-gb.ml.cloud.ibm.com",
    "https://au-syd.ml.cloud.ibm.com",
    "https://jp-tok.ml.cloud.ibm.com",
    "https://ca-tor.ml.cloud.ibm.com",
]

# Ollama API constants
HTTP_STATUS_OK = 200
JSON_MODELS_KEY = "models"
JSON_NAME_KEY = "name"
JSON_CAPABILITIES_KEY = "capabilities"
DESIRED_CAPABILITY = "completion"
#DEFAULT_OLLAMA_URL = "http://localhost:11434"

class Agentics(Component):
    display_name = "Agentics"
    name = "agentics"
    description = "Enables Map Reduce Style Agentic data transformations amongs dataframes"
    icon= "Agentics"
    
    
    inputs = [
         DataFrameInput(
            name="source",
            display_name="Source DataFrame",
            info="Accepts JSON (list of dicts) or DataFrame.",
        ),
        
        DropdownInput(
            name="transduction_type",
            display_name="transduction_type",
            options=["amap", "areduce", "generate"],
            value="amap",
            required=True,

        ),
         
        MessageTextInput(
            name="atype_name",
            display_name="Generated Type",
            info="Provide a name for the generated target type",
            value="",
            required=True,
            # advanced=True,
        ),
        TableInput(
            name="schema",
            display_name="Generated Fields",
            info="Define the structure and data types for the model's output.",
            required=True,
            # TODO: remove deault value
            table_schema=[
                {
                    "name": "name",
                    "display_name": "Name",
                    "type": "str",
                    "description": "Specify the name of the output field.",
                    "default": "text",
                    "edit_mode": EditMode.INLINE,
                },
                {
                    "name": "description",
                    "display_name": "Description",
                    "type": "str",
                    "description": "Describe the purpose of the output field.",
                    "default": "",
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
                    "default": False,
                    "edit_mode": EditMode.INLINE,
                },
            ],
            value=[
                {
                    "name": "text",
                    "description": "",
                    "type": "str",
                    "multiple": False,
                }
            ],
        ),
        MessageTextInput(
            name="instructions",
            display_name="instructions",
            value="",
        ),
        BoolInput(
            name="merge_source",
            display_name="merge_source_states",
            value=True,
            advanced=True
        ),
        IntInput(
            name="batch_size",
            display_name="Batch Size",
            value=10,
            advanced=True
        ),
       
        
        
        DropdownInput(
            name="provider",
            display_name="Model Provider",
            #options=["OpenAI", "Anthropic", "Google", "IBM watsonx.ai", "Ollama"],
            options=["IBM watsonx.ai"],
            #value="IBM watsonx.ai"",
            info="Select the model provider",
            real_time_refresh=True,
            options_metadata=[
                # {"icon": "OpenAI"},
                # {"icon": "Anthropic"},
                # {"icon": "GoogleGenerativeAI"},
                {"icon": "WatsonxAI"}
                # {"icon": "Ollama"},
            ],
            required = True,
        ),
        DropdownInput(
            name="model_name",
            display_name="Model Name",
            #options=OPENAI_CHAT_MODEL_NAMES + OPENAI_REASONING_MODEL_NAMES + GOOGLE_GENERATIVE_AI_MODELS + 
            options= IBM_WATSONX_DEFAULT_MODELS,
            value=IBM_WATSONX_DEFAULT_MODELS[0],
            info="Select the model to use",
            advanced=True,
            real_time_refresh=True,
            refresh_button=True,
        ),
        SecretStrInput(
            name="api_key",
            display_name="OpenAI API Key",
            info="Model Provider API key",
            required=False,
            show=True,
            real_time_refresh=True,
            advanced=True
        ),
        SecretStrInput(
            name="project_id",
            display_name="watsonx Project ID (Leave blank not use of other providers)",
            info="The project ID associated with the foundation model (IBM watsonx.ai only)",
            show=True,
            required=False,
            advanced=True
        ),
       
    ]

    outputs = [
        Output(
            name="states",
            display_name="Target DataFrame",
            method="transduce",
            tool_mode=True
        ),
    ]
    
    
    

    # --------------------------------------------------------


    
    async def transduce(self) ->  DataFrame:
        llm=None
        if self.provider == "IBM watsonx.ai":
            llm = LLM(
                    model="watsonx/" + self.model_name,
                    base_url="https://us-south.ml.cloud.ibm.com",
                    project_id=self.project_id,
                    api_key=self.api_key,
                    temperature=0,
                    max_tokens=4000,
                    max_input_tokens=100000)
                    
        else: return "Please fix model paramters"
        
        # print("AAAAAA" , type(self.source))
        
        # if isinstance(self.source, list):
            
        source = AG.from_dataframe(DataFrame(self.source))
        schema_fields = [(field["name"] , field["description"], field["type"] if field["multiple"] == False else f'list[{field["type"]}]' , False) for field in self.schema]
        atype = create_pydantic_model(schema_fields, name=self.atype_name)
        if self.transduction_type == "generate":
            output_states = await generate_prototypical_instances(atype,n_instances=self.batch_size)
            output = AG(states=output_states)
        else:
        
            target = AG(atype=atype, 
                    instructions=self.instructions, 
                    transduction_type=self.transduction_type,
                    amap_batch_size=self.batch_size,
                    llm=llm)
            output=await (target << source)
            if self.merge_source and self.transduction_type == "amap":
                output = source.merge_states(output)
        
        
        df = output.to_dataframe()
        return df.to_dict(orient="records")
