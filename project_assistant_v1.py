# Import necessary libraries
import os # For file operations
import json # For JSON operations
import google.generativeai as genai # Import the Google Generative AI library
from dotenv import load_dotenv # For loading environment variables from .env file
from google.generativeai.types import HarmCategory, HarmBlockThreshold # For configuring the safety settings
from google.api_core.exceptions import DeadlineExceeded # For handling deadline exceeded errors
from print_color import print

DEBUG = False

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
PRICING_DATE = '2024-07-13'
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
'save' - Save the chat history to a file.
'delete' - Delete messages from chat history.
'files' - Add files and their paths to context from project directory.
'history' - Display concise chat history.
'view' - View a full message's content.
'exit' - Exit the chat session and give the option to save chat history.
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
    """Load system instructions from the config file. If not found, use the default system instructions.
    
    Args:
        None
    
    Returns:
        str: The model name to use.
        str: The system instructions to provide to the model.
        str: The safety settings to use.
        int: The timeout setting to use.
        str: The project directory to use.
        list: A list of file extensions to ignore in the project directory.
        float: The temperature setting to use.
        int: The maxOutputTokens setting to use.
        list: A list of stop sequences to use.
    """
    model = 'gemini-1.5-pro-latest'
    system_instructions = "You are an expert developer. Assist the user with their needs. Ask questions to clarify the user's requirements. Provide detailed and helpful responses. Refrain from using emojis." # default
    safety = 'medium' # default
    timeout = 60 # default
    project_dir = None # default
    ignored_extensions = [] # default
    temperature = 1.0 # default
    max_output_tokens = 8192 # default
    stop_sequences = [] # default

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
                project_dir = config['project_directory']
            except:
                print(f"Error loading project directory from config file, this will severely limit usefullness of this application.", tag='Critical', tag_color='red')
            # Load ignored extensions
            try:
                ignored_extensions = config['ignored_extensions']
            except:
                print(f"Error loading ignored extensions from config file. Using default ignored extensions. ({ignored_extensions})", tag='Warning', tag_color='yellow')
            # Load temperature
            try:
                temperature = config['temperature']
            except:
                print(f"Error loading temperature from config file. Using default value. ({temperature})", tag='Warning', tag_color='yellow')
            # Load maxOutputTokens
            try:
                max_output_tokens = config['max_output_tokens']
            except:
                print(f"Error loading max_output_tokens from config file. Using default value. ({max_output_tokens})", tag='Warning', tag_color='yellow')
            # Load stopSequences
            try:
                stop_sequences = config['stop_sequences']
            except:
                print(f"Error loading stop_sequences from config file. Using default value. ({stop_sequences})", tag='Warning', tag_color='yellow')
    except:
        print(f"Error loading config file ({CONFIG}). Make sure it's set in the .env file. Using default values.", tag='Warning', tag_color='yellow')
    return model, system_instructions, safety, timeout, project_dir, ignored_extensions, temperature, max_output_tokens, stop_sequences

def get_context_token_count():
    """Get the total number of tokens in the context.
    
    Args:
        None
    
    Returns:
        int: The total number of tokens in the context."""
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

def initialize_chat(model_name, instructions, safety, temperature, max_output_tokens, stop_sequences):
    """Initialize the chat session with the Gemini model.

    Args:
        model_name (str): The name of the model to use.
        instructions (str): The system instructions to provide to the model.
        safety (dict): The safety settings to use.
    
    Returns:
        genai.ChatSession: The chat session object.
        int: The number of tokens used in the system instructions.
        model: The GenerativeModel object.
    """
    
    genai.configure(api_key=API_KEY) # Configure the API key
    config = {
        "temperature": temperature,
        "max_output_tokens": max_output_tokens,
        "stop_sequences": stop_sequences
    }

    model = genai.GenerativeModel(model_name = model_name, generation_config=config, safety_settings=safety, system_instruction=instructions) # Initialize the GenerativeModel

    # Return the chat session and the number of tokens used in the system instructions
    return model.start_chat(), model.count_tokens(" ").total_tokens, model

