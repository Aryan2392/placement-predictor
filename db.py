import mysql.connector

# ─── HOW THIS WORKS ───────────────────────────────────────────────────────────
# This file creates ONE function: get_db()
# Call it anywhere in app.py to get a live database connection.
# Change host/user/password/database below to match YOUR MySQL setup.
# ──────────────────────────────────────────────────────────────────────────────

def get_db():
    return mysql.connector.connect(
        host="localhost",        # usually localhost
        user="root",             # your MySQL username
        password="Aryan@2392", # your MySQL password
        database="placement_db"  # database name (we create this in setup.sql)
    )
