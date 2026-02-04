
import csv
from flask import Flask, render_template, request, session, redirect, url_for
from deep_translator import GoogleTranslator

# ---------------- FLASK APP ----------------
app = Flask(__name__)
app.secret_key = "yojana_ai_secret"  # session safety

# ---------------- TRANSLATION FUNCTION ----------------
def t(text, lang):
    if lang == "en":
        return text
    try:
        translated = GoogleTranslator(source="en", target=lang).translate(text)
        return f"{translated} ({text})"
    except:
        return f"{text} ({text})"

# ---------------- CSV SCHEMES ----------------
SCHEMES_CSV = "schemes_1000.csv"

def load_schemes_from_csv():
    schemes = []
    with open(SCHEMES_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            schemes.append(row)
    return schemes

# ---------------- ELIGIBILITY CHECK ----------------
def is_eligible(scheme, user):
    if int(user.get("age", 0)) < int(scheme.get("min_age", 0)):
        return False
    if scheme.get("gender","Any") != "Any" and scheme.get("gender") != user["gender"]:
        return False
    if scheme.get("states","ALL") != "ALL":
        allowed_states = [s.strip() for s in scheme["states"].split(",")]
        if user["state"] not in allowed_states:
            return False
    if scheme.get("occupations","Any") != "Any":
        allowed_occ = [o.strip() for o in scheme["occupations"].split(",")]
        if user["occupation"] not in allowed_occ:
            return False
    if scheme.get("residence","Any") != "Any" and scheme.get("residence") != user["residence"]:
        return False
    if scheme.get("minority","Any") != "Any" and scheme.get("minority") != user["minority"]:
        return False
    if scheme.get("disabled","Any") != "Any" and scheme.get("disabled") != user["disabled"]:
        return False
    return True

# ---------------- PAGE 1 ----------------
@app.route("/", methods=["GET","POST"])
def page1():
    lang = request.args.get("lang","en")
    if request.method=="POST":
        lang = request.form.get("language","en")
        session["lang"] = lang
        return redirect(url_for("page2"))
    labels = {"title": t("Yojana.ai - Home", lang)}
    return render_template("page1.html", labels=labels, lang=lang)

# ---------------- PAGE 2 ----------------
@app.route("/page2", methods=["GET", "POST"])
def page2():
    lang = request.args.get("lang", "en")

    # Labels
    labels = {
        "title": t("Basic Information", lang),
        "state": t("State", lang),
        "gender": t("Gender", lang),
        "age": t("Age", lang),
        "caste": t("Caste", lang),
        "residence": t("Residence", lang),
        "occupation": t("Occupation", lang),
        "salary": t("Monthly Salary", lang),
        "minority": t("Minority", lang),
        "disabled": t("Differently Abled", lang),
        "select": t("Select", lang),
        "submit": t("Submit", lang)
    }

    # Dropdown options
    states = [
        "Andhra Pradesh","Arunachal Pradesh","Assam","Bihar","Chhattisgarh","Goa",
        "Gujarat","Haryana","Himachal Pradesh","Jharkhand","Karnataka","Kerala",
        "Madhya Pradesh","Maharashtra","Manipur","Meghalaya","Mizoram","Nagaland",
        "Odisha","Punjab","Rajasthan","Sikkim","Tamil Nadu","Telangana","Tripura",
        "Uttar Pradesh","Uttarakhand","West Bengal","Delhi","Jammu & Kashmir","Ladakh"
    ]
    castes = ["All","Scheduled Tribe (ST)","Scheduled Caste (SC)","General","OBC","PVTG"]
    genders = ["Male","Female","Other"]
    yes_no = ["Yes","No"]
    residence_types = ["Urban","Rural"]
    occupations = [
        "Student","Farmer","Self Employed","Private Employee",
        "Government Employee","Unemployed","Daily Wage Worker","Other"
    ]
    salary_ranges = [
        "No Income","Below ₹10,000","₹10,000 – ₹25,000","₹25,001 – ₹50,000",
        "₹50,001 – ₹1,00,000","Above ₹1,00,000"
    ]

    # Translate dropdowns
    states_display = [t(s, lang) for s in states]
    castes_display = [t(c, lang) for c in castes]
    genders_display = [t(g, lang) for g in genders]
    yes_no_display = [t(y, lang) for y in yes_no]
    residence_display = [t(r, lang) for r in residence_types]
    occupations_display = [t(o, lang) for o in occupations]
    salary_display = [t(s, lang) for s in salary_ranges]

    data = {
        "states": states_display,
        "castes": castes_display,
        "genders": genders_display,
        "yes_no": yes_no_display,
        "residence_types": residence_display,
        "occupations": occupations_display,
        "salary_ranges": salary_display,
    }

    if request.method == "POST":
        raw_data = {
            "state": states[states_display.index(request.form.get("state"))],
            "caste": castes[castes_display.index(request.form.get("caste"))],
            "gender": genders[genders_display.index(request.form.get("gender"))],
            "residence": residence_types[residence_display.index(request.form.get("residence"))],
            "occupation": occupations[occupations_display.index(request.form.get("occupation"))],
            "salary": salary_ranges[salary_display.index(request.form.get("salary"))],
            "minority": yes_no[yes_no_display.index(request.form.get("minority"))],
            "disabled": yes_no[yes_no_display.index(request.form.get("disabled"))],
            "age": request.form.get("age")
        }
        session["user_data"] = raw_data
        session["lang"] = lang
        return redirect(url_for("page3"))

    return render_template("page2.html", labels=labels, **data, lang=lang)


# ---------------- PAGE 3 ----------------

@app.route("/page3")
def page3():
    lang = session.get("lang", "en")
    user_data = session.get("user_data", {})

    def t_scheme(text):
        if lang == "en":
            return text
        try:
            translated = GoogleTranslator(source="en", target=lang).translate(text)
            return f"{translated} ({text})"
        except:
            return f"{text} ({text})"

    schemes = load_schemes_from_csv()

    all_schemes = []
    central_schemes = []
    state_schemes = []

    for scheme in schemes:
        if is_eligible(scheme, user_data):
            name = t_scheme(scheme["name"])

            if lang == "en":
                desc = scheme["description"]
            else:
                try:
                    desc = GoogleTranslator(source="en", target=lang).translate(
                        scheme["description"]
                    )
                except:
                    desc = scheme["description"]

            # ✅ ONLY ADDITION
            scheme_data = {
                "name": name,
                "description": desc,
                "website": scheme.get("website")
            }

            all_schemes.append(scheme_data)
            if scheme["type"].lower() == "central":
                central_schemes.append(scheme_data)
            else:
                state_schemes.append(scheme_data)

    all_schemes = all_schemes or None
    central_schemes = central_schemes or None
    state_schemes = state_schemes or None

    column_titles = {
        "all": t("All Schemes", lang),
        "central": t("Central Schemes", lang),
        "state": t("State Schemes", lang)
    }

    none_text = t("None", lang)

    return render_template(
        "page3.html",
        all_schemes=all_schemes,
        central_schemes=central_schemes,
        state_schemes=state_schemes,
        column_titles=column_titles,
        none_text=none_text,
        lang=lang
    )

# ---------------- RUN APP ----------------
if __name__=="__main__":
    app.run(debug=True)