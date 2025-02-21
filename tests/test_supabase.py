import configparser
import asyncio
from supabase import AsyncClient

# Read the properties file
config = configparser.ConfigParser()
config.read('local_config.properties')

# Extract values from the properties file
SUPABASE_URL = config.get('DEFAULT', 'SUPABASE_URL')
SUPABASE_KEY = config.get('DEFAULT', 'SUPABASE_KEY')

# Initialize Supabase client
supabase = AsyncClient(SUPABASE_URL, SUPABASE_KEY)

# Test data to insert and update
test_url = "https://apnews.com/article/trump-air-force-one-boeing-plane-355ed87b00d7d82a061297f68c4ed89b"
test_headline = "Trump says he’s considering buying used planes to serve as Air Force One amid Boeing delays"
test_content = "WASHINGTON (AP) — President Donald Trump said Wednesday he is considering buying used Boeing aircraft — perhaps from an overseas seller — to use as Air Force One when he’s aboard, as he fumes over the U.S. plane-maker’s delays in producing two specially modified ones for presidential use."

# Full test data with all fields
test_data = {
    "url": test_url,
    "headline": test_headline,
    "content": test_content,
    "sentiment": "Neutral",
    "bias": "Strongly Left",
    "bias_score": -1.0,
    "bias_percentage": 100.0,
    "flagged_phrases": [],
    "media_score": {
        "media_unmasked_score": 49.6,
        "rating": "Misleading",
        "details": {
            "headline_analysis": {
                "headline_vs_content_score": 38.5,
                "contradictory_phrases": []
            },
            "sentiment_analysis": {
                "sentiment": "Neutral",
                "manipulation_score": 0.0,
                "flagged_phrases": []
            },
            "bias_analysis": {
                "bias": "Strongly Left",
                "bias_score": -1.0,
                "bias_percentage": 100.0
            },
            "evidence_analysis": {
                "evidence_based_score": 60.0
            }
        }
    }
}

# 1. Insert data into the 'article_analysis' table
async def insert_data():
    try:
        # Use upsert with conflict on the 'url' field
        response = await supabase.table('article_analysis').upsert(test_data, on_conflict=['url']).execute()
        print("Data inserted or updated successfully")
        print(f"Response data: {response.data}")
    except Exception as e:
        print(f"Error inserting or updating data: {str(e)}")

# 2. Update data (e.g., changing the sentiment)
async def update_data():
    try:
        updated_sentiment = "Positive"
        # Ensure that we are not leaving any required fields as null
        response = await supabase.table('article_analysis').upsert({
            'url': test_url,
            'sentiment': updated_sentiment,
            'headline': test_headline,
            'content': test_content,
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
        }, on_conflict=['url']).execute()  # Use on_conflict to handle the conflict by updating the existing URL row
        print("Data updated successfully")
        print(f"Response data: {response.data}")
    except Exception as e:
        print(f"Error updating data: {str(e)}")

# 3. Retrieve data by URL
async def retrieve_data():
    try:
        result = await supabase.table('article_analysis').select('*').eq('url', test_url).execute()
        if result.data:
            print(f"Retrieved data: {result.data}")
        else:
            print("No data found for the given URL")
    except Exception as e:
        print(f"Error retrieving data: {str(e)}")

# Run the tests: Insert, Update, and Retrieve data
async def run_tests():
    await insert_data()
    await update_data()
    await retrieve_data()

# Execute the async function using asyncio
if __name__ == "__main__":
    asyncio.run(run_tests())
