from transformers import pipeline, AutoTokenizer
import unittest
from mediaunmasked.scrapers.article_scraper import ArticleScraper
from tabulate import tabulate
import torch
from typing import List
import logging
import transformers

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MediaUnmaskLLMTester(unittest.TestCase):
    transformers.logging.set_verbosity_error()
    def setUp(self):
        """Set up LLMs and scrape article."""
        self.models = {
            # Upgraded Evidence-Based Models
            "RoBERTa-MNLI": {"model": "roberta-large-mnli", "max_length": 512},  # Corrected to standard MNLI model
            "DeBERTa-Fact": {"model": "MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli", "max_length": 512},
            "T5-Large": {"model": "google/t5-v1_1-large", "max_length": 512},
            "SciBERT": {"model": "allenai/scibert_scivocab_uncased", "max_length": 512},
            "BART-FEVER": {"model": "facebook/bart-large", "max_length": 1024},  # Note: Needs FEVER fine-tuning
            "MultiQA-MiniLM": {"model": "sentence-transformers/multi-qa-MiniLM-L6-cos-v1", "max_length": 512},

            # Existing Models for Benchmarking
            "BART-MNLI": {"model": "facebook/bart-large-mnli", "max_length": 1024},
            "RoBERTa-Bias": {"model": "cardiffnlp/twitter-roberta-base-hate", "max_length": 512},
            "DistilBERT-Sentiment": {"model": "distilbert-base-uncased-finetuned-sst-2-english", "max_length": 512},
            "GPT2-Generation": {"model": "gpt2", "max_length": 1024},
        }

        self.device = 0 if torch.cuda.is_available() else -1
        self.scraper = ArticleScraper()
        self.article_url = "https://www.snopes.com/fact-check/trump-super-bowl-cost-taxpayers/"
        self.article_data = self.scraper.scrape_article(self.article_url) or {}

        self.results = {
            "headline": self.article_data.get("headline", "No headline"),
            "content": self.article_data.get("content", "No content available"),
            "scores": {}
        }

        self.tokenizers = {name: AutoTokenizer.from_pretrained(model["model"]) for name, model in self.models.items()}

    def _split_content(self, model_name: str, content: str) -> List[str]:
        """Split content into sections within model token limits, ensuring valid output."""
        tokenizer = self.tokenizers[model_name]
        max_length = self.models[model_name]["max_length"]

        if not content or not content.strip():
            return ["No valid content"]

        encoded = tokenizer.encode_plus(content, add_special_tokens=True, truncation=True, max_length=max_length)
        decoded = tokenizer.decode(encoded["input_ids"], skip_special_tokens=True)
        
        return [decoded] if decoded.strip() else ["No valid content"]

    def _get_flagged_phrases(self, model_pipeline, sections, threshold=0.6, top_k=5):
        """Extract top-scoring flagged phrases while handling None values safely."""
        if not sections or not isinstance(sections, list):
            return [("None", "N/A")]

        flagged_phrases = []
        
        for section in sections:
            if not section or not isinstance(section, str) or not section.strip():  # Ensure section is a valid string
                continue

            sentences = [s.strip() for s in section.split(". ") if s.strip()]
            for sentence in sentences:
                if not sentence or not isinstance(sentence, str):  # Double-check before running the model
                    continue

                try:
                    preds = model_pipeline(sentence)
                    if preds and isinstance(preds, list):
                        top_pred = max(preds, key=lambda x: x["score"])
                        if top_pred["score"] >= threshold:
                            short_phrase = " ".join(sentence.split()[:10])  # Shorten for readability
                            flagged_phrases.append((short_phrase, top_pred["score"], top_pred["label"]))
                except Exception as e:
                    logger.error(f"Error analyzing sentence: {e}")
                    continue

        flagged_phrases.sort(key=lambda x: x[1], reverse=True)
        return [(phrase, label) for phrase, _, label in flagged_phrases[:top_k]] or [("None", "N/A")]

    def test_headline_vs_content(self):
        """Check headline-content alignment."""
        headline = self.results["headline"]
        content = self.results["content"]

        for model_name in self.models:
            with self.subTest(model=model_name):
                analyzer = pipeline("text-classification", model=self.models[model_name]["model"], device=self.device)
                sections = self._split_content(model_name, content)

                headline_score = max(analyzer(headline), key=lambda x: x["score"])["score"]
                content_scores = [max(analyzer(section), key=lambda x: x["score"])["score"] for section in sections]
                avg_content_score = sum(content_scores) / len(content_scores)
                consistency_score = abs(headline_score - avg_content_score)

                flagged_phrases = self._get_flagged_phrases(analyzer, sections)
                self.results["scores"].setdefault("headline_vs_content", {})[model_name] = {
                    "score": consistency_score,
                    "flagged_phrases": flagged_phrases
                }
                self.assertIsNotNone(consistency_score)

    def test_evidence_based(self):
        """Test evidence-based content."""
        content = self.results["content"]

        for model_name in self.models:
            if any(keyword in model_name.lower() for keyword in ["mnli", "fact", "fever", "qa"]):
                with self.subTest(model=model_name):
                    classifier = pipeline("zero-shot-classification", model=self.models[model_name]["model"], device=self.device)
                    sections = self._split_content(model_name, content)

                    results = [classifier(section, candidate_labels=["evidence-based", "opinion", "misleading"]) for section in sections]
                    avg_score = sum(r["scores"][r["labels"].index("evidence-based")] for r in results) / len(results)

                    flagged_phrases = self._get_flagged_phrases(classifier, sections)
                    self.results["scores"].setdefault("evidence_based", {})[model_name] = {
                        "score": avg_score,
                        "flagged_phrases": flagged_phrases
                    }
                    self.assertIsNotNone(avg_score)

    def test_manipulative_language(self):
        """Detect manipulative language."""
        content = self.results["content"]

        for model_name in self.models:
            if "sentiment" in model_name.lower() or "emotion" in model_name.lower() or "gpt" in model_name.lower():
                with self.subTest(model=model_name):
                    detector = pipeline("text-classification", model=self.models[model_name]["model"], device=self.device)
                    sections = self._split_content(model_name, content)

                    results = [max(detector(section), key=lambda x: x["score"]) for section in sections]
                    avg_score = sum(r["score"] for r in results) / len(results)

                    flagged_phrases = self._get_flagged_phrases(detector, sections)
                    self.results["scores"].setdefault("manipulative_language", {})[model_name] = {
                        "score": avg_score,
                        "flagged_phrases": flagged_phrases
                    }
                    self.assertIsNotNone(avg_score)

    def test_bias_detection(self):
        """Detect bias."""
        content = self.results["content"]

        for model_name in self.models:
            if "bias" in model_name.lower() or "toxic" in model_name.lower() or "roberta" in model_name.lower():
                with self.subTest(model=model_name):
                    detector = pipeline("text-classification", model=self.models[model_name]["model"], device=self.device)
                    sections = self._split_content(model_name, content)

                    results = [max(detector(section), key=lambda x: x["score"]) for section in sections]
                    avg_score = sum(r["score"] for r in results) / len(results)

                    flagged_phrases = self._get_flagged_phrases(detector, sections)
                    self.results["scores"].setdefault("bias_detection", {})[model_name] = {
                        "score": avg_score,
                        "flagged_phrases": flagged_phrases
                    }
                    self.assertIsNotNone(avg_score)

    def tearDown(self):
        """Print top 2 models per test with clearer formatting."""
        print("\n=== Top Model Recommendations ===")
        
        for test_type, model_results in self.results["scores"].items():
            print(f"\nTop 2 Models for {test_type}:")
            
            sorted_results = sorted(
                model_results.items(),
                key=lambda x: x[1]["score"],
                reverse=(test_type != "headline_vs_content")
            )
            
            top_2 = sorted_results[:2]
            table = [
                [
                    model,
                    f"{res['score']:.6f}",
                    ", ".join(f"{phrase} ({label})" for phrase, label in res["flagged_phrases"])
                ]
                for model, res in top_2
            ]

            print(tabulate(table, headers=["Model", "Score", "Flagged Phrases"], tablefmt="grid"))
            criteria = "Lowest consistency score (better alignment)" if test_type == "headline_vs_content" else "Highest detection score"
            print(f"Criteria: {criteria}")

if __name__ == "__main__":
    unittest.main()