import os
import json
import google.generativeai as genai
from google.generativeai import GenerativeModel, ChatSession
from dotenv import load_dotenv
from google.generativeai.types import HarmCategory, HarmBlockThreshold

load_dotenv()

# Configuration
GODOT_PROJECT_DIR = r"D:\Godot_v4.2.2-stable_win64.exe\projects\SpaceRoguelikeV1"
MODEL_NAME = "gemini-1.5-pro-latest"
API_KEY = os.getenv("API_KEY")

# Gemini Safety Settings
NO_SAFETY = {
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE
}

def get_all_files(directory):
    """Gets a list of all files, ignoring hidden items and specified types."""
    ignored_extensions = ['.tmp', '.svg', '.png', '.ttf', '.import']
    file_list = []
    for root, dirs, files in os.walk(directory):
        dirs[:] = [d for d in dirs if not d.startswith('.')] 
        for file in files:
            if not any(file.endswith(ext) for ext in ignored_extensions) and not file.startswith('.'):
                file_list.append(os.path.join(root, file))
    return file_list

def select_files(file_list):
    """Lets the user select files by number or extension."""
    selected_files = []
    for i, file in enumerate(file_list):
        print(f"{i + 1}. {file}")

    while True:
        choices = input("Enter file numbers, extensions (e.g., '.gd, .tscn'), 'all', or 'none' (comma-separated): ")
        choices = [choice.strip() for choice in choices.split(',')]

        try:
            for choice in choices:
                if choice.lower() == 'all':
                    selected_files = file_list
                    break 
                elif choice.lower() == 'none':
                    selected_files = []
                    break 
                elif choice.startswith("."): 
                    selected_files.extend([f for f in file_list if f.endswith(choice)])
                else:  
                    index = int(choice) - 1
                    selected_files.append(file_list[index])
            break 
        except (ValueError, IndexError):
            print("Invalid input. Please try again.")

    return selected_files

def read_file_content(file_path):
    """Reads the content of a file."""
    with open(file_path, "r") as f:
        return f.read()

def generate_context_message(selected_files):
    """Generates a context message for Gemini from selected files."""
    context = "Files and content provided for context:\n\n"
    for file_path in selected_files:
        content = read_file_content(file_path)
        context += f"{file_path}\n```{content}```\n"
    return context

def start_gemini_chat(context_message):
    """Starts a chat session with Gemini and provides system instructions."""
    genai.configure(api_key=API_KEY)

    system_instructions = """
    You are an expert Godot game developer. You are helping me with my Godot project, 'SpaceRoguelikeV1'. 
    I have provided you with the code for some of my scenes and scripts.

    - Prioritize Godot-specific advice and code examples.
    - Refer to the provided context when asked about a file or node. 
    - Ask clarifying questions if you need more information.
    """

    model = genai.GenerativeModel(model_name=MODEL_NAME, 
                                  safety_settings=NO_SAFETY, 
                                  system_instruction=system_instructions)  
    chat = model.start_chat()

    # Add initial user input to context message
    context_message += f"\nInitial instructions: " + input("You: ")

    # Send the context message directly 
    print("\nCHAT:")
    print(f"\nYou: {context_message}")
    response = chat.send_message(context_message)
    '''EXAMPLE RESPONSE:
        GenerateContentResponse(
        done=True,
        iterator=None,
        result=protos.GenerateContentResponse({
        "candidates": [
            {
            "content": {
                "parts": [
                {
                    "text": "It seems like you're outputting debug information about a player in your game. \n\nTo give you tailored help, could you provide me with the code for your `Player.gd` script, or whichever script is responsible for printing this debug info? Knowing how you're currently handling player movement and outputting this data will allow me to provide more specific guidance. \n"
                }
                ],
                "role": "model"
            },
            "finish_reason": "STOP",
            "index": 0,
            "safety_ratings": [
                {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "probability": "NEGLIGIBLE"
                },
                {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "probability": "NEGLIGIBLE"
                },
                {
                "category": "HARM_CATEGORY_HARASSMENT",
                "probability": "NEGLIGIBLE"
                },
                {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "probability": "NEGLIGIBLE"
                }
            ]
            }
        ],
        "usage_metadata": {
            "prompt_token_count": 5549,
            "candidates_token_count": 75,
            "total_token_count": 5624
        }
        }),
    )'''
    print(f"\nGemini: {response.text}\nTOKENS USED: {response.usage_metadata.total_token_count}")
    return chat

def delete_messages(chat, message_indices):
    """Deletes messages from the chat history."""
    for index in sorted(message_indices, reverse=True):
        try:
            del chat.history[index] 
            print(f"Message at index {index} deleted.")
        except IndexError:
            print(f"Invalid message index: {index}")

def update_files_in_context(chat, all_files):
    """Allows the user to update files in the chat context."""
    selected_files = select_files(all_files)
    if selected_files:
        update_message = generate_context_message(selected_files)
        # Add user input to the update message
        update_message += input("You: ")
        print(f"\nYou: Updating files:\n{update_message}")
        response = chat.send_message(update_message)
        return response

def main():
    """Main function to run the Godot Helper."""
    print("Godot Helper - Gemini API Integration")

    all_files = get_all_files(GODOT_PROJECT_DIR)
    selected_files = select_files(all_files)
    context_message = generate_context_message(selected_files)
    chat = start_gemini_chat(context_message)

    print("Chat session started. Type 'exit', 'delete', update, or 'history'.")

    while True:
        user_message = input("\nYou: ")
        if user_message.lower() == "exit":
            break
        elif user_message.lower() == "delete":
            while True:
                try:
                    message_indices_str = input("Enter message indices to delete (comma-separated): ")
                    message_indices = [int(x.strip()) for x in message_indices_str.split(",")]
                    delete_messages(chat, message_indices)
                    break
                except ValueError:
                    print("Invalid input. Please enter numbers.")
        elif user_message.lower() == "history": 
            print("Chat History:")
            for i, message in enumerate(chat.history):
                print(f"{i}. Role: {message.role}, Content: {message.parts[0].text}\n---\n") 
        elif user_message.lower() == "update": # New command to update files
            response = update_files_in_context(chat, all_files)
            print(f"\nGemini: {response.text}\nTOKENS USED: {response.usage_metadata.total_token_count}")
            # Send updated files and input to Gemini API

        else:
            response = chat.send_message(user_message)
            print(f"\nGemini: {response.text}\nTOKENS USED: {response.usage_metadata.total_token_count}")

if __name__ == "__main__":
    main()