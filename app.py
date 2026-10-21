import os
import json
import secrets
from functools import wraps
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
STATIC_UPLOAD_DIR = BASE_DIR / "static" / "uploads"
INSTANCE_DIR = BASE_DIR / "instance"
UPLOAD_DIR = STATIC_UPLOAD_DIR
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
DATA_FILE = INSTANCE_DIR / "portfolio.json"  # legacy file, imported once if present
DATABASE_FILE = INSTANCE_DIR / "gloria.db"
ADMIN_FILE = INSTANCE_DIR / "admin.json"
SECRET_FILE = INSTANCE_DIR / "secret_key.txt"
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "").strip()
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")
ADMIN_PASSWORD_HASH = generate_password_hash(ADMIN_PASSWORD) if ADMIN_PASSWORD else ""
ALLOWED_CV_EXTENSIONS = {"pdf"}
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

if os.environ.get("RENDER") and (not ADMIN_USERNAME or len(ADMIN_PASSWORD) < 12):
    raise RuntimeError(
        "Set ADMIN_USERNAME and an ADMIN_PASSWORD of at least 12 characters in Render Environment."
    )

app = Flask(__name__)
# Persist a random session secret locally unless the hosting environment supplies one.
if os.environ.get("SECRET_KEY"):
    app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
else:
    if not SECRET_FILE.exists():
        SECRET_FILE.write_text(secrets.token_urlsafe(48), encoding="utf-8")
    app.config["SECRET_KEY"] = SECRET_FILE.read_text(encoding="utf-8").strip()
app.config["MAX_CONTENT_LENGTH"] = 12 * 1024 * 1024
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + DATABASE_FILE.as_posix()
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


class Profile(db.Model):
    __tablename__ = "profile"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False, default="Gloria NZIENGI")
    title_fr = db.Column(db.String(255), default="")
    title_en = db.Column(db.String(255), default="")
    tagline_fr = db.Column(db.Text, default="")
    tagline_en = db.Column(db.Text, default="")
    bio_fr = db.Column(db.Text, default="")
    bio_en = db.Column(db.Text, default="")
    email = db.Column(db.String(255), default="")
    phone = db.Column(db.String(100), default="")
    location = db.Column(db.String(255), default="")
    linkedin = db.Column(db.String(500), default="")
    github = db.Column(db.String(500), default="")
    whatsapp = db.Column(db.String(100), default="")
    photo = db.Column(db.String(255), default="")
    cv_file = db.Column(db.String(255), default="")
    cv_original_name = db.Column(db.String(255), default="")


class Skill(db.Model):
    __tablename__ = "skills"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False)
    detail_fr = db.Column(db.String(255), default="")
    detail_en = db.Column(db.String(255), default="")
    position = db.Column(db.Integer, nullable=False, default=0)


class Project(db.Model):
    __tablename__ = "projects"
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(100), nullable=False, unique=True)
    title = db.Column(db.String(255), nullable=False)
    image = db.Column(db.String(255), default="")
    year = db.Column(db.String(80), default="")
    category = db.Column(db.String(120), default="")
    description_fr = db.Column(db.Text, default="")
    description_en = db.Column(db.Text, default="")
    stack = db.Column(db.Text, default="")
    github = db.Column(db.String(500), default="")
    demo = db.Column(db.String(500), default="")
    visible = db.Column(db.Boolean, nullable=False, default=True)
    position = db.Column(db.Integer, nullable=False, default=0)


class Experience(db.Model):
    __tablename__ = "experiences"
    id = db.Column(db.Integer, primary_key=True)
    title_fr = db.Column(db.String(255), default="")
    title_en = db.Column(db.String(255), default="")
    period = db.Column(db.String(120), default="")
    detail_fr = db.Column(db.Text, default="")
    detail_en = db.Column(db.Text, default="")
    position = db.Column(db.Integer, nullable=False, default=0)


class Education(db.Model):
    __tablename__ = "education"
    id = db.Column(db.Integer, primary_key=True)
    title_fr = db.Column(db.String(255), default="")
    title_en = db.Column(db.String(255), default="")
    org = db.Column(db.String(255), default="")
    period = db.Column(db.String(120), default="")
    detail_fr = db.Column(db.Text, default="")
    detail_en = db.Column(db.Text, default="")
    position = db.Column(db.Integer, nullable=False, default=0)


