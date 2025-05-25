import requests
import pandas as pd
from bs4 import BeautifulSoup
from io import StringIO
import os

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
        return None

def create_email_body(location, forecast_df):
    if forecast_df.empty:
        return "<p>Could not retrieve UV forecast data.</p>"

    today_forecast = forecast_df.iloc[0]
    advice, color = get_uv_protection_advice(today_forecast['uv_index'])

    email_html = f"""\
    <html>
    <head>
        <style>
            body {{ font-family: sans-serif; margin: 20px; }}
            h1 {{ color: #333; }}
            h2 {{ color: #555; }}
            table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            .uv-today {{ background-color: {color}; color: {'black' if color not in ['#d8001d', '#b54cff'] else 'white'}; padding: 10px; border-radius: 5px; }}
            .footer {{ font-size: 0.8em; color: #777; margin-top: 30px; }}
        </style>
    </head>
    <body>
        <h1>UV Forecast for {location}</h1>
        
        <h2>Today's Forecast ({today_forecast['date'].strftime('%A, %B %d, %Y')})</h2>
        <div class="uv-today">
            <p><strong>UV Index: {today_forecast['uv_index']}</strong></p>
            <p>{advice}</p>
            <p>Ozone Column: {today_forecast['ozone_column']:.1f} DU</p>
        </div>

        <h2>Weekly Outlook</h2>
        <table>
            <tr><th>Date</th><th>UV Index</th><th>Ozone Column (DU)</th><th>Protection Advice</th></tr>
    """
    for _, row in forecast_df.iterrows():
        advice_loop, color_loop = get_uv_protection_advice(row['uv_index'])
        email_html += f"""\
            <tr>
                <td>{row['date'].strftime('%A, %b %d')}</td>
                <td style="background-color:{color_loop}; color:{'black' if color_loop not in ['#d8001d', '#b54cff'] else 'white'}">{row['uv_index']}</td>
                <td>{row['ozone_column']:.1f}</td>
                <td>{advice_loop.split(':')[0]}</td>
            </tr>
        """
    email_html += """\
        </table>
        <p class="footer">Data sourced from the <a href="https://www.temis.nl/uvradiation/nrt/uvindex.php?lon=-118.02&lat=35.12">Royal Netherlands Meteorological Institute</a>. Stay safe!</p>
    </body>
    </html>
    """
    return email_html

html_page = fetch_html_content(url)
location_name = "Your Location" # Default if not found

if html_page:
    soup = BeautifulSoup(html_page, 'html.parser')
    forecast_table_element = soup.find('table', {'border': '2'})

    if forecast_table_element:
        try:
            # Try to extract location from H2 tag within the table
            h2_tag = forecast_table_element.find('h2')
            if h2_tag and h2_tag.string:
                location_name = h2_tag.string.strip()

            df_list = pd.read_html(StringIO(str(forecast_table_element)), header=1)
            
            if df_list:
                df = df_list[0]
                df = df.iloc[1:] # Skip the first data row (which was the HTML h2 title)
                df = df.dropna(subset=['UV index', 'ozone column']) # Drop metadata/footer rows
                df = df.reset_index(drop=True)

                # Snake_case column names
                df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
                
                # Ensure 'date' column exists before trying to rename
                if 'date' in df.columns:
                    pass # Already named 'date' effectively by snake_casing
                # Rename other columns if necessary, though snake_casing should handle them
                # e.g. df = df.rename(columns={'uv_index': 'uv_index', 'ozone_column': 'ozone_column'})

                if 'ozone_column' in df.columns:
                    df['ozone_column'] = df['ozone_column'].astype(str).str.replace('DU', '', regex=False).str.strip()
                    df['ozone_column'] = pd.to_numeric(df['ozone_column'], errors='coerce')
                
                if 'uv_index' in df.columns:
                    df['uv_index'] = pd.to_numeric(df['uv_index'], errors='coerce')
                
                if 'date' in df.columns:
                    df['date'] = df['date'].astype(str).str.strip()
                    try:
                        df['date'] = pd.to_datetime(df['date'])
                    except ValueError as e:
                        # Fallback for dates that might not parse with default format
                        try:
                            df['date'] = pd.to_datetime(df['date'], format='%d %B %Y', errors='coerce')
                        except Exception as final_e:
                             print(f"Warning: Could not parse all dates in 'Date' column accurately. Error: {final_e}")
                             df['date'] = pd.NaT # Set to NaT if parsing fails
                
                # Drop rows where date parsing failed
                df = df.dropna(subset=['date'])

                if not df.empty:
                    email_content = create_email_body(location_name, df)
                    print(email_content)
                else:
                    print("<p>No valid forecast data to display after processing.</p>")

            else:
                print("<p>Pandas could not parse the table found by BeautifulSoup.</p>")
        except Exception as e:
            print(f"<p>An error occurred during table processing: {e}</p>")
    else:
        print("<p>Could not find the forecast table in the HTML. The website structure might have changed.</p>")
else:
    print("<p>Failed to fetch HTML content.</p>")