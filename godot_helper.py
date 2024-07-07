# TODO: color code the output for user, model, and system messages (user = green, model = blue, system = yellow)
# TODO: Add color functions for print() and print(f) to a helper file and import/integrate them
# TODO: Refactor the code to use functions for repetitive tasks

# Import necessary libraries
import os # Provides functions for interacting with the operating system
import json # Used for working with JSON data
import google.generativeai as genai # Import the Google Generative AI library
from google.generativeai import GenerativeModel, ChatSession # Import specific classes for interacting with Gemini
from dotenv import load_dotenv # For loading environment variables from a .env file
from google.generativeai.types import HarmCategory, HarmBlockThreshold # For configuring safety settings

# Load environment variables from a .env file (like your API key)
load_dotenv()

# Configuration
PROJECT_DIR = os.getenv("PROJECT_DIRECTORY") # Get the Godot project directory from environment variables
MODEL_NAME = "gemini-1.5-pro-latest" # Specify the Gemini model to use
API_KEY = os.getenv("API_KEY") # Get your Google Cloud API key from environment variables

# Gemini Safety Settings - Currently set to allow all content
# For more info on safety settings and thresholds: https://developers.generativeai.google/api/rest/generativelanguage/v1beta2/SafetySetting
NO_SAFETY = {
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE, # No blocking for hate speech
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE, # No blocking for harassment
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE, # No blocking for sexually explicit content
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE # No blocking for dangerous content
}

# Pricing per 1 million tokens (as of July 6, 2024)
PRICING_DATE = "July 6, 2024"
INPUT_PRICING = {
    "upto_128k": 3.50, # Price per million tokens for prompts up to 128,000 tokens
    "over_128k": 7.00  # Price per million tokens for prompts larger than 128,000 tokens
}
OUTPUT_PRICING = {
    "upto_128k": 10.50, # Price per million tokens for completions up to 128,000 tokens
    "over_128k": 21.00  # Price per million tokens for completions larger than 128,000 tokens
}

# Help message for special commands and instructions
INSTRUCTIONS = """
\033[33mIMPORTANT: Use the .env_template and set the API_KEY and the PROJECT_DIRECTORY environment variable to your Gemini API key and project directory in your .env file.
 \033[31mMake sure to add the .env file to your .gitignore to keep your API key secure.

\033[32mINSTRUCTIONS:
Converse with the LLM model to get help with your project. Ex. 'Help me debug this script.', 'Complete the TODOs in this file.', 'What can I add to improve this project?', etc.
Cost will be shown for each message and the total cost of the session will be displayed.
You can provide context by selecting files from your project directory.
You can delete messages to refine the chat history and save costs while maintaining the context you need.

\033[31mWARNING:
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
- The author of this script is not responsible for any consequences of using this application.\033[0m
"""
HELP_MSG = """
\033[36mSPECIAL COMMANDS:
'exit' - Exit the chat session and give the option to save chat history.
'delete' - Delete messages from chat history.
'update' - Update files in context.
'history' - Display concise chat history.
'view' - View a full message's content.
'help' - Display special commands and instructions.\033[0m
\033[31mIf you enter a command wrong, it will be sent as a message to the API, incurring costs.\033[0m
"""

# Initialize a global list to store message tokens and costs
message_costs = []
# Initialize a global variable to store system instruction tokens
sys_instruct_tokens = 0

def get_all_files(directory):
    """Gets a list of all files within a directory, ignoring hidden files and specific file types.

    Args:
        directory (str): The path to the directory you want to search.

    Returns:
        list: A list of file paths for all valid files found in the directory.
    """
    ignored_extensions = ['.tmp', '.svg', '.png', '.ttf', '.import'] # List of file extensions to ignore
    file_list = [] # Initialize an empty list to store file paths
    for root, dirs, files in os.walk(directory): # Walk through the directory structure
        dirs[:] = [d for d in dirs if not d.startswith('.')] # Ignore hidden directories
        for file in files: # Iterate through files in the current directory
            if not any(file.endswith(ext) for ext in ignored_extensions) and not file.startswith('.'): # Filter out ignored files and hidden files
                file_list.append(os.path.join(root, file)) # Add the full path of the file to the list
    return file_list # Return the list of file paths

