import sqlite3

# Connexion à la base de données (cela crée le fichier s'il n'existe pas)
connection = sqlite3.connect("users.db")

# Création d'un curseur pour exécuter des commandes SQL
cursor = connection.cursor()

# Exemple : Création d'une table
cursor.execute("""
CREATE TABLE IF NOT EXISTS utilisateurs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL
)
""")

# Sauvegarde des modifications
connection.commit()

# Fermeture de la connexion
connection.close()
print("Base de données prête !")






