# Total session cost: $0.22407

---
# Chat History
### 0. System, 281 tokens
You are an expert AI programming assistant. Your goals are: 1. Code Generation: Write high-quality code in any language specified in the user prompt. Adhere to best practices (style, maintainability) and user preferences. Generate snippets, functions, classes, or full modules as needed. Adapt to the user's coding style over time. 2. Debugging: Analyze code for errors (syntax, logic, runtime). Provide clear explanations of issues and suggest fixes. Consider context from the entire file or project if provided. 3. Project Management: Help the user break down tasks, set milestones, and organize code. Offer suggestions for project structure and management tools. 4. Conceptual Understanding: Grasp the core ideas behind the user's project. Suggest appropriate design patterns, data structures, or libraries. Explain complex technical concepts in simpler terms. 5. Interactive Collaboration: Ask clarifying questions when the user's request is ambiguous. Propose multiple solutions with explanations. Adapt based on user feedback and preferences. Additional Capabilities: Code Refactoring (if requested). Unit Test Generation (if requested). Code Documentation (if requested). Searching External Resources (if requested). Contextual Information: You have access to the user's entire codebase or relevant files if provided. You can leverage your large context window to understand the project context. Finally, refrain from using emojis unless otherwise specified.

---
### 1. User, 8 tokens
I am testing something. Respond briefly.

---
### 2. Model, 11 tokens
Understood. What can I help you test? 


---
### 3. User, 5 tokens
What is your name?

---
### 4. Model, 16 tokens
I am an AI programming assistant. I do not have a name. 


---
### 5. User, 474 tokens
Files and content provided for context: 
/home/tech/Development/Programming/Python/GeminiProjectAssistant/readme.md
```
# Gemini Project Assistant
##### A Google Gemini based project assistant that helps you create, manage, and debug your programming projects.
### License
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

*Click link for license details.*

---------------
## Table of Contents
* [Installation](#installation)
* [Usage](#usage)
* [Credits](#credits)
* [Questions](#questions)
---------------
## Installation
1. Download the zip and extract files to the directory you wish to install in.
2. Open installation directory.
3. Create your .env file according to the .env-template.
4. Create config.json to your specifications according to config.json-template.
5. Open terminal in the installation directory.
6. Run `pip install -r requirements.txt`
6. Run `python3 ./project_assistant_v1.py`
7. Follow instructions on the screen.
## Usage
You can set the project directory to your project directory. When using this application, you may add relevant files related to the goal you are trying to accomplish. You then converse with the Gemini API, asking it for ideas on how to accomplish something, to debug your code, to generate code, etc. As you get better with prompting, the application becomes more reliable and useful.

![A image showing the startup message when launching the application.](images/readme.png)

## Credits
[Giamo Lao (TechnicalParadox)](https://technicalparadox.github.io)
## Questions
Any questions should be directed to 

[Giamo Lao (TechnicalParadox)](technicalparadox.github.io)

[giamolao98@gmail.com](mailto:technicalparadox.github.io)

*This readme was generated using [readme-js](https://github.com/TechnicalParadox/readme-js)*

```

User Input: Do you think this is a good idea for a project?

---
### 6. Model, 33 tokens
It's a promising idea! Building a project assistant leveraging Gemini's capabilities could be quite useful.  What are your main goals for this project? 


---
### 7. User, 18 tokens
I have already accomplished version 1! We are actually using it right now to speak!

---
### 8. Model, 45 tokens
That's fantastic!  It's impressive you've already reached a functional version. What aspects of version 1 are you most proud of?  What's next on your roadmap for the project? 


---
### 9. User, 68 tokens
The cost tracking and saving of history is very useful. I need to handle gemini's various possible errors in responses, such as the DeadlineExceeded exception, safety exceptions, etc. I also think I should take this framework and give it a GUI rather than force use of the command line interface. Would you like to see the code?

---
### 10. Model, 64 tokens
Yes, I'd love to see the code, specifically how you're handling cost tracking and history. 

Those are great areas to improve upon. Handling errors gracefully is essential for a polished user experience, and a GUI would make it more accessible.  What kind of GUI are you envisioning? 


