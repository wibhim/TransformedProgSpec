#!/usr/bin/env python3
"""
Enhanced Cache System for Specification Generation

This module provides a comprehensive caching system that stores specification data
in the same format as the final JSON output, including metadata and detailed statistics.
"""

import sqlite3
import json
import os
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional

# Cache database path
ENHANCED_CACHE_DB = "data/cache/enhanced_specification_cache.db"

class EnhancedCacheManager:
    """Enhanced cache manager that stores data in output JSON format."""
    
    def __init__(self, db_path: str = ENHANCED_CACHE_DB):
        self.db_path = db_path
        self.setup_database()
    
    def setup_database(self):
        """Initialize the enhanced cache database with proper schema."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create metadata table for tracking generation sessions
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS generation_metadata (
            session_id TEXT PRIMARY KEY,
            total_programs INTEGER DEFAULT 0,
            api_requests INTEGER DEFAULT 0,
            cached_results INTEGER DEFAULT 0,
            errors INTEGER DEFAULT 0,
            success_rate REAL DEFAULT 0.0,
            total_duration_seconds REAL DEFAULT 0.0,
            total_duration_formatted TEXT DEFAULT '',
            average_per_request_seconds REAL DEFAULT 0.0,
            total_tokens INTEGER DEFAULT 0,
            input_tokens INTEGER DEFAULT 0,
            output_tokens INTEGER DEFAULT 0,
            average_tokens_per_request REAL DEFAULT 0.0,
            total_cost_usd REAL DEFAULT 0.0,
            average_cost_per_request_usd REAL DEFAULT 0.0,
            cost_per_token_usd REAL DEFAULT 0.0,
            model TEXT DEFAULT '',
            generation_timestamp TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create detailed specifications table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS enhanced_specifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            code_hash TEXT UNIQUE,
            file_path TEXT,
            code TEXT,
            program_specification TEXT,
            spec_type TEXT DEFAULT 'original',
            transformation_type TEXT,
            duration_seconds REAL,
            duration_formatted TEXT,
            input_tokens INTEGER,
            output_tokens INTEGER,
            total_tokens INTEGER,
            cost_usd REAL,
            model TEXT,
            timestamp TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES generation_metadata (session_id)
        )
        ''')
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_code_hash ON enhanced_specifications (code_hash)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_session_id ON enhanced_specifications (session_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_spec_type ON enhanced_specifications (spec_type)')
        
        conn.commit()
        conn.close()
        
        print(f"💾 Enhanced cache database initialized at {self.db_path}")
    
    def create_session(self, session_id: str = None, model: str = "gpt-4.1") -> str:
        """Create a new generation session."""
        if session_id is None:
            session_id = datetime.now().strftime("session_%Y%m%d_%H%M%S")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT OR REPLACE INTO generation_metadata (
            session_id, model, generation_timestamp
        ) VALUES (?, ?, ?)
        ''', (session_id, model, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        
        print(f"📋 Created generation session: {session_id}")
        return session_id
    
    def cache_specification(self, session_id: str, code: str, file_path: str, 
                          specification: str, spec_type: str = "original",
                          transformation_type: str = None,
                          usage_stats: Dict[str, Any] = None) -> bool:
        """Cache a specification with detailed metadata."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Generate code hash
            code_hash = hashlib.md5(code.encode()).hexdigest()
            
            # Extract usage stats
            duration_seconds = usage_stats.get('duration_seconds', 0.0) if usage_stats else 0.0
            duration_formatted = usage_stats.get('duration_formatted', '0s') if usage_stats else '0s'
            tokens = usage_stats.get('tokens', {}) if usage_stats else {}
            input_tokens = tokens.get('input', 0)
            output_tokens = tokens.get('output', 0)
            total_tokens = tokens.get('total', input_tokens + output_tokens)
            cost_usd = usage_stats.get('cost_usd', 0.0) if usage_stats else 0.0
            model = usage_stats.get('model', 'gpt-4.1') if usage_stats else 'gpt-4.1'
            timestamp = usage_stats.get('timestamp', datetime.now().isoformat()) if usage_stats else datetime.now().isoformat()
            
            # Insert specification
            cursor.execute('''
            INSERT OR REPLACE INTO enhanced_specifications (
                session_id, code_hash, file_path, code, program_specification,
                spec_type, transformation_type, duration_seconds, duration_formatted,
                input_tokens, output_tokens, total_tokens, cost_usd, model, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (session_id, code_hash, file_path, code, specification,
                  spec_type, transformation_type, duration_seconds, duration_formatted,
                  input_tokens, output_tokens, total_tokens, cost_usd, model, timestamp))
            
            conn.commit()
            conn.close()
            
            print(f"💾 Cached enhanced specification for {file_path} (session: {session_id})")
            return True
            
        except Exception as e:
            print(f"❌ Failed to cache specification: {e}")
            return False
    
    def get_cached_specification(self, code: str, spec_type: str = "original") -> Optional[Dict[str, Any]]:
        """Retrieve a cached specification."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            code_hash = hashlib.md5(code.encode()).hexdigest()
            
            cursor.execute('''
            SELECT file_path, code, program_specification, spec_type, transformation_type,
                   duration_seconds, duration_formatted, input_tokens, output_tokens, 
                   total_tokens, cost_usd, model, timestamp
            FROM enhanced_specifications 
            WHERE code_hash = ? AND spec_type = ?
            ORDER BY created_at DESC LIMIT 1
            ''', (code_hash, spec_type))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'file_path': result[0],
                    'code': result[1],
                    'program_specification': result[2],
                    'spec_type': result[3],
                    'transformation_type': result[4],
                    'usage_stats': {
                        'duration_seconds': result[5],
                        'duration_formatted': result[6],
                        'tokens': {
                            'input': result[7],
                            'output': result[8],
                            'total': result[9]
                        },
                        'cost_usd': result[10],
                        'model': result[11],
                        'timestamp': result[12]
                    }
                }
            return None
            
        except Exception as e:
            print(f"❌ Failed to retrieve cached specification: {e}")
            return None
    
    def update_session_metadata(self, session_id: str):
        """Update session metadata based on cached specifications."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get aggregated statistics
            cursor.execute('''
            SELECT 
                COUNT(*) as total_programs,
                SUM(duration_seconds) as total_duration,
                SUM(input_tokens) as total_input_tokens,
                SUM(output_tokens) as total_output_tokens,
                SUM(total_tokens) as total_tokens,
                SUM(cost_usd) as total_cost,
                AVG(duration_seconds) as avg_duration,
                AVG(total_tokens) as avg_tokens,
                AVG(cost_usd) as avg_cost
            FROM enhanced_specifications 
            WHERE session_id = ?
            ''', (session_id,))
            
            stats = cursor.fetchone()
            
            if stats and stats[0] > 0:
                total_programs = stats[0]
                total_duration = stats[1] or 0.0
                total_input_tokens = stats[2] or 0
                total_output_tokens = stats[3] or 0
                total_tokens = stats[4] or 0
                total_cost = stats[5] or 0.0
                avg_duration = stats[6] or 0.0
                avg_tokens = stats[7] or 0.0
                avg_cost = stats[8] or 0.0
                
                # Format duration
                hours = int(total_duration // 3600)
                minutes = int((total_duration % 3600) // 60)
                seconds = total_duration % 60
                duration_formatted = f"{hours}h {minutes}m {seconds:.1f}s"
                
                # Update metadata
                cursor.execute('''
                UPDATE generation_metadata SET
                    total_programs = ?,
                    api_requests = ?,
                    cached_results = 0,
                    errors = 0,
                    success_rate = 100.0,
                    total_duration_seconds = ?,
                    total_duration_formatted = ?,
                    average_per_request_seconds = ?,
                    total_tokens = ?,
                    input_tokens = ?,
                    output_tokens = ?,
                    average_tokens_per_request = ?,
                    total_cost_usd = ?,
                    average_cost_per_request_usd = ?,
                    cost_per_token_usd = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE session_id = ?
                ''', (total_programs, total_programs, total_duration, duration_formatted,
                      avg_duration, total_tokens, total_input_tokens, total_output_tokens,
                      avg_tokens, total_cost, avg_cost, 
                      total_cost / total_tokens if total_tokens > 0 else 0.0,
                      session_id))
                
                conn.commit()
            
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Failed to update session metadata: {e}")
            return False
    
    def export_to_json(self, session_id: str, output_path: str = None) -> str:
        """Export session data to JSON format matching your output structure."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get metadata
            cursor.execute('SELECT * FROM generation_metadata WHERE session_id = ?', (session_id,))
            metadata_row = cursor.fetchone()
            
            if not metadata_row:
                print(f"❌ Session {session_id} not found")
                return None
            
            # Get specifications
            cursor.execute('''
            SELECT file_path, code, program_specification, spec_type, transformation_type,
                   duration_seconds, duration_formatted, input_tokens, output_tokens,
                   total_tokens, cost_usd, model, timestamp
            FROM enhanced_specifications 
            WHERE session_id = ?
            ORDER BY file_path
            ''', (session_id,))
            
            spec_rows = cursor.fetchall()
            conn.close()
            
            # Build JSON structure
            output_data = {
                "metadata": {
                    "summary": {
                        "total_programs": metadata_row[1],
                        "api_requests": metadata_row[2], 
                        "cached_results": metadata_row[3],
                        "errors": metadata_row[4],
                        "success_rate": f"{metadata_row[5]:.1f}%"
                    },
                    "timing": {
                        "total_duration_seconds": metadata_row[6],
                        "total_duration_formatted": metadata_row[7],
                        "average_per_request_seconds": metadata_row[8]
                    },
                    "tokens": {
                        "total": metadata_row[9],
                        "input": metadata_row[10],
                        "output": metadata_row[11],
                        "average_per_request": metadata_row[12]
                    },
                    "cost": {
                        "total_usd": metadata_row[13],
                        "average_per_request_usd": metadata_row[14],
                        "cost_per_token_usd": metadata_row[15]
                    },
                    "model": metadata_row[16],
                    "generation_timestamp": metadata_row[17]
                },
                "specifications": []
            }
            
            # Add specifications
            for row in spec_rows:
                spec_data = {
                    "file_path": row[0],
                    "code": row[1],
                    "program_specification": row[2],
                    "spec_type": row[3],
                    "usage_stats": {
                        "duration_seconds": row[5],
                        "duration_formatted": row[6],
                        "tokens": {
                            "input": row[7],
                            "output": row[8],
                            "total": row[9]
                        },
                        "cost_usd": row[10],
                        "model": row[11],
                        "timestamp": row[12]
                    }
                }
                
                # Add transformation_type if it exists
                if row[4]:
                    spec_data["transformation_type"] = row[4]
                    
                output_data["specifications"].append(spec_data)
            
            # Save to file
            if output_path is None:
                output_path = f"output/specification/{session_id}_specifications.json"
            
            # Ensure output directory exists
            output_dir = os.path.dirname(output_path)
            if output_dir:  # Only create if there's a directory part
                os.makedirs(output_dir, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            print(f"📄 Exported {len(spec_rows)} specifications to {output_path}")
            return output_path
            
        except Exception as e:
            print(f"❌ Failed to export session data: {e}")
            return None
    
    def get_session_progress(self, session_id: str) -> Dict[str, Any]:
        """Get current progress for a session."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT * FROM generation_metadata WHERE session_id = ?', (session_id,))
            metadata = cursor.fetchone()
            
            cursor.execute('SELECT COUNT(*) FROM enhanced_specifications WHERE session_id = ?', (session_id,))
            cached_count = cursor.fetchone()[0]
            
            conn.close()
            
            if metadata:
                return {
                    'session_id': session_id,
                    'total_programs': metadata[1],
                    'cached_specifications': cached_count,
                    'progress_percentage': (cached_count / metadata[1] * 100) if metadata[1] > 0 else 0,
                    'total_cost_usd': metadata[13],
                    'total_duration': metadata[7],
                    'model': metadata[16]
                }
            
            return {'session_id': session_id, 'cached_specifications': cached_count}
            
        except Exception as e:
            print(f"❌ Failed to get session progress: {e}")
            return {}

# Global instance
enhanced_cache = EnhancedCacheManager()

# Convenience functions for backward compatibility
def setup_enhanced_cache():
    """Setup the enhanced cache system."""
    return enhanced_cache.setup_database()

def create_generation_session(session_id: str = None, model: str = "gpt-4.1") -> str:
    """Create a new generation session."""
    return enhanced_cache.create_session(session_id, model)

def cache_enhanced_specification(session_id: str, code: str, file_path: str, 
                               specification: str, spec_type: str = "original",
                               transformation_type: str = None,
                               usage_stats: Dict[str, Any] = None) -> bool:
    """Cache a specification with enhanced metadata."""
    return enhanced_cache.cache_specification(
        session_id, code, file_path, specification, spec_type, 
        transformation_type, usage_stats
    )

def get_enhanced_cached_specification(code: str, spec_type: str = "original") -> Optional[Dict[str, Any]]:
    """Get a cached specification."""
    return enhanced_cache.get_cached_specification(code, spec_type)

def export_session_to_json(session_id: str, output_path: str = None) -> str:
    """Export session to JSON."""
    return enhanced_cache.export_to_json(session_id, output_path)

def get_session_progress(session_id: str) -> Dict[str, Any]:
    """Get session progress."""
    return enhanced_cache.get_session_progress(session_id)

if __name__ == "__main__":
    # Test the enhanced cache system
    print("🧪 Testing Enhanced Cache System...")
    
    # Create a test session
    session_id = create_generation_session("test_session_001")
    
    # Test caching
    test_usage_stats = {
        'duration_seconds': 4.858,
        'duration_formatted': '4.86s',
        'tokens': {'input': 236, 'output': 358, 'total': 594},
        'cost_usd': 0.02856,
        'model': 'gpt-4.1',
        'timestamp': datetime.now().isoformat()
    }
    
    cache_enhanced_specification(
        session_id=session_id,
        code='def test(): return "hello"',
        file_path='test.py',
        specification='method Test() returns (s: string) { s := "hello"; }',
        spec_type='original',
        transformation_type=None,
        usage_stats=test_usage_stats
    )
    
    # Update metadata
    enhanced_cache.update_session_metadata(session_id)
    
    # Export to JSON
    output_file = export_session_to_json(session_id)
    
    print(f"✅ Enhanced cache system test completed! Output: {output_file}")
