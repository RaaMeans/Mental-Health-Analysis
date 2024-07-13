from flask import Flask, request, render_template, redirect, url_for, jsonify
import pandas as pd
import plotly.express as px
import plotly.io as pio
import os
from sqlalchemy import create_engine

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

# MySQL connection setup
DATABASE_URI = 'mysql+pymysql://root:12345@localhost:3306/mental_health'
engine = create_engine(DATABASE_URI)

summary_data = None
dataframe_html = None
total_records = 0
chart_paths = []
chart_names = []
chart_descriptions = []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)

    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)

    if file:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)

        # Load the entire CSV into a Pandas DataFrame for analysis
        df = pd.read_csv(filepath)

        # Create a truncated DataFrame for display (first 100 rows)
        truncated_df = df.head(100)

        # Extract insights using the entire DataFrame
        global summary_data, dataframe_html, total_records
        summary_data = df.describe().to_html()
        dataframe_html = truncated_df.to_html()
        total_records = len(df)

        # Gender distribution
        gender_distribution = df['Gender'].value_counts(normalize=True) * 100

        # Country distribution (Top 10 countries)
        country_distribution = df['Country'].value_counts().head(10)

        # Family History vs. Treatment
        family_history_treatment = df.groupby('family_history')['treatment'].value_counts(normalize=True).unstack() * 100

        # Days Spent Indoors vs. Stress Levels
        days_indoors_stress = df.groupby('Days_Indoors')['Growing_Stress'].value_counts(normalize=True).unstack() * 100

        # Mental Health History vs. Current Treatment
        mental_health_history_treatment = df.groupby('Mental_Health_History')['treatment'].value_counts(normalize=True).unstack() * 100

        try:
            # Save insights to the database, without creating an index
            df.describe().to_sql('summary', engine, if_exists='replace', index=False)
        except Exception as e:
            return f"An error occurred while saving to the database: {e}"

        global chart_paths, chart_names, chart_descriptions
        chart_paths = []
        chart_names = []
        chart_descriptions = []

        # Create charts for each insight using Plotly
        # Gender Distribution Chart
        fig = px.bar(gender_distribution, title='Gender Distribution', labels={'index': 'Gender', 'value': 'Percentage'})
        chart_path = os.path.join('static', 'chart_gender_distribution.html')
        pio.write_html(fig, file=chart_path, auto_open=False)
        chart_paths.append('chart_gender_distribution.html')
        chart_names.append('Gender Distribution')
        chart_descriptions.append("This chart displays the distribution of genders within the dataset. It visualizes the proportion of different gender categories among the respondents.")

        # Country Distribution Chart
        fig = px.bar(country_distribution, title='Top 10 Countries Distribution', labels={'index': 'Country', 'value': 'Number of Participants'})
        chart_path = os.path.join('static', 'chart_country_distribution.html')
        pio.write_html(fig, file=chart_path, auto_open=False)
        chart_paths.append('chart_country_distribution.html')
        chart_names.append('Top 10 Countries Distribution')
        chart_descriptions.append("This chart represents the distribution of respondents across different countries. It shows the number of respondents from each country, highlighting the top 10 countries in the dataset.")

        # Family History vs. Treatment Chart
        fig = px.bar(family_history_treatment, title='Family History vs. Treatment', labels={'index': 'Family History', 'value': 'Percentage'}, barmode='stack')
        chart_path = os.path.join('static', 'chart_family_history_treatment.html')
        pio.write_html(fig, file=chart_path, auto_open=False)
        chart_paths.append('chart_family_history_treatment.html')
        chart_names.append('Family History vs. Treatment')
        chart_descriptions.append("This chart analyzes the relationship between having a family history of mental health issues and the respondents' current treatment status.")

        # Days Indoors vs. Stress Levels Chart
        fig = px.bar(days_indoors_stress, title='Days Indoors vs. Stress Levels', labels={'index': 'Days Indoors', 'value': 'Percentage'}, barmode='stack')
        chart_path = os.path.join('static', 'chart_days_indoors_stress.html')
        pio.write_html(fig, file=chart_path, auto_open=False)
        chart_paths.append('chart_days_indoors_stress.html')
        chart_names.append('Days Indoors vs. Stress Levels')
        chart_descriptions.append("This chart explores the relationship between the number of days respondents spend indoors and their reported stress levels.")

        # Mental Health History vs. Current Treatment Chart
        fig = px.bar(mental_health_history_treatment, title='Mental Health History vs. Current Treatment', labels={'index': 'Mental Health History', 'value': 'Percentage'}, barmode='stack')
        chart_path = os.path.join('static', 'chart_mental_health_history_treatment.html')
        pio.write_html(fig, file=chart_path, auto_open=False)
        chart_paths.append('chart_mental_health_history_treatment.html')
        chart_names.append('Mental Health History vs. Current Treatment')
        chart_descriptions.append("This chart examines the relationship between respondents' mental health history and their current treatment status.")

        return redirect(url_for('summary'))

@app.route('/summary')
def summary():
    total_charts = len(chart_paths)
    return render_template('summary.html', chart_paths=chart_paths, chart_names=chart_names, total_charts=total_charts, summary_data=summary_data, dataframe_html=dataframe_html, total_records=total_records)

@app.route('/chart/<int:chart_id>')
def show_chart(chart_id):
    if chart_id < 0 or chart_id >= len(chart_paths):
        return redirect(url_for('summary'))

    chart_path = chart_paths[chart_id]
    chart_name = chart_names[chart_id]
    chart_description = chart_descriptions[chart_id]
    return render_template('chart.html', chart_path=chart_path, chart_name=chart_name, chart_description=chart_description, chart_id=chart_id, total_charts=len(chart_paths))

@app.route('/dataframe')
def show_dataframe():
    return render_template('dataframe.html', dataframe_html=dataframe_html)

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    if not os.path.exists('static'):
        os.makedirs('static')
    app.run(debug=True)