def select_files(file_list):
    """Presents an interactive menu for the user to select specific files.

    Args:
        file_list (list): A list of file paths.

    Returns:
        list: A list of selected file paths.
    """
    selected_files = [] # Initialize an empty list to store selected file paths
    for i, file in enumerate(file_list): # Iterate through the list of files, displaying an index for each
        print(f"{i + 1}. {file}") # Print the index and file path for user selection

    while True: # Loop until valid input is received
        choices = input("Enter file numbers, extensions (e.g., '.gd, .tscn'), 'all', or 'none' (comma-separated): ")
        choices = [choice.strip() for choice in choices.split(',')] # Split user input into individual choices

        try: # Attempt to process user input
            for choice in choices: # Iterate through each choice
                if choice.lower() == 'all': # Select all files
                    selected_files = file_list 
                    break # Exit the loop after selecting all
                elif choice.lower() == 'none': # Select no files
                    selected_files = [] 
                    break # Exit the loop after selecting none
                elif choice.startswith("."): # Choice is a file extension
                    selected_files.extend([f for f in file_list if f.endswith(choice)]) # Add files with the specified extension
                else: # Choice is assumed to be a file number
                    index = int(choice) - 1 # Adjust for zero-based indexing
                    selected_files.append(file_list[index]) # Add the file at the specified index
            break # Exit the loop after processing all choices
        except (ValueError, IndexError): # Catch invalid input types or out-of-range indices
            print("Invalid input. Please try again.") # Prompt the user for valid input

    return selected_files # Return the list of selected files

def read_file_content(file_path):
    """Reads and returns the content of a file.

    Args:
        file_path (str): The path to the file.

    Returns:
        str: The content of the file.
    """
    with open(file_path, "r") as f: # Open the file in read mode
        return f.read() # Read and return the content of the file

def generate_context_message(selected_files):
    """Constructs a context message for the Gemini model.

    The context message includes file names and their content, formatted for clarity.

    Args:
        selected_files (list): A list of selected file paths.

    Returns:
        str: A formatted context message.
    """
    context = "Files and content provided for context:" # Begin the context message
    if selected_files == []:
        context += " <none>\n"
    else:
        context += "\n"
    for file_path in selected_files: # Iterate through selected files
        content = read_file_content(file_path) # Read the content of the current file
        context += f"{file_path}\n```{content}```\n" # Append the file name and content to the message, using Markdown code blocks for formatting
    return context # Return the constructed context message

def get_context_token_count():
    tokens = 0 # Initialize token count
    for m in message_costs:
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

