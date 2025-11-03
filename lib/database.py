"""
PostgreSQL database models and initialization for Oxford Events
"""

from sqlalchemy import create_engine, Column, String, Text, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import os
import time

Base = declarative_base()


class TeamLogo(Base):
    """Team logo metadata"""
    __tablename__ = 'team_logos'
    
    team_name = Column(String(200), primary_key=True)
    logo_urls = Column(Text)  # JSON array of URLs
    source = Column(String(50))  # 'wikipedia', 'espn', etc.
    fetched_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class VenueImage(Base):
    """Venue image metadata"""
    __tablename__ = 'venue_images'
    
    venue_name = Column(String(200), primary_key=True)
    image_url = Column(String(500))
    source = Column(String(50))  # 'wikipedia', 'google', etc.
    fetched_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ImageCache(Base):
    """Cache for generated images (sports matchup images, category images)"""
    __tablename__ = 'image_cache'
    
    cache_key = Column(String(200), primary_key=True)
    image_data = Column(Text)  # Base64 encoded or file path
    content_type = Column(String(50), default='image/png')
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)


# Database connection
_engine = None
_session_factory = None


def get_database_url():
    """
    Get database URL from environment variable or use SQLite on persistent disk.
    Priority:
    1. PostgreSQL (if DATABASE_URL is set) - optional, requires paid subscription after 30 days
    2. SQLite on persistent disk (free, persistent) - RECOMMENDED
    3. SQLite in local data/ (development)
    """
    # First, check if PostgreSQL is configured (optional)
    db_url = os.getenv('DATABASE_URL')
    
    if db_url:
        # Render uses postgres:// but SQLAlchemy needs postgresql://
        if db_url.startswith('postgres://'):
            db_url = db_url.replace('postgres://', 'postgresql://', 1)
        return db_url
    
    # Use SQLite on persistent disk (free, persistent)
    try:
        from utils.storage import get_sqlite_db_path, is_persistent_disk
        sqlite_path = get_sqlite_db_path()
        
        # Convert to absolute path for SQLite
        abs_path = os.path.abspath(sqlite_path)
        
        # SQLite URL format: sqlite:///absolute/path/to/db.db
        sqlite_url = f'sqlite:///{abs_path}'
        
        if is_persistent_disk():
            print(f"[Database] Using SQLite on persistent disk: {abs_path}")
        else:
            print(f"[Database] Using SQLite (local): {abs_path}")
        
        return sqlite_url
    except Exception as e:
        # Ultimate fallback
        print(f"[Database] Error getting persistent disk path, using local: {e}")
        os.makedirs('data', exist_ok=True)
        return 'sqlite:///data/oxford_events.db'


def get_engine():
    """Get database engine, creating if needed"""
    global _engine
    if _engine is None:
        db_url = get_database_url()
        _engine = create_engine(db_url, pool_pre_ping=True, echo=False)
    return _engine


def get_session() -> Session:
    """Get database session"""
    global _session_factory
    if _session_factory is None:
        engine = get_engine()
        _session_factory = sessionmaker(bind=engine)
    return _session_factory()


def init_database():
    """Initialize database tables"""
    engine = get_engine()
    Base.metadata.create_all(engine)
    print("[Database] Tables created/verified")


def migrate_json_to_db():
    """Migrate existing JSON data to PostgreSQL (one-time migration)"""
    import json
    import os
    from datetime import datetime
    
    try:
        session = get_session()
    except Exception as e:
        print(f"[Database] Cannot get session for migration: {e}")
        return
    
    try:
        # Migrate team logos
        team_logos_json = os.path.join('data', 'team_logos.json')
        if os.path.exists(team_logos_json):
            try:
                with open(team_logos_json, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                
                migrated = 0
                for team_name, data in json_data.items():
                    # Check if already in database
                    existing = session.query(TeamLogo).filter_by(team_name=team_name.lower().strip()).first()
                    if not existing:
                        logo_urls_json = json.dumps(data.get('logos', []))
                        fetched_at_val = datetime.fromtimestamp(data.get('fetched_at', time.time()))
                        team_logo = TeamLogo(
                            team_name=team_name.lower().strip(),
                            logo_urls=logo_urls_json,
                            source=data.get('source', 'unknown'),
                            fetched_at=fetched_at_val
                        )
                        session.add(team_logo)
                        migrated += 1
                
                session.commit()
                if migrated > 0:
                    print(f"[Database] Migrated {migrated} team logos from JSON")
            except Exception as e:
                print(f"[Database] Error migrating team logos: {e}")
                session.rollback()
        
        # Migrate venue images
        venue_images_json = os.path.join('data', 'venue_images.json')
        if os.path.exists(venue_images_json):
            try:
                with open(venue_images_json, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                
                migrated = 0
                for venue_name, data in json_data.items():
                    # Check if already in database
                    existing = session.query(VenueImage).filter_by(venue_name=venue_name.lower().strip()).first()
                    if not existing:
                        fetched_at_val = datetime.fromtimestamp(data.get('fetched_at', time.time()))
                        venue_image = VenueImage(
                            venue_name=venue_name.lower().strip(),
                            image_url=data.get('image_url', ''),
                            source=data.get('source', 'unknown'),
                            fetched_at=fetched_at_val
                        )
                        session.add(venue_image)
                        migrated += 1
                
                session.commit()
                if migrated > 0:
                    print(f"[Database] Migrated {migrated} venue images from JSON")
            except Exception as e:
                print(f"[Database] Error migrating venue images: {e}")
                session.rollback()
    finally:
        session.close()