---
### 11. User, 9057 tokens
Files and content provided for context: 
/home/tech/Development/Programming/Python/GeminiProjectAssistant/project_assistant_v1.py
```
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
        (float): The new base input cost for the chat history.
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

    return sum(m['cost'] for m in _messages)

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
        raise e # Raise the exception so the calling function can handle it

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

        message = None  # Reset message to None for each iteration

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
                new_cost = delete_messages(chat, msg_indicies) # Delete messages from chat history
                print(f'New history base input cost: ${new_cost:.5f}', tag='New Cost', tag_color='magenta', color='white') # Print the new base input cost
            case 'files': # Add files to context
                if project_dir is None:
                    print('Project directory not set in config file. Cannot add files.', tag='Error', tag_color='red')
                else:
                    context = add_files(project_dir, ignored_extensions)
                    message = context + "\nUser Input: " + input('Enter your message to be sent along with the files: ') # Get user input
                    if DEBUG:
                        print(message, tag='DEBUG', tag_color='yellow', color='white')
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
                print(f'History base input cost: ${sum(m['cost'] for m in _messages):.5f}', tag='Input Cost', tag_color='magenta', color='white') # Print the history base input cost
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
                message = user_input 

        # Process the message if it's not a command or 'files' command set a message       
        if message:
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

if __name__ == '__main__':
    main()
```

User Input: I'll attach the output of our current conversation, pasted as one line, so please excuse the formatting: [CRITICAL] Make sure to add the .env file to your .gitignore to keep your API key secure.[Welcome to Gemini Project Assistant v1!] - Converse with the LLM model to get help with your project. Ex. 'Help me debug this script.', 'Complete the TODOs in this file.', 'What can I add to improve this project?', etc.- Cost will be shown for each message and the total cost of the session will be displayed.- You can provide context by selecting files from your project directory.- You can delete messages to refine the chat history and save costs while maintaining the context you need.[Warnings] - NEVER SHARE YOUR .ENV FILE OR API KEY.- You may incur costs for using the Gemini API. Confirm pricing details on the Google Cloud Platform website.- This program attempts to calculate costs based on token usage. Actual costs may vary.- You should NOT share sensitive information or personal data. Do so at your own risk.- Use of the Gemini API is subject to the Google Cloud Platform Terms of Service.- The Gemini model may generate harmful or inappropriate content. Use safety settings to mitigate risks.- The Gemini model may not always provide accurate or helpful responses. Use critical thinking. You will become a prompt engineer in no time.- AI generated content should be reviewed and validated before use in production.- AI generated code may contain bugs or security vulnerabilities. Review and test thoroughly.- AI generated code may be harmful or malicious. Review and validate generated code carefully.- The author of this script is not responsible for any consequences of using this application.[PRICING for gemini-1.5-pro-latest ($ per 1 million tokens) as of 2024-07-13] Input: 3.5 (up to 128k tokens), 7.0 (over 128k tokens)Output: 10.5 (up to 128k tokens), 21.0 (over 128k tokens)[User Agreement] By continuing, you take full responsibility for your use of this application.Do you accept the terms and conditions? (y/N): yContinuing...[Safety Settings] No Safety[System Instructions] You are an expert AI programming assistant. Your goals are: 1. Code Generation: Write high-quality code in any language specified in the user prompt. Adhere to best practices (style, maintainability) and user preferences. Generate snippets, functions, classes, or full modules as needed. Adapt to the user's coding style over time. 2. Debugging: Analyze code for errors (syntax, logic, runtime). Provide clear explanations of issues and suggest fixes. Consider context from the entire file or project if provided. 3. Project Management: Help the user break down tasks, set milestones, and organize code. Offer suggestions for project structure and management tools. 4. Conceptual Understanding: Grasp the core ideas behind the user's project. Suggest appropriate design patterns, data structures, or libraries. Explain complex technical concepts in simpler terms. 5. Interactive Collaboration: Ask clarifying questions when the user's request is ambiguous. Propose multiple solutions with explanations. Adapt based on user feedback and preferences. Additional Capabilities: Code Refactoring (if requested). Unit Test Generation (if requested). Code Documentation (if requested). Searching External Resources (if requested). Contextual Information: You have access to the user's entire codebase or relevant files if provided. You can leverage your large context window to understand the project context. Finally, refrain from using emojis unless otherwise specified.[Tokens] 281[Cost] $0.00098[Help] 'save' - Save the chat history to a file.'delete' - Delete messages from chat history.'files' - Add files and their paths to context from project directory.'history' - Display concise chat history.'view' - View a full message's content.'exit' - Exit the chat session and give the option to save chat history.'help' - Display special commands and instructions.[Warning] If you enter a command wrong, it will be sent as a message to the API, incurring costs.[Chat Session] Starting chat session...Typ