def start_gemini_chat(context_message):
    """Initializes a chat session with the Gemini model.

    Args:
        context_message (str): The initial context message containing file information.

    Returns:
        tuple: A tuple containing the ChatSession object, total input tokens, total output tokens.
    """
    genai.configure(api_key=API_KEY) # Configure the API key for the Google Generative AI library

    system_instructions = """
    You are an expert Godot game developer. You are helping me with my Godot project, 'SpaceRoguelikeV1'. 
    I have provided you with the code for some of my scenes and scripts.

    - Prioritize Godot-specific advice and code examples.
    - Refer to the provided context when asked about a file or node. 
    - Ask clarifying questions if you need more information.
    - Use spaces instead of indentation for code formatting. 
    """
    # Create a GenerativeModel instance with specified settings
    model = genai.GenerativeModel(
        model_name=MODEL_NAME, # Name of the Gemini Pro model
        safety_settings=NO_SAFETY, # Safety settings for the model
        system_instruction=system_instructions # System-level instructions to guide the model's behavior
    )
    chat = model.start_chat() # Initiate a chat session with the model

    sys_instruct_tokens = model.count_tokens(" ").total_tokens # Count tokens in system instructions
    # Store system instructions in message costs
    message_costs.append({
        "role": "system",
        "tokens": sys_instruct_tokens,
        "cost": calculate_cost(sys_instruct_tokens, INPUT_PRICING),
        "content": system_instructions
    })

    # add tools for the model if needed and if we do then we need to calculate the tokens/cost of the tools
    # no tools right now

    total_input_tokens = 0 # Initialize counter for total input tokens (used in session cost)
    total_output_tokens = 0 # Initialize counter for total output tokens (used in session cost)

    # Add initial user input to context message
    print("\033[0mProvide your initial message to the model.")
    context_message += input("\033[92mYou: ")

    # Send the context message directly 
    print(f"\n\033[92mYou: {context_message}") 
    response = chat.send_message(context_message) # Send the initial context message to the model
    total_input_tokens += response.usage_metadata.prompt_token_count # Increment input token count
    total_output_tokens += response.usage_metadata.candidates_token_count # Increment output token count
    
    # Store message cost information
    message_costs.append({
        "role": "user",
        "tokens": response.usage_metadata.prompt_token_count - sys_instruct_tokens, # Subtract system instruction tokens from initial user input tokens
        "cost": calculate_cost(response.usage_metadata.prompt_token_count, INPUT_PRICING),
        "content": context_message
    })
    message_costs.append({
        "role": "model",
        "tokens": response.usage_metadata.candidates_token_count,
        "cost": calculate_cost(response.usage_metadata.candidates_token_count, OUTPUT_PRICING),
        "content": response.text
    })

    print(f"\n\033[94mGemini: {response.text}\033[0m") # Display the model's response
    print(f"INPUT TOKENS: {response.usage_metadata.prompt_token_count}, INPUT COST: ${calculate_cost(response.usage_metadata.prompt_token_count, INPUT_PRICING):.5f}") # Display input token count and cost
    print(f"OUTPUT TOKENS: {response.usage_metadata.candidates_token_count}, OUTPUT COST: ${calculate_cost(response.usage_metadata.candidates_token_count, OUTPUT_PRICING):.5f}") # Display output token count and cost
    print(f"SESSION COST: ${calculate_cost(total_input_tokens, INPUT_PRICING) + calculate_cost(total_output_tokens, OUTPUT_PRICING):.5f}")  # Display session cost
    return chat, total_input_tokens, total_output_tokens, message_costs # Return the chat session object and token counts

def delete_messages(chat, message_indices, message_costs):
    """Deletes messages from the chat history and updates message costs.

    Args:
        chat (ChatSession): The active chat session object.
        message_indices (list): A list of indices for messages to be deleted.
        message_costs (list): A list of dictionaries containing message token counts and costs.
    """

    # Prevent deletion of system instructions by filtering out index 0. TODO: !ONLY IF TOOLS ARE ADDED!, this may need to be adjusted.
    message_indices = [index for index in message_indices if index != 0]

    for index in sorted(message_indices, reverse=True): # Iterate through indices in reverse order to avoid shifting issues
        try:
            del chat.history[index] # Attempt to delete the message at the specified index
            del message_costs[index] # Delete the corresponding cost information
            print(f"Message at index {index} deleted.") # Confirmation message
        except IndexError:
            print(f"Invalid message index: {index}") # Error message for invalid index

def update_files_in_context(chat, all_files, message_costs, total_input_tokens, total_output_tokens):
    """Allows the user to update files included in the context.

    Args:
        chat (ChatSession): The active chat session object.
        all_files (list): A list of all files available for selection.
        message_costs (list): A list of dictionaries containing message token counts and costs.
        total_input_tokens (int): The total number of input tokens used in the session.

    Returns:
        GenerateContentResponse: The model's response after updating the context.
    """
    selected_files = select_files(all_files) # Allow the user to select files
    if selected_files: # Proceed if files were selected
        update_message = generate_context_message(selected_files) # Generate an updated context message with the selected files
        # Add user input to the update message
        update_message += input("\033[96mYou: ") 
        print(f"\nYou: Updating files:\n{update_message}") # Display the updated context message
        response = chat.send_message(update_message) # Send the updated context message to the model

