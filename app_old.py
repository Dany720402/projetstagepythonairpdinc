from flask import Flask,  Response, render_template_string, render_template, request, redirect, flash

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score
import requests
import matplotlib
matplotlib.use('Agg')  # Utiliser le backend 'Agg' pour les environnements sans interface graphique
import matplotlib.pyplot as plt
import io
import base64
import sqlite3

app = Flask(__name__)
app.secret_key = "secret_key"

@app.route('/')
def home():
    return render_template('index.html', message="Bienvenue sur notre site web dynamique !")

@app.route('/user/<username>')
def user_profile(username):
    return render_template('user.html', username=username)



# Route pour afficher le formulaire
@app.route('/integration-api-financieres/')
def form_invest():
    return render_template('integration-api.html')





def update_prix_action_actuel(noportefeuille):
    if not noportefeuille:
        print("Erreur : Veuillez fournir un numéro de portefeuille.")
        return

    try:

        # Configuration
        db_path = "saab.db"  # Chemin vers la base de données
        alpha_vantage_api_key = "TQXI3APYZZA55UK5"  # Remplacez par votre clé API Alpha Vantage
        base_url = "https://www.alphavantage.co/query"


        # Connexion à la base de données
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Permet de récupérer les résultats sous forme de dictionnaires
        cursor = conn.cursor()

        # Récupération des compagnies pour le portefeuille donné
        query = """
        SELECT id, symbolecompagnie
        FROM detailportefeuille
        WHERE noportefeuille = ?
        """
        cursor.execute(query, (noportefeuille,))
        rows = cursor.fetchall()

        if not rows:
            print("Aucune compagnie trouvée pour ce portefeuille.")
            return

        # Mise à jour des prix actuels pour chaque compagnie
        for row in rows:
            symbolecompagnie = row["symbolecompagnie"]
            id_record = row["id"]

            # Requête à l'API Alpha Vantage pour obtenir le dernier prix
            params = {
                "function": "GLOBAL_QUOTE",
                "symbol": symbolecompagnie,
                "apikey": alpha_vantage_api_key
            }
            response = requests.get(base_url, params=params)
            data = response.json()

            # Vérification des données reçues
            try:
                last_price = float(data["Global Quote"]["05. price"])
                print(f"Symbole : {symbolecompagnie}, Dernier prix : {last_price}")

                # Mise à jour de la base de données
                update_query = """
                UPDATE detailportefeuille
                SET prixactionactuel = ?
                WHERE id = ?
                """
                cursor.execute(update_query, (last_price, id_record))

            except (KeyError, ValueError):
                print(f"Erreur lors de la récupération du prix pour {symbolecompagnie}. Données reçues : {data}")

        # Validation des changements
        conn.commit()
        print("Mise à jour des prix terminée.")

    except sqlite3.Error as e:
        print(f"Erreur de base de données : {e}")
    except requests.RequestException as e:
        print(f"Erreur de requête : {e}")
    finally:
        if conn:
            conn.close()






# Route pour afficher le formulaire
@app.route('/portefeuille/')
def form_portefeuille():
    return render_template('totalportefeuille.html')

