"""
chatbot.py
──────────
PURPOSE : Context-aware rule-based chatbot for placement guidance
SUBJECT : AI (Conversational AI, Intent Detection, Pattern Matching)

HOW IT WORKS:
  1. User sends a message
  2. We lowercase + scan for keywords (intent detection)
  3. We match to a response from our knowledge base
  4. We return a structured response

WHY IS THIS AI?
  Intent Detection → the system understands WHAT the user means
  (e.g., "how do I get placed" and "placement tips" → same intent)
  This is a simplified version of what Siri/Alexa does.
"""

import re

# ── KNOWLEDGE BASE ─────────────────────────────────────────────────────────
# Each entry: list of trigger keywords → response text
# Keywords are matched with OR logic (any keyword triggers the response)

KNOWLEDGE_BASE = [
    {
        "keywords": ["hello", "hi", "hey", "hii", "helo", "start", "help"],
        "response": """👋 Hello! I'm your Placement AI Assistant.

I can help you with:
• 📚 Placement roadmap & preparation tips
• 💻 Technical interview guidance (DSA, coding)
• 🗣️ HR interview preparation
• 📝 Resume improvement tips
• 🎯 Career path recommendations
• 📊 CGPA / marks related queries

Just type your question naturally!"""
    },
    {
        "keywords": ["roadmap", "how to prepare", "preparation", "plan", "where to start", "starting"],
        "response": """🗺️ Placement Preparation Roadmap:

**Phase 1 – Foundation (6 months before)**
• Master Data Structures & Algorithms
• Practice on LeetCode / HackerRank (100+ problems)
• Learn 1 programming language deeply (Python/Java)

**Phase 2 – Building Profile (3 months before)**
• Build 2-3 good projects (deploy them!)
• Complete 1 internship or open-source contribution
• Get certifications (AWS, Google, Coursera)

**Phase 3 – Final Prep (1 month before)**
• Mock interviews & aptitude tests
• Polish resume and LinkedIn
• Research target companies

Start early — most students start too late! 🚀"""
    },
    {
        "keywords": ["dsa", "data structure", "algorithm", "coding", "leetcode", "competitive"],
        "response": """💻 DSA Preparation Strategy:

**Topics to cover (in order):**
1. Arrays, Strings, Hashing
2. Linked Lists, Stacks, Queues
3. Trees, Binary Search Trees
4. Graphs (BFS, DFS)
5. Dynamic Programming
6. Sorting & Searching

**Practice targets:**
• Easy: 50+ problems
• Medium: 80+ problems
• Hard: 20+ problems

**Best platforms:** LeetCode > CodeChef > HackerRank

Tip: Solve problems daily — consistency beats cramming! ✅"""
    },
    {
        "keywords": ["cgpa", "marks", "percentage", "low cgpa", "backlog", "aggregate"],
        "response": """📊 Low CGPA? Don't worry — here's the truth:

**Companies with no CGPA cutoff:**
• Many startups, product companies
• Service companies usually need 60%+

**How to compensate:**
✅ Build strong GitHub profile with projects
✅ Competitive programming ratings (LeetCode 1800+)
✅ Internship experience
✅ Open source contributions
✅ Good communication in interviews

Many IIT/NIT students with 6.5 CGPA got placed in top companies because of strong skills.

Focus on skills > marks! 💪"""
    },
    {
        "keywords": ["resume", "cv", "resume tips", "resume format", "ats"],
        "response": """📄 Resume Tips for Freshers:

**Format:**
• 1 page only
• Use ATS-friendly format (no tables/columns)
• Font: Calibri/Arial, Size 10-12

**Sections (in order):**
1. Contact info + GitHub + LinkedIn
2. Education (CGPA, year)
3. Skills (categorised)
4. Projects (2-3 with links + impact)
5. Internship / Experience
6. Achievements & Certifications

**Common mistakes to avoid:**
❌ Objective statement (outdated)
❌ Photos in resume
❌ Personal info like DOB/religion
❌ Skills you can't explain in interview

Use our Resume Analyzer tool above for personalised feedback! 🔍"""
    },
    {
        "keywords": ["hr", "hr interview", "soft skills", "tell me about yourself", "behavioural"],
        "response": """🗣️ HR Interview Preparation:

**Tell me about yourself (formula):**
"I'm [name], pursuing [degree] at [college]. I'm passionate about [field]. I've worked on [project] and completed [internship]. I'm looking to contribute to [company's domain]."

**Common HR Questions:**
• Why this company?
• Where do you see yourself in 5 years?
• Strengths & weaknesses
• Why should we hire you?
• Describe a challenge you overcame

**Golden rules:**
✅ Research the company before interview
✅ Ask questions at the end
✅ Show enthusiasm + energy
✅ Be honest about what you don't know

Confidence + Preparation = Placement! 🎯"""
    },
    {
        "keywords": ["project", "projects", "which project", "project ideas", "mini project", "major project"],
        "response": """🛠️ Best Project Ideas for Placement:

**Web Development:**
• E-commerce site with payment gateway
• Job portal (like this system!)
• Real-time chat app using WebSockets

**AI / ML:**
• House price prediction
• Sentiment analysis of Twitter/reviews
• Face recognition attendance system
• Chatbot using NLP

**Mobile:**
• Expense tracker app
• Food delivery clone (React Native)

**Tips for projects:**
✅ Deploy it (Render / Vercel / Railway)
✅ Write good README on GitHub
✅ Track commits — shows consistency
✅ Use real data, not just toy datasets

Projects with live links impress 10x more! 🚀"""
    },
    {
        "keywords": ["company", "companies", "which company", "top company", "mnc", "startup", "service", "product"],
        "response": """🏢 Understanding Company Types:

**Service Companies** (TCS, Infosys, Wipro, Cognizant):
• Mass hiring via campuses
• Lower package (3-6 LPA for freshers)
• Good for learning basics
• Usually require 60%+ CGPA

**Product Companies** (Google, Amazon, Flipkart, Swiggy):
• Fewer seats, competitive selection
• Higher package (8-30+ LPA)
• Heavy DSA & system design focus
• Profile needs to be strong

**Startups:**
• Varied packages
• More responsibility & learning
• Good if you want fast growth

Recommendation: Target service as backup, product as goal! 🎯"""
    },
    {
        "keywords": ["package", "salary", "lpa", "ctc", "how much", "average salary"],
        "response": """💰 Placement Package Reality Check:

**Fresher packages (2024-25 average):**
• Service companies: 3.5 – 6 LPA
• Mid-tier product: 8 – 15 LPA
• Top product (FAANG-like): 20 – 50+ LPA

**Factors that affect your package:**
✅ College tier (NIT/IIT > state colleges)
✅ CGPA (matters for eligibility cutoffs)
✅ DSA skills (biggest factor for product)
✅ Projects & internships
✅ Interview performance

Don't chase package alone — company culture and learning matter more early in career! 🌱"""
    },
    {
        "keywords": ["internship", "how to get internship", "internship tips", "stipend"],
        "response": """🏫 How to Get a Good Internship:

**Where to find:**
• LinkedIn (most used)
• Internshala
• AngelList / Wellfound (startups)
• Company career pages directly
• College placement cell

**How to apply effectively:**
✅ Cold email HR with personalised message
✅ Reference through alumni network
✅ Build GitHub profile first
✅ Apply to 20+ places simultaneously

**What to include in application:**
• 3-4 line intro
• Why this specific company
• Your relevant project link
• Portfolio/GitHub link

Tip: Even unpaid internships are valuable early on! Experience > money initially. 💡"""
    },
    {
        "keywords": ["skill", "which skill", "learn", "technology", "tech stack", "what to learn"],
        "response": """🎓 Skills to Learn for Placement (2024-25):

**Most in-demand skills:**
1. Python / Java (coding interviews)
2. React.js (frontend roles)
3. Node.js / Django (backend)
4. SQL + MongoDB (databases)
5. DSA (all product companies)
6. Git & GitHub (version control)
7. Docker basics (DevOps awareness)

**Trending (bonus points):**
• Gen AI / LLM integration
• Cloud (AWS free tier)
• System Design basics

**Don't try to learn everything!**
Pick one path: Full Stack / Data Science / Backend
Go deep on that. Recruiters prefer T-shaped skills. 🎯"""
    },
    {
        "keywords": ["system design", "design interview", "hld", "lld", "architecture"],
        "response": """🏗️ System Design for Freshers:

You're NOT expected to be an expert — but knowing basics impresses.

**Topics to study:**
• Client-Server model
• REST APIs (you already use Flask!)
• Databases — SQL vs NoSQL
• Caching (Redis basics)
• Load balancing concept
• Microservices vs Monolith

**Resources:**
• Gaurav Sen YouTube (free)
• System Design Primer (GitHub)
• ByteByteGo book

**In interview:** Draw a diagram, talk through trade-offs, ask clarifying questions. Process matters more than perfect answer! ✅"""
    }
]

