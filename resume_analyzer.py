"""
resume_analyzer.py
──────────────────
PURPOSE : NLP-based resume text analysis
SUBJECT : AI (NLP - Natural Language Processing) + DSBDA (Text Analytics)

HOW IT WORKS:
  1. User uploads .txt resume file
  2. We lowercase + clean the text
  3. We search for skill keywords (NLP keyword extraction)
  4. We score based on skills found
  5. We generate personalised suggestions

WHY IS THIS NLP?
  Text → Tokenization (splitting) → Keyword Matching → Score Generation
  This is a simplified version of what tools like LinkedIn / Naukri do.
"""

import re

# ── SKILL DATABASE ────────────────────────────────────────────────────────────
# Grouped by category so we can give category-wise feedback
SKILL_CATEGORIES = {
    "Programming Languages": [
        "python", "java", "c++", "c", "javascript", "typescript",
        "kotlin", "swift", "go", "rust", "php", "ruby"
    ],
    "Web Technologies": [
        "html", "css", "react", "angular", "vue", "node.js", "nodejs",
        "express", "django", "flask", "bootstrap", "tailwind"
    ],
    "Data & AI": [
        "machine learning", "deep learning", "data science", "tensorflow",
        "pytorch", "scikit-learn", "pandas", "numpy", "sql", "mongodb",
        "tableau", "power bi", "data analysis", "statistics"
    ],
    "Cloud & DevOps": [
        "aws", "azure", "gcp", "docker", "kubernetes", "git", "github",
        "linux", "ci/cd", "jenkins"
    ],
    "Core CS Concepts": [
        "data structures", "algorithms", "operating systems", "dbms",
        "computer networks", "oops", "object oriented"
    ],
    "Soft Skills": [
        "communication", "leadership", "teamwork", "problem solving",
        "analytical", "presentation", "management"
    ]
}

# Flatten to one list for quick lookup
ALL_SKILLS = [skill for group in SKILL_CATEGORIES.values() for skill in group]

# ── MAIN FUNCTION ─────────────────────────────────────────────────────────────
def analyze_resume(text):
    """
    Input  : raw resume text (string)
    Output : dict with score, found_skills, category_breakdown, suggestions
    """
    text_lower = text.lower()

    # ── 1. Skill Extraction ────────────────────────────────────────────────
    # Check which skills from our database appear in the resume text
    found_skills = []
    category_scores = {}

    for category, skills in SKILL_CATEGORIES.items():
        found_in_cat = [s for s in skills if s in text_lower]
        category_scores[category] = {
            "found": found_in_cat,
            "count": len(found_in_cat),
            "total": len(skills)
        }
        found_skills.extend(found_in_cat)

    # ── 2. Scoring Algorithm ───────────────────────────────────────────────
    # Base score: each skill = 5 points, max from skills = 60
    skill_score = min(len(found_skills) * 5, 60)

    # Bonus points for resume sections
    bonus = 0
    has_projects    = bool(re.search(r'\bproject', text_lower))
    has_internship  = bool(re.search(r'\binternship|\bexperience', text_lower))
    has_education   = bool(re.search(r'\beducation|\bcgpa|\bgrade', text_lower))
    has_achievements = bool(re.search(r'\bachievement|\baward|\bcertif', text_lower))
    has_github      = bool(re.search(r'github', text_lower))
    has_linkedin    = bool(re.search(r'linkedin', text_lower))

    if has_projects:    bonus += 10
    if has_internship:  bonus += 10
    if has_education:   bonus +=  5
    if has_achievements: bonus += 8
    if has_github:      bonus +=  4
    if has_linkedin:    bonus +=  3

    total_score = min(skill_score + bonus, 100)

    # ── 3. Grade ───────────────────────────────────────────────────────────
    if total_score >= 80:
        grade = "Excellent"
    elif total_score >= 60:
        grade = "Good"
    elif total_score >= 40:
        grade = "Average"
    else:
        grade = "Needs Work"

    # ── 4. Personalised Suggestions ────────────────────────────────────────
    suggestions = []

    if not has_projects:
        suggestions.append("Add a dedicated 'Projects' section with 2-3 technical projects")
    if not has_internship:
        suggestions.append("Add internship experience or mention freelance/open-source work")
    if not has_education:
        suggestions.append("Include your education section with CGPA and graduation year")
    if not has_achievements:
        suggestions.append("Add certifications, awards, or hackathon achievements")
    if not has_github:
        suggestions.append("Add your GitHub profile link to showcase code")
    if not has_linkedin:
        suggestions.append("Include your LinkedIn profile URL")
    if category_scores["Core CS Concepts"]["count"] < 2:
        suggestions.append("Mention core CS subjects like DSA, DBMS, OS, OOPs")
    if category_scores["Programming Languages"]["count"] < 2:
        suggestions.append("List at least 2 programming languages with proficiency levels")
    if category_scores["Soft Skills"]["count"] < 2:
        suggestions.append("Add soft skills: communication, leadership, teamwork")
    if len(found_skills) < 5:
        suggestions.append("Expand your skills section — recruiters scan for keywords")

    if not suggestions:
        suggestions.append("Great resume! Keep it updated with latest projects.")

    return {
        "score":            total_score,
        "grade":            grade,
        "skills":           found_skills,
        "skill_count":      len(found_skills),
        "category_scores":  category_scores,
        "suggestions":      suggestions,
        "sections_found": {
            "projects":     has_projects,
            "internship":   has_internship,
            "education":    has_education,
            "achievements": has_achievements,
            "github":       has_github,
            "linkedin":     has_linkedin
        }
    }