# Media Unmasked API

## Project Overview

Media Unmasked API is an AI-powered tool designed to detect media bias in articles. It scrapes articles from the web, analyzes their content for bias, sentiment, and credibility, and provides a comprehensive analysis report.

## Features

- Scrape articles from various websites
- Analyze content for bias and sentiment
- Provide detailed analysis reports
- Store analysis results in a database

## Installation

To set up the project locally, follow these steps:

1. Clone the repository:
   ```bash
   git clone https://github.com/LtShibby/media-unmasked-api.git
   ```

2. Navigate to the project directory:
   ```bash
   cd media-unmasked-api
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables by creating a `.env` file based on the `.env.example` provided.

## Usage

To run the application, use the following command:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 7860 --reload
```

Once the server is running, you can access the API at `http://localhost:7860`.

## Configuration

The application can be configured using environment variables. Key variables include:

- `SUPABASE_URL`: The URL for the Supabase database.
- `SUPABASE_KEY`: The API key for accessing Supabase.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request for any improvements or bug fixes.

## License

This project is licensed under the Apache-2.0 License.

## Contact

For any questions or inquiries, please [contact the maintainers](https://wozwize.com/contact).

## About

MediaUnmasked is a product of [Wozwize](https://wozwize.com), dedicated to providing insightful analysis of media content.