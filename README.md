# Torrent Forge Bot

This bot allows users to convert files, Google Drive links to torrent files via Telegram.

## Features

- Convert uploaded files to .torrent files
- Convert Google Drive links to .torrent files

## Prerequisites

- Python 3.7+
- A Telegram Bot Token (obtain from @BotFather on Telegram)
- Google Cloud Project with Drive API enabled
- Service Account credentials for Google Drive API

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/david96182/telegram-nzb-gdrive-bot.git
   cd telegram-nzb-gdrive-bot
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root and add the following:
   ```
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
   GOOGLE_SERVICE_ACCOUNT_INFO={"type": "service_account", "project_id": "your-project-id", ...}
   ```
   Replace `your_telegram_bot_token_here` with your actual Telegram Bot Token.
   For `GOOGLE_SERVICE_ACCOUNT_INFO`, paste the entire contents of your service account JSON key file as a single line.

## Usage

1. Start the bot:
   ```
   python main.py
   ```

2. In Telegram, start a conversation with your bot.

3. Send a file, Google Drive link to the bot.

4. The bot will process the input and return a .torrent file.

## Configuration

- `TELEGRAM_BOT_TOKEN`: Your Telegram Bot Token
- `GOOGLE_SERVICE_ACCOUNT_INFO`: Your Google Service Account credentials JSON

## Troubleshooting

- If you encounter issues with Google Drive authentication, ensure that your service account has the necessary permissions to access the files you're trying to download.
- Make sure all environment variables are correctly set in the `.env` file.
- Check the console output for any error messages or logs that might indicate the source of any issues.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.