class SiteContent(db.Model):
    __tablename__ = "site_content"
    id = db.Column(db.Integer, primary_key=True)
    strengths_fr = db.Column(db.JSON, nullable=False, default=list)
    strengths_en = db.Column(db.JSON, nullable=False, default=list)
    languages_fr = db.Column(db.JSON, nullable=False, default=list)
    languages_en = db.Column(db.JSON, nullable=False, default=list)


DEFAULT_DATA = {
    "profile": {
        "name": "Gloria NZIENGI",
        "title_fr": "Développeuse Backend & IA",
        "title_en": "Backend Developer & AI Engineer",
        "tagline_fr": "Je conçois des architectures applicatives modernes et des solutions d’intelligence artificielle utiles.",
        "tagline_en": "I build modern application architectures and practical artificial intelligence solutions.",
        "bio_fr": "Licenciée en Conception des systèmes d'information et développeuse certifiée en IA (Simplon / Kadea Academy), je conçois des APIs REST avec Flask, des bases PostgreSQL, des pipelines ETL et des projets d'IA, dont le fine-tuning de modèles de traduction NLLB.",
        "bio_en": "Information Systems Design graduate and AI-certified developer (Simplon / Kadea Academy). I build REST APIs with Flask, PostgreSQL databases, ETL pipelines, and AI projects, including fine-tuning NLLB translation models.",
        "email": "gnziengi@gmail.com",
        "phone": "0997 924 970",
        "location": "Kinshasa, R.D. Congo",
        "linkedin": "https://www.linkedin.com/",
        "github": "https://github.com/",
        "whatsapp": "243997924970",
        "photo": "profile_c8820cf3b0addf2b_gloria.jpg",
        "cv_file": "CV_2026-10-15_Gloria_NZIENGI.pdf",
        "cv_original_name": "CV_2026-10-15_Gloria_NZIENGI.pdf"
    },
    "skills": [
        {"name":"Python","detail_fr":"Backend · Data · IA","detail_en":"Backend · Data · AI"},
        {"name":"Flask","detail_fr":"APIs REST · Web","detail_en":"REST APIs · Web"},
        {"name":"FastAPI","detail_fr":"APIs asynchrones","detail_en":"Async APIs"},
        {"name":"PostgreSQL","detail_fr":"Bases de données","detail_en":"Databases"},
        {"name":"SQLAlchemy","detail_fr":"ORM · Modélisation","detail_en":"ORM · Data modeling"},
        {"name":"Docker","detail_fr":"Conteneurisation","detail_en":"Containerization"},
        {"name":"Git / GitHub","detail_fr":"Versionnement","detail_en":"Version control"},
        {"name":"Machine Learning","detail_fr":"Modèles IA","detail_en":"AI models"},
        {"name":"Hugging Face / NLLB","detail_fr":"Traduction automatique","detail_en":"Machine translation"},
        {"name":"ETL & SQL","detail_fr":"Traitement des données","detail_en":"Data processing"}
    ],
    "projects": [
        {
            "id":"cvboost","title":"CVBoost","year":"2026","category":"Web App",
            "description_fr":"Plateforme de valorisation de CV avec parsing et gestion automatisée des profils. MVP développé avec des endpoints REST, un upload sécurisé et une base relationnelle.",
            "description_en":"CV enhancement platform with resume parsing and automated profile management. MVP featuring REST endpoints, secure uploads, and a relational database.",
            "stack":"Python, Flask, SQLite, SQLAlchemy","github":"","demo":"","visible":True
        },
        {
            "id":"gloria-transcript","title":"Gloria Transcript","year":"2026","category":"Backend / Speech-to-Text",
            "description_fr":"Application de transcription audio en texte pensée pour les usages professionnels, avec génération de documents PDF téléchargeables. Le projet met en avant le traitement audio et l’intégration d’un backend Python.",
            "description_en":"An audio-to-text transcription application for professional workflows, with downloadable PDF documents. The project highlights audio processing and a Python backend.",
            "stack":"Python, Flask, API de transcription, PDF","github":"","demo":"","visible":True
        },
        {
            "id":"ia-drh","title":"IA DRH — Simulation d’entretien","year":"2026","category":"IA / Recrutement",
            "description_fr":"Projet d’assistance au recrutement autour de la simulation d’entretien et de l’IA conversationnelle, conçu pour explorer des expériences candidat plus interactives.",
            "description_en":"An AI-assisted recruitment project exploring interview simulation and conversational AI for more interactive candidate experiences.",
            "stack":"Python, API, IA conversationnelle","github":"","demo":"","visible":True
        }
    ],
    "experience": [
        {"title_fr":"Stage académique — Bracongo","title_en":"Academic internship — Bracongo","period":"juin 2022 – juil. 2022","detail_fr":"Recueil et analyse des besoins fonctionnels, conception de l’architecture logicielle et de la base de données, développement d’un MVP web pour le suivi des dépôts relais et de l’inventaire.","detail_en":"Gathered and analysed functional requirements, designed the software architecture and database, and developed a web MVP for relay-depot and inventory tracking."}
    ],
    "education": [
        {"title_fr":"Certification en Développement IA","title_en":"AI Development Certification","org":"Simplon & Kadea Academy","period":"Depuis jan. 2026","detail_fr":"Formation intensive axée sur le développement backend d’applications IA, le Machine Learning, la Computer Vision et l’intégration d’APIs spécialisées.","detail_en":"Intensive training in AI application backend development, machine learning, computer vision, and specialised API integration."},
        {"title_fr":"AWS Cloud Practitioner","title_en":"AWS Cloud Practitioner","org":"Orange Digital Center Kinshasa","period":"jan. 2024 – avr. 2024","detail_fr":"Formation pratique sur le cloud, le stockage, les réseaux, la sécurité et l’optimisation des coûts.","detail_en":"Practical training in cloud resources, storage, networking, security, and cost optimisation."},
        {"title_fr":"Licence en Conception des systèmes d'information","title_en":"Bachelor’s in Information Systems Design","org":"Université William Booth","period":"oct. 2022 – oct. 2024","detail_fr":"Gestion informatique d’entreprise, bases de données relationnelles, analyse des systèmes d’information et génie logiciel backend.","detail_en":"Enterprise IT management, relational databases, information systems analysis, and backend software engineering."},
        {"title_fr":"African Girls Can Code Initiative (AGCCI)","title_en":"African Girls Can Code Initiative (AGCCI)","org":"ONU Femmes","period":"mars 2023","detail_fr":"Formation intensive en programmation et création de solutions digitales.","detail_en":"Intensive training in programming and digital solution development."},
        {"title_fr":"Graduat en Informatique de Gestion","title_en":"Undergraduate Degree in Business IT","org":"Université William Booth","period":"oct. 2019 – juil. 2022","detail_fr":"Architecture des systèmes d’information, bases de données relationnelles et solutions web sur mesure.","detail_en":"Information systems architecture, relational databases, and custom web solutions."}
    ],
    "strengths_fr":["Esprit d’analyse","Autonomie","Organisation rigoureuse"],
    "strengths_en":["Analytical thinking","Autonomy","Strong organisation"],
    "languages_fr":["Français — langue maternelle / courant","Anglais — technique"],
    "languages_en":["French — native / fluent","English — technical"]
}

