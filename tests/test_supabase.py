import configparser
from supabase import create_client

# Read the properties file
config = configparser.ConfigParser()
config.read('local_config.properties')

# Extract values from the properties file
SUPABASE_URL = config.get('DEFAULT', 'SUPABASE_URL')
SUPABASE_KEY = config.get('DEFAULT', 'SUPABASE_KEY')

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Test data to insert and update
test_url = "https://www.straitstimes.com/world/united-states/us-senate-confirms-trump-loyalist-kash-patel-to-head-fbi"
test_headline = "US Senate confirms Trump loyalist Kash Patel to head FBI"
test_content = "This is some test content for the article."

# 1. Insert data into the 'article_analysis' table
def insert_data():
    try:
        response = supabase.table('article_analysis').upsert({
            'url': test_url,
            'headline': test_headline,
            'content': test_content,
            'sentiment': 'Neutral',
            'bias': 'Neutral',
            'bias_score': 0.0,
            'bias_percentage': 0.0,
            'flagged_phrases': [],
            'media_score': {
                'media_unmasked_score': 75.0,
                'rating': 'Neutral',
                'details': {
                    'headline_analysis': {'headline_vs_content_score': 50},
                    'sentiment_analysis': {'sentiment': 'Neutral'},
                    'bias_analysis': {'bias': 'Neutral'},
                    'evidence_analysis': {'evidence_based_score': 80.0}
                }
            }
        }).execute()
        print("Data inserted successfully")
        print(f"Response data: {response.data}")
    except Exception as e:
        print(f"Error inserting data: {str(e)}")

# 2. Update data (e.g., changing the sentiment)
def update_data():
    try:
        updated_sentiment = "Positive"
        response = supabase.table('article_analysis').upsert({
            'url': test_url,
            'sentiment': updated_sentiment  # Update only the sentiment field
        }).execute()
        print("Data updated successfully")
        print(f"Response data: {response.data}")
    except Exception as e:
        print(f"Error updating data: {str(e)}")

# 3. Retrieve data by URL
def retrieve_data():
    try:
        result = supabase.table('article_analysis').select('*').eq('url', test_url).execute()
        if result.data:
            print(f"Retrieved data: {result.data}")
        else:
            print("No data found for the given URL")
    except Exception as e:
        print(f"Error retrieving data: {str(e)}")

# Run the tests: Insert, Update, and Retrieve data
insert_data()
update_data()
retrieve_data() 