# TODO: fix this similar to how we did in the main function
        input_tokens = response.usage_metadata.prompt_token_count - total_input_tokens - total_output_tokens
        output_tokens = response.usage_metadata.candidates_token_count

        # Store message cost information
        message_costs.append({
            "role": "user",
            "tokens": input_tokens,
            "cost": calculate_cost(input_tokens, INPUT_PRICING),
            "content": update_message
        })
        message_costs.append({
            "role": "model",
            "tokens": output_tokens,
            "cost": calculate_cost(output_tokens, OUTPUT_PRICING),
            "content": response.text
        })
        return response, input_tokens, output_tokens # Return the model's response

def save_chat_history(message_costs, total_session_cost):
    """Asks the user if they want to save the chat history to a file and saves it if they do.

    Args:
        message_costs (list): A list of dictionaries containing message information (role, tokens, cost, content).
        total_session_cost (float): The total cost of the chat session.
    """
    save_history = input("Would you like to save the chat history to a file? (y/N): ")
    if save_history.lower() == 'y':
        # TODO handle bad file name
        file_name = input("Enter a file name for the chat history (e.g., chat_history.json): ")
        # TODO: try/catch and ask again if failed
        with open(file_name, 'w') as f:
            json.dump({"total_cost": total_session_cost, "messages": message_costs}, f, indent=4)
        print(f"Chat history saved to {file_name}")