def _default_or_legacy_data():
    """Read an old JSON portfolio once during migration, otherwise use bundled defaults."""
    if DATA_FILE.exists():
        try:
            data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            merged = dict(DEFAULT_DATA)
            merged.update(data)
            profile = dict(DEFAULT_DATA.get("profile", {}))
            profile.update(data.get("profile", {}))
            merged["profile"] = profile
            for key in ("skills", "projects", "experience", "education", "strengths_fr", "strengths_en", "languages_fr", "languages_en"):
                if key not in data:
                    merged[key] = DEFAULT_DATA[key]
            return merged
        except (ValueError, OSError):
            pass
    return DEFAULT_DATA


def _write_data_to_database(data):
    """Replace the portfolio content in normalized SQLite tables in one transaction."""
    profile_data = dict(data.get("profile", {}))
    profile = db.session.get(Profile, 1)
    if profile is None:
        profile = Profile(id=1)
        db.session.add(profile)
    for field in Profile.__table__.columns.keys():
        if field != "id" and field in profile_data:
            setattr(profile, field, profile_data[field])

    Skill.query.delete()
    Project.query.delete()
    Experience.query.delete()
    Education.query.delete()
    SiteContent.query.delete()

    for position, item in enumerate(data.get("skills", [])):
        db.session.add(Skill(name=item.get("name", ""), detail_fr=item.get("detail_fr", ""), detail_en=item.get("detail_en", ""), position=position))
    used_slugs = set()
    for position, item in enumerate(data.get("projects", [])):
        slug = str(item.get("id") or secrets.token_hex(4))[:100]
        if slug in used_slugs:
            slug = f"{slug}-{position}"
        used_slugs.add(slug)
        db.session.add(Project(slug=slug, title=item.get("title", "Projet"), image=item.get("image", ""), year=item.get("year", ""), category=item.get("category", ""), description_fr=item.get("description_fr", ""), description_en=item.get("description_en", ""), stack=item.get("stack", ""), github=item.get("github", ""), demo=item.get("demo", ""), visible=bool(item.get("visible", True)), position=position))
    for position, item in enumerate(data.get("experience", [])):
        db.session.add(Experience(title_fr=item.get("title_fr", ""), title_en=item.get("title_en", ""), period=item.get("period", ""), detail_fr=item.get("detail_fr", ""), detail_en=item.get("detail_en", ""), position=position))
    for position, item in enumerate(data.get("education", [])):
        db.session.add(Education(title_fr=item.get("title_fr", ""), title_en=item.get("title_en", ""), org=item.get("org", ""), period=item.get("period", ""), detail_fr=item.get("detail_fr", ""), detail_en=item.get("detail_en", ""), position=position))
    db.session.add(SiteContent(id=1, strengths_fr=data.get("strengths_fr", []), strengths_en=data.get("strengths_en", []), languages_fr=data.get("languages_fr", []), languages_en=data.get("languages_en", [])))
    db.session.commit()