def add_message(role, content, tokens):
    """Add a message to the history lists.
    
    Args:
        role (str): The role of the message sender.
        content (str): The content of the message.
        tokens (int): The number of tokens used in the message.
    
    Returns:
        None
    """
    cost = calculate_cost(tokens, INPUT_PRICING)
    _all_messages.append({'role': role, 'content': content, 'tokens': tokens, 'cost': cost})
    _messages.append({'role': role, 'content': content, 'tokens': tokens, 'cost': cost})

def delete_messages(chat, msg_indices):
    """Delete messages from the chat history.

    Args:
        chat (genai.ChatSession): The chat session object.
        msg_indicies (list): A list of message indicies to delete.

    Returns:
        None
    """

    for i in sorted(msg_indices, reverse=True):
        if msg_indices == []:
            print('No message indicies provided.', tag='Error', tag_color='red')
            return
        try:
            if i == 0:  # Protect system instructions at index 0
                print("Cannot delete system instructions.", tag='Error', tag_color='red')
                continue
            del _messages[i]  # Index 0 is the system instructions
            del chat.history[i-1]  # index 0 is the first message stored in the chat history, system instructions are not stored in the chat history
            print(f"Deleted message at index {i}.", tag='Delete', tag_color='magenta', color='white')
        except IndexError:
            print(f"Invalid message index. Message index out of range. Enter between 0 and {len(_messages) - 1}.", tag='Error', tag_color='red')
        except ValueError:
            print('Invalid message index. Enter a valid integer.', tag='Error', tag_color='red')

def save(session_cost):
    full = input('Do you want to save the full chat history, or exclude the messages you deleted? (f/E): ').lower() # Ask user if they want to save the full chat history
    if full == 'e' or full == 'exclude': # Save chat history excluding deleted messages
        print('Saving chat history excluding deleted messages...', color='magenta')
        save_chat_history(_messages, session_cost)
    else: # Save full chat history
        print('Saving full chat history...', color='magenta')
        save_chat_history(_all_messages, session_cost)

def save_chat_history(history, session_cost):
    """Save the chat history to a file, with total cost of session at the start of the file.

    Args:
        history (list): The chat history to save.

    Returns:
        None
    """
    
    while True:
        filetype = input('Enter the format you wish to save the chat history in (text, markdown, json, or csv): ').lower() # Get the file format from the user
        if filetype not in ['json', 'text', 'markdown', 'csv']: # Check if the file format is valid
            print('Invalid file format. Enter "text", "markdown", "json", or "csv".', tag='Error', tag_color='red')
            continue
        filename = input('Enter the filename (no extension) to save the chat history to (This will save in your current directory): ') # Get the filename from the user
        match filetype:
            case 'json': # Save chat history as JSON
                with open(filename + '.json', 'w') as f:
                    modified_history = [{'role': m['role'], 'content': m['content'], 'tokens': m['tokens']} for m in history]
                    json.dump({"total_session_cost": session_cost, "chat_history": modified_history}, f, indent=4) # Write the chat history to the file
                print(f'Chat history saved to {filename}.json', tag='Success', tag_color='green') # Print success message
                break
            case 'text': # Save chat history as text, formatted for easy reading
                with open(filename + '.txt', 'w') as f:
                    f.write(f'Total session cost: ${session_cost:.5f}\n') # Write the total cost of the session to the file
                    for i, m in enumerate(history): # Write the chat history to the file
                        f.write(f'{i}. {m["role"]}, {m["tokens"]} tokens - {m["content"]}\n') 
                print(f'Chat history saved to {filename}.txt', tag='Success', tag_color='green') # Print success message
                break
            case 'markdown': # Save chat history as markdown
                with open(filename + '.md', 'w') as f:
                    f.write(f'# Total session cost: ${session_cost:.5f}\n\n') # Write the total cost of the session to the file
                    f.write('---\n')
                    f.write('# Chat History\n')
                    for i, m in enumerate(history): # Write the chat history to the file
                        f.write(f'### {i}. {m["role"]}, {m["tokens"]} tokens\n')
                        f.write(f'{m["content"]}\n\n')
                        f.write('---\n')
                print(f'Chat history saved to {filename}.md', tag='Success', tag_color='green') # Print success message
                break
            case 'csv': # Save chat history as csv
                with open(filename + '.csv', 'w') as f:
                    f.write(f'Session Cost:,{session_cost:.5f}\n') # Write the total cost of the session to the file
                    f.write('Role,Tokens,Content\n') # Write the header row to the file
                    for m in history: # Write the chat history to the file
                        f.write(f'{m["role"]},{m["tokens"]},\"{m["content"]}\"\n')
                print(f'Chat history saved to {filename}.csv', tag='Success', tag_color='green') # Print success message
                break

