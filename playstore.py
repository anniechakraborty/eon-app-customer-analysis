from google_play_scraper import Sort, reviews_all
from deep_translator import GoogleTranslator
from dotenv import load_dotenv
from ollama import chat
import google.generativeai as genai

import pandas as pd
import os

load_dotenv()
class PlayStoreReviews:
    APP_ID = 'de.ones.eon.csc'
    file = "eon_europe_reviews.csv"
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
    GOOGLE_API = os.getenv('GOOGLE_API_KEY')

    few_shot_eg = """
            Example 1:
            Review: Fingerprint sensor still doesn't work, so you always have to provide your data, which is extremely annoying. Please fix errors! ..
            Category: app_operational_issues

            Example 2:
            Review: Very poor . Very poor customer service . Am still waiting my yealy calculation bill . You make great mistake on my yealy calculation bill and i am still waiting the correct one . I will not advice anyone to join E.on Germany . ðŸ˜’ðŸ˜’ðŸ˜’ðŸ˜’ðŸ˜’
            Category: billing_issues, customer_service

            Example 3:
            Review: Would be 5 stars if I could see the monthly usage. It is an essential feature. What's the point of entering the meter readings every month?
            Category:  feature_demand

            Example 4:
            Review: Slick app and easy to navigate. Pity the call center is so inefficient and waiting time to talk to an agent is absolutely ridiculous.
            Category: customer_service

            Example 5:
            Review: Hi to long for a little sleep
            Category: not_related

            Example 6:
            Review: If you do not give consent to advertising, the app annoys all the time that you have open tasks in the checklist. Awful.
            Category: app_operational_issues
        """
        

    def get_reviews(self):
        EU_COUNTRIES = [
            'de', 'fr', 'it', 'es', 'nl', 'pl', 'se', 'fi', 'dk', 'be',
            'at', 'ie', 'pt', 'cz', 'sk', 'gr', 'hu', 'ro', 'bg', 'hr',
            'si', 'ee', 'lv', 'lt', 'lu', 'mt', 'cy'
        ]

        LANGUAGES = ['en', 'de']

        all_reviews = []
        for lang in LANGUAGES:
            for country in EU_COUNTRIES:
                print(f"Fetching reviews for lang={lang}, country={country}...")
                try:
                    reviews = reviews_all(
                        self.APP_ID,
                        sleep_milliseconds=0,
                        lang=lang,
                        country=country,
                        sort=Sort.NEWEST
                    )
                    print(f" -> Retrieved {len(reviews)} reviews")
                    all_reviews.extend(reviews)
                except Exception as e:
                    print(f" !! Error for lang={lang}, country={country}: {e}")
                
        # Convert to DataFrame
        df = pd.DataFrame(all_reviews)
        df.drop_duplicates(subset="reviewId", inplace=True)

        # Saving to CSV
        df.to_csv(self.file, index=False)
        print(f"Reviews saved to {self.file}")
        print()
    
    def translate_reviews(self):
        df = pd.read_csv(self.file)
        def translate_if_needed(row):
            try:
                print(row['reviewId'])
                review = row['content']
                review_translated = ''
                if isinstance(review, str):
                    review = review.strip()
                    review_translated = GoogleTranslator(target='en').translate(review[:5000])
                    print(review_translated)
                    print()
                return review_translated
            except Exception as e:
                print(f"Translation error: {e}")
                return row['content']

        df['translated_content'] = df.apply(translate_if_needed, axis=1)
        print(df.head())
        df.to_csv(self.file, index=False)
        print(f"Reviews saved to {self.file}")
        
    def categorise_reviews_llama(self, review):
        prompt = f"""
            You are a helpful agent that is tasked with categorizing customer reviews into the following categories:
            ['language_feature', 'feature_demand', 'app_operational_issues', 'billing_issues', 'customer_service', 'smart_meter_operational_issues', 'positive_feedback', 'not_related', 'others']
            You are provided with some few-shot examples below to understand the categories appropriate for the review text. Use these examples to categorize the review text into the appropriate categories.
            Stick to the instructions mentioned below.

            Few-shot examples: {self.few_shot_eg}

            Instructions:
            1. For every review text, return a single word as the category.
            2. Don't need to provide an explanation.
            3. Don't invent new categories, use the category list: ['language_feature', 'feature_demand', 'app_operational_issues', 'billing_issues', 'customer_service', 'smart_meter_operational_issues', 'positive_feedback', 'not_related', 'others']

            Review: {review}
            The response should be a single word indicating the category for the review.
        """
        response = chat(
            model=self.OLLAMA_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        # print(prompt)
        # print('LLM response: ', response['message']['content'])
        # print()
        return response['message']['content']
    
    def categorise_reviews_gemini(self, review):
        genai.configure(api_key=self.GOOGLE_API)
        model = genai.GenerativeModel('gemini-2.0-flash')

        prompt = f"""
            You are a helpful agent that is tasked with categorizing customer reviews into the following categories:
            ['language_feature', 'feature_demand', 'app_operational_issues', 'billing_issues', 'customer_service', 'smart_meter_operational_issues', 'positive_feedback', 'not_related', 'others']
            You are provided with some few-shot examples below to understand the categories appropriate for the review text. Use these examples to categorize the review text into the appropriate categories.
            Stick to the instructions mentioned below.

            Few-shot examples: {self.few_shot_eg}

            Instructions:
            1. For every review text, return a single word as the category.
            2. Don't need to provide an explanation.
            3. Don't invent new categories, use the category list: ['language_feature', 'feature_demand', 'app_operational_issues', 'billing_issues', 'customer_service', 'smart_meter_operational_issues', 'positive_feedback', 'not_related', 'others']

            Review: {review}
            The response should be a single word indicating the category for the review.
        """
        response = model.generate_content(prompt)
        return response.text

    def visualise_reviews(self):
        df = pd.read_csv(self.file)
        print('Implementing categorization using LLAMA 3.2 and Gemini')
        for i in range(50):
            row = df.iloc[i]
            try:
                review = row['translated_content']
                print()
                print(review)
                category_llama = self.categorise_reviews_llama(review)
                print('Category LLAMA: ', category_llama)

                category_gemini = self.categorise_reviews_gemini(review)
                print('Category GEMINI: ', category_gemini)
            except Exception as e:
                print(f"Category error: {e}")
        # df['category'] = df.apply(review_category, axis=1)
        # print(df.head())
        # df.to_csv(self.file, index=False)
        # print(f"Reviews saved to {self.file}")
        



if __name__ == "__main__":
    ps_review = PlayStoreReviews()
    # ps_review.get_reviews()
    # ps_review.translate_reviews()
    ps_review.visualise_reviews()