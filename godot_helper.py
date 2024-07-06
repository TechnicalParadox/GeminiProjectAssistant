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
GODOT_PROJECT_DIR = os.getenv("PROJECT_DIRECTORY") # Get the Godot project directory from environment variables
MODEL_NAME = "gemini-1.5-pro-latest" # Specify the Gemini Pro model to use
API_KEY = os.getenv("API_KEY") # Get your Google Cloud API key from environment variables

# Gemini Safety Settings - Currently set to allow all content
# For more info on safety settings and thresholds: https://developers.generativeai.google/api/rest/generativelanguage/v1beta2/SafetySetting
NO_SAFETY = {
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE, # No blocking for hate speech
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE, # No blocking for harassment
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE, # No blocking for sexually explicit content
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE # No blocking for dangerous content
}

# Pricing per 1 million tokens (as of November 14, 2023)
INPUT_PRICING = {
    "upto_128k": 3.50, # Price per million tokens for prompts up to 128,000 tokens
    "over_128k": 7.00  # Price per million tokens for prompts larger than 128,000 tokens
}
OUTPUT_PRICING = {
    "upto_128k": 10.50, # Price per million tokens for completions up to 128,000 tokens
    "over_128k": 21.00  # Price per million tokens for completions larger than 128,000 tokens
}

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
    context = "Files and content provided for context:\n\n" # Begin the context message
    for file_path in selected_files: # Iterate through selected files
        content = read_file_content(file_path) # Read the content of the current file
        context += f"{file_path}\n```{content}```\n" # Append the file name and content to the message, using Markdown code blocks for formatting
    return context # Return the constructed context message

def calculate_cost(tokens, pricing):
    """Calculates the cost based on token usage.

    Args:
        tokens (int): The number of tokens used.
        pricing (dict): A dictionary containing the pricing tiers for input or output tokens.

    Returns:
        float: The calculated cost.
    """
    million_tokens = tokens / 1_000_000 # Convert tokens to millions of tokens
    if tokens <= 128_000: # Check if token usage falls within the lower pricing tier
        return million_tokens * pricing['upto_128k'] # Calculate cost using the lower tier pricing
    else: 
        return million_tokens * pricing['over_128k'] # Calculate cost using the higher tier pricing