def load_data():
    """Return a template-compatible dictionary, reading portfolio content from SQLite."""
    profile = db.session.get(Profile, 1)
    if profile is None:
        return DEFAULT_DATA
    site = db.session.get(SiteContent, 1)
    return {
        "profile": {column.name: getattr(profile, column.name) for column in Profile.__table__.columns if column.name != "id"},
        "skills": [{"name": x.name, "detail_fr": x.detail_fr, "detail_en": x.detail_en} for x in Skill.query.order_by(Skill.position, Skill.id).all()],
        "projects": [{"id": x.slug, "title": x.title, "image": x.image or "", "year": x.year, "category": x.category, "description_fr": x.description_fr, "description_en": x.description_en, "stack": x.stack, "github": x.github, "demo": x.demo, "visible": x.visible} for x in Project.query.order_by(Project.position, Project.id).all()],
        "experience": [{"title_fr": x.title_fr, "title_en": x.title_en, "period": x.period, "detail_fr": x.detail_fr, "detail_en": x.detail_en} for x in Experience.query.order_by(Experience.position, Experience.id).all()],
        "education": [{"title_fr": x.title_fr, "title_en": x.title_en, "org": x.org, "period": x.period, "detail_fr": x.detail_fr, "detail_en": x.detail_en} for x in Education.query.order_by(Education.position, Education.id).all()],
        "strengths_fr": site.strengths_fr if site else [], "strengths_en": site.strengths_en if site else [],
        "languages_fr": site.languages_fr if site else [], "languages_en": site.languages_en if site else [],
    }


def save_data(data):
    _write_data_to_database(data)


def initialize_database():
    """Create tables, migrate older SQLite databases, and import initial data once."""
    with app.app_context():
        db.create_all()
        project_columns = {
            column["name"]
            for column in inspect(db.engine).get_columns("projects")
        }
        if "image" not in project_columns:
            with db.engine.begin() as connection:
                connection.execute(text(
                    "ALTER TABLE projects ADD COLUMN image VARCHAR(255) DEFAULT ''"
                ))
        if db.session.get(Profile, 1) is None:
            _write_data_to_database(_default_or_legacy_data())


initialize_database()

def find_upload_directory(filename):
    for directory in (UPLOAD_DIR, STATIC_UPLOAD_DIR, BASE_DIR):
        if (directory / filename).is_file():
            return directory
    return None

