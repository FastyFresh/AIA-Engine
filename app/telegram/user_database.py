"""
User Database for Telegram Bot Subscriptions
Uses SQLite with versioned migrations for safe schema updates
"""
import aiosqlite
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

DB_PATH = Path("data/telegram_users.db")
CURRENT_SCHEMA_VERSION = 4

@dataclass
class TelegramUser:
    telegram_id: int
    username: Optional[str]
    first_name: Optional[str]
    persona_id: str
    subscription_tier: str
    messages_used: int
    messages_reset_date: str
    stripe_customer_id: Optional[str]
    stripe_subscription_id: Optional[str]
    created_at: str
    last_message_at: str
    last_nudge_at: Optional[str] = None

@dataclass
class ChatMessage:
    id: int
    telegram_id: int
    persona_id: str
    role: str
    content: str
    created_at: str

@dataclass
class UserOnboarding:
    telegram_id: int
    persona_id: str
    day0_sent: bool
    day3_sent: bool
    day7_sent: bool
    created_at: str

class UserDatabase:
    """Async SQLite database for user management with versioned migrations"""
    
    def __init__(self):
        self.db_path = str(DB_PATH)
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._migrations: Dict[int, Callable] = {
            1: self._migrate_v1_initial_schema,
            2: self._migrate_v2_composite_primary_key,
            3: self._migrate_v3_add_nudge_tracking,
            4: self._migrate_v4_add_webchat_tables,
        }
    
    async def _get_schema_version(self, db) -> int:
        """Get current schema version from database"""
        try:
            cursor = await db.execute(
                "SELECT version FROM schema_versions ORDER BY version DESC LIMIT 1"
            )
            row = await cursor.fetchone()
            return row[0] if row else 0
        except aiosqlite.OperationalError:
            return 0
    
    async def _set_schema_version(self, db, version: int):
        """Record a migration as applied"""
        await db.execute(
            "INSERT INTO schema_versions (version, applied_at) VALUES (?, ?)",
            (version, datetime.utcnow().isoformat())
        )
    
    async def _migrate_v1_initial_schema(self, db):
        """Version 1: Create initial tables"""
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER NOT NULL,
                username TEXT,
                first_name TEXT,
                persona_id TEXT NOT NULL,
                subscription_tier TEXT DEFAULT 'free',
                messages_used INTEGER DEFAULT 0,
                messages_reset_date TEXT,
                stripe_customer_id TEXT,
                stripe_subscription_id TEXT,
                created_at TEXT,
                last_message_at TEXT,
                PRIMARY KEY (telegram_id, persona_id)
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER NOT NULL,
                persona_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT
            )
        """)
        
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_chat_user_persona 
            ON chat_history(telegram_id, persona_id)
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_onboarding (
                telegram_id INTEGER,
                persona_id TEXT,
                day0_sent INTEGER DEFAULT 0,
                day3_sent INTEGER DEFAULT 0,
                day7_sent INTEGER DEFAULT 0,
                created_at TEXT,
                PRIMARY KEY (telegram_id, persona_id)
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS content_drops (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER,
                persona_id TEXT,
                content_type TEXT,
                content_path TEXT,
                sent_at TEXT,
                tier_required TEXT
            )
        """)
        
        logger.info("Migration v1: Initial schema created")
    
    async def _migrate_v2_composite_primary_key(self, db):
        """Version 2: Ensure composite primary key (handles legacy tables)"""
        cursor = await db.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name='users'"
        )
        row = await cursor.fetchone()
        
        if row and "PRIMARY KEY (telegram_id, persona_id)" not in (row[0] or ""):
            logger.info("Migration v2: Converting to composite primary key...")
            await db.execute("ALTER TABLE users RENAME TO users_old")
            await db.execute("""
                CREATE TABLE users (
                    telegram_id INTEGER NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    persona_id TEXT NOT NULL,
                    subscription_tier TEXT DEFAULT 'free',
                    messages_used INTEGER DEFAULT 0,
                    messages_reset_date TEXT,
                    stripe_customer_id TEXT,
                    stripe_subscription_id TEXT,
                    created_at TEXT,
                    last_message_at TEXT,
                    PRIMARY KEY (telegram_id, persona_id)
                )
            """)
            await db.execute("""
                INSERT OR IGNORE INTO users 
                SELECT telegram_id, username, first_name, persona_id, subscription_tier,
                       messages_used, messages_reset_date, stripe_customer_id, 
                       stripe_subscription_id, created_at, last_message_at
                FROM users_old
            """)
            await db.execute("DROP TABLE users_old")
            logger.info("Migration v2: Composite primary key migration complete")
        else:
            logger.info("Migration v2: Composite primary key already present, skipping")
    
    async def _migrate_v3_add_nudge_tracking(self, db):
        """Version 3: Add last_nudge_at column for re-engagement messages"""
        try:
            cursor = await db.execute("PRAGMA table_info(users)")
            columns = await cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            if 'last_nudge_at' not in column_names:
                logger.info("Migration v3: Adding last_nudge_at column")
                await db.execute("ALTER TABLE users ADD COLUMN last_nudge_at TEXT")
                logger.info("Migration v3: last_nudge_at column added")
            else:
                logger.info("Migration v3: last_nudge_at already exists, skipping")
        except Exception as e:
            logger.error(f"Migration v3 error: {e}")
    
    async def _migrate_v4_add_webchat_tables(self, db):
        """Version 4: Add webchat session tables for website DM feature"""
        await db.execute("""
            CREATE TABLE IF NOT EXISTS webchat_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                visitor_id TEXT NOT NULL,
                persona_id TEXT NOT NULL,
                ready INTEGER DEFAULT 0,
                created_at TEXT,
                last_message_at TEXT,
                UNIQUE(visitor_id, persona_id)
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS webchat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                visitor_id TEXT NOT NULL,
                persona_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT
            )
        """)
        
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_webchat_visitor_persona 
            ON webchat_messages(visitor_id, persona_id)
        """)
        
        logger.info("Migration v4: Webchat tables created")
    
    async def init_db(self):
        """Initialize database with versioned migrations"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS schema_versions (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT NOT NULL
                )
            """)
            await db.commit()
            
            current_version = await self._get_schema_version(db)
            
            for version in range(current_version + 1, CURRENT_SCHEMA_VERSION + 1):
                if version in self._migrations:
                    logger.info(f"Running migration v{version}...")
                    try:
                        await self._migrations[version](db)
                        await self._set_schema_version(db, version)
                        await db.commit()
                        logger.info(f"Migration v{version} completed successfully")
                    except Exception as e:
                        logger.error(f"Migration v{version} failed: {e}")
                        await db.rollback()
                        raise
            
            logger.info(f"Database initialized at schema version {CURRENT_SCHEMA_VERSION}")
    
    async def get_or_create_user(
        self,
        telegram_id: int,
        persona_id: str,
        username: Optional[str] = None,
        first_name: Optional[str] = None
    ) -> TelegramUser:
        """Get existing user or create new one"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            cursor = await db.execute(
                "SELECT * FROM users WHERE telegram_id = ? AND persona_id = ?",
                (telegram_id, persona_id)
            )
            row = await cursor.fetchone()
            
            if row:
                return TelegramUser(**dict(row))
            
            now = datetime.utcnow().isoformat()
            reset_date = (datetime.utcnow() + timedelta(days=30)).isoformat()
            
            await db.execute("""
                INSERT INTO users (
                    telegram_id, username, first_name, persona_id,
                    subscription_tier, messages_used, messages_reset_date,
                    created_at, last_message_at
                ) VALUES (?, ?, ?, ?, 'free', 0, ?, ?, ?)
            """, (telegram_id, username, first_name, persona_id, reset_date, now, now))
            await db.commit()
            
            return TelegramUser(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                persona_id=persona_id,
                subscription_tier="free",
                messages_used=0,
                messages_reset_date=reset_date,
                stripe_customer_id=None,
                stripe_subscription_id=None,
                created_at=now,
                last_message_at=now
            )
    
    async def update_subscription(
        self,
        telegram_id: int,
        persona_id: str,
        tier: str,
        stripe_customer_id: Optional[str] = None,
        stripe_subscription_id: Optional[str] = None
    ):
        """Update user's subscription tier"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE users SET 
                    subscription_tier = ?,
                    stripe_customer_id = COALESCE(?, stripe_customer_id),
                    stripe_subscription_id = COALESCE(?, stripe_subscription_id),
                    messages_used = 0,
                    messages_reset_date = ?
                WHERE telegram_id = ? AND persona_id = ?
            """, (
                tier,
                stripe_customer_id,
                stripe_subscription_id,
                (datetime.utcnow() + timedelta(days=30)).isoformat(),
                telegram_id,
                persona_id
            ))
            await db.commit()
    
    async def increment_message_count(self, telegram_id: int, persona_id: str) -> int:
        """Increment message count and return new count"""
        async with aiosqlite.connect(self.db_path) as db:
            now = datetime.utcnow().isoformat()
            
            cursor = await db.execute(
                "SELECT messages_used, messages_reset_date FROM users WHERE telegram_id = ? AND persona_id = ?",
                (telegram_id, persona_id)
            )
            row = await cursor.fetchone()
            
            if row:
                messages_used, reset_date = row
                if datetime.fromisoformat(reset_date) < datetime.utcnow():
                    messages_used = 0
                    reset_date = (datetime.utcnow() + timedelta(days=30)).isoformat()
                
                messages_used += 1
                
                await db.execute("""
                    UPDATE users SET 
                        messages_used = ?,
                        messages_reset_date = ?,
                        last_message_at = ?
                    WHERE telegram_id = ? AND persona_id = ?
                """, (messages_used, reset_date, now, telegram_id, persona_id))
                await db.commit()
                
                return messages_used
            
            return 0
    
    async def save_message(
        self,
        telegram_id: int,
        persona_id: str,
        role: str,
        content: str
    ):
        """Save a message to chat history"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO chat_history (telegram_id, persona_id, role, content, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (telegram_id, persona_id, role, content, datetime.utcnow().isoformat()))
            await db.commit()
    
    async def get_chat_history(
        self,
        telegram_id: int,
        persona_id: str,
        limit: int = 20
    ) -> List[ChatMessage]:
        """Get recent chat history for context"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            cursor = await db.execute("""
                SELECT * FROM chat_history 
                WHERE telegram_id = ? AND persona_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """, (telegram_id, persona_id, limit))
            
            rows = await cursor.fetchall()
            messages = [ChatMessage(**dict(row)) for row in reversed(rows)]
            return messages
    
    async def get_user_stats(self, persona_id: str) -> Dict[str, Any]:
        """Get stats for a persona's bot"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT COUNT(*) FROM users WHERE persona_id = ?",
                (persona_id,)
            )
            total_users = (await cursor.fetchone())[0]
            
            cursor = await db.execute("""
                SELECT subscription_tier, COUNT(*) 
                FROM users WHERE persona_id = ?
                GROUP BY subscription_tier
            """, (persona_id,))
            tier_counts = dict(await cursor.fetchall())
            
            return {
                "total_users": total_users,
                "free_users": tier_counts.get("free", 0),
                "companion_users": tier_counts.get("companion", 0),
                "vip_users": tier_counts.get("vip", 0)
            }
    
    async def get_recent_conversations(self, persona_id: str, limit: int = 50) -> List[Dict]:
        """Get recent conversations across all users for a persona"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT c.telegram_id, c.role, c.content, c.created_at, u.first_name, u.subscription_tier
                FROM chat_history c
                LEFT JOIN users u ON c.telegram_id = u.telegram_id AND c.persona_id = u.persona_id
                WHERE c.persona_id = ?
                ORDER BY c.created_at DESC
                LIMIT ?
            """, (persona_id, limit))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def init_onboarding(self, telegram_id: int, persona_id: str):
        """Initialize onboarding tracking for a new user"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR IGNORE INTO user_onboarding 
                (telegram_id, persona_id, day0_sent, day3_sent, day7_sent, created_at)
                VALUES (?, ?, 0, 0, 0, ?)
            """, (telegram_id, persona_id, datetime.utcnow().isoformat()))
            await db.commit()
    
    async def mark_onboarding_sent(self, telegram_id: int, persona_id: str, day: int):
        """Mark an onboarding day as sent"""
        column = f"day{day}_sent"
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(f"""
                UPDATE user_onboarding SET {column} = 1
                WHERE telegram_id = ? AND persona_id = ?
            """, (telegram_id, persona_id))
            await db.commit()
    
    async def get_users_for_onboarding(self, persona_id: str, day: int) -> List[Dict]:
        """Get users who need a specific onboarding message"""
        column = f"day{day}_sent"
        days_ago = datetime.utcnow() - timedelta(days=day)
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(f"""
                SELECT o.telegram_id, u.first_name, u.subscription_tier
                FROM user_onboarding o
                JOIN users u ON o.telegram_id = u.telegram_id AND o.persona_id = u.persona_id
                WHERE o.persona_id = ? 
                AND o.{column} = 0
                AND o.created_at <= ?
                AND u.subscription_tier = 'free'
            """, (persona_id, days_ago.isoformat()))
            
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def get_subscribers_for_content(self, persona_id: str, tier: str = "companion") -> List[Dict]:
        """Get all subscribers of a specific tier or higher for content drops"""
        tiers = ["companion", "vip"] if tier == "companion" else ["vip"]
        placeholders = ",".join(["?" for _ in tiers])
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(f"""
                SELECT telegram_id, first_name, subscription_tier
                FROM users
                WHERE persona_id = ? AND subscription_tier IN ({placeholders})
            """, (persona_id, *tiers))
            
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def record_content_drop(self, telegram_id: int, persona_id: str, content_type: str, content_path: str, tier: str):
        """Record a content drop sent to a user"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO content_drops (telegram_id, persona_id, content_type, content_path, sent_at, tier_required)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (telegram_id, persona_id, content_type, content_path, datetime.utcnow().isoformat(), tier))
            await db.commit()
    
    async def get_inactive_users(self, persona_id: str, hours: int = 24) -> List[Dict]:
        """Get users who haven't messaged in the specified hours and haven't been nudged recently"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        nudge_cutoff = datetime.utcnow() - timedelta(hours=24)
        
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT telegram_id, first_name, subscription_tier, last_message_at, last_nudge_at
                FROM users
                WHERE persona_id = ? 
                AND last_message_at <= ?
                AND (last_nudge_at IS NULL OR last_nudge_at <= ?)
            """, (persona_id, cutoff.isoformat(), nudge_cutoff.isoformat()))
            
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
    
    async def mark_user_nudged(self, telegram_id: int, persona_id: str):
        """Mark that we sent a nudge to this user"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE users SET last_nudge_at = ?
                WHERE telegram_id = ? AND persona_id = ?
            """, (datetime.utcnow().isoformat(), telegram_id, persona_id))
            await db.commit()
    
    async def get_or_create_webchat_session(self, visitor_id: str, persona_id: str) -> Dict:
        """Get or create a webchat session"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM webchat_sessions WHERE visitor_id = ? AND persona_id = ?",
                (visitor_id, persona_id)
            )
            row = await cursor.fetchone()
            
            if row:
                return dict(row)
            
            now = datetime.utcnow().isoformat()
            await db.execute("""
                INSERT INTO webchat_sessions (visitor_id, persona_id, ready, created_at, last_message_at)
                VALUES (?, ?, 0, ?, ?)
            """, (visitor_id, persona_id, now, now))
            await db.commit()
            
            cursor = await db.execute(
                "SELECT * FROM webchat_sessions WHERE visitor_id = ? AND persona_id = ?",
                (visitor_id, persona_id)
            )
            row = await cursor.fetchone()
            return dict(row) if row else {}
    
    async def set_webchat_ready(self, visitor_id: str, persona_id: str):
        """Mark webchat session as ready for conversation"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE webchat_sessions SET ready = 1, last_message_at = ?
                WHERE visitor_id = ? AND persona_id = ?
            """, (datetime.utcnow().isoformat(), visitor_id, persona_id))
            await db.commit()
    
    async def add_webchat_message(self, visitor_id: str, persona_id: str, role: str, content: str):
        """Add a message to webchat history"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO webchat_messages (visitor_id, persona_id, role, content, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (visitor_id, persona_id, role, content, datetime.utcnow().isoformat()))
            
            await db.execute("""
                UPDATE webchat_sessions SET last_message_at = ?
                WHERE visitor_id = ? AND persona_id = ?
            """, (datetime.utcnow().isoformat(), visitor_id, persona_id))
            await db.commit()
    
    async def get_webchat_history(self, visitor_id: str, persona_id: str, limit: int = 50) -> List[Dict]:
        """Get webchat message history"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT role, content, created_at FROM webchat_messages
                WHERE visitor_id = ? AND persona_id = ?
                ORDER BY id DESC LIMIT ?
            """, (visitor_id, persona_id, limit))
            rows = await cursor.fetchall()
            return [dict(row) for row in reversed(rows)]
    
    async def get_all_webchat_conversations(self, persona_id: str = None, limit: int = 50) -> List[Dict]:
        """Get all webchat conversations for admin view"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            if persona_id:
                cursor = await db.execute("""
                    SELECT s.visitor_id, s.persona_id, s.created_at, s.last_message_at,
                           (SELECT COUNT(*) FROM webchat_messages m WHERE m.visitor_id = s.visitor_id AND m.persona_id = s.persona_id) as message_count
                    FROM webchat_sessions s
                    WHERE s.persona_id = ?
                    ORDER BY s.last_message_at DESC LIMIT ?
                """, (persona_id, limit))
            else:
                cursor = await db.execute("""
                    SELECT s.visitor_id, s.persona_id, s.created_at, s.last_message_at,
                           (SELECT COUNT(*) FROM webchat_messages m WHERE m.visitor_id = s.visitor_id AND m.persona_id = s.persona_id) as message_count
                    FROM webchat_sessions s
                    ORDER BY s.last_message_at DESC LIMIT ?
                """, (limit,))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

db = UserDatabase()
