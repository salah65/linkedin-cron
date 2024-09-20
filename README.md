> ⚠️ **Warning:** This script does not support two-factor authentication for LinkedIn. For the automation to work properly, please ensure that your LinkedIn account is set up for single sign-on (i.e., no two-factor authentication).
# LinkedIn Auto Connections

This project automates the process of sending connection requests to LinkedIn recruiters. It uses a `.env` file to securely store login credentials and includes a `script.sh` file to run the necessary commands.

## Prerequisites

Before running the project, ensure that the following are installed:

- Python 3.x
- Selenium (for browser automation)
- `python-dotenv` (for loading environment variables from the `.env` file)
- Bash (for executing the `script.sh`)

## Setting Up the Environment

### 1. Create a `.env` File

In the root directory of your project, create a `.env` file to store your LinkedIn login credentials. The `.env` file should be structured like this:

EMAIL=your-email@example.com  

PASSWORD=your-password


This file will be used to log into LinkedIn during the automated process.

### 2. Ensure the script.sh is Executable
Make sure that the script.sh file has the proper permissions to be executed. You can do this by running:

```bash
chmod +x script.sh
```

### 3. Install Python Dependencies

Before running the project, make sure you have all necessary Python dependencies installed. Run the following command to install `selenium`, `python-dotenv`, and any other required libraries:

```bash
bash script.sh
```

### 4.Running the Project

```bash
python3 cron.py
```


