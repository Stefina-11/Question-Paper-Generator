from flask import Flask, request, send_file, render_template
from werkzeug.utils import secure_filename
import os
import random
import io

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')  # Ensure this matches your HTML filename

# Extract questions from uploaded text
def extract_questions_from_text(text):
    return [line.strip() for line in text.split('\n') 
            if line.strip() and (line.endswith('?') or line.endswith('.') or line.endswith(':'))]

def split_marks_among_modules(total, modules):
    if modules == 0 or total == 0:
        return []
    if total % modules != 0:
        return None
    base = total // modules
    return [base] * modules

def select_questions_for_marks(questions, mark_goal):
    selected, used = [], set()
    available = [20, 16, 12, 10, 8, 6, 5, 2, 1]
    current = 0
    while current < mark_goal and len(used) < len(questions):
        pick_mark = next((m for m in available if m + current <= mark_goal), None)
        if not pick_mark:
            break
        q = random.choice(questions)
        while q in used and len(used) < len(questions):
            q = random.choice(questions)
        used.add(q)
        selected.append((pick_mark, q))
        current += pick_mark
    return selected

@app.route('/generate', methods=['POST'])
def generate():
    files = request.files.getlist("files")
    total_marks = int(request.form.get("total_marks", 0))
    auto_split = request.form.get("auto_split", "no") == "yes"

    all_q, modules = [], []
    for f in files:
        fname = secure_filename(f.filename)
        path = os.path.join(app.config['UPLOAD_FOLDER'], fname)
        f.save(path)
        content = open(path, 'r', encoding='utf8', errors='ignore').read()
        qs = extract_questions_from_text(content)
        if qs:
            modules.append(qs)
            all_q.extend(qs)

    if auto_split:
        if total_marks == 0 or len(modules) == 0:
            return "❌ Upload files and enter total marks.", 400
        splits = split_marks_among_modules(total_marks, len(modules))
        if not splits:
            return f"❌ {total_marks} not divisible by {len(modules)} modules.", 400
        selected = []
        for i, qs in enumerate(modules):
            selected.extend(select_questions_for_marks(qs, splits[i]))
    else:
        # manual inputs from mark_1, mark_2 ... mark_20
        dist = {
            1: int(request.form.get("mark_1", 0)),
            2: int(request.form.get("mark_2", 0)),
            5: int(request.form.get("mark_5", 0)),
            6: int(request.form.get("mark_6", 0)),
            8: int(request.form.get("mark_8", 0)),
            10: int(request.form.get("mark_10", 0)),
            12: int(request.form.get("mark_12", 0)),
            16: int(request.form.get("mark_16", 0)),
            20: int(request.form.get("mark_20", 0)),
        }
        selected, used = [], set()
        for mark, count in dist.items():
            for _ in range(count):
                if len(used) == len(all_q): break
                q = random.choice(all_q)
                while q in used:
                    q = random.choice(all_q)
                used.add(q)
                selected.append((mark, q))

    if not selected:
        return "❌ No questions selected — check inputs and uploads.", 400

    # build paper
    mt = request.form.get("main_title", "")
    lt = request.form.get("left_title", "")
    rt = request.form.get("right_title", "")
    paper = f"\t\t{mt}\n{lt}{' ' * 60}{rt}\n\n"
    for i, (mark, q) in enumerate(selected, 1):
        paper += f"{i}. [{mark} Marks] {q}\n\n"

    return send_file(io.BytesIO(paper.encode('utf8')), mimetype='text/plain',
                     as_attachment=True, download_name='question_paper.txt')

if __name__ == "__main__":
    app.run(debug=True)
