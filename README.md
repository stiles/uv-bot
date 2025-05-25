# UV Forecast Bot

This Python script fetches a 6-day UV forecast from the [Royal Netherlands Meteorological Institute (KNMI)](https://www.temis.nl/uvradiation/nrt/uvindex.php?lon=-118.02&lat=35.12), generates a customized HTML email, sends it to a list of recipients, and stores the forecast data locally in a CSV file.

## Features

*   Fetches a 6-day UV index and ozone column forecast.
*   Provides UV protection advice based on World Health Organization (WHO) guidelines.
*   Generates a personalized HTML email with the current day's UV index and a weekly outlook (UV index and summary advice).
*   Sends the email to a configurable list of recipients using SMTP.
*   Stores historical forecast data (including UV index and ozone column) in `data/uv_forecast_history.csv`.
    *   New data is appended, and entries for existing dates are updated with the latest forecast.
    *   The history file is automatically added to `.gitignore`.
*   Includes a GitHub Actions workflow (`.github/workflows/daily_forecast.yml`) to run the script daily.
    *   The workflow is scheduled to run at a time suitable for receiving a morning forecast in Pacific Time.
    *   The script now exits with an error code to ensure GitHub Actions correctly reports failures.
*   Parses data for a specific location (currently hardcoded to lon=-118.02, lat=35.12 for Los Angeles).

## Setup for automated email

1.  **Configure GitHub Secrets:** For the GitHub Action to send emails, you need to set up the following secrets in your repository settings (`Settings` -> `Secrets and variables` -> `Actions` -> `New repository secret`):
    *   `EMAIL_ADDRESS`: The sender's email address (e.g., your Gmail address).
    *   `EMAIL_PASSWORD`: Your email account password. **Important:** If using Gmail with 2-Factor Authentication, generate an "App Password" for this.
    *   `EMAIL_RECIPIENT`: A comma-separated string of recipient email addresses (e.g., `email1@example.com,email2@example.org`).
    *   `SMTP_SERVER`: The SMTP server address for your email provider (e.g., `smtp.gmail.com`).
    *   `SMTP_PORT`: The SMTP port (e.g., `465` for SMTP_SSL with Gmail).

2.  **Adjust Workflow Schedule (Optional):**
    *   The GitHub Actions workflow in `.github/workflows/daily_forecast.yml` is currently set to `cron: '0 15 * * *'` (3:00 PM UTC). This aims to deliver the email in the morning for the US Pacific Timezone.
    *   You can adjust this cron schedule to your preferred UTC time.

## Usage

*   **Automated via GitHub Actions:** Once secrets are configured, the script will run automatically based on the schedule in `.github/workflows/daily_forecast.yml`.
*   **Local Execution:**
    1.  Ensure Python 3 is installed.
    2.  Install dependencies: `pip install requests pandas beautifulsoup4`
    3.  (Optional) Set the environment variables mentioned in "Setup for automated email" if you want to test email sending locally.
    4.  Run the script: `python uv_forecast.py`
    5.  If email variables are not set, the script will print error messages about missing variables and exit. If they are set but an email fails to send, it will also exit with an error.
    6.  The script will create/update `data/uv_forecast_history.csv`.

## Dependencies

*   requests
*   pandas
*   beautifulsoup4

## Future improvements

*   Allow users to specify location (latitude and longitude) via command-line arguments or a configuration file.
*   Optionally include the historical data CSV in Git tracking (if desired by the user).
*   More sophisticated parsing error handling for the source website. 