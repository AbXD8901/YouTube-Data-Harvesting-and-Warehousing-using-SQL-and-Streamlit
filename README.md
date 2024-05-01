# YouTube Channel Analytics Tool

This project is designed to fetch and analyze YouTube channel data using the YouTube Data API and store the fetched data into a MySQL database. It provides a Streamlit-based web interface that allows users to initiate data fetching, view, and analyze various statistics such as video views, comment counts, and channel popularity.

## Getting Started

These instructions will guide you through setting up the project on your local machine for development and testing purposes.

### Prerequisites

You need to have Python installed on your machine, along with pip to install the necessary packages. This project also requires access to a MySQL database.

```
python --version
pip --version
mysql --version
sqlalchemy --verion
pandas --version
```

You will also need a Google API key with access to the YouTube Data API. Refer to [Google Cloud Documentation](https://cloud.google.com/docs) to obtain an API key.

### Installing

Clone the repository to your local machine:

```
git clone https://github.com/yourusername/youtube-channel-analytics.git
cd youtube-channel-analytics
```

Install the required Python packages:

```
pip install -r requirements.txt
```

### Setup Database

Ensure your MySQL database is running and execute the SQL scripts found in `database_setup.sql` to create the necessary tables:

```
mysql -u username -p database_name < database_setup.sql
```

### Configuration

Create a `.env` file in the project directory and add your database credentials and API key:

```
DATABASE_URL=mysql+pymysql://username:password@localhost/dbname
API_KEY=your_youtube_data_api_key
```
(IMPORTANT ; TRY TO KEEP SIMPLE AND NEAT SCRIPT FOR EACH SECTION, ONLY ONE FULL SCRIPT BUT NEAT.)
### Running the Application

Run the Streamlit application using:
streamlit run app.py

Navigate to `http://localhost:8501` in your web browser to view the application.

## Usage

The application has two main sections:

1. **Data Loading Section**: Enter a YouTube channel ID and click the "Fetch and Load Data" button to retrieve and store channel, playlists, videos, and comments data.
2. **Query Section**: Select a predefined query from the dropdown menu and click "Get Answer" to execute the query and display results in the interface.

## Contributing

Contributions are welcome, especially on improving the efficiency of data fetching and expanding the set of analytics queries. Please fork the repository and submit a pull request with your enhancements.

##(Attaching a Script file) 

### Notes:
- **Adjust the URL** in the git clone command to your repository's URL.
- **Update the credentials** in the `.env` example as per your setup.
- **Modify and expand** the "Usage" section to include more specific details or screenshots if the application has a more complex interface or additional features.

This README should give anyone looking at your repository a clear understanding of what the project does, how to set it up, and how to use it.
