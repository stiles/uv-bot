import requests
import pandas as pd
from bs4 import BeautifulSoup
from io import StringIO
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import sys

url = 'https://www.temis.nl/uvradiation/nrt/uvindex.php?lon=-118.02&lat=35.12'

def get_uv_protection_advice(uv_index):
    uv_index = float(uv_index)
    if uv_index <= 2:
        return "Low (0-2): No protection needed. You can safely enjoy the outdoors.", "#4eb400" # Green
    elif uv_index <= 5: # Corresponds to 3-5 in WHO guidelines
        return "Moderate (3-5): Wear sunglasses on bright days. If you burn easily, cover up and use broad spectrum SPF 30+ sunscreen. Seek shade during midday hours.", "#f7e400" # Yellow
    elif uv_index <= 7: # Corresponds to 6-7
        return "High (6-7): Protection needed. Reduce time in the sun between 10 a.m. and 4 p.m. Wear sunglasses, apply SPF 30+ sunscreen every 2 hours, wear a wide-brimmed hat, and cover up with clothing. Seek shade.", "#f8b600" # Orange
    elif uv_index <= 10: # Corresponds to 8-10
        return "Very High (8-10): Extra protection needed. Avoid sun exposure between 10 a.m. and 4 p.m. Wear sunglasses, apply SPF 30+ sunscreen every 2 hours, wear a wide-brimmed hat, and protective clothing. Seek shade.", "#d8001d" # Red
    else: # 11+
        return "Extreme (11+): Take all precautions. Avoid sun exposure between 10 a.m. and 4 p.m. Wear sunglasses, apply SPF 30+ sunscreen every 2 hours, wear a wide-brimmed hat, and protective clothing. Seek shade.", "#b54cff" # Violet/Purple