def start_gemini_chat(context_message):
    """Initializes a chat session with the Gemini model.

    Args:
        context_message (str): The initial context message containing file information.

    Returns:
        tuple: A tuple containing the ChatSession object, total input tokens, and total output tokens.
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

    total_input_tokens = 0 # Initialize counter for total input tokens
    total_output_tokens = 0 # Initialize counter for total output tokens
    # Initialize a list to store message tokens and costs
    message_costs = []

    # Add initial user input to context message
    context_message += f"\nInitial instructions: " + input("You: ")

    # Send the context message directly 
    print("\nCHAT:")
    print(f"\nYou: {context_message}") 
    response = chat.send_message(context_message) # Send the initial context message to the model
    total_input_tokens += response.usage_metadata.prompt_token_count # Increment input token count
    total_output_tokens += response.usage_metadata.candidates_token_count # Increment output token count
    
    # Store message cost information
    message_costs.append({
        "role": "user",
        "tokens": response.usage_metadata.prompt_token_count,
        "cost": calculate_cost(response.usage_metadata.prompt_token_count, INPUT_PRICING),
        "content": context_message
    })
    message_costs.append({
        "role": "model",
        "tokens": response.usage_metadata.candidates_token_count,
        "cost": calculate_cost(response.usage_metadata.candidates_token_count, OUTPUT_PRICING),
        "content": response.text
    })

    print(f"\nGemini: {response.text}") # Display the model's response
    print(f"INPUT TOKENS: {response.usage_metadata.prompt_token_count}, INPUT COST: ${calculate_cost(response.usage_metadata.prompt_token_count, INPUT_PRICING):.4f}") # Display input token count and cost
    print(f"OUTPUT TOKENS: {response.usage_metadata.candidates_token_count}, OUTPUT COST: ${calculate_cost(response.usage_metadata.candidates_token_count, OUTPUT_PRICING):.4f}") # Display output token count and cost
    print(f"SESSION COST: ${calculate_cost(total_input_tokens, INPUT_PRICING) + calculate_cost(total_output_tokens, OUTPUT_PRICING):.4f}")  # Display session cost
    return chat, total_input_tokens, total_output_tokens, message_costs # Return the chat session object and token counts

def delete_messages(chat, message_indices, message_costs):
    """Deletes messages from the chat history and updates message costs.

    Args:
        chat (ChatSession): The active chat session object.
        message_indices (list): A list of indices for messages to be deleted.
        message_costs (list): A list of dictionaries containing message token counts and costs.
    """
    for index in sorted(message_indices, reverse=True): # Iterate through indices in reverse order to avoid shifting issues
        try:
            del chat.history[index] # Attempt to delete the message at the specified index
            del message_costs[index] # Delete the corresponding cost information
            print(f"Message at index {index} deleted.") # Confirmation message
        except IndexError:
            print(f"Invalid message index: {index}") # Error message for invalid index

def update_files_in_context(chat, all_files, message_costs, total_input_tokens):
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
        update_message += input("You: ") 
        print(f"\nYou: Updating files:\n{update_message}") # Display the updated context message
        response = chat.send_message(update_message) # Send the updated context message to the model

        # Store message cost information
        message_costs.append({
            "role": "user",
            "tokens": response.usage_metadata.prompt_token_count - total_input_tokens,
            "cost": calculate_cost(response.usage_metadata.prompt_token_count - total_input_tokens, INPUT_PRICING),
            "content": update_message
        })
        message_costs.append({
            "role": "model",
            "tokens": response.usage_metadata.candidates_token_count,
            "cost": calculate_cost(response.usage_metadata.candidates_token_count, OUTPUT_PRICING),
            "content": response.text
        })
        return response # Return the model's response

def save_chat_history(message_costs, total_session_cost):
    """Asks the user if they want to save the chat history to a file and saves it if they do.

    Args:
        message_costs (list): A list of dictionaries containing message information (role, tokens, cost, content).
        total_session_cost (float): The total cost of the chat session.
    """
    save_history = input("Would you like to save the chat history to a file? (y/N): ")
    if save_history.lower() == 'y':
        file_name = input("Enter a file name for the chat history (e.g., chat_history.json): ")
        with open(file_name, 'w') as f:
            json.dump({"messages": message_costs, "total_cost": total_session_cost}, f, indent=4)
        print(f"Chat history saved to {file_name}")

def main():
    """Main function to run the Godot Helper application."""
    print("Godot Helper - Gemini API Integration") # Welcome message

    all_files = get_all_files(GODOT_PROJECT_DIR) # Get a list of all files in the Godot project directory
    selected_files = select_files(all_files) # Allow the user to select specific files for the context
    context_message = generate_context_message(selected_files) # Construct the initial context message
    chat, total_input_tokens, total_output_tokens, message_costs = start_gemini_chat(context_message) # Start the chat session

    print("Chat session started. Type 'exit', 'delete', 'update', or 'history'.") # Instructions for the user

    while True: # Main chat loop
        user_message = input("\nYou: ") # Prompt the user for input

        if user_message.lower() == "exit": # Exit the application
            total_session_cost = calculate_cost(total_input_tokens, INPUT_PRICING) + calculate_cost(total_output_tokens, OUTPUT_PRICING)
            save_chat_history(message_costs, total_session_cost)  # Offer to save chat history
            break

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
            for i, message_cost in enumerate(message_costs):
                content_preview = message_cost['content'][:75] + ' ... ' + message_cost['content'][-75:] if len(message_cost['content']) > 150 else message_cost['content']
                content_preview = content_preview.replace('\n', ' ')  # Replace newlines with spaces for single-line display
                print(f"{i}. Tokens: {message_cost['tokens']}, Cost to keep: ${message_cost['cost']:.4f}\nRole: {message_cost['role']}, Content: {content_preview}\n---")
                

        elif user_message.lower() == "update": # Update files in context
            response = update_files_in_context(chat, all_files, message_costs, total_input_tokens) # Update context and get the model's response
            if response is not None:  # Only update if response is successful
                total_input_tokens = response.usage_metadata.prompt_token_count # Update total input tokens
                total_output_tokens += response.usage_metadata.candidates_token_count
                print(f"\nGemini: {response.text}") # Display the model's response
                print(f"INPUT TOKENS: {response.usage_metadata.prompt_token_count - total_input_tokens}, INPUT COST: ${calculate_cost(response.usage_metadata.prompt_token_count - total_input_tokens, INPUT_PRICING):.4f}") # Display token usage and cost
                print(f"OUTPUT TOKENS: {response.usage_metadata.candidates_token_count}, OUTPUT COST: ${calculate_cost(response.usage_metadata.candidates_token_count, OUTPUT_PRICING):.4f}")
                print(f"SESSION COST: ${calculate_cost(total_input_tokens, INPUT_PRICING) + calculate_cost(total_output_tokens, OUTPUT_PRICING):.4f}") 

        else: # Send a regular chat message
            response = chat.send_message(user_message) # Send the message and receive the model's response
            
            message_costs.append({
                "role": "user",
                "tokens": response.usage_metadata.prompt_token_count - total_input_tokens - total_output_tokens,
                "cost": calculate_cost(response.usage_metadata.prompt_token_count - total_input_tokens, INPUT_PRICING),
                "content": user_message
            })
            message_costs.append({
                "role": "model",
                "tokens": response.usage_metadata.candidates_token_count,
                "cost": calculate_cost(response.usage_metadata.candidates_token_count, INPUT_PRICING), # even though this is output, when continuing the conversation it will be treated as input. In the history we want the user to see/delete messages based on their input cost.
                "content": response.text
            })
            total_input_tokens += response.usage_metadata.prompt_token_count
            total_output_tokens += response.usage_metadata.candidates_token_count # Update total output tokens
            print(f"\nGemini: {response.text}") # Display the model's response
            print(f"INPUT TOKENS: {response.usage_metadata.prompt_token_count}, INPUT COST: ${calculate_cost(response.usage_metadata.prompt_token_count, INPUT_PRICING):.4f}") # Display token usage and cost
            print(f"OUTPUT TOKENS: {response.usage_metadata.candidates_token_count}, OUTPUT COST: ${calculate_cost(response.usage_metadata.candidates_token_count, OUTPUT_PRICING):.4f}")
            print(f"SESSION COST: ${calculate_cost(total_input_tokens, INPUT_PRICING) + calculate_cost(total_output_tokens, OUTPUT_PRICING):.4f}") 

# Run the main function if the script is executed directly
if __name__ == "__main__": 
    main()