def save_upload(upload, filename):
    upload.save(UPLOAD_DIR / filename)

def is_allowed(filename, extensions):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in extensions

def save_profile_photo(photo):
    filename = "profile_" + secrets.token_hex(8) + "_" + secure_filename(photo.filename)
    save_upload(photo, filename)
    return filename

def admin_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login", next=request.path))
        return fn(*args, **kwargs)
    return wrapped

@app.context_processor
def inject_globals():
    return {"year_now": 2026}

@app.route("/")
def index():
    data = load_data()
    lang = request.args.get("lang", session.get("lang", "fr"))
    if lang not in ("fr", "en"):
        lang = "fr"
    session["lang"] = lang
    return render_template("index.html", data=data, lang=lang,
                           projects=[p for p in data["projects"] if p.get("visible", True)])

@app.route("/cv")
def view_cv():
    data = load_data()
    filename = data["profile"].get("cv_file", "")
    if not filename:
        flash("Aucun CV n’a encore été ajouté.", "error")
        return redirect(url_for("index"))
    directory = find_upload_directory(filename)
    if directory is None:
        flash("Le fichier du CV est introuvable. L’administratrice peut le remettre à jour.", "error")
        return redirect(url_for("index"))
    return send_from_directory(directory, filename, as_attachment=False, download_name=data["profile"].get("cv_original_name") or filename)

@app.route("/cv/download")
def download_cv():
    data = load_data()
    filename = data["profile"].get("cv_file", "")
    directory = find_upload_directory(filename) if filename else None
    if directory is None:
        flash("Le CV n’est pas disponible pour le moment.", "error")
        return redirect(url_for("index"))
    return send_from_directory(directory, filename, as_attachment=True, download_name=data["profile"].get("cv_original_name") or "CV_Gloria_Nziengi.pdf")

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    directory = find_upload_directory(filename)
    if directory is None or directory == BASE_DIR:
        abort(404)
    return send_from_directory(directory, filename)

def load_admin_credentials():
    """Return the one locally configured administrator account, if created."""
    if ADMIN_USERNAME and ADMIN_PASSWORD:
        return {
            "username": ADMIN_USERNAME,
            "password_hash": ADMIN_PASSWORD_HASH,
        }
    if not ADMIN_FILE.exists():
        return None
    try:
        credentials = json.loads(ADMIN_FILE.read_text(encoding="utf-8"))
        if credentials.get("username") and credentials.get("password_hash"):
            return credentials
    except (ValueError, OSError):
        pass
    return None


@app.route("/admin/setup", methods=["GET", "POST"])
def admin_setup():
    # One-time setup: after the first account is created, this URL is permanently closed
    # unless the owner manually removes instance/admin.json on the server.
    if ADMIN_USERNAME and ADMIN_PASSWORD or load_admin_credentials():
        abort(404)
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        if len(username) < 3:
            error = "Le nom d’utilisateur doit contenir au moins 3 caractères."
        elif len(password) < 12:
            error = "Choisis un mot de passe d’au moins 12 caractères."
        elif password != confirm:
            error = "Les deux mots de passe ne correspondent pas."
        else:
            try:
                with ADMIN_FILE.open("x", encoding="utf-8") as f:
                    json.dump({
                        "username": username,
                        "password_hash": generate_password_hash(password),
                    }, f)
            except FileExistsError:
                abort(404)
            session.clear()
            session["admin_logged_in"] = True
            session["admin_username"] = username
            flash("Compte administrateur créé. L’inscription est maintenant désactivée.", "success")
            return redirect(url_for("admin_dashboard"))
    return render_template("setup_admin.html", error=error)


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("admin_logged_in"):
        return redirect(url_for("admin_dashboard"))
    if not load_admin_credentials():
        return redirect(url_for("admin_setup"))
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        credentials = load_admin_credentials() or {}
        ok = (secrets.compare_digest(username, credentials.get("username", "")) and
              check_password_hash(credentials.get("password_hash", ""), password))
        if ok:
            session.clear()
            session["admin_logged_in"] = True
            session["admin_username"] = username
            flash("Connexion réussie.", "success")
            return redirect(url_for("admin_dashboard"))
        error = "Identifiants incorrects."
    return render_template("login.html", error=error)

