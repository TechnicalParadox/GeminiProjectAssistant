import sys
import os
import json
import asyncio
from print_color import print
import google.generativeai as genai
from dotenv import load_dotenv, set_key
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from google.api_core.exceptions import DeadlineExceeded, InvalidArgument
from PyQt6.QtWidgets import ( QApplication, QMainWindow, QProgressBar, QWidget, QPushButton, QScrollArea, QLabel, QVBoxLayout, QLineEdit, QMessageBox, QFileDialog, QTextEdit,
                              QFontDialog, QColorDialog, QInputDialog, QListWidget, QStatusBar, QHBoxLayout, QComboBox, QSpinBox, QDoubleSpinBox, QDialog
                            )
from PyQt6.QtCore import Qt, QSize, QEvent, QTimer, QThread, pyqtSignal
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

# Gemini 1.5 Pro Latest Pricing per 1 million tokens (as of July 15, 2024)
G1_5_PRO_PRICING_DATE = '2024-07-15'
G1_5_PRO_PRICING_MODEL = 'gemini-1.5-pro-latest'
G1_5_PRO_INPUT_PRICING = {
    "upto_128k": 3.50, # Price per million tokens for prompts up to 128,000 tokens
    "over_128k": 7.00 # Price per million tokens for prompts over 128,000 tokens
}
G1_5_PRO_OUTPUT_PRICING = {
    "upto_128k": 10.50, # Price per million tokens for outputs up to 128,000 tokens
    "over_128k": 21.00 # Price per million tokens for outputs over 128,000 tokens
}

# Gemini 1.5 Flash Latest Pricing per 1 million tokens (as of July 15, 2024)
G1_5_FLASH_PRICING_DATE = '2024-07-15'
G1_5_FLASH_PRICING_MODEL = 'gemini-1.5-flash-latest'
G1_5_FLASH_INPUT_PRICING = {
    "upto_128k": 0.35, # Price per million tokens for prompts up to 128,000 tokens
    "over_128k": 0.70 # Price per million tokens for prompts over 128,000 tokens
}
G1_5_FLASH_OUTPUT_PRICING = {
    "upto_128k": 1.05, # Price per million tokens for outputs up to 128,000 tokens
    "over_128k": 2.10 # Price per million tokens for outputs over 128,000 tokens
}

PRICING_DATE = None
PRICING_MODEL = None
INPUT_PRICING = None
OUTPUT_PRICING = None

