import sys
import os
import json
from print_color import print
import google.generativeai as genai
from dotenv import load_dotenv, set_key
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from google.api_core.exceptions import DeadlineExceeded, InvalidArgument
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QPushButton, QLabel, QVBoxLayout, QLineEdit, QMessageBox, QFileDialog, QTextEdit, QFontDialog, QColorDialog, QInputDialog, QListWidget, QStatusBar
from PyQt6.QtCore import Qt, QSize, QEvent
from PyQt6.QtGui import QFont, QColor, QAction

DEBUG = True  # Set to True to enable debug messages

# Calculate the .env file path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_FILE = os.path.join(SCRIPT_DIR, '.env')

# Load environment variables once at the start
load_dotenv(dotenv_path=ENV_FILE) 
API_KEY = os.getenv('API_KEY')

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

# TODO: Format these and display on startup
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
Available Commands:
'save' - Save the chat history to a file.
'delete' - Delete messages from chat history.
'files' - Add files and their paths to context from project directory.
'history' - Display concise chat history.
'view' - View a full message's content.
'timeout' - Change the response timeout setting for this session.
'exit' - Exit the chat session and give the option to save chat history.
'help' - Display special commands and instructions.

If you enter a command wrong, it will be sent as a message to the API, incurring costs.
'''

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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Gemini Project Assistant")
        self.setGeometry(100, 100, 1200, 800)

        # Center the window on the primary screen
        screen_geometry = QApplication.primaryScreen().availableGeometry() # Get primary screen geometry
        center_point = screen_geometry.center()  # Get the center point
        qtRectangle = self.frameGeometry()
        qtRectangle.moveCenter(center_point)
        self.move(qtRectangle.topLeft())

        # Initialize variables
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.last_input_tokens = 0
        self.last_output_tokens = 0
        self.session_cost = 0.00
        self.timeout = 60
        self.project_dir = None
        self.ignored_extensions = []
        self.chat_history = []  # Stores message content for display
        self.messages = [] # Stores detailed message data (including tokens, cost) - used for saving history
        self.model = None
        self.chat = None
        self.model_name = 'gemini-1.5-pro-latest'
        self.temperature = 1.0
        self.max_output_tokens = 8192
        self.stop_sequences = []
        self.system_instructions = "You are an expert AI programming assistant. Your goals are: 1. Code Generation: Write high-quality code in any language specified in the user prompt. Adhere to best practices (style, maintainability) and user preferences. Generate snippets, functions, classes, or full modules as needed. Adapt to the user's coding style over time. 2. Debugging: Analyze code for errors (syntax, logic, runtime). Provide clear explanations of issues and suggest fixes. Consider context from the entire file or project if provided. 3. Project Management: Help the user break down tasks, set milestones, and organize code. Offer suggestions for project structure and management tools. 4. Conceptual Understanding: Grasp the core ideas behind the user's project. Suggest appropriate design patterns, data structures, or libraries. Explain complex technical concepts in simpler terms. 5. Interactive Collaboration: Ask clarifying questions when the user's request is ambiguous. Propose multiple solutions with explanations. Adapt based on user feedback and preferences. Additional Capabilities: Code Refactoring (if requested). Unit Test Generation (if requested). Code Documentation (if requested). Searching External Resources (if requested). Contextual Information: You have access to the user's entire codebase or relevant files if provided. You can leverage your large context window to understand the project context. Finally: Refrain from using emojis unless otherwise specified. Keep your responses short unless otherwise instructed to do so by the user. You can use HTML formatting in your responses, never use markdown formatting." # default
        self.safety_level = 'medium' # default
        self.safety_settings = MEDIUM_SAFETY
        self.system_message_displayed = False

        # Create UI elements
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        self.create_menu_bar()
        self.create_chat_window()
        self.create_input_area()
        self.create_status_bar()

        # Load system instructions
        self.load_system_instructions()
        self.display_message("Welcome", "Welcome to Gemini Project Assistant!")


        # Load Configuration and API Key
        self.load_config()  
        self.load_api_key()
        self.generation_config = {
            "temperature": self.temperature,
            "max_output_tokens": self.max_output_tokens,
            "stop_sequences": self.stop_sequences
        }

        # Display settings after UI setup
        self.display_loaded_settings()

        # Initialize the model
        self.initialize_model()

    def send_message(self):
        """Sends the user's message to the Gemini model and handles the response."""
        user_input = self.input_box.text()
        self.input_box.clear()

        self.process_user_input(user_input)

    def process_user_input(self, user_input):
        """Processes user input, handling both messages and special commands."""
        message = None  # Reset message to None for each iteration

        match user_input.lower():  # Convert input to lowercase for matching
            case 'exit':  # Exit chat session, give user option to save chat history
                if (
                    QMessageBox.question(
                        self,
                        "Exit",
                        "Are you sure you want to exit? Do you want to save the chat history?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    )
                    == QMessageBox.StandardButton.Yes
                ):
                    self.save_chat_history()
                    QApplication.quit()
            case 'save':  # Save chat history
                self.save_chat_history()
            case 'delete':  # Delete messages from history
                self.delete_messages()
            case 'files':  # Add files to context
                self.add_files_to_context()
            case 'history':  # Display concise chat history
                self.display_chat_history()
            case 'view':  # View a full message's content
                self.view_full_message()
            case 'timeout':  # Adjust the timeout setting
                timeout, ok = QInputDialog.getInt(self, "Timeout", "Enter new timeout (seconds):", self.timeout, step=10)
                if ok:
                    self.timeout = timeout
                    self.display_message("Timeout", f'Timeout set to {self.timeout} seconds.')
            case 'help':  # Display help message
                self.display_message("Help", HELP_MSG)
            case _:  # Send user input to the model
                message = user_input

        if message:
            self.send_message_to_model(message, self.timeout)

    def delete_messages(self):
        """Deletes messages from history and updates the model's context."""
        message_indices_str, ok = QInputDialog.getText(
            self,
            "Delete Messages",
            "Enter the indices of messages to delete (comma-separated):",
        )
        if DEBUG:
            print("DEBUG: User entered message indices:", message_indices_str, tag="DEBUG", tag_color="cyan", color="white")
        if ok and message_indices_str:
            try:
                message_indices = [
                    int(x.strip()) for x in message_indices_str.split(",")
                ]
                if DEBUG:
                    print("DEBUG: Message Indices (as integers):", message_indices, tag="DEBUG", tag_color="cyan", color="white")
                message_indices.sort(reverse=True)  # Delete in reverse order
                if DEBUG:
                    print("DEBUG: Sorted message Indices:", message_indices, tag="DEBUG", tag_color="cyan", color="white")
                for i in message_indices:
                    # Adjust for zero-based indexing and user-visible indexing (starting from 1)
                    python_index = i - 1
                    if 0 <= python_index < len(self.messages):  
                        if DEBUG:
                            print(f"DEBUG: Deleting message at index: {i} (python_index: {python_index})", tag="DEBUG", tag_color="cyan", color="white")
                            print(f"DEBUG: all_messages before deletion: {self.messages}", tag="DEBUG", tag_color="cyan", color="white")
                        deleted_message = self.messages.pop(python_index)
                        if DEBUG:
                            print(f"DEBUG: Deleted message: {deleted_message}", tag="DEBUG", tag_color="cyan", color="white")
                            print(f"DEBUG: all_messages after deletion: {self.messages}", tag="DEBUG", tag_color="cyan", color="white")
                        if DEBUG:
                            print(f"DEBUG: chat.history before deletion: {self.chat.history}", tag="DEBUG", tag_color="cyan", color="white")
                        del self.chat.history[python_index]
                        if DEBUG:
                            print(f"DEBUG: chat.history after deletion: {self.chat.history}", tag="DEBUG", tag_color="cyan", color="white")

                    else:
                        self.display_message("Error", f"Invalid message index: {i}")
                # Refresh the chat history after deleting
                self.chat_history = [f"<span style='color:#00ff00;'><strong>You:</strong></span> {m['content']}<br>" if m['role'] == "User" else f"<span style='color:cyan;'><strong>Model:</strong></span> {m['content']}<br>" for m in self.messages] 
                self.update_chat_window()
            except ValueError:
                self.display_message("Error", "Invalid input. Enter message indices as comma-separated numbers.")
    
    def add_files_to_context(self):
        """Adds files to the chat context."""
        if self.project_dir is None:
            self.display_message("Error", 'Project directory not set in config file. Cannot add files.')
            return

        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        file_dialog.setDirectory(self.project_dir)  

        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            context = "\n".join(
                [
                    f"File and content provided for context: \n{file}\n```\n{open(file, 'r', errors='ignore').read()}\n```"
                    for file in selected_files
                ]
            )
            self.display_message("Files", context)  

            # Get additional user input after adding files
            user_message, ok = QInputDialog.getText(
                self, "Input", "Enter your message:"
            )
            if ok and user_message:
                self.send_message_to_model(context + "\nUser Input: " + user_message, self.timeout)

    def display_chat_history(self):
        """Displays a concise chat history in a larger message box."""
        history_text = []
        for i, m in enumerate(self.messages):
            # Calculate message content preview, removing newlines
            content_preview = m['content'][:75] + ' ... ' + m['content'][-75:] if len(m['content']) > 150 else m['content']
            content_preview = content_preview.replace('\n', ' ')
            
            # Apply color based on message role 
            color = "#00ff00" if m['role'] == "User" else "cyan"
            history_text.append(f"{i+1}. <span style='color:{color};'>{m['role']}:</span> {content_preview}")

        if DEBUG:
            print('Model Chat History:', self.chat.history, tag='Debug', tag_color='cyan', color='white')

        message_box = QMessageBox(self)
        message_box.setWindowTitle("Chat History")
        message_box.setText("<br>".join(history_text))  # Join with <br> for line breaks
        message_box.setStyleSheet("QLabel{min-width: 800px;}")
        message_box.exec()

    def view_full_message(self):
        """Allows the user to view the full content of a message."""
        message_index, ok = QInputDialog.getInt(
            self, "View Message", "Enter message index:", 1, 1, len(self.chat_history), 1
        )
        if ok:
            try:
                message = self.chat_history[message_index - 1]
                QMessageBox.information(self, "Message Content", message)
            except IndexError:
                self.display_message("Error", "Invalid message index.")
    
    def send_message_to_model(self, message, timeout):
        """Sends the message to the Gemini model and handles the response."""
        try:
            # Calculate token counts for the user's message and subtract system instructions tokens
            total_message_tokens = self.model.count_tokens([{'role': 'user', 'parts':[message]}]).total_tokens
            input_tokens = total_message_tokens - self.system_instruction_tokens

            # Add messages to history for display and saving BEFORE sending the request
            self.chat_history.append(f"<span style='color:#00ff00;'><strong>You:</strong></span> {message}<br>")
            self.messages.append({"role": "User", "content": message, "tokens": input_tokens}) # Store message in all_messages
            self.update_chat_window()

            if DEBUG:
                print("Sending message to model:", message, tag='Debug', tag_color='cyan', color='white')

            # Send the message to the model. Overrides settings in case they are changed during the session
            response = self.chat.send_message(
                message,
                request_options={'timeout': timeout},
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
                )

            if DEBUG:
                print("Full response from model:", response, tag='Debug', tag_color='cyan', color='white') 

            # Update token counts
            self.last_input_tokens = response.usage_metadata.prompt_token_count
            self.last_output_tokens = response.usage_metadata.candidates_token_count
            self.total_input_tokens += input_tokens # Only add the input tokens without system instructions
            self.total_output_tokens += self.last_output_tokens

            # Add Model response to chat history
            self.chat_history.append(f"<span style='color:cyan;'><strong>Model:</strong></span> {response.text}<br>") 
            self.messages.append({"role": "Model", "content": response.text, "tokens": self.last_output_tokens}) # Store message in all_messages
            self.update_chat_window()

            # Update session cost 
            self.session_cost = calculate_cost(self.total_input_tokens, INPUT_PRICING) + calculate_cost(self.total_output_tokens, OUTPUT_PRICING)

            self.update_status_bar()

            return self.last_input_tokens, self.last_output_tokens, response.text

        except Exception as e:
            if DEBUG:
                print(f"DEBUG: Error sending message: {e}")
            # Handle other exceptions appropriately
            raise e

    def display_message(self, sender, message):
        """Displays a message in the chat window with appropriate formatting."""
        color = ""
        match sender:
            case "You":
                color = "#00ff00" # Code green
            case "Model":
                color = "#00ffff" # Cyan
            case "Error":
                color = "#ff0000" # Red
            case "Warning":
                color = "#ff9900" # Orange
            case _:
                color = "#ff00ff" # Magenta
                
        self.chat_window.append(f"<strong style='color:{color};'>{sender}:</strong> {message}<br>")

    def load_chat_history(self):
        """Opens a dialog to load chat history from a file."""
         # Display a warning message box
        warning_msg = QMessageBox(self)
        warning_msg.setIcon(QMessageBox.Icon.Warning)
        warning_msg.setWindowTitle("File Type Warning")
        warning_msg.setText("Warning: Only select '.json' files generated by this application!")
        warning_msg.setStandardButtons(QMessageBox.StandardButton.Ok)  # Only an "OK" button
        warning_msg.exec()

        file_dialog = QFileDialog()
        file_dialog.setNameFilter("Chat History (*.json)")
        if file_dialog.exec():
            filename = file_dialog.selectedFiles()[0]
            try:
                with open(filename, 'r') as f:
                    data = json.load(f)

                    # Load messages and add to chat.history and all_messages
                    for message_data in data.get("chat_history", []):
                        role = message_data['role']
                        content = message_data['content']
                        tokens = message_data.get('tokens', 0) # Get tokens, default to 0 if not present in older files
                        self.messages.append({"role": role, "content": content, "tokens": tokens})
                        self.chat_history.append(f"<span style='color:#00ff00;'><strong>You:</strong></span> {content}<br>" if role == "User" else f"<span style='color:cyan;'><strong>Model:</strong></span> {content}<br>")
                        self.chat.history.append({'parts': [{'text': content}], 'role': role.lower()})
                    self.update_chat_window()
                    self.update_status_bar()
                    self.display_message("System", "Chat history loaded successfully.")
            except Exception as e:
                self.display_message("Error", f"Error loading chat history: {e}")

    def save_chat_history(self):
        # Display an information message box about file formats
        format_info_msg = QMessageBox(self)
        format_info_msg.setIcon(QMessageBox.Icon.Information)
        format_info_msg.setWindowTitle("Save Format Information")
        format_info_msg.setText("You can save in '.json', '.txt', '.md', or '.csv' formats, "
                                "but this application can only load '.json' files.")
        format_info_msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        format_info_msg.exec()  # Wait for the user to acknowledge

        """Opens a dialog to save chat history to a file."""
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("Chat History (*.json *.txt *.md *.csv)")  # Allow multiple file types
        file_dialog.setDefaultSuffix(".json")  # Set default to JSON
        file_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)

        if file_dialog.exec():
            filename = file_dialog.selectedFiles()[0]

            # Get the chosen file format based on the file extension
            file_extension = os.path.splitext(filename)[1].lower()

            try:
                with open(filename, "w") as f:
                    match file_extension:
                        case ".json":
                            data = {
                                "total_session_cost": self.session_cost,
                                "system_instruction": {
                                    "content": self.system_instructions,
                                    "tokens": self.system_instruction_tokens,
                                    "cost": calculate_cost(self.system_instruction_tokens, INPUT_PRICING) # Calculate the cost of the system instructions
                                },
                                "chat_history": self.messages
                            }
                            json.dump(data, f, indent=4)
                        case ".txt":
                            f.write(f"Total session cost: ${self.session_cost:.5f}\n\n")
                            f.write(f"0. System Instructions, {self.system_instruction_tokens} tokens - {self.system_instructions}\n") # System instructions at index 0
                            for i, m in enumerate(self.messages):
                                f.write(f"{i+1}. {m['role']}, {m['tokens']} tokens - {m['content']}\n")
                        case ".md":
                            f.write(f"# Total session cost: ${self.session_cost:.5f}\n\n")
                            f.write("---\n")
                            f.write(f"### 0. System Instructions, {self.system_instruction_tokens} tokens\n")
                            f.write(f"{self.system_instructions}\n\n")
                            f.write("---\n")
                            f.write("# Chat History\n")
                            for i, m in enumerate(self.messages):
                                f.write(f"### {i+1}. {m['role']}, {m['tokens']} tokens\n")
                                f.write(f"{m['content']}\n\n")
                                f.write("---\n")
                        case ".csv":
                            f.write(f'Session Cost:,{self.session_cost:.5f}\n')
                            f.write("Role,Tokens,Content\n")
                            f.write(f"System Instructions,{self.system_instruction_tokens},\"{self.system_instructions}\"\n") # System instructions on the first line
                            for m in self.messages:
                                f.write(f"{m['role']},{m['tokens']},\"{m['content']}\"\n") 
                        case _:
                            raise ValueError("Invalid file format")

                self.display_message("System", f"Chat history saved to {filename}")
            except Exception as e:
                self.display_message("Error", f"Error saving chat history: {e}")

    def create_menu_bar(self):
        """Creates the menu bar for the application."""
        menu_bar = self.menuBar()

        # File Menu
        file_menu = menu_bar.addMenu("File")

        open_action = QAction("Load History Into Current Session", self)
        open_action.triggered.connect(self.load_chat_history)
        file_menu.addAction(open_action)

        save_action = QAction("Save Chat History", self)
        save_action.triggered.connect(self.save_chat_history)
        file_menu.addAction(save_action)

        # Settings Menu
        settings_menu = menu_bar.addMenu("Settings")

        api_key_action = QAction("Set API Key", self)
        api_key_action.triggered.connect(self.set_api_key)
        settings_menu.addAction(api_key_action)

        config_action = QAction("Configuration", self)
        config_action.triggered.connect(self.configure_settings)
        settings_menu.addAction(config_action)

        # Help Menu
        help_menu = menu_bar.addMenu("Help")
        help_action = QAction("Show Help", self)
        help_action.triggered.connect(lambda: self.display_message("Help", HELP_MSG))
        help_menu.addAction(help_action)

    def create_chat_window(self):
        """Creates the chat window area."""
        self.chat_window = QTextEdit()
        self.chat_window.setReadOnly(True)
        self.layout.addWidget(self.chat_window)

    def create_input_area(self):
        """Creates the input area for user messages."""
        self.input_box = QLineEdit()
        self.input_box.returnPressed.connect(self.send_message)
        self.layout.addWidget(self.input_box)

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        self.layout.addWidget(self.send_button)

    def create_status_bar(self):
        """Creates the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.update_status_bar()

    def load_api_key(self):
        """Loads the API key from the .env file. If not found,
        it prompts the user to set it.
        """
        global API_KEY
        if not API_KEY:
            self.set_api_key()  # Prompt for API key if not found
        else:
            self.display_message('API Key', 'API Key loaded from .env')

    def set_api_key(self):
        """Prompts the user to enter and save their API key, with a warning
        if an API key is already present in the .env file.
        """
        global API_KEY

        # Check if an API key is already set in the .env file
        load_dotenv(dotenv_path=ENV_FILE)
        existing_api_key = os.getenv("API_KEY")

        if existing_api_key and not self.api_key_invalid:
            # Warn the user about overwriting the existing API key
            warning_message = (
                "An API key is already set in the '.env' file.\n"
                "Entering a new key will overwrite the existing one.\n"
                "You will need to restart the application for the changes to take effect.\n\n"
                "Do you want to continue?"
            )

            reply = QMessageBox.question(
                self,
                "API Key Already Set",
                warning_message,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,  # Set default to 'No'
            )

            if reply == QMessageBox.StandardButton.No:
                return  # Don't proceed with setting a new key

        api_key, ok = QInputDialog.getText(
            self,
            "API Key",
            "Enter your Google Gemini API Key (https://aistudio.google.com/app/u/1/apikey):",
        )
        if ok and api_key:
            API_KEY = api_key
            set_key(ENV_FILE, "API_KEY", API_KEY)
            self.display_message(
                "API Key", "API Key set successfully. You may have to restart the application."
            )
        elif not ok:
            self.display_message(
                "API Key", "API Key not set. Using the existing key from .env."
            )
    
    def configure_settings(self):
        """Allows the user to configure application settings."""
        pass  # TODO: Implement this

    def load_system_instructions(self):
        """Loads and displays the system instructions."""
        if self.model and not self.system_message_displayed:
            system_instructions = self.model.system_instruction # TODO: Why is .system_instruction whited out in code like it's not a valid variable
            si_tokens = self.model.count_tokens(" ").total_tokens
            self.display_message("System Instructions", system_instructions)
            self.display_message("Tokens", si_tokens)
            self.display_message("Cost", f"${calculate_cost(si_tokens, INPUT_PRICING):.5f}")
            self.system_message_displayed = True # TODO: Only needs to show again if they're changed while running

    def update_chat_window(self):
        """Updates the chat window with the current chat history."""
        self.chat_window.setHtml("\n".join(self.chat_history)) # TODO: Ensure the entire history isn't repeatedly added each time since we aren't clearing

    def update_status_bar(self):
        """Updates the status bar with session information."""
        last_message_input_cost = calculate_cost(self.last_input_tokens, INPUT_PRICING)
        last_message_output_cost = calculate_cost(self.last_output_tokens, OUTPUT_PRICING)
        message = ( # TODO: Use a permanent widget for this, color code
            f"Session Cost: ${self.session_cost:.5f} | "
            f"Last Message: Input: {self.last_input_tokens} tokens, ${last_message_input_cost:.5f}, "
            f"Output: {self.last_output_tokens} tokens, ${last_message_output_cost:.5f}"
        )
        self.status_bar.showMessage(message)

    def load_config(self):
        """Loads configuration settings from a JSON file."""
        config_file = os.path.join(SCRIPT_DIR, 'config.json')

        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                if DEBUG:
                    print("Configuration loaded from:", config_file, tag="DEBUG", tag_color="cyan", color="white")
                    print("Configuration:", json.dumps(config, indent=4), tag="DEBUG", tag_color="cyan", color="white") # Pretty-print config
                # Load settings from config file
                self.model_name = config.get('model', self.model_name)
                self.system_instructions = config.get('system_instructions', self.system_instructions)
                self.safety_level = config.get('safety', self.safety_level)
                self.timeout = config.get('timeout', self.timeout)
                self.project_dir = config.get('project_directory', self.project_dir)
                self.ignored_extensions = config.get('ignored_extensions', self.ignored_extensions)
                self.temperature = config.get('temperature', self.temperature)
                self.max_output_tokens = config.get('max_output_tokens', self.max_output_tokens)
                self.stop_sequences = config.get('stop_sequences', self.stop_sequences)
                # Set safety settings based on loaded level
                match self.safety_level: 
                    case "none":
                        self.safety_settings = NO_SAFETY
                    case "low":
                        self.safety_settings = LOW_SAFETY
                    case "medium":
                        self.safety_settings = MEDIUM_SAFETY
                    case "high":
                        self.safety_settings = HIGH_SAFETY
                    case _: 
                        self.safety_settings = MEDIUM_SAFETY

        except FileNotFoundError:
            if DEBUG:
                print("Configuration file not found:", config_file, tag="DEBUG", tag_color="cyan", color="white")
            self.display_message("Warning", f"Configuration file not found: {config_file}")
        except json.JSONDecodeError:
            self.display_message("Error", f"Error parsing configuration file: {config_file}")
        except Exception as e:
            self.display_message("Error", f"An error occurred loading configuration: {e}")

    def initialize_model(self):
        """Initializes the Gemini model with the loaded settings, 
        handling InvalidArgument exceptions for invalid API keys.
        """
        global API_KEY
        try:
            genai.configure(api_key=API_KEY) 

            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings,
                system_instruction=self.system_instructions,
            )

            self.chat = self.model.start_chat()
            self.system_instruction_tokens = self.model.count_tokens(" ").total_tokens

        except InvalidArgument as e:
            if "API key not valid" in str(e):
                reply = QMessageBox.critical(
                    self,
                    "Invalid API Key",
                    "The API key you provided is invalid.\n"
                    "Would you like to try entering a new one or quit the application?",
                    QMessageBox.StandardButton.Retry | QMessageBox.StandardButton.Close,
                    QMessageBox.StandardButton.Retry  # Set Retry as the default button
                )

                if reply == QMessageBox.StandardButton.Retry:
                    self.api_key_invalid = True
                    self.set_api_key()  # Prompt the user to enter a new API key
                    self.initialize_model() # Retry initializing the model after setting a new key
                else:
                    sys.exit()  # Close the application if the user chooses to quit
            else:
                self.display_message("Error", f"An error occurred: {e}")
                raise e # Re-raise the exception for other InvalidArgument errors


    def display_loaded_settings(self):
        """Displays the loaded settings in the chat window."""
        if DEBUG:
            print("Model:", self.model_name, tag="DEBUG", tag_color="cyan", color="white")
            print("System Instructions:", self.system_instructions, tag="DEBUG", tag_color="cyan", color="white")
            print("Safety Level:", self.safety_level, tag="DEBUG", tag_color="cyan", color="white")
            print("Timeout:", self.timeout, tag="DEBUG", tag_color="cyan", color="white")
            print("Project Directory:", self.project_dir, tag="DEBUG", tag_color="cyan", color="white")
            print("Ignored Extensions:", self.ignored_extensions, tag="DEBUG", tag_color="cyan", color="white")
            print("Temperature:", self.temperature, tag="DEBUG", tag_color="cyan", color="white")
            print("Max Output Tokens:", self.max_output_tokens, tag="DEBUG", tag_color="cyan", color="white")
            print("Stop Sequences:", self.stop_sequences, tag="DEBUG", tag_color="cyan", color="white")

        self.display_message("Using Model", self.model_name)
        self.display_message("System Instructions", self.system_instructions)
        self.display_message("Safety Level", self.safety_level)
        self.display_message("Timeout", self.timeout)
        self.display_message("Project Directory", self.project_dir)
        self.display_message("Ignored Extensions", self.ignored_extensions)
        self.display_message("Temperature", self.temperature)
        self.display_message("Max Output Tokens", self.max_output_tokens)
        self.display_message("Stop Sequences", self.stop_sequences)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())