# -*- coding: utf-8 -*-
"""
Netflix Data Analysis Flask Application
"""

from flask import Flask, render_template, request, jsonify
import pandas as pd
import json

app = Flask(__name__)

try:
    df = pd.read_csv('netflix_cleaned.csv')
except FileNotFoundError:
    print("❌ Error: netflix_cleaned.csv not found!")
    df = None


def get_filtered_data(dataframe, content_type=None):
    if dataframe is None or dataframe.empty:
        return dataframe
    
    if content_type and content_type != 'All':
        return dataframe[dataframe['type'] == content_type]
    
    return dataframe


def get_top_directors(dataframe, n=10):
    if dataframe is None or dataframe.empty:
        return {}
    
    directors_exploded = dataframe[dataframe['director'] != 'Not Available'].copy()
    if directors_exploded.empty:
        return {}
    
    directors_exploded['director'] = directors_exploded['director'].str.split(', ')
    directors_exploded = directors_exploded.explode('director')
    
    top_directors = directors_exploded['director'].value_counts().head(n)
    return top_directors.to_dict()


def get_top_countries(dataframe, n=10):
    if dataframe is None or dataframe.empty:
        return {}
    
    countries_exploded = dataframe[dataframe['country'] != 'Not Available'].copy()
    if countries_exploded.empty:
        return {}
    
    countries_exploded['country'] = countries_exploded['country'].str.split(', ')
    countries_exploded = countries_exploded.explode('country')
    
    top_countries = countries_exploded['country'].value_counts().head(n)
    return top_countries.to_dict()


def get_top_categories(dataframe, n=10):
    if dataframe is None or dataframe.empty:
        return {}
    
    categories_exploded = dataframe[dataframe['listed_in'] != 'Not Categorized'].copy()
    if categories_exploded.empty:
        return {}
    
    categories_exploded['listed_in'] = categories_exploded['listed_in'].str.split(', ')
    categories_exploded = categories_exploded.explode('listed_in')
    
    top_categories = categories_exploded['listed_in'].value_counts().head(n)
    return top_categories.to_dict()


def get_content_type_distribution(dataframe):
    if dataframe is None or dataframe.empty:
        return {}
    
    return dataframe['type'].value_counts().to_dict()


def get_rating_distribution(dataframe):
    if dataframe is None or dataframe.empty:
        return {}
    
    return dataframe[dataframe['rating'] != 'Not Rated']['rating'].value_counts().head(8).to_dict()


def get_content_by_year(dataframe, n=10):
    if dataframe is None or dataframe.empty:
        return {}
    
    return dataframe['year_added'].value_counts().sort_index().tail(n).to_dict()


def get_dataset_statistics(dataframe):
    if dataframe is None or dataframe.empty:
        return {}
    
    return {
        'total_titles': len(dataframe),
        'unique_directors': dataframe[dataframe['director'] != 'Not Available']['director'].nunique(),
        'unique_countries': dataframe[dataframe['country'] != 'Not Available']['country'].nunique(),
        'unique_categories': dataframe[dataframe['listed_in'] != 'Not Categorized']['listed_in'].nunique(),
        'average_rating': dataframe[dataframe['rating'] != 'Not Rated']['rating'].nunique(),
        'year_range': f"{int(dataframe['release_year'].min())} - {int(dataframe['release_year'].max())}",
        'movies_count': len(dataframe[dataframe['type'] == 'Movie']),
        'tv_shows_count': len(dataframe[dataframe['type'] == 'TV Show']),
    }


def prepare_chart_data(directors, countries, categories, types, ratings, years):
    return {
        'directors': [{'name': k, 'count': v} for k, v in list(directors.items())],
        'countries': [{'name': k, 'count': v} for k, v in list(countries.items())],
        'categories': [{'name': k, 'count': v} for k, v in list(categories.items())],
        'types': [{'name': k, 'count': v} for k, v in types.items()],
        'ratings': [{'name': k, 'count': v} for k, v in ratings.items()],
        'years': [{'year': int(k), 'count': v} for k, v in sorted(years.items())]
    }


@app.route('/')
def index():
    if df is None:
        return "Error: Data not loaded", 500
    
    content_filter = request.args.get('filter', 'All')
    filtered_df = get_filtered_data(df, content_filter)
    
    top_directors = get_top_directors(filtered_df, n=10)
    top_countries = get_top_countries(filtered_df, n=10)
    top_categories = get_top_categories(filtered_df, n=10)
    content_type_dist = get_content_type_distribution(df)
    rating_dist = get_rating_distribution(filtered_df)
    content_by_year = get_content_by_year(filtered_df, n=10)
    dataset_stats = get_dataset_statistics(filtered_df)
    
    chart_data = prepare_chart_data(
        top_directors, top_countries, top_categories, 
        content_type_dist, rating_dist, content_by_year
    )
    
    return render_template(
        'index.html',
        current_filter=content_filter,
        dataset_stats=dataset_stats,
        directors=chart_data['directors'],
        countries=chart_data['countries'],
        categories=chart_data['categories'],
        content_types=chart_data['types'],
        ratings=chart_data['ratings'],
        content_by_year=chart_data['years'],
        directors_json=json.dumps(chart_data['directors']),
        countries_json=json.dumps(chart_data['countries']),
        categories_json=json.dumps(chart_data['categories']),
        types_json=json.dumps(chart_data['types']),
        ratings_json=json.dumps(chart_data['ratings']),
        years_json=json.dumps(chart_data['years'])
    )


@app.route('/api/filter', methods=['POST'])
def api_filter():
    if df is None:
        return {"error": "Data not loaded"}, 500
    
    content_type = request.json.get('filter', 'All')
    filtered_df = get_filtered_data(df, content_type)
    
    top_directors = get_top_directors(filtered_df, n=10)
    top_countries = get_top_countries(filtered_df, n=10)
    top_categories = get_top_categories(filtered_df, n=10)
    rating_dist = get_rating_distribution(filtered_df)
    content_by_year = get_content_by_year(filtered_df, n=10)
    dataset_stats = get_dataset_statistics(filtered_df)
    
    chart_data = prepare_chart_data(
        top_directors, top_countries, top_categories,
        get_content_type_distribution(df), rating_dist, content_by_year
    )
    
    return {
        'status': 'success',
        'filter': content_type,
        'stats': dataset_stats,
        'data': {
            'directors': chart_data['directors'],
            'countries': chart_data['countries'],
            'categories': chart_data['categories'],
            'ratings': chart_data['ratings'],
            'years': chart_data['years']
        }
    }


@app.route('/api/top-directors')
def api_top_directors():
    if df is None:
        return {"error": "Data not loaded"}, 500
    
    directors = get_top_directors(df, n=10)
    return {'status': 'success', 'data': directors}


@app.route('/api/top-countries')
def api_top_countries():
    if df is None:
        return {"error": "Data not loaded"}, 500
    
    countries = get_top_countries(df, n=10)
    return {'status': 'success', 'data': countries}


@app.route('/api/top-categories')
def api_top_categories():
    if df is None:
        return {"error": "Data not loaded"}, 500
    
    categories = get_top_categories(df, n=10)
    return {'status': 'success', 'data': categories}


@app.route('/api/statistics')
def api_statistics():
    if df is None:
        return {"error": "Data not loaded"}, 500
    
    stats = get_dataset_statistics(df)
    return {'status': 'success', 'data': stats}


@app.errorhandler(404)
def not_found(error):
    return "Page not found", 404


@app.errorhandler(500)
def server_error(error):
    return "Server error", 500


if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=5000)