def add_files(project_dir, ignored_extensions): # TODO - Multimodal input
    """Add files to the context.
    
    Args:
        project_dir (str): The project directory to use.
        ignored_extensions (list): A list of file extensions to ignore.

    Returns:
        str: The context string with the files and content provided.
    """
    all_files = [] # Initialize list to store all file paths in the project directory
    selected_files = [] # Initialize list to store selected file paths

    # Walk through the project directory and add all files to the all_files list
    for root, dirs, files in os.walk(project_dir):
        dirs[:] = [d for d in dirs if not d.startswith('.')] # Ignore hidden directories
        for file in files:
            if not any(file.endswith(ext) for ext in ignored_extensions) and not file.startswith('.'): # Check if the file extension is not in the ignored extensions list
                all_files.append(os.path.join(root, file)) # Add the file to the selected files list
    
    # Print the list of files in the project directory
    for i, file in enumerate(all_files):
        print(file, tag=str(i+1), tag_color='magenta', color='white')
    
    while True: # Loop until the user selects files or cancels
        choices = input('Enter file numbers, extensions (e.g. ".py", ".txt", etc.), "all", or "none" (comma-separated): ') # Get user input for file selection
        choices = [choice.strip() for choice in choices.split(',')] # Split user input by commas and remove whitespace

        try: # Attempt to process user input
            for choice in choices: # Iterate through each choice
                if choice.lower() == 'all': # Select all files
                    selected_files = all_files
                    break # Exit the loop after selecting all
                elif choice.lower() == 'none': # Select no files
                    break # Exit the loop after selecting none
                elif choice.startswith('.'): # Choice is a file extension
                    selected_files.extend([file for file in all_files if file.endswith(choice)]) # Add files with the specified extension to the selected files list
                else: # Choice is assuemd to be a file number
                    selected_files.append(all_files[int(choice) - 1]) # Add the file to the selected files list
            break # Exit the loop after processing all choices
        except ValueError:
            print('Invalid input. Enter a valid file number, extension, "all", or "none".', tag='Error', tag_color='red')
        except IndexError:
            print(f'Invalid file number. Enter a number between 1 and {len(all_files)}.', tag='Error', tag_color='red')
    
    context = 'Files and content provided for context: ' # Initialize the context string
    if selected_files == []:
        context += '<none>\n' # Add a placeholder for no files selected
    else:
        context += '\n'
    retry = 'c'
    for file_path in selected_files: # Loop through the selected files
        try:
            content = open(file_path, 'r').read() # Read the content of the file
            context += f'{file_path}\n```\n{content}\n```\n' # Add the file path and content to the context string
        except:
            print(f'Error reading file: {file_path}', tag='Error', tag_color='red')
            retry = input ('Would you like to reselect files or continue? (r/C): ').lower()
            if retry == 'c':
                continue
            elif retry == 'r':
                print('Reselecting files...\n', color='magenta')
                return add_files(project_dir, ignored_extensions)
            else:
                print('Reselecting files...\n', color='magenta')
                return add_files(project_dir, ignored_extensions)

    if retry == 'r':
        print('Reselecting files...\n', color='magenta')
        return add_files(project_dir, ignored_extensions)
    elif retry == 'c':
        return context
    else:
        print('Reselecting files...\n', color='magenta')
        return add_files(project_dir, ignored_extensions)
    
def send_message(chat, message, timeout):
    print("Waiting for response...\n", color='magenta') # Print waiting message
    try:
        response = chat.send_message(message, request_options={'timeout': timeout}) # Send the message to the model
        input_tokens = response.usage_metadata.prompt_token_count # Get the number of input tokens used
        output_tokens = response.usage_metadata.candidates_token_count # Get the number of output tokens used
        response_msg = response.text # Get the response message
        if DEBUG:
            print(response)
    except Exception as e:
        print(e, tag='Response Error', tag_color='red')


    return input_tokens, output_tokens, response_msg

