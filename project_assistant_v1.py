# Import necessary libraries
import os # For file operations
import json # For JSON operations
import google.generativeai as genai # Import the Google Generative AI library
from dotenv import load_dotenv # For loading environment variables from .env file
from google.generativeai.types import HarmCategory, HarmBlockThreshold # For configuring the safety settings
from print_color import print

# Load the environment variables from the .env file
load_dotenv()

# Load the environment variables
API_KEY = os.getenv('API_KEY') # The API key
CONFIG = os.getenv('CONFIG') # The config file

# Gemini Safety Settings - for more info visit https://ai.google.dev/gemini-api/docs/safety-settings
#  No safety settings
NO_SAFETY = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE
}
# Low safety settings
LOW_SAFETY = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH
}
# Medium safety settings
MEDIUM_SAFETY = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE
}
# High safety settings
HIGH_SAFETY = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_LOW_AND_ABOVE
}

# Gemini Pricing per 1 million tokens (as of July 10, 2024)
PRICING_DATE = '2024-07-10'
PRICING_MODEL = 'gemini-1.5-pro-latest'
INPUT_PRICING = {
    "upto_128k": 3.50, # Price per million tokens for prompts up to 128,000 tokens
    "over_128k": 7.00 # Price per million tokens for prompts over 128,000 tokens
}
OUTPUT_PRICING = {
    "upto_128k": 10.50, # Price per million tokens for outputs up to 128,000 tokens
    "over_128k": 21.00 # Price per million tokens for outputs over 128,000 tokens
}

INSTRUCTIONS = '''
- Converse with the LLM model to get help with your project. Ex. 'Help me debug this script.', 'Complete the TODOs in this file.', 'What can I add to improve this project?', etc.
- Cost will be shown for each message and the total cost of the session will be displayed.
- You can provide context by selecting files from your project directory.
- You can delete messages to refine the chat history and save costs while maintaining the context you need.'''

WARNINGS = '''
- NEVER SHARE YOUR .ENV FILE OR API KEY.
- You may incur costs for using the Gemini API. Confirm pricing details on the Google Cloud Platform website.
- This program attempts to calculate costs based on token usage. Actual costs may vary.
- You should NOT share sensitive information or personal data. Do so at your own risk.
- Use of the Gemini API is subject to the Google Cloud Platform Terms of Service.
- The Gemini model may generate harmful or inappropriate content. Use safety settings to mitigate risks.
- The Gemini model may not always provide accurate or helpful responses. Use critical thinking. You will become a prompt engineer in no time.
- AI generated content should be reviewed and validated before use in production.
- AI generated code may contain bugs or security vulnerabilities. Review and test thoroughly.
- AI generated code may be harmful or malicious. Review and validate generated code carefully.
- The author of this script is not responsible for any consequences of using this application.'''

HELP_MSG = '''
'exit' - Exit the chat session and give the option to save chat history.
'delete' - Delete messages from chat history.
'files' - Add files to context from project directory.
'history' - Display concise chat history.
'view' - View a full message's content.
'help' - Display special commands and instructions.'''

HELP_WARNING = 'If you enter a command wrong, it will be sent as a message to the API, incurring costs.'

# Initialize global lists to store message information
_all_messages = []
_messages = []

def display_help():
    """Display help message."""
    print(HELP_MSG, tag='Help', tag_color='cyan')
    print(HELP_WARNING, tag='Warning', tag_color='yellow')

def load_config():
    """Load system instructions from the config file. If not found, use the default system instructions."""
    model = 'gemini-1.5-pro-latest'
    system_instructions = "You are an expert developer. Assist the user with their needs. Ask questions to clarify the user's requirements. Provide detailed and helpful responses." # default
    safety = 'medium' # default
    timeout = 60 # default
    project_dir = None # default
    # Load configuration from file
    try:
        with open(CONFIG, 'r') as f:
            config = json.load(f)
            # Load model
            try:
                model = config['model']
            except:
                print(f"Error loading model from config file. Using {model}", tag='Warning', tag_color='yellow')
            # Load system instructions
            try:
                system_instructions = config['system_instructions']
            except:
                print(f"Error loading system instructions from config file. Using default value.", tag='Warning', tag_color='yellow')
            # Load safety setting
            try:
                safety = config['safety']
            except:
                print(f"Error loading safety setting from config file. Using default {safety} safety settings.", tag='Warning', tag_color='yellow')
            # Load timeout
            try:
                timeout = config['timeout']
            except: 
                print(f"Error loading timeout from config file. Using default {timeout} seconds.", tag='Warning', tag_color='yellow')
            # Load project directory
            try:
                project_dir = config['project_dir']
            except:
                print(f"Error loading project directory from config file, this will severely limit usefullness of this application.", tag='Critical', tag_color='red')
    except:
        print(f"Error loading config file ({CONFIG}). Make sure it's set in the .env file. Using default values.", tag='Warning', tag_color='yellow')
    return model, system_instructions, safety, timeout, project_dir

