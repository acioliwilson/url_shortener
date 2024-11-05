from flask import Flask, request, redirect, render_template
import sqlite3
import random
import string
import os

app = Flask(__name__)

# Função para gerar um código curto caso o usuário não forneça uma máscara
def generate_short_code(length=6):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

# Conexão com o banco de dados
def get_db_connection():
    db_path = os.path.join(os.getcwd(), 'database.db')  # Caminho absoluto do banco de dados
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# Rota para encurtar e mascarar a URL
@app.route('/shorten', methods=['POST'])
def shorten_url():
    original_url = request.form['url']
    custom_alias = request.form['alias'].strip() or generate_short_code()  # Alias ou código gerado

    # Verifica se o alias já existe no banco de dados
    conn = get_db_connection()
    existing_alias = conn.execute('SELECT * FROM urls WHERE short_code = ?', (custom_alias,)).fetchone()
    if existing_alias:
        return f"Alias '{custom_alias}' já está em uso, escolha outro.", 400

    # Insere no banco de dados e confirma
    conn.execute('INSERT INTO urls (original_url, short_code) VALUES (?, ?)', (original_url, custom_alias))
    conn.commit()
    conn.close()

    return f"URL encurtada e mascarada: {request.host_url}{custom_alias}"

# Rota para redirecionar URL encurtada/mascarada
@app.route('/<short_code>')
def redirect_url(short_code):
    conn = get_db_connection()
    url_data = conn.execute('SELECT * FROM urls WHERE short_code = ?', (short_code,)).fetchone()
    conn.close()
    
    if url_data:
        return redirect(url_data['original_url'])
    else:
        return "URL não encontrada", 404

# Página inicial para inserir a URL e a máscara (alias)
@app.route('/')
def index():
    return render_template('index.html')

# Função para obter o IP real, considerando proxies
@app.before_request
def get_real_ip():
    if request.headers.get('X-Forwarded-For'):
        ip = request.headers.get('X-Forwarded-For').split(',')[0]
    else:
        ip = request.remote_addr
    print(f"IP Real: {ip}")
    # Você pode utilizar o IP aqui para fazer geolocalização ou outras verificações

if __name__ == "__main__":
    # Usa a porta configurada pelo Render ou a porta 5000 como fallback
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
