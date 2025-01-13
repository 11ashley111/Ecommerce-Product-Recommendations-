from flask import Flask,request,render_template
import pandas as pd 
import random
import pymysql
pymysql.install_as_MySQLdb()

from flask_sqlalchemy import SQLAlchemy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd



app = Flask(__name__)

# load files 
trending_products=pd.read_csv("models/trending_products.csv")
train_data=pd.read_csv("models/clean_data.csv")

# database configuration---------------------------------------
app.secret_key = "Iphone12promax1"
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql://root:@localhost/ecomer"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define your model class for the 'signup' table
class Signup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)

# Define your model class for the 'signup' table
class Signin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)


# Function to truncate product name
def truncate(text, length):
    if len(text) > length:
        return text[:length] + "..."
    else:
        return text
    
    
def content_based_recommendations(train_data, input_name, top_n=10):
    # Ensure the 'Tags' column has no NaN values
    train_data['Tags'] = train_data['Tags'].fillna('')

    # Combine the input product's "tags" with the dataset's "Tags"
    combined_tags = train_data['Tags'].tolist() + [input_name]

    # Create a TF-IDF vectorizer for the tags
    tfidf_vectorizer = TfidfVectorizer(stop_words='english')

    # Apply TF-IDF vectorization to tags and the input name
    tfidf_matrix_content = tfidf_vectorizer.fit_transform(combined_tags)

    # Calculate cosine similarity between the input and dataset items
    cosine_similarities_content = cosine_similarity(
        tfidf_matrix_content[-1], tfidf_matrix_content[:-1]
    )  # Last row is the input

    # Get similarity scores for each item in the dataset
    similarity_scores = list(enumerate(cosine_similarities_content[0]))

    # Sort similar items by similarity score in descending order
    similarity_scores = sorted(similarity_scores, key=lambda x: x[1], reverse=True)

    # Get the top N most similar items
    top_similar_items = similarity_scores[:top_n]

    # Get the indices of the top similar items
    recommended_item_indices = [x[0] for x in top_similar_items]

    # Get the details of the top similar items
    recommended_items_details = train_data.iloc[recommended_item_indices][
        ['Name', 'ReviewCount', 'Brand', 'ImageURL', 'Tags']
    ]

    # If no recommendations are found (e.g., all similarity scores are 0), return an empty DataFrame
    if recommended_items_details.empty:
        print(f"No recommendations found for the input: '{input_name}'.")
        return pd.DataFrame(columns=['Name', 'ReviewCount', 'Brand', 'ImageURL', 'Tags'])

    return recommended_items_details



## route =================================================================================
random_image_urls = [
    "static/img/img_1.png",
    "static/img/img_2.png",
    "static/img/img_3.png",
    "static/img/img_4.png",
    "static/img/img_5.png",
    "static/img/img_6.png",
    "static/img/img_7.png",
    "static/img/img_8.png",
]


@app.route("/")
def index():
    # Create a list of random image URLs for each product
    random_product_image_urls = [random.choice(random_image_urls) for _ in range(len(trending_products))]
    price = [40, 50, 60, 70, 100, 122, 106, 50, 30, 50]
    return render_template('index.html',trending_products=trending_products.head(8),truncate = truncate,
                           random_product_image_urls=random_product_image_urls,
                           random_price = random.choice(price))


@app.route('/main')
def main():
    return render_template('main.html')

@app.route("/index")
def indexredirect():
    # Create a list of random image URLs for each product
    random_product_image_urls = [random.choice(random_image_urls) for _ in range(len(trending_products))]
    price = [40, 50, 60, 70, 100, 122, 106, 50, 30, 50]
    return render_template('index.html', trending_products=trending_products.head(8), truncate=truncate,
                           random_product_image_urls=random_product_image_urls,
                           random_price=random.choice(price))


@app.route("/signup", methods=['POST','GET'])
def signup():
    if request.method=='POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        new_signup = Signup(username=username, email=email, password=password)
        db.session.add(new_signup)
        db.session.commit()

        # Create a list of random image URLs for each product
        random_product_image_urls = [random.choice(random_image_urls) for _ in range(len(trending_products))]
        price = [40, 50, 60, 70, 100, 122, 106, 50, 30, 50]
        return render_template('index.html', trending_products=trending_products.head(8), truncate=truncate,
                               random_product_image_urls=random_product_image_urls, random_price=random.choice(price),
                               signup_message='User signed up successfully!'
                               )
        
        
@app.route('/signin', methods=['POST', 'GET'])
def signin():
    if request.method == 'POST':
        username = request.form['signinUsername']
        password = request.form['signinPassword']
        new_signup = Signin(username=username,password=password)
        db.session.add(new_signup)
        db.session.commit()

        # Create a list of random image URLs for each product
        random_product_image_urls = [random.choice(random_image_urls) for _ in range(len(trending_products))]
        price = [40, 50, 60, 70, 100, 122, 106, 50, 30, 50]
        return render_template('index.html', trending_products=trending_products.head(8), truncate=truncate,
                               random_product_image_urls=random_product_image_urls, random_price=random.choice(price),
                               signup_message='User signed in successfully!'
                               )

@app.route("/recommendations", methods=['POST', 'GET'])
def recommendations():
    if request.method == 'POST':
        prod = request.form.get('prod')
        nbr = int(request.form.get('nbr'))
        
        # Get recommendations
        content_based_rec = content_based_recommendations(train_data, prod, top_n=nbr)

        if content_based_rec.empty:
            # If no recommendations, send a message to the template
            message = "No recommendations available for this product."
            return render_template('main.html', message=message)
        else:
            # Assign random image URLs and prices to each recommended product
            random_product_image_urls = [random.choice(random_image_urls) for _ in range(len(content_based_rec))]
            random_prices = [random.choice([40, 50, 60, 70, 100, 122, 106, 50, 30, 50]) for _ in range(len(content_based_rec))]

            # Add these to the recommendations DataFrame
            #content_based_rec['ImageURL'] = random_product_image_urls
            #content_based_rec['Price'] = random_prices

            # Truncate product names for display
            content_based_rec['ShortName'] = content_based_rec['Name'].apply(lambda x: x[:12] + '...' if len(x) > 12 else x)

            return render_template('main.html', 
                                   content_based_rec=content_based_rec.to_dict(orient='records'),
                                   message=None)

if __name__ == '__main__':
    app.run(debug=True)