def fetch_html_content(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        sys.exit(1)

def create_email_body(location, forecast_df):
    if forecast_df.empty:
        return "<p>Could not retrieve UV forecast data.</p>"

    today_forecast = forecast_df.iloc[0]
    advice_full, color = get_uv_protection_advice(today_forecast['uv_index'])
    # Extract only the advice text part, not the UV range like "Very High (8-10): ..."
    advice_text = advice_full.split(": ", 1)[1] if ": " in advice_full else advice_full 

    email_html = f"""\
    <html>
    <head>
        <style>
            body {{ font-family: sans-serif; margin: 20px; color: #333; }}
            h1 {{ color: #333; font-size: 24px; margin-bottom: 10px; }}
            h2 {{ color: #444; font-size: 20px; margin-top: 30px; margin-bottom: 10px; }}
            p {{ margin-bottom: 10px; line-height: 1.6; }}
            table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; font-size: 14px; }}
            th, td {{ border: 1px solid #ddd; padding: 10px; text-align: left; }}
            th {{ background-color: #f2f2f2; font-weight: bold; }}
            .uv-today-index {{ background-color: {color}; color: {'black' if color not in ['#d8001d', '#b54cff'] else 'white'}; padding: 15px; border-radius: 5px; text-align: center; margin-bottom: 15px; }}
            .uv-today-index strong {{ font-size: 18px; }}
            .advice-text {{ margin-top: 15px; font-size: 16px; }}
            .footer {{ font-size: 0.8em; color: #777; margin-top: 30px; text-align: center; }}
        </style>
    </head>
    <body>
        <h1>Good morning, Eva! Here's your UV forecast for {location}</h1>
        
        <h2>Today's forecast for {today_forecast['date'].strftime('%A, %B %d, %Y')}</h2>
        <div class="uv-today-index">
            <p><strong>UV index: {today_forecast['uv_index']}</strong></p>
        </div>
        <p class="advice-text">{advice_text}</p>

        <h2>Weekly outlook</h2>
        <table>
            <tr><th>Date</th><th>UV index</th><th>Protection advice</th></tr>
    """
    for _, row in forecast_df.iterrows():
        advice_loop_full, color_loop = get_uv_protection_advice(row['uv_index'])
        advice_summary = advice_loop_full.split(':')[0] # e.g., "Very High (8-10)"
        email_html += f"""\
            <tr>
                <td>{row['date'].strftime('%A, %b %d')}</td>
                <td style="background-color:{color_loop}; color:{'black' if color_loop not in ['#d8001d', '#b54cff'] else 'white'}">{row['uv_index']}</td>
                <td>{advice_summary}</td>
            </tr>
        """
    email_html += """\
        </table>
        <p class="footer">Data sourced from the <a href="https://www.temis.nl/uvradiation/nrt/uvindex.php?lon=-118.02&lat=35.12">Royal Netherlands Meteorological Institute</a>. Bot developed by <a href="https://github.com/stiles/uv-bot">Matt Stiles</a>. Stay safe, Eva!</p>
    </body>
    </html>
    """
    return email_html

def send_email(subject, html_content, sender_email, receiver_emails_str, smtp_server, smtp_port, smtp_username, smtp_password):
    # Split the string of receiver emails into a list
    # Clean each email: strip whitespace, then strip common quote characters
    cleaned_receiver_email_list = []
    for email in receiver_emails_str.split(','):
        stripped_email = email.strip()
        if stripped_email:
            # Remove leading/trailing single or double quotes
            if stripped_email.startswith(('"', "'")) and stripped_email.endswith(('"', "'")) and len(stripped_email) > 1:
                stripped_email = stripped_email[1:-1]
            cleaned_receiver_email_list.append(stripped_email)

    if not cleaned_receiver_email_list:
        print("Error: No valid receiver email addresses provided after cleaning.")
        print(f"Original receiver_emails_str: '{receiver_emails_str}'") # Log original string for debugging
        return False
    
    # For debugging in GitHub Actions logs - shows exactly what addresses are being used
    print(f"Attempting to send email to the following cleaned addresses: {cleaned_receiver_email_list}")

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = ", ".join(cleaned_receiver_email_list) # Comma-separated list for the 'To' header

    # Attach HTML content
    part = MIMEText(html_content, "html")
    message.attach(part)

    try:
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server: # Use SMTP_SSL for implicit TLS
            server.login(smtp_username, smtp_password)
            server.sendmail(sender_email, cleaned_receiver_email_list, message.as_string()) # Pass the list to sendmail
        print(f"Email sent successfully to: {', '.join(cleaned_receiver_email_list)}")
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def main():
    html_page = fetch_html_content(url)
    location_name = "Your Location" # Default if not found

    if not html_page: # Already exits in fetch_html_content if error
        return # Should not be reached if fetch_html_content exits

    soup = BeautifulSoup(html_page, 'html.parser')
    forecast_table_element = soup.find('table', {'border': '2'})

    if not forecast_table_element:
        print("<p>Could not find the forecast table in the HTML. The website structure might have changed.</p>")
        sys.exit(1)

    try:
        # Try to extract location from H2 tag within the table
        h2_tag = forecast_table_element.find('h2')
        if h2_tag and h2_tag.string:
            location_name = h2_tag.string.strip()
            if not location_name: # If string is empty after stripping
                location_name = "UV Forecast" # Default subject if location is not found

        df_list = pd.read_html(StringIO(str(forecast_table_element)), header=1)
        
        if not df_list:
            print("<p>Pandas could not parse the table found by BeautifulSoup.</p>")
            sys.exit(1)

        df = df_list[0]
        df = df.iloc[1:] # Skip the first data row (which was the HTML h2 title)
        df = df.dropna(subset=['UV index', 'ozone column']) # Drop metadata/footer rows
        df = df.reset_index(drop=True)

        # Snake_case column names
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        
        # Data processing and validation
        if 'ozone_column' in df.columns:
            df['ozone_column'] = df['ozone_column'].astype(str).str.replace('DU', '', regex=False).str.strip()
            df['ozone_column'] = pd.to_numeric(df['ozone_column'], errors='coerce')
        else:
            print("Warning: 'ozone_column' not found in the table.")
            # Decide if this is a critical error: sys.exit(1)
        
        if 'uv_index' in df.columns:
            df['uv_index'] = pd.to_numeric(df['uv_index'], errors='coerce')
        else:
            print("Warning: 'uv_index' not found in the table.")
            # Decide if this is a critical error: sys.exit(1)
        
        if 'date' in df.columns:
            df['date'] = df['date'].astype(str).str.strip()
            try:
                df['date'] = pd.to_datetime(df['date'])
            except ValueError as e:
                try:
                    df['date'] = pd.to_datetime(df['date'], format='%d %B %Y', errors='coerce')
                except Exception as final_e:
                     print(f"Warning: Could not parse all dates in 'Date' column accurately. Error: {final_e}")
                     df['date'] = pd.NaT 
        else:
            print("Warning: 'date' column not found in the table.")
            # Decide if this is a critical error: sys.exit(1)
        
        df = df.dropna(subset=['date', 'uv_index']) # Ensure critical columns are good after conversion

        if df.empty:
            print("<p>No valid forecast data to display after processing. Check for parsing errors or missing critical data.</p>")
            sys.exit(1)

        email_content = create_email_body(location_name, df)

        SENDER_EMAIL = os.environ.get('EMAIL_ADDRESS')
        RECEIVER_EMAILS_STR = os.environ.get('EMAIL_RECIPIENT') # Changed variable name for clarity
        SMTP_SERVER = os.environ.get('SMTP_SERVER')
        SMTP_PORT_STR = os.environ.get('SMTP_PORT')
        SMTP_USERNAME = os.environ.get('EMAIL_ADDRESS')
        SMTP_PASSWORD = os.environ.get('EMAIL_PASSWORD')

        if not all([SENDER_EMAIL, RECEIVER_EMAILS_STR, SMTP_SERVER, SMTP_PORT_STR, SMTP_USERNAME, SMTP_PASSWORD]):
            print("One or more email environment variables are not set. Email not sent.")
            print("Ensure EMAIL_ADDRESS, EMAIL_PASSWORD, EMAIL_RECIPIENT, SMTP_SERVER, SMTP_PORT are set.")
            sys.exit(1) # Critical: cannot send email
        
        try:
            smtp_port_int = int(SMTP_PORT_STR)
        except ValueError:
            print("Error: SMTP_PORT environment variable is not a valid integer.")
            sys.exit(1)

        email_subject = f"Daily UV Forecast for {location_name} - {df.iloc[0]['date'].strftime('%A, %B %d')}"
        if not send_email(email_subject, email_content, SENDER_EMAIL, RECEIVER_EMAILS_STR, SMTP_SERVER, smtp_port_int, SMTP_USERNAME, SMTP_PASSWORD):
            print("Email sending failed. Exiting with error.")
            sys.exit(1) # Critical: email failed to send

    except pd.errors.EmptyDataError:
        print("<p>Pandas read_html found a table but it was empty or unparseable.</p>")
        sys.exit(1)
    except KeyError as e:
        print(f"<p>A required column was not found in the parsed data: {e}. The table structure might have changed.</p>")
        sys.exit(1)
    except Exception as e:
        print(f"<p>An unexpected error occurred during table processing: {e}</p>")
        sys.exit(1)

if __name__ == "__main__":
    main()