@app.route("/admin/logout", methods=["POST"])
@admin_required
def admin_logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/admin")
@admin_required
def admin_dashboard():
    return render_template("admin.html", data=load_data())

@app.route("/admin/profile", methods=["POST"])
@admin_required
def admin_profile():
    data = load_data()
    profile = data["profile"]
    for field in ["name","title_fr","title_en","tagline_fr","tagline_en","bio_fr","bio_en","email","phone","location","linkedin","github","whatsapp"]:
        profile[field] = request.form.get(field, "").strip()
    photo = request.files.get("photo")
    if photo and photo.filename:
        if not is_allowed(photo.filename, ALLOWED_IMAGE_EXTENSIONS):
            flash("Format photo non accepté. Utilise PNG, JPG ou WEBP.", "error")
            return redirect(url_for("admin_dashboard") + "#profile")
        profile["photo"] = save_profile_photo(photo)
    save_data(data)
    flash("Profil mis à jour.", "success")
    return redirect(url_for("admin_dashboard") + "#profile")

@app.route("/admin/profile/photo", methods=["POST"])
@admin_required
def admin_profile_photo():
    photo = request.files.get("photo")
    if not photo or not photo.filename:
        flash("Choisis une photo avant de l’enregistrer.", "error")
        return redirect(url_for("admin_dashboard") + "#profile")
    if not is_allowed(photo.filename, ALLOWED_IMAGE_EXTENSIONS):
        flash("Format photo non accepté. Utilise PNG, JPG ou WEBP.", "error")
        return redirect(url_for("admin_dashboard") + "#profile")

    data = load_data()
    data["profile"]["photo"] = save_profile_photo(photo)
    save_data(data)
    flash("Photo de profil mise à jour.", "success")
    return redirect(url_for("admin_dashboard") + "#profile")

@app.route("/admin/cv", methods=["POST"])
@admin_required
def admin_cv():
    file = request.files.get("cv")
    if not file or not file.filename:
        flash("Choisis un fichier PDF avant d’enregistrer.", "error")
        return redirect(url_for("admin_dashboard") + "#cv")
    if not is_allowed(file.filename, ALLOWED_CV_EXTENSIONS):
        flash("Le CV doit être au format PDF.", "error")
        return redirect(url_for("admin_dashboard") + "#cv")
    original = secure_filename(file.filename)
    filename = "cv_" + secrets.token_hex(6) + ".pdf"
    save_upload(file, filename)
    data = load_data()
    data["profile"]["cv_file"] = filename
    data["profile"]["cv_original_name"] = original
    save_data(data)
    flash("CV remplacé avec succès. Les boutons publics utilisent maintenant le nouveau fichier.", "success")
    return redirect(url_for("admin_dashboard") + "#cv")

@app.route("/admin/projects/save", methods=["POST"])
@admin_required
def admin_projects_save():
    data = load_data()
    projects = []
    ids = request.form.getlist("project_id")
    titles = request.form.getlist("title")
    years = request.form.getlist("year")
    categories = request.form.getlist("category")
    desc_fr = request.form.getlist("description_fr")
    desc_en = request.form.getlist("description_en")
    stacks = request.form.getlist("stack")
    githubs = request.form.getlist("github")
    demos = request.form.getlist("demo")
    visibles = request.form.getlist("visible")
    image_files = request.files.getlist("project_image")
    existing_images = {
        project.get("id"): project.get("image", "")
        for project in data.get("projects", [])
    }

    for i, title in enumerate(titles):
        title = title.strip()
        if not title:
            continue
        pid = (ids[i] if i < len(ids) else "").strip() or secrets.token_hex(4)
        image_name = existing_images.get(pid, "")
        uploaded = image_files[i] if i < len(image_files) else None

        if uploaded and uploaded.filename:
            if not is_allowed(uploaded.filename, ALLOWED_IMAGE_EXTENSIONS):
                flash("Format d’image non accepté. Utilise PNG, JPG, JPEG ou WEBP.", "error")
                return redirect(url_for("admin_dashboard") + "#projects")
            safe_filename = secure_filename(uploaded.filename)
            if not safe_filename:
                flash("Nom de fichier image invalide.", "error")
                return redirect(url_for("admin_dashboard") + "#projects")
            image_name = "project_" + secrets.token_hex(8) + "_" + safe_filename
            save_upload(uploaded, image_name)

        projects.append({
            "id": pid,
            "title": title,
            "image": image_name,
            "year": years[i] if i < len(years) else "",
            "category": categories[i] if i < len(categories) else "Projet",
            "description_fr": desc_fr[i] if i < len(desc_fr) else "",
            "description_en": desc_en[i] if i < len(desc_en) else "",
            "stack": stacks[i] if i < len(stacks) else "",
            "github": githubs[i] if i < len(githubs) else "",
            "demo": demos[i] if i < len(demos) else "",
            "visible": pid in visibles
        })

    data["projects"] = projects
    save_data(data)
    flash("Projets enregistrés.", "success")
    return redirect(url_for("admin_dashboard") + "#projects")

