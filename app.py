from flask import Flask, render_template, request, session, redirect, url_for, send_from_directory
import os
from translations import translations

app = Flask(__name__)
app.secret_key = "portfolio_gloria_secret_key_2026"

@app.route('/')
def index():
    lang = session.get('lang', 'fr')
    content = translations.get(lang, translations['fr'])
    return render_template('index.html', content=content, current_lang=lang)

@app.route('/set_language/<lang>')
def set_language(lang):
    if lang in ['fr', 'en']:
        session['lang'] = lang
    return redirect(url_for('index'))

@app.route('/download-cv')
def download_cv():
    directory = os.path.join(app.root_path, 'static')
    filename = 'cv_gloria_nziengi.pdf'
    # Fallback to empty file if not exists yet
    filepath = os.path.join(directory, filename)
    if not os.path.exists(filepath):
        with open(filepath, 'w') as f:
            f.write("%PDF-1.4 Mock CV File. Please replace this with your real cv_gloria_nziengi.pdf")
    return send_from_directory(
        directory, 
        filename, 
        as_attachment=True, 
        download_name='CV_Gloria_Nziengi_Dev_IA.pdf'
    )

if __name__ == '__main__':
    app.run(debug=True)
