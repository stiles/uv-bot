# UV Forecast Bot

This Python script fetches UV forecast data from the [Royal Netherlands Meteorological Institute (KNMI)](https://www.temis.nl/uvradiation/nrt/uvindex.php?lon=-118.02&lat=35.12) and generates an HTML email body with the forecast and protection advice.

## Features

*   Fetches UV index and ozone column data.
*   Provides UV protection advice based on the World Health Organization (WHO) guidelines.
*   Generates an HTML email body with today's forecast and a weekly outlook.
*   Parses data for a specific location (currently set to lon=-118.02, lat=35.12).

## Usage

1.  Run the `uv_forecast.py` script.
2.  The script will print the HTML email content to the console.
3.  You can then copy and paste this HTML into an email client.

## Dependencies

*   requests
*   pandas
*   beautifulsoup4

## Future improvements

*   Allow users to specify location via command-line arguments or a configuration file.
*   Send the email automatically using `smtplib`.
*   Add error handling for more robust data parsing. 