@app.route("/admin/projects/add", methods=["POST"])
@admin_required
def admin_project_add():
    data = load_data()
    data["projects"].append({
        "id": secrets.token_hex(4), "title":"Nouveau projet", "image":"", "year":"2026", "category":"IA / Web",
        "description_fr":"Description en français à compléter.", "description_en":"English description to complete.",
        "stack":"Python", "github":"", "demo":"", "visible":False
    })
    save_data(data)
    flash("Projet ajouté. Complète ses informations puis enregistre.", "success")
    return redirect(url_for("admin_dashboard") + "#projects")

@app.route("/admin/projects/delete/<project_id>", methods=["POST"])
@admin_required
def admin_project_delete(project_id):
    data = load_data()
    data["projects"] = [p for p in data["projects"] if p.get("id") != project_id]
    save_data(data)
    flash("Projet supprimé.", "success")
    return redirect(url_for("admin_dashboard") + "#projects")

@app.route("/admin/education/save", methods=["POST"])
@admin_required
def admin_education_save():
    data = load_data()
    rows = []
    fields = {k: request.form.getlist(k) for k in ["title_fr","title_en","org","period","detail_fr","detail_en"]}
    for i, title in enumerate(fields["title_fr"]):
        if not title.strip():
            continue
        rows.append({k: values[i] if i < len(values) else "" for k, values in fields.items()})
    data["education"] = rows
    save_data(data)
    flash("Parcours et formations enregistrés.", "success")
    return redirect(url_for("admin_dashboard") + "#education")

@app.route("/assistant", methods=["POST"])
def assistant():
    message = request.form.get("message", "").lower()
    data = load_data()
    p = data["profile"]
    if any(word in message for word in ["cv", "resume", "curriculum"]):
        answer = "Tu peux consulter ou télécharger le CV de Gloria avec les boutons « Voir mon CV » et « Télécharger mon CV » en haut de la page."
    elif any(word in message for word in ["projet", "project", "cvboost", "nllb", "entretien"]):
        names = ", ".join(x["title"] for x in data["projects"] if x.get("visible", True))
        answer = "Les projets présentés sont : " + names + ". Ouvre la section Projets pour consulter les détails et les liens disponibles."
    elif any(word in message for word in ["compétence", "skill", "technologie", "tech"]):
        answer = "Les principales technologies de Gloria incluent Python, Flask, FastAPI, PostgreSQL, SQLAlchemy, Docker, Git/GitHub et les outils de NLP/Hugging Face."
    elif any(word in message for word in ["parcours", "formation", "education", "expérience", "experience"]):
        answer = "Son parcours comprend la formation en développement IA chez Simplon/Kadea Academy, la certification AWS Cloud Practitioner, une licence en Conception des systèmes d'information et un stage académique chez Bracongo."
    elif any(word in message for word in ["contact", "email", "mail", "joindre"]):
        answer = f"Tu peux contacter Gloria à l’adresse {p.get('email','')} ou via WhatsApp au numéro affiché sur le portfolio."
    else:
        answer = "Je suis l’assistant de présentation de Gloria. Tu peux me poser une question sur ses projets, ses compétences, son parcours ou son CV."
    return {"answer": answer}

@app.errorhandler(413)
def too_large(_error):
    flash("Fichier trop volumineux. La taille maximale est de 12 Mo.", "error")
    return redirect(url_for("admin_dashboard"))

if __name__ == "__main__":
    app.run(debug=False)
