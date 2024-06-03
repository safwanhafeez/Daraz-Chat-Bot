from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
from nltk import word_tokenize
from nltk.corpus import stopwords
import re

app = Flask(__name__)

df = pd.read_csv('src/final.csv')

keywords = ['1GB', '2GB', '3GB', '4GB', '8GB', '6GB', '10MP', '20MP', '32MP', '64MP', '108MP', 'fast charging']

def extract_brand_and_price(prompt):
    words = word_tokenize(prompt.lower())
    stop_words = set(stopwords.words("english"))

    words = [word for word in words if word.lower() not in stop_words]
    brand_name = next((word for word in words if word.lower() in df['Brand'].str.lower().values), None)

    if brand_name:
        words.remove(brand_name.lower())

    price = next((word for word in words if word.isdigit()), None)
    rating = extract_float(prompt)

    return brand_name, price, rating

def extract_float(str):
    words = word_tokenize(str.lower())

    for w in words:
        if '.' in w:
            return w

    return None

def process_search_results(brand_name):
    brand_data = df[df['Brand'].str.lower() == brand_name.lower()]

    if brand_data.empty:
        return None  # or handle this case as needed

    avg_price = brand_data['Price'].mean()
    highest_price = brand_data['Price'].max()
    lowest_price = brand_data['Price'].min()
    avg_sellerrating = brand_data['Seller Rating'].mean()
    avg_productrating = brand_data['Product Rating'].mean()
    avg_review_count = brand_data['Reviews'].mean()
    total_listings = len(brand_data)

    return {
        'avg_price': avg_price,
        'highest_price': highest_price,
        'lowest_price': lowest_price,
        'avg_sellerrating': avg_sellerrating,
        'avg_productrating': avg_productrating,
        'avg_review_count': avg_review_count,
        'total_listings': total_listings,
    }

@app.route('/', methods=['GET', 'POST'])
def filter_mobiles():
    try:
        data = pd.DataFrame()
        best_check = False

        if request.method == 'POST':
            prompt = str(request.form.get('prompt'))
            brand, price, rating = extract_brand_and_price(prompt)
            data = df

            lesser = ['lesser', 'less than', 'less', 'smaller', 'under', 'below']
            greater = ['greater', 'above', 'more than', 'starting']
            range = ['between', 'range', 'from']

            words = word_tokenize(prompt.lower())

            if brand:
                data = df[df['Brand'].str.lower() == brand.lower()]

            if price:
                if any(word in lesser for word in words):
                    data = data[data['Price'] <= int(price)]

                elif any(word in greater for word in words):
                    data = data[data['Price'] > int(price)]

                elif any(word in range for word in words):
                    prices = [int(word) for word in words if word.isdigit()]

                    if len(prices) == 2:
                        data = data[(data['Price'] >= prices[0]) & (data['Price'] <= prices[1])]

                else:
                    data = data[data['Price'] <= int(price)]

            if rating:
                if any(word in lesser for word in words):
                    data = data[data['Product Rating'] <= float(rating)]
                    
                elif any(word in greater for word in words):
                    data = data[data['Product Rating'] > float(rating)]

                elif any(word in range for word in words):
                    ratings = [float(word) for word in words if word.replace('.', '', 1).isdigit()]
                    
                    if len(ratings) == 2:
                        data = data[(data['Product Rating'] >= ratings[0]) & (data['Product Rating'] <= ratings[1])]
                else:
                    data = data[data['Product Rating'] == float(rating)]

            if 'best' in prompt:
                best_check = True
                data = data.sort_values('Rank', ascending=False)
                data = data.head(10)

            elif brand is None and price is None and rating is None and not best_check:
                data = pd.DataFrame()

        if data.empty:
            raise ValueError("No results found for the given criteria.")

        result_mobiles = data.to_dict(orient='records')

        return render_template('home.html', mobiles=result_mobiles)

    except Exception as e:
        return render_template('home.html', error=str(e))

@app.route('/sellerdashboard', methods=['GET', 'POST'])
def seller_dashboard():
    if request.method == 'POST':
        user_search = request.form.get('usersearch', '')
        results = process_search_results(user_search)

        if results is not None:
            return render_template('dashboard.html', usersearch=user_search, **results)
        else:
            return render_template('dashboard.html', usersearch=user_search, error='Brand not found.')

    else:
        return render_template('dashboard.html', usersearch=None)

@app.route('/stats')
def statistics():
    return render_template('stats.html')

if __name__ == '__main__':
    app.run(debug=True)