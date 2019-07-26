# import libraries
import sys
import pandas as pd
from sqlalchemy import create_engine
import re
import nltk
nltk.download(['punkt', 'wordnet'])
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.pipeline import Pipeline, FeatureUnion
from sklearn.multioutput import MultiOutputClassifier
from sklearn.feature_extraction.text import CountVectorizer, TfidfTransformer
from sklearn.metrics import classification_report
import pickle

def load_data(database_filepath):
    # load data from database
    engine = create_engine('sqlite:///' + database_filepath)
    df = pd.read_sql('disasterResponse', engine)
    X = df['message']
    y = df.drop(['id', 'message', 'original', 'genre'], axis=1)
    category_names = y.columns
    return X, y, category_names


url_regex = 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
#a tokenization function to process your text data
def tokenize(text):
    detected_urls = re.findall(url_regex, text)
    for url in detected_urls:
        text = text.replace(url, 'urlplaceholder')
    
    tokens = word_tokenize(text)
    lemmatizer = WordNetLemmatizer()
    
    clean_tokens = []
    for tok in tokens:
        clean_tok = lemmatizer.lemmatize(tok).lower().strip()
        clean_tokens.append(clean_tok)
        
    return clean_tokens


def build_model():
    model = Pipeline([
        ('vect',CountVectorizer(tokenizer = tokenize)),
        ('tfidf',TfidfTransformer()),
        ('clf', MultiOutputClassifier(AdaBoostClassifier(n_estimators=100, learning_rate = 0.5)))
	])
    return model


def evaluate_model(model, X_test, y_test, category_names):
    #predict on the test data
    y_pred = model.predict(X_test)
    #classification report
    for i, col in enumerate(category_names): 
            print('---------------------------------')
            print(col)
            print(classification_report(y_test.iloc[:,i], y_pred[:,i]))


def save_model(model, model_filepath):
    # Save model to pickle
   pickle.dump(model, open(model_filepath, 'wb'))


def main():
    if len(sys.argv) == 3:
        database_filepath, model_filepath = sys.argv[1:]
        print('Loading data...\n    DATABASE: {}'.format(database_filepath))
        X, y, category_names = load_data(database_filepath)
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
        
        print('Building model...')
        model = build_model()
        
        print('Training model...')
        model.fit(X_train, y_train)
        
        print('Evaluating model...')
        evaluate_model(model, X_test, y_test, category_names)

        print('Saving model...\n    MODEL: {}'.format(model_filepath))
        save_model(model, model_filepath)

        print('Trained model saved!')

    else:
        print('Please provide the filepath of the disaster messages database '\
              'as the first argument and the filepath of the pickle file to '\
              'save the model to as the second argument. \n\nExample: python '\
              'train_classifier.py ../data/DisasterResponse.db classifier.pkl')


if __name__ == '__main__':
    main()