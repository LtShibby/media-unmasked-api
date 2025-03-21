Here’s your updated `README.md`, now with a **step-by-step Supabase table setup guide** for local testing. This version keeps the tone clean and practical while making sure your contributors don’t end up breaking production or getting lost.

---

```markdown
---
title: Media Unmasked API
emoji: 👀
colorFrom: purple
colorTo: red
sdk: docker
pinned: false
license: apache-2.0
short_description: AI-powered media bias detection API
---

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

4. Set up environment variables by creating a `.env` file.

## Usage

To run the application locally:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 7860 --reload
```

Access the API at: `http://localhost:7860`

## Configuration

The application is configured using environment variables. Be sure to include the following in your `.env` file:

- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_KEY`: Your Supabase anon or service role key

---

## 🔧 Supabase Setup Guide (for Local Testing)

To store analysis results in your Supabase database, create the required table like so:

### 1. Go to [Supabase](https://app.supabase.com/)

- Log in or create an account
- Create a new project
- Open your project and go to the **SQL Editor**

### 2. Paste and run the following SQL script to create the table:

```sql
CREATE TABLE public.article_analysis (
  id SERIAL PRIMARY KEY,
  url TEXT NOT NULL,
  headline TEXT NOT NULL,
  content TEXT NOT NULL,
  sentiment TEXT NOT NULL,
  bias TEXT NOT NULL,
  bias_score DOUBLE PRECISION NOT NULL,
  bias_percentage DOUBLE PRECISION NOT NULL,
  media_score JSONB NOT NULL,
  requester_id TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  analysis_mode TEXT NOT NULL
);
```

### 3. Get Your Supabase URL and Key

- Go to **Project Settings** → **API**
- Copy the `Project URL` and `anon/public API key`
- Paste them into your `.env` file like so:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
```

> ⚠️ For testing, the anon key is fine. For production or team testing, use a **service role key** with caution.

---

## Contributing

We love contributors. If you're interested in building AI scoring models, improving performance, or UX tweaks—jump in.

1. Fork the repo
2. Make changes on a branch
3. Submit a pull request with clear notes

## License

Apache-2.0

## Contact

[Reach out here](https://wozwize.com/contact) with questions or interest in deeper collaboration.

## About

MediaUnmasked is a project by [Wozwize](https://wozwize.com), dedicated to building transparent, powerful AI tooling to detect and expose media bias.
