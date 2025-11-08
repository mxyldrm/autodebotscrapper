# 🚗 AutoDE Car Listings Bot

![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

A secure, professional, and efficient web scraper for monitoring car listings on [Auto.de](https://www.auto.de). This bot automatically collects car information including make, model, price, specifications, and stores them in a local database with Telegram notifications for errors.

## ⚠️ Important Disclaimer

**This project is strictly for educational purposes only.** The responsibility for how this code is used lies entirely with the user. The authors of this project do not assume any liability for misuse or any damages arising from the use of this code.

**Before using this bot:**
- Review Auto.de's Terms of Service and robots.txt
- Ensure compliance with applicable laws and regulations
- Use rate limiting and respectful scraping practices
- Do not overload the target server

## ✨ Features

### 🔒 Security Features (v2.0)
- ✅ **Request Timeout Protection** - Prevents hanging on unresponsive servers
- ✅ **SSL/TLS Verification** - Protects against MITM attacks
- ✅ **Rate Limiting** - Prevents server overload and IP bans
- ✅ **Input Validation & Sanitization** - Prevents injection attacks
- ✅ **Retry Mechanism** - Exponential backoff for failed requests
- ✅ **Error Handling** - Comprehensive exception handling
- ✅ **Secure Configuration** - Environment variables for sensitive data
- ✅ **robots.txt Compliance** - Optional ethical scraping checks

### 📊 Core Features
- 🔍 Automated scraping of car listings from Auto.de
- 💾 SQLite database storage with proper schema
- 🔔 Telegram notifications for errors and critical events
- 📈 Statistics tracking (runs, successes, failures)
- 🧹 Automatic cleanup of old listings
- 📝 Comprehensive logging to file and console
- 🔄 Graceful shutdown handling (SIGINT/SIGTERM)
- ⚙️ Highly configurable via environment variables

### 🏗️ Architecture
- **Modular Design** - Separated concerns (config, common utilities, main bot)
- **Object-Oriented** - Clean class-based structure
- **Type Hints** - Python typing for better code quality
- **Professional Code** - Follows Python best practices (PEP 8)

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Internet connection
- Telegram Bot (optional, for notifications)

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/mxyldrm/autodebotscrapper.git
cd autodebotscrapper
```

### 2. Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Copy the example environment file and edit it with your settings:

```bash
cp .env.example .env
```

Edit `.env` file with your favorite text editor:

```bash
nano .env  # or vim, code, etc.
```

**Required Configuration:**

```env
# Telegram Bot Configuration (Get from @BotFather)
TELEGRAM_API_KEY=your_telegram_bot_api_key_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here
```

**Optional Configuration (with defaults):**

```env
# Scraping Configuration
MAX_PAGES=5                    # Number of pages to scrape (default: 5)
REQUEST_TIMEOUT=30             # Request timeout in seconds (default: 30)
RATE_LIMIT_REQUESTS=10         # Max requests per time window (default: 10)
RATE_LIMIT_WINDOW=60           # Rate limit time window in seconds (default: 60)

# Database Configuration
DATABASE_PATH=autode_cars.db   # SQLite database path (default: autode_cars.db)
DELETE_OLD_CARS_DAYS=7         # Delete cars older than N days (default: 7)

# Logging Configuration
LOG_LEVEL=INFO                 # Logging level (DEBUG, INFO, WARNING, ERROR)
LOG_FILE=autode_bot.log        # Log file path (default: autode_bot.log)

# Bot Behavior
MAIN_LOOP_INTERVAL=300         # Seconds between scraping cycles (default: 300 = 5 min)
CHECK_ROBOTS_TXT=true          # Check robots.txt before scraping (default: true)
```

### 5. Get Telegram Credentials (Optional but Recommended)

To receive error notifications via Telegram:

1. **Create a Telegram Bot:**
   - Open Telegram and search for `@BotFather`
   - Send `/newbot` command
   - Follow the instructions to create your bot
   - Copy the API token (e.g., `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

2. **Get Your Chat ID:**
   - Search for `@userinfobot` on Telegram
   - Start a chat and it will show your chat ID
   - Copy the numeric chat ID (e.g., `987654321`)

3. **Add to .env file:**
   ```env
   TELEGRAM_API_KEY=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
   TELEGRAM_CHAT_ID=987654321
   ```

## 💻 Usage

### Running the Bot

```bash
python auto_de_bot.py
```

The bot will:
1. Validate configuration
2. Start continuous monitoring loop
3. Scrape Auto.de listings every 5 minutes (configurable)
4. Store car information in SQLite database
5. Clean up old listings (older than 7 days by default)
6. Send error notifications to Telegram if configured
7. Log all activities to `autode_bot.log`

### Stopping the Bot

Press `Ctrl+C` to gracefully shut down the bot. It will:
- Complete the current operation
- Save final statistics to log
- Close database connections properly

### Viewing Logs

```bash
# View real-time logs
tail -f autode_bot.log

# Search for errors
grep ERROR autode_bot.log

# View last 100 lines
tail -n 100 autode_bot.log
```

### Querying the Database

```bash
# Open SQLite database
sqlite3 autode_cars.db

# Example queries:
sqlite> SELECT COUNT(*) FROM cars;
sqlite> SELECT * FROM cars ORDER BY created_at DESC LIMIT 10;
sqlite> SELECT model_make, price FROM cars WHERE price < 20000;
sqlite> .exit
```

## 📁 Project Structure

```
autodebotscrapper/
├── auto_de_bot.py          # Main bot application
├── common.py               # Common utilities (logging, database, sanitization)
├── config.py               # Configuration and settings
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (create from .env.example)
├── .env.example           # Example environment configuration
├── .gitignore             # Git ignore rules
├── README.md              # This file
├── autode_bot.log         # Log file (created on first run)
└── autode_cars.db         # SQLite database (created on first run)
```

## 🗄️ Database Schema

```sql
CREATE TABLE cars (
    id TEXT PRIMARY KEY,              -- Unique car ID from Auto.de
    model_make TEXT NOT NULL,         -- Car make and model
    price REAL,                       -- Price in EUR
    link TEXT,                        -- Direct link to listing
    image_url TEXT,                   -- Car image URL
    company TEXT,                     -- Platform (autode)
    transmission TEXT,                -- Manual/Automatic
    mileage INTEGER,                  -- Mileage in km
    first_registration INTEGER,       -- First registration year
    fuel_type TEXT,                   -- Petrol/Diesel/Electric/Hybrid
    power_data TEXT,                  -- Power in KW and PS
    co2_emission TEXT,                -- CO2 emissions
    consumption TEXT,                 -- Fuel consumption
    created_at TIMESTAMP,             -- When first added
    updated_at TIMESTAMP              -- Last update time
);
```

## 🔧 Configuration Options

### Rate Limiting

Adjust rate limiting to be more or less aggressive:

```env
# Conservative (safer)
RATE_LIMIT_REQUESTS=5
RATE_LIMIT_WINDOW=60

# Default (balanced)
RATE_LIMIT_REQUESTS=10
RATE_LIMIT_WINDOW=60

# Aggressive (not recommended)
RATE_LIMIT_REQUESTS=20
RATE_LIMIT_WINDOW=60
```

### Scraping Frequency

Change how often the bot runs:

```env
# Every 5 minutes (default)
MAIN_LOOP_INTERVAL=300

# Every 15 minutes (recommended for production)
MAIN_LOOP_INTERVAL=900

# Every hour
MAIN_LOOP_INTERVAL=3600
```

## 🛡️ Security Best Practices

1. **Never commit `.env` file** - It contains sensitive credentials
2. **Use strong Telegram bot tokens** - Keep them secret
3. **Enable SSL verification** - Already enabled by default
4. **Use rate limiting** - Respect the target server
5. **Monitor logs regularly** - Check for suspicious activity
6. **Keep dependencies updated** - Run `pip install --upgrade -r requirements.txt`
7. **Use virtual environments** - Isolate project dependencies
8. **Backup your database** - Regularly backup `autode_cars.db`

## 🐛 Troubleshooting

### Bot won't start

```bash
# Check Python version
python --version  # Should be 3.8+

# Check dependencies
pip list

# Reinstall dependencies
pip install --force-reinstall -r requirements.txt

# Check configuration
python -c "from config import validate_config; validate_config()"
```

### No data being collected

1. Check internet connection
2. Verify Auto.de website is accessible
3. Check logs for errors: `tail -f autode_bot.log`
4. Verify endpoint format hasn't changed
5. Check rate limiting settings

### Telegram notifications not working

1. Verify bot token is correct
2. Verify chat ID is correct
3. Start a conversation with your bot first
4. Check bot has permission to send messages
5. Test with: `python -c "from common import send_telegram_message; from config import TELEGRAM_API_KEY, CHAT_ID; send_telegram_message('Test', TELEGRAM_API_KEY, CHAT_ID)"`

### Database errors

```bash
# Check database file permissions
ls -l autode_cars.db

# Backup and reset database
mv autode_cars.db autode_cars.db.backup
# Restart bot to create new database
```

## 📈 Performance Tips

1. **Adjust MAX_PAGES** - Start with fewer pages (1-2) for testing
2. **Increase MAIN_LOOP_INTERVAL** - Run less frequently in production
3. **Enable CHECK_ROBOTS_TXT** - Respect server policies
4. **Monitor resource usage** - Use `htop` or `top` to check CPU/memory
5. **Rotate logs** - Use logrotate or similar tool for log management

## 🔄 Updates and Maintenance

### Updating the Bot

```bash
git pull origin main
pip install --upgrade -r requirements.txt
```

### Database Maintenance

```bash
# Vacuum database to reclaim space
sqlite3 autode_cars.db "VACUUM;"

# Check database integrity
sqlite3 autode_cars.db "PRAGMA integrity_check;"
```

## 📝 Changelog

### Version 2.0.0 (Current)
- ✨ Complete security overhaul
- ✨ Added rate limiting and retry mechanisms
- ✨ Input validation and sanitization
- ✨ Modular architecture (config, common, main)
- ✨ Class-based design (AutoDEBot)
- ✨ Graceful shutdown handling
- ✨ Comprehensive error handling
- ✨ Statistics tracking
- ✨ Type hints and documentation
- ✨ Updated User-Agent
- ✨ Environment-based configuration
- ✨ robots.txt compliance check

### Version 1.0.0
- Initial release
- Basic scraping functionality
- Simple database storage
- Telegram notifications

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👨‍💻 Author

**mxyldrm**
- GitHub: [@mxyldrm](https://github.com/mxyldrm)

## 🙏 Acknowledgments

- Auto.de for providing the car listings platform
- Python community for excellent libraries
- Contributors and testers

## ⚖️ Legal Notice

This software is provided "as is" without warranty of any kind. Web scraping may be against the terms of service of some websites. Users are responsible for ensuring their use of this software complies with all applicable laws, regulations, and terms of service. The authors accept no liability for any misuse of this software.

**Use responsibly and ethically.**

---

Made with ❤️ for educational purposes
