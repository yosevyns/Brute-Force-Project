from flask import Flask, render_template, request, jsonify
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import base64

app = Flask(__name__)

# Load the data
data = pd.read_csv('spotify.csv')
data['Artist Name'] = data['Artist Name'].str.strip()

# Fungsi rekursif untuk mencari lagu dengan solusi optimal secara brute force
def algoritma(data, criteria='total_streams', current_index=0, current_combination=None, best_combination=None, best_value=0):
    if current_combination is None:
        current_combination = []

    if current_index == len(data):
        current_value = sum(row['Total Streams'] for row in current_combination)
        if current_value > best_value:
            return current_combination, current_value
        else:
            return best_combination, best_value

    # Coba lagu saat ini masuk atau tidak masuk ke dalam kombinasi
    without_current_song = algoritma(data, criteria, current_index + 1, current_combination, best_combination, best_value)
    with_current_song = algoritma(data, criteria, current_index + 1, current_combination + [data.iloc[current_index]], best_combination, best_value)

    # Pilih kombinasi dengan nilai terbaik
    if with_current_song[1] > without_current_song[1]:
        return with_current_song
    else:
        return without_current_song

# Fungsi untuk menampilkan grafik berdasarkan kriteria tertentu
def plot_graph(data, criteria='total_streams'):
    x = data['Song Name'] + ' - ' + data['Artist Name']
    y = data[criteria]

    plt.figure(figsize=(12, 8))
    plt.bar(x, y, color='skyblue')
    plt.xlabel('Song - Artist')
    plt.ylabel(criteria.capitalize())
    plt.title(f'Graph of Songs based on {criteria.capitalize()}')
    plt.xticks(rotation=45, ha='right', fontsize=10)
    plt.tight_layout()

    # Save the plot to a BytesIO object and encode it to base64
    buffer = BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    plt.close()

    return image_base64

# Fungsi untuk menerapkan batasan dan menampilkan hasil dengan deskripsi lengkap
def apply_and_display_constraints(data, constraints=None):
    if constraints is None:
        constraints = {}

    filtered_data = data.copy()

    for criterion, value in constraints.items():
        if criterion == 'stream_min' and 'Total Streams' in filtered_data.columns and not pd.isna(value):
            filtered_data = filtered_data[filtered_data['Total Streams'] > value]
        elif criterion == 'days_min' and 'Days' in filtered_data.columns and not pd.isna(value):
            filtered_data = filtered_data[filtered_data['Days'] > value]
        elif criterion == 'artists' and 'Artist Name' in filtered_data.columns and value:
            # Membersihkan spasi ekstra di nama artis dalam batasan
            value = [artist.strip() for artist in value]
            filtered_data = filtered_data[filtered_data['Artist Name'].isin(value)]
        elif criterion == 'peak_position' and 'Peak Position' in filtered_data.columns and not pd.isna(value):
            filtered_data = filtered_data[filtered_data['Peak Position'] == filtered_data['Peak Position'].min()]
        elif criterion == 'top_10_entries' and 'Top 10 (xTimes)' in filtered_data.columns and not pd.isna(value):
            # Ensure the column exists before applying the filter
            filtered_data = filtered_data[filtered_data['Top 10 (xTimes)'] > value]

    # Menampilkan hasil dengan deskripsi lengkap
    if not filtered_data.empty:
        optimal_combination, total_value = algoritma(filtered_data, criteria='Total Streams')

        # Return the optimal combination, total value, and base64-encoded image
        return optimal_combination, total_value, plot_graph(filtered_data, criteria='Total Streams')
    else:
        return None


# Flask route to handle AJAX request and return artist names
@app.route('/get_artist_names', methods=['GET'])
def get_artist_names():
    artist_names = data['Artist Name'].unique().tolist()
    return jsonify({'artist_names': artist_names})

# Flask route to handle the request and render the results in a view
@app.route('/', methods=['GET', 'POST'])
def index():
    artist_names = data['Artist Name'].unique().tolist()
    
    if request.method == 'POST':
        # Collect user input
        user_input = {
            'stream_min': int(request.form['stream_min']) if request.form['stream_min'].isdigit() else 0,
            'days_min': int(request.form['days_min']) if request.form['days_min'].isdigit() else 0,
            'artists': [artist.strip() for artist in request.form.getlist('artists')],
            'top_10_entries': int(request.form['top_10_entries']) if request.form['top_10_entries'].isdigit() else 0,
            'peak_position': int(request.form['peak_position']) if request.form['peak_position'].isdigit() else 0,
        }

        # Apply constraints and display results
        result = apply_and_display_constraints(data, user_input)
        return render_template('index.html', result=result)
    else:
        return render_template('index.html', result=None)


if __name__ == '__main__':
    app.run(debug=True)
