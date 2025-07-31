#!/usr/bin/env python3
"""
Database Migration Runner for Enterprise AI System
Runs PostgreSQL migrations in order and tracks migration state.
"""

import os
import sys
import psycopg2
import argparse
from datetime import datetime
from pathlib import Path

class MigrationRunner:
    def __init__(self, database_url):
        self.database_url = database_url
        self.migrations_dir = Path(__file__).parent
        
    def connect(self):
        """Connect to PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(self.database_url)
            self.conn.autocommit = False
            self.cursor = self.conn.cursor()
            print(f"✓ Connected to database")
        except Exception as e:
            print(f"✗ Failed to connect to database: {e}")
            sys.exit(1)
    
    def create_migration_table(self):
        """Create migration tracking table if it doesn't exist"""
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    id SERIAL PRIMARY KEY,
                    migration_name VARCHAR(255) UNIQUE NOT NULL,
                    executed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    checksum VARCHAR(64),
                    execution_time_ms INTEGER
                )
            """)
            self.conn.commit()
            print("✓ Migration tracking table ready")
        except Exception as e:
            print(f"✗ Failed to create migration table: {e}")
            self.conn.rollback()
            sys.exit(1)
    
    def get_executed_migrations(self):
        """Get list of already executed migrations"""
        try:
            self.cursor.execute("SELECT migration_name FROM schema_migrations ORDER BY id")
            return [row[0] for row in self.cursor.fetchall()]
        except Exception as e:
            print(f"✗ Failed to get executed migrations: {e}")
            return []
    
    def get_migration_files(self):
        """Get list of migration files in order"""
        migration_files = []
        for file_path in sorted(self.migrations_dir.glob("*.sql")):
            if file_path.name != "run_migrations.py":
                migration_files.append(file_path)
        return migration_files
    
    def calculate_checksum(self, content):
        """Calculate SHA-256 checksum of migration content"""
        import hashlib
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def execute_migration(self, migration_file):
        """Execute a single migration file"""
        migration_name = migration_file.name
        
        try:
            # Read migration content
            with open(migration_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            checksum = self.calculate_checksum(content)
            start_time = datetime.now()
            
            print(f"  Executing {migration_name}...")
            
            # Execute migration in a transaction
            self.cursor.execute(content)
            
            # Record migration execution
            end_time = datetime.now()
            execution_time = int((end_time - start_time).total_seconds() * 1000)
            
            self.cursor.execute("""
                INSERT INTO schema_migrations (migration_name, checksum, execution_time_ms)
                VALUES (%s, %s, %s)
            """, (migration_name, checksum, execution_time))
            
            self.conn.commit()
            print(f"  ✓ {migration_name} completed in {execution_time}ms")
            
        except Exception as e:
            print(f"  ✗ {migration_name} failed: {e}")
            self.conn.rollback()
            raise
    
    def run_migrations(self, target_migration=None):
        """Run all pending migrations or up to target migration"""
        executed_migrations = self.get_executed_migrations()
        migration_files = self.get_migration_files()
        
        pending_migrations = []
        for migration_file in migration_files:
            if migration_file.name not in executed_migrations:
                pending_migrations.append(migration_file)
                if target_migration and migration_file.name == target_migration:
                    break
        
        if not pending_migrations:
            print("✓ No pending migrations")
            return
        
        print(f"Running {len(pending_migrations)} migration(s):")
        
        for migration_file in pending_migrations:
            self.execute_migration(migration_file)
        
        print(f"✓ All migrations completed successfully")
    
    def status(self):
        """Show migration status"""
        executed_migrations = self.get_executed_migrations()
        migration_files = self.get_migration_files()
        
        print("Migration Status:")
        print("-" * 60)
        
        for migration_file in migration_files:
            status = "✓ EXECUTED" if migration_file.name in executed_migrations else "✗ PENDING"
            print(f"{migration_file.name:<40} {status}")
        
        executed_count = len(executed_migrations)
        total_count = len(migration_files)
        pending_count = total_count - executed_count
        
        print("-" * 60)
        print(f"Total: {total_count}, Executed: {executed_count}, Pending: {pending_count}")
    
    def rollback(self, target_migration):
        """Rollback to a specific migration (removes records, doesn't undo changes)"""
        print(f"⚠️  Rolling back to {target_migration}")
        print("Note: This only removes migration records, it doesn't undo schema changes")
        
        try:
            self.cursor.execute("""
                DELETE FROM schema_migrations 
                WHERE migration_name > %s
                ORDER BY migration_name DESC
            """, (target_migration,))
            
            affected_rows = self.cursor.rowcount
            self.conn.commit()
            
            print(f"✓ Removed {affected_rows} migration record(s)")
            
        except Exception as e:
            print(f"✗ Rollback failed: {e}")
            self.conn.rollback()
    
    def close(self):
        """Close database connection"""
        if hasattr(self, 'cursor'):
            self.cursor.close()
        if hasattr(self, 'conn'):
            self.conn.close()

def main():
    parser = argparse.ArgumentParser(description='Database Migration Runner')
    parser.add_argument('--database-url', 
                       default=os.getenv('DATABASE_URL', 'postgresql://localhost/enterprise_ai'),
                       help='PostgreSQL database URL')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Migrate command
    migrate_parser = subparsers.add_parser('migrate', help='Run pending migrations')
    migrate_parser.add_argument('--target', help='Target migration to run up to')
    
    # Status command
    subparsers.add_parser('status', help='Show migration status')
    
    # Rollback command
    rollback_parser = subparsers.add_parser('rollback', help='Rollback to specific migration')
    rollback_parser.add_argument('target', help='Target migration to rollback to')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    runner = MigrationRunner(args.database_url)
    
    try:
        runner.connect()
        runner.create_migration_table()
        
        if args.command == 'migrate':
            runner.run_migrations(args.target)
        elif args.command == 'status':
            runner.status()
        elif args.command == 'rollback':
            runner.rollback(args.target)
            
    except KeyboardInterrupt:
        print("\n⚠️  Migration interrupted by user")
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        sys.exit(1)
    finally:
        runner.close()

if __name__ == '__main__':
    main()