# TODO: catch force quit and give option to save chat history
def main():
    """Main function to run the Godot Helper application."""
    print("Godot Helper with Gemini API Integration") # Welcome message

    # Display initial instructions and help message
    print(INSTRUCTIONS)
    print(HELP_MSG)

    # Display the currently set pricing information
    print(f"PRICING ($ per 1 million tokens) as of {PRICING_DATE}:\nInput: {INPUT_PRICING['upto_128k']} (up to 128k tokens), {INPUT_PRICING['over_128k']} (over 128k tokens)\nOutput: {OUTPUT_PRICING['upto_128k']} (up to 128k tokens), {OUTPUT_PRICING['over_128k']} (over 128k tokens)")

    # Check if the user needs to set up the .env file, otherwise proceed
    print("\nIf you need to setup your .env file, type 'exit' now and hit enter.")
    print("By continuing, you accept full responsibility for any costs incurred and your usage of this application.")
    print("Press enter to continue.")
    if input() != "":
        return

    # Ask user to select files for context
    print("First, select files from your project directory to provide context.")
    all_files = get_all_files(PROJECT_DIR) # Get a list of all files in the Godot project directory
    selected_files = select_files(all_files) # Allow the user to select specific files for the context
    context_message = generate_context_message(selected_files) # Construct the initial context message
    chat, total_input_tokens, total_output_tokens, message_costs = start_gemini_chat(context_message) # Start the chat session
    
    previous_prompt_token_count = total_input_tokens
    previous_output_token_count = total_output_tokens

    while True: # Main chat loop
        user_message = input(f"\nType \033[36m'help'\033[0m for special commands.\n\033[32mYou: ") # Prompt the user for input
        print("\033[0m")

        if user_message.lower() == "exit": # Exit the application
            total_session_cost = calculate_cost(total_input_tokens, INPUT_PRICING) + calculate_cost(total_output_tokens, OUTPUT_PRICING)
            save_chat_history(message_costs, total_session_cost)  # Offer to save chat history
            break

        elif user_message.lower() == "help": # Display special commands and instructions
            print(HELP_MSG)

        elif user_message.lower() == "view": # View a full message's content
            while True:
                try:
                    message_index = int(input("Enter message index to view: ")) # Prompt for message index
                    print(f"Message {message_index}: {message_costs[message_index]['content']}") # Display the full message content
                    break # Exit the view loop
                except (ValueError, IndexError):
                    print("Invalid message index. Please try again.")

        elif user_message.lower() == "delete": # Delete messages from history
            while True:
                try:
                    message_indices_str = input("Enter message indices to delete (comma-separated): ") # Prompt for message indices
                    message_indices = [int(x.strip()) for x in message_indices_str.split(",")] # Convert input to a list of integers
                    delete_messages(chat, message_indices, message_costs) # Delete the specified messages
                    break # Exit the deletion loop
                except ValueError:
                    print("Invalid input. Please enter numbers.") # Handle invalid input type

        elif user_message.lower() == "history": # Display chat history
            print("Chat History:\n---")
            for i, message_data in enumerate(message_costs):
                content_preview = message_data['content'][:75] + ' ... ' + message_data['content'][-75:] if len(message_data['content']) > 150 else message_data['content']
                content_preview = content_preview.replace('\n', ' ') 
                cost_to_keep = calculate_cost(message_data['tokens'], INPUT_PRICING, True)  # Use input pricing for both user and model messages and ensure we calculate based off of global token count
                if (message_data['role'] == "system"):
                    print(f"{i}. Tokens: {message_data['tokens']}, Cost to keep: ${cost_to_keep:.5f}\n\033[33mRole: {message_data['role']}, Content: {content_preview}\033[0m\n---")
                elif (message_data['role'] == "user"):
                    print(f"{i}. Tokens: {message_data['tokens']}, Cost to keep: ${cost_to_keep:.5f}\n\033[92mRole: {message_data['role']}, Content: {content_preview}\033[0m\n---")
                else:
                    print(f"{i}. Tokens: {message_data['tokens']}, Cost to keep: ${cost_to_keep:.5f}\n\033[94mRole: {message_data['role']}, Content: {content_preview}\033[0m\n---")

        elif user_message.lower() == "update": # Update files in context
            response, input_tokens, output_tokens = update_files_in_context(chat, all_files, message_costs, total_input_tokens, total_output_tokens) # Update context and get the model's response
            if response is not None:  # Only update if response is successful
                total_input_tokens += input_tokens # Update total input tokens for session cost calculation
                total_output_tokens += output_tokens # Update total output tokens for session cost calculation
                print(f"\n\033[94mGemini: {response.text}\033[0m") # Display the model's response
                print(f"INPUT TOKENS: {response.usage_metadata.prompt_token_count}, INPUT COST: ${calculate_cost(response.usage_metadata.prompt_token_count, INPUT_PRICING):.5f}") # Display token usage and cost
                print(f"OUTPUT TOKENS: {output_tokens}, OUTPUT COST: ${calculate_cost(output_tokens, OUTPUT_PRICING):.5f}")
                print(f"SESSION COST: ${calculate_cost(total_input_tokens, INPUT_PRICING) + calculate_cost(total_output_tokens, OUTPUT_PRICING):.5f}") 

        else: # Send a regular chat message
            response = chat.send_message(user_message) # Send the message and receive the model's response

            input_tokens = response.usage_metadata.prompt_token_count - previous_prompt_token_count - previous_output_token_count
            output_tokens = response.usage_metadata.candidates_token_count
            
            total_input_tokens += input_tokens # Update total input tokens for session cost calculation
            total_output_tokens += output_tokens # Update total output tokens for session cost calculation
            
            # Store message cost information
            message_costs.append({
                "role": "user",
                "tokens": input_tokens, 
                "cost": calculate_cost(input_tokens, INPUT_PRICING),
                "content": user_message
            })
            message_costs.append({
                "role": "model",
                "tokens": output_tokens,
                "cost": calculate_cost(output_tokens, OUTPUT_PRICING),
                "content": response.text
            })

            print(f"\n\033[94mGemini: {response.text}\033[0m") 
            print(f"INPUT TOKENS: {response.usage_metadata.prompt_token_count}, INPUT COST: ${calculate_cost(response.usage_metadata.prompt_token_count, INPUT_PRICING):.5f}") 
            print(f"OUTPUT TOKENS: {output_tokens}, OUTPUT COST: ${calculate_cost(output_tokens, OUTPUT_PRICING):.5f}")
            print(f"SESSION COST: ${calculate_cost(total_input_tokens, INPUT_PRICING) + calculate_cost(total_output_tokens, OUTPUT_PRICING):.5f}") 
            
            # Update previous prompt and output token counts for next calculation
            previous_prompt_token_count = response.usage_metadata.prompt_token_count
            previous_output_token_count = output_tokens

# Run the main function if the script is executed directly
if __name__ == "__main__": 
    main()