def main(): # TODO: If the response fails, message is added but the model has no access to it. Need to fix this somehow.
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
    print('Continuing...\n', color='green')

    # Verify environment variables are set
    if (not API_KEY or  not CONFIG):
        # Exit if not set
        print("Set your .env as specified in the .env-template", tag='Error', tag_color='red')
        quit()

    # Load the config file
    model, system_instructions, safety, timeout, project_dir, ignored_extensions, temperature, max_output_tokens, stop_sequences = load_config()

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
    chat, si_tokens, model = initialize_chat(model, system_instructions, safety, temperature, max_output_tokens, stop_sequences)

    # Add the system instructions to the chat history
    add_message('System', system_instructions, si_tokens)

    # Print system instructions, token count and cost
    print(_all_messages[0]['content'], tag='System Instructions', tag_color='magenta', color='white')
    print(_all_messages[0]['tokens'], tag='Tokens', tag_color='magenta', color='white')
    print(f'${calculate_cost(_all_messages[0]['tokens'], INPUT_PRICING):.5f}', tag='Cost', tag_color='magenta', color='white')

    # Display help message
    display_help()

    # Initialize variables
    total_input_tokens = 0
    total_output_tokens = 0
    session_cost = 0

    print('Starting chat session...', tag='Chat Session', tag_color='magenta', color='white')

    # Main chat loop
    while True:
        # Get user input
        user_input = input(f"\nType \033[36m'help'\033[0m for special commands.\n\033[32mYou: ")
        print()

        match user_input:
            case 'exit': # Exit chat session, give user option to save chat history
                s = input('Do you want to save the chat history? (y/N): ').lower() # Ask user if they want to save chat history
                if s != 'n' and s != 'no':
                    save(session_cost) # Save chat history
                quit() # Exit the program
            case 'save': # Save chat history
                save(session_cost) # Save chat history
            case 'delete': # Delete messages from history
                msg_indicies_str = input('Enter the message indicies to delete (comma-separated):') # Get message indicies from user
                msg_indicies = [int(x.strip()) for x in msg_indicies_str.split(',')] # Convert message indicies to integers
                delete_messages(chat, msg_indicies) # Delete messages from chat history
            case 'files': # Add files to context
                if project_dir is None:
                    print('Project directory not set in config file. Cannot add files.', tag='Error', tag_color='red')
                else:
                    context = add_files(project_dir, ignored_extensions)

                message = context + "\nUser Input: " + input('Enter your message to be sent along with the files: ') # Get user input
                if DEBUG:
                    print(message, tag='DEBUG', tag_color='yellow', color='white')
                try:
                    input_tokens, output_tokens, response = send_message(chat, message, timeout) # Send the message to the model
                except Exception as e:
                    tokens = model.count_tokens([{'role': 'user', 'parts':[message]}]).total_tokens - si_tokens
                    total_input_tokens += tokens
                    add_message('User', message, tokens) # Add the user message to the chat history
                    print(message, tag='You', tag_color='green') # Print the user's message
                    continue

                # Add the number of tokens used in this message to the total token counts
                total_input_tokens += input_tokens
                total_output_tokens += output_tokens

                add_message('User', message, model.count_tokens([{'role': 'user', 'parts':[message]}]).total_tokens - si_tokens) # Add the user message to the chat history
                print(message+'\n', tag='You', tag_color='green') # Print the user's message

                add_message('Model', response, model.count_tokens([{'role': 'model', 'parts':[response]}]).total_tokens - si_tokens) # Add the model response to the chat history
                print(response, tag='Model', tag_color='blue') # Print the model's response
                
                # Print the number of input and output tokens used and the costs
                print(f'Tokens: {input_tokens}, Cost: ${calculate_cost(input_tokens, INPUT_PRICING):.5f}', tag='Input', tag_color='magenta', color='white') # Print the number of input tokens used and the cost
                print(f'Tokens: {output_tokens}, Cost: ${calculate_cost(output_tokens, OUTPUT_PRICING):.5f}', tag='Output', tag_color='magenta', color='white') # Print the number of output tokens used and the cost
                session_cost = calculate_cost(total_input_tokens, INPUT_PRICING) + calculate_cost(total_output_tokens, OUTPUT_PRICING)
                print(f'${session_cost:.5f}', tag='Session Cost', tag_color='magenta', color='white') # Print the total cost of the session
            case 'history': # Display chat history
                print(tag='Chat History', tag_color='magenta')
                for i, m in enumerate(_messages): # Loop through messages in chat history
                    # Calculate message content preview, removing newlines
                    content_preview = m['content'][:75] + ' ... ' + m['content'][-75:] if len(m['content']) > 150 else m['content']
                    content_preview = content_preview.replace('\n', ' ')
                    cost_to_keep = calculate_cost(m['tokens'], INPUT_PRICING, history=True) # Calculate cost to keep message
                    match m['role']:
                        case 'System':
                            print(f'Tokens: {m['tokens']}, Cost to keep: ${cost_to_keep:.5f}', tag=str(i), tag_color='magenta', color='white')
                            print(content_preview, tag='System', tag_color='magenta')
                        case 'User':
                            print(f'Tokens: {m['tokens']}, Cost to keep: ${cost_to_keep:.5f}', tag=str(i), tag_color='magenta', color='white')
                            print(content_preview, tag='User', tag_color='green')
                        case 'Model':
                            print(f'Tokens: {m['tokens']}, Cost to keep: ${cost_to_keep:.5f}', tag=str(i), tag_color='magenta', color='white')
                            print(content_preview, tag='Model', tag_color='blue')
            case 'view': # View a full message's content
                message_index = input('Enter the message index to view: ') # Get message index from user
                try:
                    match _messages[int(message_index)]['role']: # Display and color message content based on role
                        case 'System':
                            print(_messages[int(message_index)]['content'], tag='System', tag_color='magenta')
                        case 'User':
                            print(_messages[int(message_index)]['content'], tag='User', tag_color='green')
                        case 'Model':
                            print(_messages[int(message_index)]['content'], tag='Model', tag_color='blue')
                except IndexError:
                    print(f'Invalid message index. Message index out of range. Enter between 0 and {len(_messages) - 1}.', tag='Error', tag_color='red')
                except ValueError:
                    print('Invalid message index. Enter a valid integer.', tag='Error', tag_color='red')
            case 'help': # Display help message
                print(HELP_MSG, tag='Help', tag_color='cyan')
            case _: # Send user input to the model
                try:
                    input_tokens, output_tokens, response = send_message(chat, user_input, timeout) # Send the message to the model
                except Exception as e:
                    tokens = model.count_tokens([{'role': 'user', 'parts':[user_input]}]).total_tokens - si_tokens
                    total_input_tokens += tokens
                    add_message('User', user_input, tokens) # Add the user message to the chat history
                    print(user_input+'\n', tag='You', tag_color='green') # Print the user's message
                    continue

                # Add the number of tokens used in this message to the total token counts
                total_input_tokens += input_tokens
                total_output_tokens += output_tokens

                add_message('User', user_input, model.count_tokens([{'role': 'user', 'parts':[user_input]}]).total_tokens - si_tokens) # Add the user message to the chat history
                print(user_input+'\n', tag='You', tag_color='green') # Print the user's message

                add_message('Model', response, model.count_tokens([{'role': 'model', 'parts':[response]}]).total_tokens - si_tokens) # Add the model response to the chat history
                print(response, tag='Model', tag_color='blue') # Print the model's response
                
                # Print the number of input and output tokens used and the costs
                print(f'Tokens: {input_tokens}, Cost: ${calculate_cost(input_tokens, INPUT_PRICING):.5f}', tag='Input', tag_color='magenta', color='white') # Print the number of input tokens used and the cost
                print(f'Tokens: {output_tokens}, Cost: ${calculate_cost(output_tokens, OUTPUT_PRICING):.5f}', tag='Output', tag_color='magenta', color='white') # Print the number of output tokens used and the cost
                session_cost = calculate_cost(total_input_tokens, INPUT_PRICING) + calculate_cost(total_output_tokens, OUTPUT_PRICING)
                print(f'${session_cost:.5f}', tag='Session Cost', tag_color='magenta', color='white') # Print the total cost of the session


if __name__ == '__main__':
    main()