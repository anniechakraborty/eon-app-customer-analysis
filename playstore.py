from google_play_scraper import Sort, reviews_all
from deep_translator import GoogleTranslator

import pandas as pd

class PlayStoreReviews:
    APP_ID = 'de.ones.eon.csc'
    file = "eon_europe_reviews.csv"

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
                eon_response = row['replyContent']
                review_translated = ''
                response_translated = ''
                if isinstance(review, str):
                    review = review.strip()
                    review_translated = GoogleTranslator(target='en').translate(review[:5000])
                    print(review_translated)
                    print()
                if isinstance(eon_response, str):
                    eon_response = eon_response.strip()
                    response_translated = GoogleTranslator(target='en').translate(eon_response[:5000])
                
                return review_translated, response_translated
            except Exception as e:
                print(f"Translation error: {e}")
                return row['content'], row['replyContent']

        df['translated_content'], df['translated_response_content'] = df.apply(translate_if_needed, axis=1)
        print(df.head())
        df.to_csv(self.file, index=False)
        print(f"Reviews saved to {self.file}")
        


    def visualise_reviews(self):
        
        df = pd.read_csv(self.file)
        print(df.head())
        print()



if __name__ == "__main__":
    ps_review = PlayStoreReviews()
    # ps_review.get_reviews()
    ps_review.translate_reviews()
    ps_review.visualise_reviews()