# ── FALLBACK RESPONSES ────────────────────────────────────────────────────────
FALLBACK_RESPONSES = [
    "I'm not sure about that specific topic yet. Try asking about: roadmap, DSA, resume, HR interview, projects, companies, or salary.",
    "That's a great question! For detailed help on this, try asking about: placement tips, technical interview, HR prep, skill recommendations, or project ideas.",
    "I didn't catch that. You can ask me about: preparation roadmap, CGPA impact, resume tips, interview strategies, or best companies to target."
]

fallback_index = 0  # rotate through fallbacks so it doesn't feel repetitive

# ── MAIN FUNCTION ─────────────────────────────────────────────────────────────
def get_chatbot_response(message):
    """
    Input  : user message (string)
    Output : response string
    
    Steps:
    1. Clean the message (lowercase, strip)
    2. Check each knowledge base entry for keyword matches
    3. Return matched response or a friendly fallback
    """
    global fallback_index

    if not message or not message.strip():
        return "Please type a question! I'm here to help with placement preparation. 😊"

    msg = message.lower().strip()

    # Remove common filler words so matching is more robust
    msg = re.sub(r'\b(please|can you|tell me|what is|how to|i want to know about)\b', '', msg).strip()

    # Try to find a matching intent
    for entry in KNOWLEDGE_BASE:
        for keyword in entry["keywords"]:
            if keyword in msg:
                return entry["response"]

    # No match found — return rotating fallback
    response = FALLBACK_RESPONSES[fallback_index % len(FALLBACK_RESPONSES)]
    fallback_index += 1
    return response