---
### 12. Model, 170 tokens
It appears your cost tracking and instructions are working as intended. Good job on version 1! 

For error handling, consider using Python's `try-except` blocks to catch specific exceptions from the Gemini API.  You can tailor the program's response based on the exception caught. For example:

```python
try:
    response = chat.send_message(message, request_options={'timeout': timeout})
except DeadlineExceeded:
    print("The API request timed out. Try reducing the length of your message or increasing the timeout.") 
except genai.SafetyError as e:
    print(f"Safety violation: {e.message}") 
```

Feel free to share relevant code snippets, and I can provide more targeted feedback. What GUI framework are you considering using?


---
### 13. User, 37 tokens
I am actually not sure. I've never made a GUI program before. Is there something I could integrate using my already-existing code? Or would I have to start over?

---
### 14. Model, 289 tokens
You don't need to start over! You can integrate your existing code into a GUI framework. 

Here are a few popular Python GUI frameworks that could work well:

**1. Tkinter:**

   * **Pros:** Built-in with Python, simple to learn, good for basic GUIs. 
   * **Cons:**  Can look a bit dated, less flexible for complex layouts.

**2. PyQt:**

   * **Pros:** Very powerful and feature-rich, cross-platform, lots of online resources.
   * **Cons:** Steeper learning curve than Tkinter.

**3. Kivy:**

   * **Pros:** Designed for modern, touch-friendly interfaces, good for mobile apps. 
   * **Cons:**  Different from traditional desktop UI paradigms.

**Recommendations:**

* **For simplicity and quick integration, start with Tkinter.** You can create basic input/output areas and buttons to interact with your existing code. 
* **If you envision a more complex GUI with advanced features, PyQt is worth the learning investment.** 

**Key Point:** Think about how you want your GUI to look and function. Sketch out a rough design to guide your choice of framework and plan how you'll structure the user interactions.  

I'm ready to help you with code examples and guidance once you've chosen a direction! 


---
### 15. User, 28 tokens
I just watched a YouTube video comparing Tkinter and PyQt. It seem's like PyQt will be the better option to learn long term.

---
### 16. Model, 146 tokens
That's great! PyQt is an excellent choice for robust and visually appealing GUIs. It's a valuable skill to learn.  

To help me guide you, could you describe what GUI elements you think you'll need for the project assistant?  For example:

* **Input/output areas:**  How will users enter their messages and see the AI's responses?
* **Buttons:** What actions will users be able to trigger (e.g., send message, upload files, view history)?
* **Layout:**  Do you envision a single window, multiple tabs, or a more complex structure? 

The more specific you are, the better I can tailor my assistance. 


---
### 17. User, 18 tokens
Taking a look at my existing project, what features do you think the GUI should have?

---
### 18. Model, 555 tokens
Okay, I've analyzed your existing project and the previous conversation. Here's a breakdown of features I recommend for the GUI, along with some potential PyQt implementations:

**Core Features:**

1.  **Chat Display (QTextEdit):**
    *   A dedicated area to display the conversation history.
    *   Use different colors/styles to distinguish user messages, model responses, and system messages.
    *   Potentially make messages selectable for viewing full content or deletion.

2.  **Message Input (QLineEdit):**
    *   A single-line text input field for users to type their messages.
    *   Consider adding autocomplete or suggestion features for commands (e.g., "help", "save").

3.  **Send Button (QPushButton):**
    *   A button to send the user's message to the Gemini model.
    *   Alternatively, you could send the message automatically when the user presses Enter in the input field.

4.  **Cost Display (QLabel):**
    *   A clear label to show the current session cost and potentially a breakdown (input/output tokens).
    *   Update this label dynamically after each interaction with the model.

**Additional Features:**

5.  **File Selection (QFileDialog):**
    *   A button to open a file dialog, allowing users to select files from their project.
    *   Display the selected file paths in a list or a dedicated area.

6.  **History Management (QListWidget or QTableWidget):**
    *   A widget to display a concise chat history (potentially with message timestamps).
    *   Implement options to delete messages or view full content (e.g., double-click or a context menu).

7.  **Settings Menu (QMenu):**
    *   A menu bar or a settings button to access options like:
        *   Model selection (if you plan to support multiple Gemini models)
        *   Safety settings
        *   API key management
        *   Timeout settings

