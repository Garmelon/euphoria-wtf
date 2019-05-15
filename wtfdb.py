import asyncio
import configparser
import logging
import re

import yaboli
from yaboli.util import *

logger = logging.getLogger(__name__)

class WtfDB(yaboli.Database):
    def initialize(self, db):
        with db:
            db.execute("""
            CREATE TABLE IF NOT EXISTS acronyms (
                acronym_id INTEGER PRIMARY KEY,
                acronym TEXT NOT NULL,
                explanation TEXT NOT NULL,
                author TEXT NOT NULL,
                deleted BOOLEAN NOT NULL DEFAULT 0
            )
            """)
            db.create_function("p_lower", 1, str.lower)

    @yaboli.operation
    def add(self, db, acronym, explanation, author):
        with db:
            db.execute("""
            INSERT INTO acronyms (acronym, explanation, author)
            VALUES (?, ?, ?)
            """, (acronym, explanation, author))

    @yaboli.operation
    def find(self, db, acronym, limit):
        c = db.execute("""
        SELECT acronym, explanation FROM acronyms
        WHERE NOT deleted AND p_lower(acronym) = ?
        ORDER BY acronym_id ASC
        LIMIT ?
        """, (acronym.lower(), limit))
        return c.fetchall()

    @yaboli.operation
    def find_full(self, db, acronym, limit):
        c = db.execute("""
        SELECT acronym_id, acronym, explanation, author FROM acronyms
        WHERE NOT deleted AND p_lower(acronym) = ?
        ORDER BY acronym_id ASC
        LIMIT ?
        """, (acronym.lower(), limit))
        return c.fetchall()

    @yaboli.operation
    def get(self, db, acronym_id):
        c = db.execute("""
        SELECT acronym FROM acronyms
        WHERE NOT deleted AND acronym_id = ?
        """, (acronym_id,))
        res = c.fetchone()
        return None if res is None else res[0]

    @yaboli.operation
    def delete(self, db, acronym_id):
        with db:
            db.execute("""
            UPDATE acronyms
            SET deleted = 1
            WHERE acronym_id = ?
            """, (acronym_id,))