@app.route("/total-portefeuille", methods=["GET"])
def total_portefeuille():
    noportefeuille = request.args.get("noportefeuille")

    db_path = "saab.db"  # Chemin vers la base de données

    if not noportefeuille:
        return "<h1>Erreur : Veuillez fournir un numéro de portefeuille.</h1>"

    try:

        update_prix_action_actuel(noportefeuille)

        # Connexion à la base de données
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Permet de récupérer les résultats sous forme de dictionnaires
        cursor = conn.cursor()

        # Requête pour récupérer les informations
        query = """
        SELECT *, (nombreaction * prixaction) AS total,
        (nombreaction * prixactionactuel) AS totalactuel
        FROM detailportefeuille
        WHERE noportefeuille = ?
        """

        cursor.execute(query, (noportefeuille,))
        rows = cursor.fetchall()




        # Calcul du total global
        total_global = sum(row["total"] for row in rows)

        # Calcul du total global actuel
        total_global_actuel = sum(row["totalactuel"] for row in rows)

        gaintotal = total_global_actuel-total_global

        # Template HTML pour afficher les résultats
        html_template = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Résultat Total Portefeuille</title>
             <!-- Inclusion de Bootstrap CSS -->
    <link href="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css" rel="stylesheet">
    <!-- Ajout d'une icônographie via FontAwesome -->
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css" rel="stylesheet">
    <style>
        body {
            font-family: 'Arial', sans-serif;
            background-color: #f8f9fa;
        }
        .list-group-item {
            background-color: #343a40;
            color: #ffffff;
            border: none;
        }
        .list-group-item:hover {
            background-color: #495057;
            color: #ffffff;
        }
        .list-group-item i {
            margin-right: 10px;
        }
        .container-fluid {
            border-radius: 10px;
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }
        h1 {
            color: #343a40;
        }
        .btn-primary {
            background-color: #007bff;
            border-color: #007bff;
        }
        .btn-primary:hover {
            background-color: #0056b3;
            border-color: #004085;
        }
    </style>
        
        </head>
        <body>
        <div class="container-fluid mt-5">
        <div class="row">
            <div class="col-md-3">
                <!-- Menu vertical -->
                <div class="list-group vh-100">
                    <a href="/portefeuille/" class="list-group-item list-group-item-action">
                        <i class="fas fa-chart-line"></i> Suivi des Investissements
                    </a>
                    <a href="/forminvest/" class="list-group-item list-group-item-action">
                        <i class="fas fa-plus-circle"></i> Ajouter investissement
                    </a>
                    <a href="/analyse-performance" class="list-group-item list-group-item-action">
                        <i class="fas fa-chart-pie"></i> Analyse de la Performance
                    </a>
                    <a href="/alertes-marche" class="list-group-item list-group-item-action">
                        <i class="fas fa-bell"></i> Alertes de Marché
                    </a>
                    <a href="/recommandations-personnalisees" class="list-group-item list-group-item-action">
                        <i class="fas fa-lightbulb"></i> Recommandations Personnalisées
                    </a>
                    <a href="/integration-api-financieres" class="list-group-item list-group-item-action">
                        <i class="fas fa-plug"></i> Intégration avec des API Financières
                    </a>
                </div>
            </div>
            <div class="col-md-9 py-4">
            <h1 class="text-center">Résultat Total du Portefeuille</h1>
            <table class="table table-bordered mt-4">
                <thead class="thead-dark">
                    <tr>
                        <th>#</th>
                        <th>Symbole Compagnie</th>
                        <th>Nom Compagnie</th>
                        <th>Date Achat</th>
                        <th>Nombre d'Actions</th>
                        <th>Prix par Action</th>
                        <th>Total (Nombre x Prix)</th>
                        <th>Total actuel</th>
                    </tr>
                </thead>
                <tbody>
                    {% for row in rows %}
                    <tr>
                        <td>{{ row['id'] }}</td>
                        <td>{{ row['symbolecompagnie'] }}</td>
                        <td>{{ row['nomcompagnie'] }}</td>
                        <td>{{ row['dateachat'] }}</td>
                        <td>{{ row['nombreaction'] }}</td>
                        <td>{{ row['prixaction'] }}</td>
                        <td>{{ row['total'] }}</td>
                        <td>{{ row['totalactuel'] }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            <h3 class="text-right">Gain : {{ gaintotal }}</h3>
        </div>
         </div>
    </div>

    <!-- Inclusion de Bootstrap JS, Popper.js et jQuery -->
    <script src="https://code.jquery.com/jquery-3.5.1.slim.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/@popperjs/core@2.9.2/dist/umd/popper.min.js"></script>
    <script src="https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js"></script>
        
        </body>
        </html>
        """


        return render_template_string(html_template, rows=rows, gaintotal=gaintotal)

    except sqlite3.Error as e:
        return f"<h1>Erreur avec la base de données : {e}</h1>"

    finally:
        if conn:
            conn.close()






# Route pour afficher le formulaire
@app.route('/forminvest/')
def form_invest():
    return render_template('forminvest.html')

# Route pour traiter le formulaire et insérer les données dans la base de données
@app.route('/ajouter-investissement', methods=['POST'])
def ajouter_investissement():
    try:
        # Récupération des données du formulaire
        symbolecompagnie = request.form['symbolecompagnie']
        nomcompagnie = request.form['nomcompagnie']
        dateachat = request.form['dateachat']
        nombreaction = int(request.form['nombreaction'])
        prixaction = float(request.form['prixaction'])
        noportefeuille = int(request.form['noportefeuille'])

        # Connexion à la base de données SQLite
        conn = sqlite3.connect('saab.db')
        cursor = conn.cursor()

        # Création de la table si elle n'existe pas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS detailportefeuille (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbolecompagnie TEXT NOT NULL,
                nomcompagnie TEXT NOT NULL,
                dateachat DATE NOT NULL,
                nombreaction INTEGER NOT NULL,
                prixaction REAL NOT NULL,
                noportefeuille INTEGER
            )
        ''')

        # Insertion des données dans la table
        cursor.execute('''
            INSERT INTO detailportefeuille (symbolecompagnie, nomcompagnie, dateachat, nombreaction, prixaction, noportefeuille)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (symbolecompagnie, nomcompagnie, dateachat, nombreaction, prixaction, noportefeuille))

        # Validation et fermeture de la connexion
        conn.commit()
        conn.close()

        flash('Investissement ajouté avec succès!', 'success')
        return redirect('/forminvest/')

    except Exception as e:
        flash(f'Erreur lors de l\'ajout : {e}', 'danger')
        return redirect('/forminvest/')




@app.route('/graphique2/')
def graphic2():
    stock_symbol = request.args.get('stock_symbol')
    ALPHA_VANTAGE_API_KEY = 'TQXI3APYZZA55UK5'
    FUNCTION = 'TIME_SERIES_DAILY'

    url = f'https://www.alphavantage.co/query?function={FUNCTION}&symbol={stock_symbol}&apikey={ALPHA_VANTAGE_API_KEY}&datatype=csv'
    response = requests.get(url)
    df = pd.read_csv(io.StringIO(response.text))

    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.sort_values('timestamp', inplace=True)
    df.set_index('timestamp', inplace=True)
    df['close'] = df['close'].astype(float)

    # Création d'une variable 'Jour' en nombre de jours depuis le début
    df['Jour'] = (df.index - df.index.min()).days
    X = df[['Jour']]
    y = df['close']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Utilisation d'une régression polynomiale
    from sklearn.preprocessing import PolynomialFeatures
    degree = 2  # Vous pouvez modifier le degré selon vos besoins
    poly_features = PolynomialFeatures(degree=degree)

    # Transformation des données d'entraînement et de test
    X_poly_train = poly_features.fit_transform(X_train)
    X_poly_test = poly_features.transform(X_test)

    # Entraînement du modèle sur les données transformées
    model = LinearRegression()
    model.fit(X_poly_train, y_train)

    # Prédiction sur les données de test
    y_pred = model.predict(X_poly_test)

    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    # Pour tracer une courbe lisse de prédiction, on peut créer une plage de valeurs
    X_range = np.linspace(X['Jour'].min(), X['Jour'].max(), 300).reshape(-1, 1)
    X_range_poly = poly_features.transform(X_range)
    y_range_pred = model.predict(X_range_poly)

    plt.figure(figsize=(10, 6))
    plt.plot(df['Jour'], df['close'], label='Prix Réels')
    plt.plot(X_range, y_range_pred, label=f'Prédictions (degré {degree})', linestyle='--')
    plt.xlabel('Jour')
    plt.ylabel("Prix de l'Action")
    plt.title(f'Prédiction du Prix de l\'Action pour {stock_symbol}')
    plt.legend()

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()

    html_template = '''
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Prédiction du Prix de l'Action</title>
    </head>
    <body>
        <h1>Prédiction du Prix de l'Action pour {{ stock_symbol }}</h1>
        <p>MSE: {{ mse }}</p>
        <p>R²: {{ r2 }}</p>
        <img src="data:image/png;base64,{{ plot_url }}" alt="Graphique de Prédiction">
        <p><a href="/">Retour au formulaire</a></p>
    </body>
    </html>
    '''

    return render_template_string(html_template, stock_symbol=stock_symbol, mse=mse, r2=r2, plot_url=plot_url)




@app.route('/graphique/')
def graphic():
    stock_symbol = request.args.get('stock_symbol')
    ALPHA_VANTAGE_API_KEY = 'TQXI3APYZZA55UK5'
    FUNCTION = 'TIME_SERIES_DAILY'

    url = f'https://www.alphavantage.co/query?function={FUNCTION}&symbol={stock_symbol}&apikey={ALPHA_VANTAGE_API_KEY}&datatype=csv'
    response = requests.get(url)
    df = pd.read_csv(io.StringIO(response.text))

    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df.sort_values('timestamp', inplace=True)
    df.set_index('timestamp', inplace=True)
    df['close'] = df['close'].astype(float)

    df['Jour'] = (df.index - df.index.min()).days
    X = df[['Jour']]
    y = df['close']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = LinearRegression()
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)

    plt.figure(figsize=(10, 6))
    plt.plot(df['Jour'], df['close'], label='Prix Réels')
    plt.plot(X_test, y_pred, label='Prédictions', linestyle='--')
    plt.xlabel('Jour')
    plt.ylabel("Prix de l'Action")
    plt.title(f'Prédiction du Prix de l\'Action pour {stock_symbol}')
    plt.legend()

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()

    html_template = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Prédiction du Prix de l'Action</title>
    </head>
    <body>
        <h1>Prédiction du Prix de l'Action pour {{ stock_symbol }}</h1>
        <p>MSE: {{ mse }}</p>
        <p>R²: {{ r2 }}</p>
        <img src="data:image/png;base64,{{ plot_url }}" alt="Graphique de Prédiction">
        <p><a href="/">Retour au formulaire</a></p>
    </body>
    </html>
    '''

    return render_template_string(html_template, stock_symbol=stock_symbol, mse=mse, r2=r2, plot_url=plot_url)

@app.route('/resultday/')
def result():
    stock_symbol1 = 'CLS.TO'
    ALPHA_VANTAGE_API_KEY1 = 'TQXI3APYZZA55UK5'
    FUNCTION1 = 'TIME_SERIES_DAILY'

    url = f'https://www.alphavantage.co/query?function={FUNCTION1}&symbol={stock_symbol1}&apikey={ALPHA_VANTAGE_API_KEY1}'
    r = requests.get(url)
    data = r.json()

    time_series = data.get('Time Series (Daily)', {})
    sorted_dates = sorted(time_series.keys(), reverse=True)

    display_data = []
    for date in sorted_dates:
        day_data = time_series[date]
        display_data.append({
            'date': date,
            'open': day_data['1. open'],
            'high': day_data['2. high'],
            'low': day_data['3. low'],
            'close': day_data['4. close'],
            'volume': day_data['5. volume']
        })

    html_template = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Données Quotidiennes de l'Action</title>
    </head>
    <body>
        <h1>Données Quotidiennes de l'Action pour {{ stock_symbol }}</h1>
        <table border="1">
            <tr>
                <th>Date</th>
                <th>Ouverture</th>
                <th>Haut</th>
                <th>Bas</th>
                <th>Fermeture</th>
                <th>Volume</th>
            </tr>
            {% for item in display_data %}
            <tr>
                <td>{{ item.date }}</td>
                <td>{{ item.open }}</td>
                <td>{{ item.high }}</td>
                <td>{{ item.low }}</td>
                <td>{{ item.close }}</td>
                <td>{{ item.volume }}</td>
            </tr>
            {% endfor %}
        </table>
        <p><a href="/">Retour au formulaire</a></p>
    </body>
    </html>
    '''

    return render_template_string(html_template, stock_symbol=stock_symbol1, display_data=display_data)

@app.route('/graphicday/')
def graphique2():
    stock_symbol1 = 'IBM'
    ALPHA_VANTAGE_API_KEY1 = 'TQXI3APYZZA55UK5'
    FUNCTION1 = 'TIME_SERIES_MONTHLY'

    url = f'https://www.alphavantage.co/query?function={FUNCTION1}&symbol={stock_symbol1}&outputsize=compact&apikey={ALPHA_VANTAGE_API_KEY1}'
    r = requests.get(url)
    data = r.json()

    time_series = data.get('Monthly Time Series', {})
    sorted_dates = sorted(time_series.keys(), reverse=True)[:10]

    dates = []
    close_prices = []
    for date in sorted_dates:
        dates.append(date)
        close_prices.append(float(time_series[date]['4. close']))

    plt.figure(figsize=(10, 6))
    plt.plot(dates, close_prices, label='Prix de clôture')
    plt.xlabel('Date')
    plt.ylabel('Prix de clôture')
    plt.title(f'Prix de clôture pour {stock_symbol1} - 10 Derniers Mois')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.legend()

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode()
    plt.close()


    return render_template('graphicday.html', stock_symbol=stock_symbol1, plot_url=plot_url)



@app.route('/graphiquesunset/')
def graphiquesunset1():
    # Données d'exemple
    sprints = np.array([0, 1,2,3,4,5,6])
    # Travail réalisé cumulé (en heures)
    real_progress = np.array([0, 8, 20, 30, 45, 57, 67])
    # Projection optimiste (vélocité identique pour simplifier)
    optimistic_projection = np.array([0, 5, 15, 20, 28, 38, 46])
    # Projection pessimiste (vélocité réduite, par exemple 50 h/sprint)
    pessimistic_projection = np.array([0, 10, 22, 32, 47, 59, 70])

    # Création du graphique
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(sprints, real_progress, 'bo-', label='Progression Réelle')
    ax.plot(sprints, optimistic_projection, 'g--', label='Projection Optimiste')
    ax.plot(sprints, pessimistic_projection, 'r--', label='Projection Pessimiste')

    ax.set_xlabel('Itération 1, 6 étapes (Sprint 1)')
    ax.set_ylabel('Portée cumulée (heures)')
    ax.set_title("Sunset Graph – Projection de l'avancement du projet")
    ax.legend()
    ax.grid(True)
    ax.set_ylim(0, max(optimistic_projection) * 1.1)
    ax.set_xlim(0, sprints[-1])

    # Sauvegarde du graphique dans un tampon en mémoire au format PNG
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    plt.close(fig)  # Ferme la figure pour libérer la mémoire

    # Retourne l'image sous forme de réponse HTTP
    return Response(buf.getvalue(), mimetype='image/png')





if __name__ == '__main__':
    app.run(debug=True)
