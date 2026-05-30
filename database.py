# database.py — работа с SQLite для хранения рекордов NeuroPix

import sqlite3
import os
from datetime import datetime


class Database:
    """Управление базой данных рекордов всех трёх игр."""

    def __init__(self):
        base = os.path.dirname(os.path.abspath(__file__))
        self.path = os.path.join(base, 'neuropix.db')
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def _init_db(self):
        """Создать таблицы при первом запуске."""
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS records (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_name TEXT    NOT NULL,
                    game        TEXT    NOT NULL,
                    score       INTEGER NOT NULL,
                    level       INTEGER NOT NULL,
                    date        TEXT    NOT NULL
                )
            """)
            # Таблица конфигурации (в т.ч. для хранения просмотренных туториалов)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS config (
                    key   TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)

    # ── Запись ───────────────────────────────────────────────────────────────

    def save_record(self, player_name: str, game: str, score: int, level: int):
        """Сохранить новый рекорд."""
        name     = (player_name.strip() or 'ANON')[:10].upper()
        date_str = datetime.now().strftime('%d.%m.%y')
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO records (player_name,game,score,level,date) VALUES (?,?,?,?,?)",
                (name, game, score, level, date_str)
            )

    # ── Чтение ───────────────────────────────────────────────────────────────

    def get_top10(self, game: str) -> list:
        """Топ-10 рекордов для конкретной игры."""
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute(
                "SELECT player_name as name, score, level, date "
                "FROM records WHERE game=? ORDER BY score DESC LIMIT 10",
                (game,)
            )
            return [dict(r) for r in cur.fetchall()]

    def get_total_top10(self) -> list:
        """Топ-10 по суммарным очкам игрока во всех играх."""
        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.execute(
                "SELECT player_name as name, SUM(score) as score "
                "FROM records GROUP BY player_name ORDER BY score DESC LIMIT 10"
            )
            return [dict(r) for r in cur.fetchall()]

    def is_record(self, game: str, score: int) -> bool:
        """Попадает ли счёт в топ-10 данной игры?"""
        top = self.get_top10(game)
        if len(top) < 10:
            return True
        return score > top[-1]['score']

    def get_last_player(self) -> str | None:
        """Имя последнего сыгравшего игрока."""
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT player_name FROM records ORDER BY id DESC LIMIT 1"
            )
            row = cur.fetchone()
            return row[0] if row else None

    def get_player_total(self, name: str) -> int:
        """Суммарные очки игрока по всем играм."""
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT COALESCE(SUM(score),0) FROM records WHERE player_name=?",
                (name,)
            )
            return cur.fetchone()[0]

    # ── Настройки / просмотренные туториалы ─────────────────────────────────

    def is_tutorial_seen(self, game: str) -> bool:
        """Был ли уже показан туториал этой игры хотя бы раз?"""
        with self._connect() as conn:
            cur = conn.execute(
                "SELECT value FROM config WHERE key=?",
                (f'tutorial_seen_{game}',)
            )
            row = cur.fetchone()
            return row is not None and row[0] == '1'

    def mark_tutorial_seen(self, game: str):
        """Пометить туториал игры как просмотренный."""
        with self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO config (key, value) VALUES (?, '1')",
                (f'tutorial_seen_{game}',)
            )
