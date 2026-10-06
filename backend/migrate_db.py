import sqlite3

def migrate_db():
    conn = sqlite3.connect("accidents.db")
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(accidents)")
    existing_cols = [c[1] for c in cursor.fetchall()]
    print("Existing columns:", existing_cols)

    new_columns = [
        ("location_name", "TEXT DEFAULT 'Sector Main Road'"),
        ("annotated_image", "TEXT"),
        ("accident_type", "TEXT DEFAULT 'photo'"),
        ("status", "TEXT DEFAULT 'potential'"),
        ("confidence_score", "REAL DEFAULT 0.0"),
        ("severity_level", "TEXT DEFAULT 'MODERATE_COLLISION'"),
        ("evidence_hash", "TEXT DEFAULT ''"),
        ("details", "TEXT DEFAULT ''")
    ]

    for col_name, col_type in new_columns:
        if col_name not in existing_cols:
            try:
                cursor.execute(f"ALTER TABLE accidents ADD COLUMN {col_name} {col_type}")
                print(f"Added column: {col_name}")
            except Exception as e:
                print(f"Error adding {col_name}: {e}")

    conn.commit()
    conn.close()
    print("DB Migration successfully completed!")

if __name__ == "__main__":
    migrate_db()
