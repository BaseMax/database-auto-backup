# Database Auto Backup with Telegram Notification

## Overview

`database-auto-backup.py` is a Python-based script designed for automating MySQL/MariaDB database backups. It supports compression, Telegram upload notifications, retention management, and logging. This script is suitable for use on servers with multiple databases that need to be backed up regularly, with Telegram integration for quick status updates.

### Features:
- Backup multiple MySQL/MariaDB databases.
- Supports database compression (gzip, bzip2, zip).
- Telegram bot integration for uploading backups with custom captions.
- Backup retention to automatically clean up old backups.
- Verbose logging for easier debugging and auditing.

## Requirements

- Python 3.6+.
- Required Python libraries: `pymysql`, `requests`.
- MySQL or MariaDB with `mysqldump` utility (optional but recommended).
- A Telegram bot token and chat ID for uploading backups to Telegram.

## Installation

1. Clone the repository or download the `database-auto-backup.py` file.
   ```bash
   git clone https://github.com/BaseMax/database-auto-backup.git
   ```

2. Ensure you have a Telegram bot. If not, create one by talking to [BotFather](https://core.telegram.org/bots#botfather) on Telegram. You will need the bot token and chat ID for sending backup files.

3. Install the required Python libraries:

   ```bash
   pip install pymysql requests
   ```

4. Configure the script:

   * Open the `database-auto-backup.py` file.
   * Modify the `config` dictionary with your database credentials and Telegram bot details.

   Example:

   ```python
   config = {
       'databases': [
           {
               'name': 'your_db_name',
               'user': 'your_db_user',
               'pass': 'your_db_password',
               'host': 'localhost',
               'port': 3306
           }
       ],
       'output_dir': './backups',
       'use_mysqldump': True, # Enable mysqldump or fallback to Python PDO
       'compression': 'gz',   # Supported: gz, bz2, zip
       'telegram': {
           'bot_token': 'your_bot_token',
           'chat_id': 'your_chat_id',
           'caption': 'Auto DB Backup'
       },
       'retention_days': 30,  # Retain backups for 30 days
       'log_file': './backups/backup.log',
   }
   ```

5. Make sure your web server or Python process has write permissions to the output directory.

## Usage

1. **Run the script manually:**

   You can run the script directly from the command line:

   ```bash
   python database-auto-backup.py
   ```

2. **Automate backups with a cron job (Linux/macOS):**

   You can automate the script to run at scheduled intervals by setting up a cron job. For example, to run it every day at midnight:

   ```bash
   crontab -e
   ```

   Add the following line:

   ```bash
   0 0 * * * /usr/bin/python /path/to/database-auto-backup.py
   ```

## Configuration Options

* **databases**: A list of dictionaries containing the database configurations (name, user, password, host, port).
* **output_dir**: Directory where the backup files will be stored.
* **use_mysqldump**: Set to `True` to use `mysqldump` for database backup, or `False` to use Python PDO fallback.
* **compression**: Specify the compression type (valid values: `gz`, `bz2`, `zip`).
* **disable_telegram**: Set to `True` to disable Telegram upload.
* **telegram**: Telegram bot configuration (includes bot token, chat ID, and caption).
* **retention_days**: Number of days to retain backup files before they are deleted.
* **cleanup_after_upload**: Set to `True` to delete the backup files after they have been uploaded to Telegram.
* **log_file**: Path to the log file for backup operations.

## Logging

The script logs all operations, including successful backups, errors, and Telegram uploads. By default, logs are written to `backups/backup.log`. You can change the log file location by modifying the `log_file` configuration.

## Backup Retention

The script supports automatic cleanup of old backups based on the `retention_days` configuration. For example, if set to `30`, the script will delete backups older than 30 days. Set `retention_days` to `0` or leave it empty to disable retention.

## License

This project is licensed under the MIT License.

© 2026 Seyyed Ali Mohammadiyeh (Max Base)