def get_context_token_count():
    """Get the total number of tokens in the context."""
    tokens = 0 # Initialize token count
    for m in _messages:
        tokens += m['tokens']
    return tokens

def calculate_cost(tokens, pricing, history=False):
    """Calculates the cost based on token usage.

    Args:
        tokens (int): The number of tokens used.
        pricing (dict): A dictionary containing the pricing tiers for input or output tokens.

    Returns:
        float: The calculated cost.
    """
    million_tokens = tokens / 1_000_000 # Convert tokens to millions of tokens
    if history and get_context_token_count() > 128_000: # Check if we are calculating history, as pricing to keep messages may be more expensive if we exceed 128k tokens
        return million_tokens * pricing['over_128k']
    elif tokens <= 128_000: # Check if token usage falls within the lower pricing tier
        return million_tokens * pricing['upto_128k'] # Calculate cost using the lower tier pricing
    else: 
        return million_tokens * pricing['over_128k'] # Calculate cost using the higher tier pricing

def initialize_chat(model_name, instructions, safety = MEDIUM_SAFETY,):
    """Initialize the chat session with the Gemini model.

    Args:
        model_name (str): The name of the model to use.
        instructions (str): The system instructions to provide to the model.
        safety (dict): The safety settings to use.
    
    Returns:
        genai.ChatSession: The chat session object.
        int: The number of tokens used in the system instructions.
    """
    
    genai.configure(api_key=API_KEY) # Configure the API key
    model = genai.GenerativeModel(model_name = model_name, safety_settings=safety, system_instruction=instructions) # Initialize the GenerativeModel

    # Return the chat session and the number of tokens used in the system instructions
    return model.start_chat(), model.count_tokens(" ").total_tokens

def add_message(role, content, tokens):
    """Add a message to the lists."""
    cost = calculate_cost(tokens, INPUT_PRICING)
    _all_messages.append({'role': role, 'content': content, 'tokens': tokens, 'cost': cost})
    _messages.append({'role': role, 'content': content, 'tokens': tokens, 'cost': cost})

def main():
    """Main function."""
    # API Key warning
    print('Make sure to add the .env file to your .gitignore to keep your API key secure.', tag='CRITICAL', tag_color='red')

    # Print instructions
    print(INSTRUCTIONS, tag='Welcome to Gemini Project Assistant v1!', tag_color='cyan')

    # Print warnings
    print(WARNINGS, tag='Warnings', tag_color='yellow')

    # Print pricing
    print(f"\nInput: {INPUT_PRICING['upto_128k']} (up to 128k tokens), {INPUT_PRICING['over_128k']} (over 128k tokens)\nOutput: {OUTPUT_PRICING['upto_128k']} (up to 128k tokens), {OUTPUT_PRICING['over_128k']} (over 128k tokens)", tag=f'PRICING for {PRICING_MODEL} ($ per 1 million tokens) as of {PRICING_DATE}', tag_color='magenta')

    # User agreement
    print('By continuing, you take full responsibility for your use of this application.', tag='User Agreement', tag_color='red')
    accept = input('Do you accept the terms and conditions? (y/N): ')
    if (accept.lower() != 'y'): # Exit if user does not accept
        print('Exiting...', tag_color='red')
        quit()

    # Verify environment variables are set
    if (not API_KEY or  not CONFIG):
        # Exit if not set
        print("Set your .env as specified in the .env-template", tag='Error', tag_color='red')
        quit()

    # Load the config file
    model, system_instructions, safety, timeout, project_dir = load_config()
    print(system_instructions, tag='System Instructions', tag_color='magenta', color='white')


    # Load the safety settings
    match safety:
        case "none":
            safety = NO_SAFETY
            print('No Safety', tag='Safety Settings', tag_color='magenta', color='white')
        case "low":
            safety = LOW_SAFETY
            print('Low Safety', tag='Safety Settings', tag_color='magenta', color='white')
        case "medium":
            safety = MEDIUM_SAFETY
            print('Medium Safety', tag='Safety Settings', tag_color='magenta', color='white')
        case "high":
            safety = HIGH_SAFETY
            print('High Safety', tag='Safety Settings', tag_color='magenta', color='white')
        case _: # Default
            safety = MEDIUM_SAFETY
            print('Medium Safety', tag='Safety Settings', tag_color='magenta', color='white')


    # Initialize the Gemini chat session and get the number of tokens used in the system instructions
    chat, si_tokens = initialize_chat(model, system_instructions, safety)

    # Add the system instructions to the chat history
    _all_messages.append({'role': 'system','content': system_instructions, 'tokens': si_tokens})

    # Display help message
    display_help()

    # Main loop
    


if __name__ == '__main__':
    main()