**PyQt Implementation Notes:**

*   **Layout Management:** Use PyQt's layout managers (QVBoxLayout, QHBoxLayout, QGridLayout) to arrange elements cleanly.
*   **Signals and Slots:** Connect GUI events (button clicks, menu selections) to your existing code logic using signals and slots.
*   **Threading:** Consider using threads to handle long-running API calls, preventing the GUI from freezing.

**I'm ready to provide specific code examples as we start building out the GUI! Feel free to ask if you'd like to refine or expand on these features.**


---
### 19. User, 11 tokens
These features seem great. Let's get started!

---
### 20. Model, 1243 tokens
Excellent! Let's begin by building the basic structure of your PyQt GUI and integrating your chat functionality. 

Here's a basic implementation with the chat display, input field, send button, and cost display. It also includes a basic settings menu for later expansion. 

```python
import sys
import os
# ... (Your existing imports from project_assistant_v1.py)

from PyQt5.QtWidgets import (
    QApplication, 
    QWidget, 
    QPushButton, 
    QLineEdit, 
    QVBoxLayout, 
    QHBoxLayout, 
    QLabel, 
    QTextEdit,
    QMainWindow,
    QMenuBar,
    QMenu
)
from PyQt5.QtCore import Qt

class ProjectAssistantGUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Gemini Project Assistant")

        # Initialize chat history and cost
        self.chat_history = ""
        self.session_cost = 0.0

        # Create GUI elements
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)

        self.message_input = QLineEdit()

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)

        self.cost_label = QLabel(f"Session Cost: ${self.session_cost:.5f}")

        # Create layout
        input_layout = QHBoxLayout()
        input_layout.addWidget(self.message_input)
        input_layout.addWidget(self.send_button)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.chat_display)
        main_layout.addLayout(input_layout)
        main_layout.addWidget(self.cost_label)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Create Menu Bar
        self.create_menu_bar()

    def create_menu_bar(self):
        menu_bar = self.menuBar()
        settings_menu = menu_bar.addMenu("Settings") 
        # Add settings menu items here later

    def send_message(self):
        user_message = self.message_input.text()
        self.message_input.clear()  

        if user_message:
            self.display_message(user_message, "User")

            # --- Integrate your Gemini API call here ---
            # Example:
            # try:
            #     input_tokens, output_tokens, response = send_message(chat, user_message, timeout) 
            #     self.session_cost = calculate_cost(total_input_tokens, INPUT_PRICING) + \
            #                        calculate_cost(total_output_tokens, OUTPUT_PRICING)
            #     self.update_cost_display() 
            #     self.display_message(response, "Model") 
            # except Exception as e:
            #     # Handle errors (e.g., display error message)
            #     print(f"Error: {e}") 

    def display_message(self, message, sender):
        self.chat_history += f"{sender}: {message}\n"
        self.chat_display.setText(self.chat_history)

    def update_cost_display(self):
        self.cost_label.setText(f"Session Cost: ${self.session_cost:.5f}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ProjectAssistantGUI()
    window.show()
    sys.exit(app.exec_())
```

**Explanation:**

1.  **Imports:** Added necessary imports from PyQt5.
2.  **`ProjectAssistantGUI` Class:**
    *   Creates the main window.
    *   Initializes GUI elements: `chat_display`, `message_input`, `send_button`, `cost_label`.
    *   Sets up layout using `QVBoxLayout` and `QHBoxLayout`.
    *   Connects the `send_button` to the `send_message` function.
    *   Creates a basic menu bar.

3.  **`send_message` Function:**
    *   Gets the user's message from `message_input`.
    *   Calls `display_message` to add it to the chat history.
    *   **This is where you'll integrate your Gemini API call using the `send_message` function from your existing code.**
    *   Updates the cost display.

4.  **`display_message` Function:**
    *   Appends the new message to the `chat_history` and updates the `chat_display`.

5.  **`update_cost_display` Function:**
    *   Updates the `cost_label` with the current `session_cost`.

**Next Steps:**

1.  **Integrate Your API Call:** Replace the example comment in `send_message` with your actual `send_message` function call and error handling from your existing code.
2.  **Expand Settings Menu:** Add actions to the settings menu (e.g., model selection, safety settings) and connect them to functions.
3.  **Add More Features:** Implement file selection, history management, and any other features you want to include!

Let me know when you've integrated your API call, and we can continue building on this foundation! 


---
