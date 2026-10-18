# Student Performance Analytics

A student analytics dashboard built using Python, Apache Spark,
Hadoop HDFS, Streamlit, Pandas, and Plotly.

## Features

- Department-wise average score and attendance analytics
- Student performance analysis
- At-risk student identification
- Intervention recommendations
- CSV report downloads

## Technologies

- Python
- Apache Hadoop HDFS
- Apache Spark
- Streamlit
- Pandas
- Plotly

## Run the dashboard locally

Activate your virtual environment:

```bash
source .venv/bin/activate
pip install -r requirements.txt
streamlit run dashboard/app.py

## Step 4: Verify `requirements.txt`

Your earlier screenshot showed that this file was missing. Check it:

```bash
ls -l requirements.txt
cat > requirements.txt <<'EOF'
streamlit
pandas
plotly