INSTRUCTIONS = '''<br>
- Converse with the LLM model to get help with your project. Ex. 'Help me debug this script.', 'Complete the TODOs in this file.', 'What can I add to improve this project?', etc.<br>
- Cost will be shown for each message and the total cost of the session will be displayed.<br>
- You can provide context by selecting files from your project directory.<br>
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

SI_TOKENS = 0

def calculate_cost(tokens, pricing, messages):
    """Calculates the cost based on token usage.

    Args:
        tokens (int): The number of tokens used.
        pricing (dict): A dictionary containing the pricing tiers for input or output tokens.

    Returns:
        float: The calculated cost.
    """
    million_tokens = tokens / 1_000_000 # Convert tokens to millions of tokens

    # Calculate based on total input tokens
    total_tokens = 0
    total_tokens += SI_TOKENS
    for m in messages:
        total_tokens += m['tokens']
    
    if total_tokens <= 128_000: # Check if token usage falls within the lower pricing tier
        return million_tokens * pricing['upto_128k'] # Calculate cost using the lower tier pricing
    else: 
        return million_tokens * pricing['over_128k'] # Calculate cost using the higher tier pricing

class MainWindow(QMainWindow):
    response_receieved = pyqtSignal(object, int) # Signal to indicate response received

    def __init__(self):
        super().__init__()

        self.loop = asyncio.new_event_loop() # Create the event loop
        asyncio.set_event_loop(self.loop)

        self.request_in_progress = False # Flag to track ongoing requests

        self.response_receieved.connect(self.update_ui_with_response) # Connect signal to slot

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
        self.system_instructions = "You are an expert AI programming assistant specializing in: 1. Code Generation (high-quality, well-formatted code in any language, following best practices and user's style, producing snippets, functions, classes, or modules as needed, adapting to user's style); 2. Debugging (analyzing code for errors, providing clear explanations and fixes, considering broader context); 3. Project Management (helping with task breakdown, milestones, code organization, suggesting structures and tools); 4. Conceptual Understanding (grasping core ideas, suggesting patterns, structures, libraries, explaining complex concepts); 5. Interactive Collaboration (asking clarifying questions, proposing multiple solutions with explanations, adapting to feedback). Additional Capabilities (on request): Code Refactoring, Unit Test Generation, Code Documentation, External Resource Search. Formatting: You should not output newlines at the start or end of your response. Context: Access relevant code files and project context. Conciseness: Keep responses short, avoid emojis unless specifically requested." # default
        self.safety_level = 'medium' # default
        self.safety_settings = MEDIUM_SAFETY
        self.system_message_displayed = False
        self.api_key_invalid = False

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
        self.display_message("Welcome", "Welcome to Gemini Project Assistant!")

        # Load Configuration and API Key
        self.load_config()
        self.load_api_key()
        self.generation_config = {
            "temperature": self.temperature,
            "max_output_tokens": self.max_output_tokens,
            "stop_sequences": self.stop_sequences
        }

        # Set pricing based on model
        global PRICING_DATE, PRICING_MODEL, INPUT_PRICING, OUTPUT_PRICING
        match self.model_name:
            case 'gemini-1.5-pro-latest':
                PRICING_DATE = G1_5_PRO_PRICING_DATE
                PRICING_MODEL = G1_5_PRO_PRICING_MODEL
                INPUT_PRICING = G1_5_PRO_INPUT_PRICING
                OUTPUT_PRICING = G1_5_PRO_OUTPUT_PRICING
            case 'gemini-1.5-flash-latest':
                PRICING_DATE = G1_5_FLASH_PRICING_DATE
                PRICING_MODEL = G1_5_FLASH_PRICING_MODEL
                INPUT_PRICING = G1_5_FLASH_INPUT_PRICING
                OUTPUT_PRICING = G1_5_FLASH_OUTPUT_PRICING
        
        # Update status bar after pricing loaded
        self.update_status_bar()

        # Display current pricing information
        self.display_message("Pricing", f"Pricing as of {PRICING_DATE} for {PRICING_MODEL}:")
        self.display_message("Input", f"${INPUT_PRICING['upto_128k']} per million tokens (up to 128k tokens), ${INPUT_PRICING['over_128k']} per million tokens (over 128k tokens).")
        self.display_message("Output", f"${OUTPUT_PRICING['upto_128k']} per million tokens (up to 128k tokens), ${OUTPUT_PRICING['over_128k']} per million tokens (over 128k tokens).")


        # Display settings after UI setup
        self.display_loaded_settings()

        # Display Warnings and User Agreement
        self.show_warnings_and_agreement()

        # Initialize the model
        self.initialize_model()
    
    def eventFilter(self, source, event):
        """Filters events for the input box to handle Ctrl+Enter key press."""
        if source is self.input_box and event.type() == QEvent.Type.KeyPress:
            if event.modifiers() == Qt.KeyboardModifier.ControlModifier and event.key() == Qt.Key.Key_Return:
                self.send_message()
                return True
        return super().eventFilter(source, event)

    def closeEvent(self, event):
        """Handles the close event of the main window."""
        reply = QMessageBox.question(
            self,
            "Confirm Exit",
            "Are you sure you want to exit?<br>Do you want to save the chat history?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel  # Set Cancel as the default button
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.save_chat_history()  # Save the chat history if the user chooses Yes
            event.accept()  # Allow the window to close
        elif reply == QMessageBox.StandardButton.No:  # Exit without saving
            event.accept()
        else:
            event.ignore()  # Prevent the window from closing if the user chooses Cancel
        
        # Close the event loop
        self.loop.close()

    def show_warnings_and_agreement(self):
        """Displays warnings and the user agreement, asking for acceptance."""

        # Formatted Warnings with HTML for line breaks 
        warnings_text = WARNINGS.replace('\n', '<br>') 

        # Create a message box for warnings
        warning_msg = QMessageBox(self)
        warning_msg.setIcon(QMessageBox.Icon.Warning)
        warning_msg.setWindowTitle("Important Warnings")
        warning_msg.setText(warnings_text)
        warning_msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        warning_msg.exec()

        # Ask for user agreement
        agreement_text = (
            "By continuing, you take full responsibility for your use of this application.<br><br>"
            "Do you accept the terms and conditions?"
        )
        reply = QMessageBox.question(
            self,
            "User Agreement", 
            agreement_text,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No # Set "No" as the default
        )

        if reply == QMessageBox.StandardButton.No:
            QApplication.quit() # Close the application if the user rejects the agreement

    def send_message(self, files = False):
        """Sends the user's message to the Gemini model and handles the response."""
        if self.request_in_progress:
            QMessageBox.warning(self, "Request in Progress", "A request is already in progress. Please wait for the current request to complete.")
            return
        
        if not files:
            user_input = self.input_box.toPlainText().strip()
            if not user_input: # Check if the input is empty
                return # Do nothing if the input is empty
            
            self.input_box.clear()
        else:
            user_input = self.files_context + self.files_message.strip()

        self.request_in_progress = True

        # Add messages to history for display and saving BEFORE sending the request
        total_message_tokens = self.model.count_tokens([{'role': 'user', 'parts':[user_input]}]).total_tokens
        input_tokens = total_message_tokens - self.system_instruction_tokens
        self.messages.append({"role": "User", "content": user_input, "tokens": input_tokens})  # Store message in messages

        if not files:
            self.display_message("User", user_input)  # Display the user message in the chat history
        else:
            self.display_message("User", self.files_message)
            self.files_message = ""  # Reset files_message for next file uploads
            self.files_context = ""   # Reset files_context for next file uploads

        # Start the progress bar
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(self.timeout * 4)  # Set the maximum value of the progress bar
        self.progress_bar.setFormat("Sending...")  # Set the progress bar text
        self.timer = QTimer(self) # Create a QTimer instance
        self.timer.timeout.connect(self.update_progress_bar) # Connect the timeout signal to the update_progress_bar method
        self.timer.start(250) # Start the timer with a .25 second interval

        thread = QThread(self)
        thread.run = lambda: self.send_message_thread(user_input, self.timeout)
        thread.start()

    def delete_messages(self):
        """Deletes messages from history and updates the model's context."""
        message_indices_str, ok = QInputDialog.getText(
            self,
            "Delete Messages",
            "You may want to save first.<br>Message indicies are shown with the Display Chat History tool.<br>Enter the indices of messages to delete (comma-separated):",
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

                        self.display_message("System", f"Deleted message at index {i}.") # Tell the user the message was deleted
                    else:
                        self.display_message("Error", f"Invalid message index: {i}")
                # Refresh the chat history after deleting
                self.update_chat_window()
            except ValueError:
                self.display_message("Error", "Invalid input. Enter message indices as comma-separated numbers.")
    
    def add_files_to_context(self): # TODO: Add functionality for ignored files and file extensions, add ability to send in project file structure.
        """Adds files to the chat context."""

        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)

        # Set the project directory if available, otherwise default to user's home directory if available
        if self.project_dir:
            file_dialog.setDirectory(self.project_dir)
        else:
            if os.path.exists(os.path.expanduser("~")):
                file_dialog.setDirectory(os.path.expanduser("~"))
            else: # Home directory not found, display error
                self.display_message("Error", "Set the project directory to add files to the context.")

        if file_dialog.exec(): # TODO: Force file dialog to open in front of chat window
            selected_files = file_dialog.selectedFiles()
            messages_to_display = []
            files_context = "Files from the user: "
            for file in selected_files:
                try:
                    with open(file, 'r', errors='ignore') as f:
                        content = f.read()
                        # Get absolute file path
                        file_path = os.path.abspath(file)
                        files_context += ("File: " + file_path + '\n')
                        files_context += ('```' + content + '```\n') # TODO: Should add filepath before content
                        messages_to_display.append(f"{file} was sent to model.")  # Display only the file path
                except Exception as e:
                    self.display_message("Error", f"Error reading file {file}: {e}")
            
            files_context += '\nUser message: '

            # Get additional user input after adding files
            # TODO: Change ok button to say send
            user_message, ok = QInputDialog.getMultiLineText(
                self, "Input", "Enter your message:"
            )
            if ok and user_message:
                for message in messages_to_display:
                    self.display_message('File', message)
                self.files_context = files_context
                self.files_message = user_message
                self.send_message(True)  # Send the user message to the model

    def display_chat_history(self):
        """Displays a concise chat history in a larger message box."""
        history_text = []
        total_cost = 0.0
        for i, m in enumerate(self.messages):
            # Calculate message content preview, removing newlines
            content_preview = m['content'][:75] + ' ... ' + m['content'][-75:] if len(m['content']) > 150 else m['content']
            content_preview = content_preview.replace('\n', ' ')
            input_cost = calculate_cost(m['tokens'], INPUT_PRICING, self.messages) # Calculate cost to keep message
            total_cost += input_cost
            
            # Apply color based on message role 
            color = "#00ff00" if m['role'] == "User" else "cyan"
            history_text.append(f"{i+1}. <span style='color:{color};'>{m['role']}:</span> Tokens: {m['tokens']}, Cost to keep: ${input_cost:.5f} | {content_preview}")
        history_text.append(f"<strong>Total cost to keep: ${total_cost:.5f}</strong>")

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
            self, "View Message", "You can view message indicies with the Display Chat History tool.<br>Enter message index:", 1, 1, len(self.messages), 1 # Use self.messages since this is what the index refers to
        )
        if ok:
            try:
                message = self.messages[message_index - 1] # Adjust for zero-based indexing
                QMessageBox.information(self, "Message Content", message['content']) # Only display the content
            except IndexError:
                self.display_message("Error", "Invalid message index.")
    
    async def send_message_async(self, message, timeout):
        """Sends the message asynchronously to the Gemini model and handles the response."""
        try:
            # Calculate token counts for the user's message and subtract system instructions tokens
            total_message_tokens = self.model.count_tokens([{'role': 'user', 'parts':[message]}]).total_tokens
            input_tokens = total_message_tokens - self.system_instruction_tokens

            if DEBUG:
                print("Sending message to model:", message, tag='Debug', tag_color='cyan', color='white')

            # Send the message asynchronously to the model. Overrides settings in case they are changed during the session
            response = await self.chat.send_message_async(
                message,
                request_options={'timeout': timeout},
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
                )

            if DEBUG:
                print("Full response from model:", response, tag='Debug', tag_color='cyan', color='white') 

            return response, input_tokens

        # Handle exceptions TODO: We need to move QBOX to main thread
        except DeadlineExceeded:
            QMessageBox.warning(self, "Timeout", "The request to the Gemini API timed out. Try increasing the timeout setting or reducing the complexity of your request. You are not charged when this happens. Please note that this message was still added to history, so delete it if you wish.")
            self.chat.history.append({'parts': [{'text': message}], 'role': 'user'})
            if DEBUG:
                print(f"DeadlineExceeded: Request timed out after {timeout} seconds.", tag='Debug', tag_color='red') # Log the timeout
            self.request_in_progress = False # Allow new requests
            self.progress_bar.setFormat("Response Timed Out")
            return None, input_tokens
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")
            if DEBUG:
                print(f"Error sending message: {e}", tag='Debug', tag_color='red')
            self.request_in_progress = False # Allow new requests
            self.progress_bar.setFormat("Response Error")
            return None, input_tokens
    
    def send_message_thread(self, message, timeout):
        """Runs the asynchronous send_message_async in a separate thread."""
        async def run_task():
            response, input_tokens = await self.send_message_async(message, timeout)
            if response:
                self.handle_response(response, input_tokens)
            else:
                self.progress_bar.setValue(self.progress_bar.maximum()) # Indicate completion (timeout or error)
        
        try:
            self.loop.run_until_complete(run_task())
        finally:
            pass
    
    def handle_response(self, response, input_tokens):
        """Handles the response from the model."""
        self.request_in_progress = False # Allow new requests
        self.progress_bar.setFormat("Response Received")
        self.response_receieved.emit(response, input_tokens) # Emit signal with response and input tokens
    
    def update_ui_with_response(self, response, input_tokens):
        """Updates the UI with the response from the model."""
        self.last_input_tokens = response.usage_metadata.prompt_token_count
        self.last_output_tokens = response.usage_metadata.candidates_token_count
        self.total_input_tokens += input_tokens  # Only add the input tokens without system instructions
        self.total_output_tokens += self.last_output_tokens

        # Add Model response to chat history
        self.messages.append({"role": "Model", "content": response.text, "tokens": self.last_output_tokens})  # Store message in all_messages
        self.display_message("Model", response.text)

        # Update session cost
        self.session_cost = calculate_cost(self.total_input_tokens, INPUT_PRICING, self.messages) + calculate_cost(self.total_output_tokens, OUTPUT_PRICING, self.messages)

        self.update_status_bar()

        self.progress_bar.setValue(self.progress_bar.maximum())  # Indicate successful completion

    def display_message(self, sender, message): # TODO: This doesn't auto scroll to bottom when new messages are added
        """Appends the formatted message to the chat_history."""
        color = ""
        match sender:
            case "User":
                color = "green" 
            case "Model":
                color = "cyan"
            case "Error":
                color = "red" 
            case "Warning":
                color = "orange" 
            case _:
                color = "magenta" 

        formatted_message = f"<p style='margin: 0px;'><strong style='color:{color};'>{sender}:</strong> {message}</p><hr style='width: 100%; border-top: 1px;'>"
        self.chat_history.append(formatted_message) # Append to chat_history list
        self.update_chat_window() # Update the chat window

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
                        self.chat.history.append({'parts': [{'text': content}], 'role': role.lower()})
                    self.update_chat_window()
                    self.update_status_bar()
                    self.display_message("System", "Chat history loaded successfully.")
            except Exception as e:
                self.display_message("Error", f"Error loading chat history: {e}")

    def save_chat_history(self):
        """Opens a dialog to save chat history to a file."""

        # Dialog for file type selection
        file_formats = ["JSON (*.json)", "Text (*.txt)", "Markdown (*.md)", "CSV (*.csv)"]
        selected_filter, ok = QInputDialog.getItem(self, "Choose File Format", "Select a file format:", file_formats, 0, False)
        if not ok:
            return  # User canceled the dialog

        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter(selected_filter)  # Set the selected filter
        file_dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)

        if file_dialog.exec():
            filename = file_dialog.selectedFiles()[0]

            try:
                with open(filename, "w") as f:
                    match selected_filter:
                        case "JSON (*.json)":
                            data = {
                                "total_session_cost": self.session_cost,
                                "system_instruction": {
                                    "content": self.system_instructions,
                                    "tokens": self.system_instruction_tokens,
                                    "cost": calculate_cost(self.system_instruction_tokens, INPUT_PRICING, self.messages) # Calculate the cost of the system instructions
                                },
                                "chat_history": self.messages
                            }
                            json.dump(data, f, indent=4)
                        case "Text (*.txt)":
                            f.write(f"Total session cost: ${self.session_cost:.5f}\n\n")
                            f.write(f"0. System Instructions, {self.system_instruction_tokens} tokens - {self.system_instructions}\n") # System instructions at index 0
                            for i, m in enumerate(self.messages):
                                f.write(f"{i+1}. {m['role']}, {m['tokens']} tokens - {m['content']}\n")
                        case "Markdown (*.md)":
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
                        case "CSV (*.csv)":
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

        load_action = QAction("Load History Into Current Session", self)
        load_action.setShortcut("Ctrl+L") # TODO: Fix, opens file dialog behind chat window, even though save doesn't
        load_action.triggered.connect(self.load_chat_history)
        file_menu.addAction(load_action)

        save_action = QAction("Save Chat History", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_chat_history)
        file_menu.addAction(save_action)

        # TODO: Save entire session chat history (need to track session history seperately from chat history)

        # **Tools Menu**
        tools_menu = menu_bar.addMenu("Tools")
        
        delete_action = QAction("Delete Messages", self)
        delete_action.setShortcut("Ctrl+D")
        delete_action.triggered.connect(self.delete_messages)
        tools_menu.addAction(delete_action)

        files_action = QAction("Add Files to Context", self)
        files_action.setShortcut("Ctrl+F")
        files_action.triggered.connect(self.add_files_to_context)
        tools_menu.addAction(files_action)
        
        history_action = QAction("Display Chat History", self)
        history_action.setShortcut("Ctrl+H")
        history_action.triggered.connect(self.display_chat_history)
        tools_menu.addAction(history_action)

        view_action = QAction("View Full Message", self)
        view_action.setShortcut("Ctrl+M")
        view_action.triggered.connect(self.view_full_message)
        tools_menu.addAction(view_action)

        timeout_action = QAction("Set Timeout", self)
        timeout_action.setShortcut("Ctrl+T")
        timeout_action.triggered.connect(self.set_timeout)
        tools_menu.addAction(timeout_action)

        clear_action = QAction("Clear Chat History", self)
        clear_action.setShortcut("Ctrl+R")
        clear_action.triggered.connect(self.clear_chat_history)
        tools_menu.addAction(clear_action)

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
        instructions_action = QAction("Show Instructions", self)
        instructions_action.triggered.connect(lambda: self.display_message("Instructions", INSTRUCTIONS))
        help_menu.addAction(instructions_action)

    def set_timeout(self):
        """Opens a dialog to adjust the timeout setting."""
        timeout, ok = QInputDialog.getInt(self, "Timeout", "Enter new timeout (seconds):", self.timeout, step=10)
        if ok: self.timeout = timeout
        self.display_message("Timeout", f'Timeout set to {self.timeout} seconds.')

    def create_chat_window(self):
        """Creates the chat window area."""
        self.chat_window = QTextEdit() 
        self.chat_window.setReadOnly(True) # Ensure the user can't directly edit the chat history
        self.chat_window.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth) # Ensure text wraps within the widget's width
        self.layout.addWidget(self.chat_window)

    def create_input_area(self):
        """Creates the input area for user messages."""
        self.input_box = QTextEdit()
        self.input_box.installEventFilter(self) # Install event filter for Ctrl+Enter handling
        # TODO: adjust height of input box, should be small but expandable
        self.layout.addWidget(self.input_box)

        # Create a horizontal layout for the input box and send button
        input_layout = QHBoxLayout()
        input_layout.addWidget(self.input_box)

        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        input_layout.addWidget(self.send_button)

        self.layout.addLayout(input_layout)

    def create_status_bar(self):
        """Creates the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Create a progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setFixedWidth(200) # Set a fixed width for the progress bar
        self.progress_bar.setMaximum(self.timeout) # Set the maximum value of the progress bar
        self.status_bar.addPermanentWidget(self.progress_bar) # Add the progress bar to the status bar

    def update_progress_bar(self):
        """Updates the progress bar."""
        current_value = self.progress_bar.value()
        self.progress_bar.setValue(current_value + 1)  # Increment progress
        if current_value >= self.progress_bar.maximum():
            self.timer.stop()

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
                "API Key", "API Key set successfully. Restart the application for it to take effect."
            )
        elif not ok:
            self.display_message(
                "API Key", "API Key not set. Using the existing key from .env."
            )

    def configure_settings(self): # TODO: If config.json doesn't exist, populate these with default values from init
        """Allows the user to configure application settings."""
        dialog = SettingsDialog(self) # Create an instance of the SettingsDialog
        if dialog.exec() == QDialog.accepted: # Use exec() instead of show() to run the dialog modally
            self.load_config() # Reload config if settings are changed
            self.generation_config = { # Update generation_config
                "temperature": self.temperature,
                "max_output_tokens": self.max_output_tokens,
                "stop_sequences": self.stop_sequences
            }
            # Update the model with the new settings and restart the chat
            self.initialize_model()
            self.chat = self.model.start_chat()
            self.display_message('System', 'Settings updated.') # Inform the user that the settings have been updated

    def update_chat_window(self):
        """Updates the chat window with the current chat history."""
        full_html = ""  # Initialize an empty string for the full HTML content
        for message in self.chat_history: 
            full_html += message # Append each formatted message to the full_html
        self.chat_window.setHtml(full_html)  # Set the HTML content of the QTextEdit

    def update_status_bar(self): # TODO: Make permanent widget instead of message so it doesn't clear when hovering over menu bar.
        """Updates the status bar with session information."""
        last_message_input_cost = calculate_cost(self.last_input_tokens, INPUT_PRICING, self.messages)
        last_message_output_cost = calculate_cost(self.last_output_tokens, OUTPUT_PRICING, self.messages)
        message = ( 
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

            global SI_TOKENS
            SI_TOKENS = self.model.count_tokens(" ").total_tokens
            self.system_instruction_tokens = SI_TOKENS
            self.display_message("System Instructions", self.system_instructions)
            self.display_message("Tokens", SI_TOKENS)
            self.display_message("Cost", f"${calculate_cost(SI_TOKENS, INPUT_PRICING, self.messages):.5f}")
            self.system_message_displayed = True # Resetting this here

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

    def clear_chat_history(self):
        """Clears the chat history for the current session."""
        if (
            QMessageBox.question(
                self,
                "Confirm Clear",
                "Are you sure you want to clear the chat history? Cancel and save first if needed.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            == QMessageBox.StandardButton.Yes
        ):
            self.chat_history.clear()  # Clear the chat history 
            self.messages.clear()  # Clear the messages list
            self.chat.history.clear() # Start a fresh chat
            self.update_chat_window()  # Update the chat window
            self.update_status_bar()  # Update the status bar


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuration")
        self.setGeometry(200, 200, 600, 400)

        # Layout
        layout = QVBoxLayout(self)

        # Model Selection
        self.model_label = QLabel("Model:")
        self.model_combo = QComboBox(self)
        self.model_combo.addItems(["gemini-1.5-pro-latest", "gemini-1.5-flash-latest"]) # Add more models as needed
        layout.addWidget(self.model_label)
        layout.addWidget(self.model_combo)

        # Safety Level Selection
        self.safety_label = QLabel("Safety Level:")
        self.safety_combo = QComboBox(self)
        self.safety_combo.addItems(["None", "Low", "Medium", "High"])
        layout.addWidget(self.safety_label)
        layout.addWidget(self.safety_combo)

        # Timeout
        self.timeout_label = QLabel("Timeout (seconds):")
        self.timeout_spin = QSpinBox(self)
        self.timeout_spin.setMinimum(1)
        self.timeout_spin.setMaximum(600)  # Set a reasonable maximum timeout
        self.timeout_spin.setSingleStep(10)

        layout.addWidget(self.timeout_label)
        layout.addWidget(self.timeout_spin)

        # Project Directory
        self.project_dir_label = QLabel("Project Directory:")
        self.project_dir_edit = QLineEdit(self)
        self.project_dir_button = QPushButton("Browse", self)
        self.project_dir_button.clicked.connect(self.browse_project_dir)
        project_dir_layout = QHBoxLayout()
        project_dir_layout.addWidget(self.project_dir_edit)
        project_dir_layout.addWidget(self.project_dir_button)
        layout.addWidget(self.project_dir_label)
        layout.addLayout(project_dir_layout)

        # Ignored Extensions
        self.ignored_extensions_label = QLabel("Ignored Extensions and/or Files (comma-separated):")
        self.ignored_extensions_edit = QLineEdit(self)
        layout.addWidget(self.ignored_extensions_label)
        layout.addWidget(self.ignored_extensions_edit)

        # Temperature
        self.temperature_label = QLabel("Temperature:")
        self.temperature_spin = QDoubleSpinBox(self)
        self.temperature_spin.setMinimum(0.0)
        self.temperature_spin.setMaximum(2.0)
        self.temperature_spin.setSingleStep(0.1)
        layout.addWidget(self.temperature_label)
        layout.addWidget(self.temperature_spin)

        # Max Output Tokens
        self.max_output_tokens_label = QLabel("Max Output Tokens:")
        self.max_output_tokens_spin = QSpinBox(self)
        self.max_output_tokens_spin.setMinimum(1)
        self.max_output_tokens_spin.setMaximum(8192)
        self.max_output_tokens_spin.setSingleStep(10)
        layout.addWidget(self.max_output_tokens_label)
        layout.addWidget(self.max_output_tokens_spin)

        # Stop Sequences (You might want to use a QLineEdit for this if you're not using a fixed set)
        self.stop_sequences_label = QLabel("Stop Sequences (comma-separated):")
        self.stop_sequences_edit = QLineEdit(self)
        layout.addWidget(self.stop_sequences_label)
        layout.addWidget(self.stop_sequences_edit)

        # System Instructions
        self.system_instructions_label = QLabel("System Instructions:")
        self.system_instructions_edit = QTextEdit(self) # Using QTextEdit to allow multiline input
        layout.addWidget(self.system_instructions_label)
        layout.addWidget(self.system_instructions_edit)

        # Buttons
        button_box = QHBoxLayout()
        self.save_button = QPushButton("Save", self)
        self.save_button.clicked.connect(self.accept)
        button_box.addWidget(self.save_button)
        self.cancel_button = QPushButton("Cancel", self)
        self.cancel_button.clicked.connect(self.reject)
        button_box.addWidget(self.cancel_button)
        layout.addLayout(button_box)

        self.load_settings() # Load and update the UI with saved settings
    
    def browse_project_dir(self):
        """Opens a directory dialog to select the project directory."""
        options = QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks
        directory = QFileDialog.getExistingDirectory(self, "Select Project Directory", "", options=options)
        if directory:
            self.project_dir_edit.setText(directory)
    
    def load_settings(self):
        """Load settings from the config file."""
        config_file = os.path.join(SCRIPT_DIR, 'config.json') # Get the path to config.json
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                # Update UI widgets with loaded settings
                self.model_combo.setCurrentText(config.get('model', self.parent().model_name))
                self.safety_combo.setCurrentText(config.get('safety', self.parent().safety_level).capitalize()) # Capitalize for display
                self.timeout_spin.setValue(config.get('timeout', self.parent().timeout))
                self.project_dir_edit.setText(config.get('project_directory', self.parent().project_dir))
                self.ignored_extensions_edit.setText(", ".join(config.get('ignored_extensions', self.parent().ignored_extensions)))
                self.temperature_spin.setValue(config.get('temperature', self.parent().temperature))
                self.max_output_tokens_spin.setValue(config.get('max_output_tokens', self.parent().max_output_tokens))
                self.stop_sequences_edit.setText(", ".join(config.get('stop_sequences', self.parent().stop_sequences)))
                self.system_instructions_edit.setPlainText(config.get('system_instructions', self.parent().system_instructions)) # Use setPlainText for QTextEdit
        except FileNotFoundError:
            # Handle case where file doesn't exist (e.g., first time running)
            QMessageBox.warning(self, "Warning", "Configuration file not found. Using default settings.")
        except Exception as e:
            # Handle other potential errors during file loading
            QMessageBox.critical(self, "Error", f"An error occurred while loading the settings: {e}")

    def save_settings(self):
        """Save settings to config.json."""
        config_file = os.path.join(SCRIPT_DIR, 'config.json')
        try:
            # Get the current settings from the UI elements
            config = {
                'model': self.model_combo.currentText(),
                'system_instructions': self.system_instructions_edit.toPlainText(), # Get text from QTextEdit
                'safety': self.safety_combo.currentText().lower(),
                'timeout': self.timeout_spin.value(),
                'project_directory': self.project_dir_edit.text(),
                'ignored_extensions': [x.strip() for x in self.ignored_extensions_edit.text().split(",")],
                'temperature': self.temperature_spin.value(),
                'max_output_tokens': self.max_output_tokens_spin.value(),
                'stop_sequences': [x.strip() for x in self.stop_sequences_edit.text().split(",")] 
            }
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=4)

            QMessageBox.information(self, "Success", "Settings saved successfully.<br>The application may need restarted for some changes to be applied. (Model, system instructions, etc.)<br>It's recommended that you save and reload.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while saving the settings: {e}")

    def accept(self):
        """Save settings when the dialog is accepted."""
        self.save_settings()
        super().accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())