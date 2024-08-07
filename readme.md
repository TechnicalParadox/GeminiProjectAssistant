# Gemini Project Assistant
##### A Google Gemini based project assistant that helps you create, manage, and debug your programming projects.
### License
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

*Click link for license details.*

---------------
## Table of Contents
* [Installation](#installation)
* [Usage](#usage)
* [Features](#features)
* [Roadmap](#roadmap)
* [Credits](#credits)
* [Questions](#questions)
---------------
## Dependencies

#### Installing System Dependencies (Ubuntu/Debian)
Before installing the Python requirements, you need to install the following system packages:
```bash
sudo apt update
sudo apt install python3-xlib libx11-xcb-dev libxcb-cursor0 libxrender1 libxi6 
```
**Explanation of the additional libraries:**
- **`libx11-xcb-dev`:** Provides development headers for the XCB (X protocol C binding) library, which PyQt6 likely uses internally.
- **`libxcb-cursor0`:** Specifically handles mouse cursor rendering using XCB, essential for GUI applications.
- **`libxrender1`:** X Render extension library, often used for advanced rendering operations (transparency, antialiasing) within X11.
- **`libxi6`:**  XInput extension library, handling input devices like keyboards and mice in X11. 

## Installation
1. Ensure you have installed the necessary dependencies.
2. Download the zip and extract files to the directory you wish to install in.
3. Open installation directory.
4. Create config.json to your specifications according to config.json-template. (Optional) This can be generated inside the application.
5. Create your .env file according to the .env-template. (Optional) This can be generated inside the application.
6. Open terminal in the installation directory.
7. Run `pip install -r requirements.txt`
8. Run `python3 ./project_assistant_v1.1.py`
9. Follow instructions on the screen.
**NOTE:** If you want to enable scraping docs from URL, you must install https://github.com/TechnicalParadox/DocScraper in your installation directory. File structure should look like this (`installation_dir/tools/DocScraper/docscraper.py`)

## Usage
[example of a saved output log in markdown format.](https://github.com/TechnicalParadox/GeminiProjectAssistant/blob/master/examples/example_use.md)

You can set the project directory to your project directory. When using this application, you may add relevant files related to the goal you are trying to accomplish. You then converse with the Gemini API, asking it for ideas on how to accomplish something, to debug your code, to generate code, etc. As you get better with prompting, the application becomes more reliable and useful.

![A image showing the startup message when launching the application.](images/readme.png)
## Features
* **Cost Tracking:** Tracks the cost of each interaction with the Gemini API, as well as the total session cost, to help you stay within your budget.
* **Contextual Awareness:** Provides the ability to add files and their content as context to the AI, allowing for more relevant and accurate responses.
* **History Management:** Allows for saving chat history, viewing past interactions within the current conversation, and deleting messages from context to save tokens/cost.
* **Documentation Scraping:** Allows you to scrape API docs from URLs and send as context, improving quality of responses.
* **Customizable:** Configure the model, safety settings, timeout, and project directory through a config.json file.
## Roadmap
* **Error Handling:** Improve the application's handling of potential errors from the Gemini API for a more robust user experience.
* **GUI Development:** Develop a user-friendly graphical user interface (GUI) using PyQt to enhance accessibility and ease of use.
* **Multimodal Input:** Explore incorporating multimodal input, such as code snippets or images, to provide richer context to the AI.
## Credits
* [Giamo Lao (TechnicalParadox)](https://technicalparadox.github.io)
## Questions
Any questions should be directed to 

[Giamo Lao (TechnicalParadox)](technicalparadox.github.io)

[giamolao98@gmail.com](mailto:technicalparadox.github.io)

*This readme was generated using [readme-js](https://github.com/TechnicalParadox/readme-js)*

*Readme improvements and edits by [GeminiProjectAssistant](https://github.com/TechnicalParadox/GeminiProjectAssistant)*
