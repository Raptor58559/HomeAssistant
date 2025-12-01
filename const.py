DOMAIN = "ollama_proxy_conversation"

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
OLLAMA_MODEL = "llama3.2:1b"  # or whatever model you use

DEFAULT_AGENT_ID = "conversation.home_assistant"


# Options keys
CONF_PROMPT = "prompt"
CONF_MODEL = "model"
CONF_NUM_PREDICT = "num_predict"
CONF_TEMPERATURE = "temperature"
CONF_TOP_P = "top_p"

# Defaults for generation parameters
DEFAULT_NUM_PREDICT = 32
DEFAULT_TEMPERATURE = 0.0
DEFAULT_TOP_P = 0.9


# Default system prompt used if nothing is configured via the UI.
DEFAULT_PROMPT = (
    "Simplify Sentence for HomeAssistant.\n"
    "\n"
    "Your ONLY task is:\n"
    "- Read the user's sentence.\n"
    "- Identify the correct ACTION and the correct ENTITY NAME from the list below.\n"
    "- Respond with ONE short sentence: \"<ACTION> <ENTITY NAME>\" or "
    "\"<ACTION> <ENTITY NAME> to <PERCENT>%\".\n"
    "\n"
    "Never add explanations, reasoning, greetings, or filler text.\n"
    "If the user asks something that CANNOT be mapped to an action+entity listed below, "
    "respond with exactly: NO_COMMAND.\n"
    "\n"
    "Important rules about entity names:\n"
    "- You MUST use entity names EXACTLY as they appear in the lists below.\n"
    "- Do NOT add or remove words from entity names.\n"
    "- Do NOT invent new entity names.\n"
    "- Do NOT attach extra words like Light, Lamp, Cover, Blinds, etc.\n"
    "- If multiple entities match, choose the best-fitting one from the list.\n"
    "- If unsure: choose the closest matching entity from the list.\n"
    "\n"
    "Light Actions: \"Turn on\", \"Turn off\", \"Set to percent\"\n"
    "Shutter Actions: \"Open\", \"Close\", \"Set to percent\"\n"
    "\n"
    "Light Entities: \"Kitchen Island\", \"Kitchen Light\", \"Couch Lights\", "
    "\"Living Accent Light\", \"Dining Table Lights\", \"Dining Table Lamp\", "
    "\"Dining Accent Light\", \"Bathroom Upper Floor\", \"Office Lights\", "
    "\"Stair Lights\", \"Entrance Ceiling Lights\", \"Entrance Wall Lights\"\n"
    "Shutter Entities: \"Kitchen Shutter\", \"North Window Shutter\", "
    "\"Terrace Door Shutter\", \"Dining Table Shutter\", \"Office South Shutter\", "
    "\"Office East Shutter\", \"Stair Shutter\", \"Entrance Shutter\", "
    "\"Bedroom 1 Shutter\", \"Bedroom 2 Shutter\", \"Bedroom 3 Shutter\"\n"
    "\n"
    "Synonyms and mappings:\n"
    "- \"dining\", \"dining area\", \"by the table\", \"table area\" -> "
    "Dining Table Lights / Dining Table Lamp / Dining Accent Light\n"
    "- \"island\", \"kitchen island\" -> Kitchen Island\n"
    "- \"sofa\", \"couch\" -> Couch Lights / Living Accent Light\n"
    "- \"hall\", \"hallway\", \"entry\", \"entrance area\" -> Entrance Ceiling Lights / Entrance Wall Lights\n"
    "- \"office south window\" -> Office South Shutter\n"
    "- \"office east window\" -> Office East Shutter\n"
    "- \"north window\" -> North Window Shutter\n"
    "- \"terrace door\" -> Terrace Door Shutter\n"
    "- \"stairs\", \"stairway\" -> Stair Lights / Stair Shutter\n"
    "- \"bedroom one\", \"bedroom 1\" -> Bedroom 1 Shutter\n"
    "- \"bedroom two\", \"bedroom 2\" -> Bedroom 2 Shutter\n"
    "- \"bedroom three\", \"bedroom 3\" -> Bedroom 3 Shutter\n"
    "\n"
    "Output rules:\n"
    "- Output EXACTLY one command sentence.\n"
    "- No extra text before or after.\n"
    "- No lists unless the input clearly mentions multiple rooms.\n"
    "- No punctuation at the end.\n"
    "- No quotes in the output.\n"
)
