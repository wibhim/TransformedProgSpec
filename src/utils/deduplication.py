#!/usr/bin/env python
"""
Deduplication utilities for the Python code collection pipeline.
Prevents collecting duplicate programs across multiple collection runs.

Features:
- Content-based hashing to identify duplicates
- Persistent index of collected programs
- Batch tracking and management
- Repository-level and cross-repository deduplication
"""

import os
import json
import hashlib
import sqlite3
from datetime import datetime
from typing import Dict, List, Set, Optional, Tuple
from pathlib import Path


class ProgramIndex:
    """
    Persistent index for tracking collected programs and preventing duplicates.
    Uses SQLite for efficient storage and querying.
    """
    
    def __init__(self, index_path: str = None):
        """Initialize the program index."""
        if index_path is None:
            # Default to cache directory
            cache_dir = Path(__file__).parent.parent.parent / "data" / "cache"
            cache_dir.mkdir(parents=True, exist_ok=True)
            index_path = cache_dir / "program_index.db"
        
        self.index_path = str(index_path)
        self._init_database()
    
    def _init_database(self):
        """Initialize the SQLite database with required tables."""
        conn = sqlite3.connect(self.index_path)
        try:
            cursor = conn.cursor()
            
            # Table for tracking collected programs
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS programs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content_hash TEXT UNIQUE NOT NULL,
                    repo_name TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    function_name TEXT,
                    complexity_score INTEGER,
                    lines_of_code INTEGER,
                    collection_batch INTEGER,
                    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    output_file_path TEXT
                )
            """)
            
            # Table for tracking collection batches
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS batches (
                    batch_id INTEGER PRIMARY KEY,
                    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_time TIMESTAMP,
                    target_count INTEGER,
                    actual_count INTEGER,
                    repositories TEXT,  -- JSON array of repo names
                    status TEXT DEFAULT 'in_progress'  -- in_progress, completed, failed
                )
            """)
            
            # Indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_content_hash ON programs(content_hash)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_repo_name ON programs(repo_name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_batch ON programs(collection_batch)")
            
            conn.commit()
        finally:
            conn.close()
    
    def compute_content_hash(self, code: str) -> str:
        """
        Compute a hash of the program content for deduplication.
        Uses normalized code to catch minor variations.
        """
        # Normalize the code: remove comments, normalize whitespace
        normalized = self._normalize_code(code)
        return hashlib.sha256(normalized.encode('utf-8')).hexdigest()
    
    def _normalize_code(self, code: str) -> str:
        """
        Normalize code for more robust deduplication.
        Removes comments and normalizes whitespace.
        """
        lines = []
        for line in code.split('\n'):
            # Remove inline comments (simple approach)
            if '#' in line:
                line = line[:line.index('#')]
            # Strip whitespace and skip empty lines
            line = line.strip()
            if line:
                lines.append(line)
        return '\n'.join(lines)
    
    def is_duplicate(self, code: str) -> bool:
        """Check if a program with this content has already been collected."""
        content_hash = self.compute_content_hash(code)
        
        conn = sqlite3.connect(self.index_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM programs WHERE content_hash = ?", (content_hash,))
            return cursor.fetchone() is not None
        finally:
            conn.close()
    
    def add_program(self, code: str, repo_name: str, file_path: str, file_name: str, 
                   function_name: str = None, complexity_score: int = None, 
                   lines_of_code: int = None, batch_id: int = None, 
                   output_file_path: str = None) -> bool:
        """
        Add a program to the index. Returns False if it's a duplicate.
        """
        content_hash = self.compute_content_hash(code)
        
        conn = sqlite3.connect(self.index_path)
        try:
            cursor = conn.cursor()
            
            # Check if already exists
            cursor.execute("SELECT 1 FROM programs WHERE content_hash = ?", (content_hash,))
            if cursor.fetchone() is not None:
                return False  # Duplicate
            
            # Add new program
            cursor.execute("""
                INSERT INTO programs 
                (content_hash, repo_name, file_path, file_name, function_name, 
                 complexity_score, lines_of_code, collection_batch, output_file_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (content_hash, repo_name, file_path, file_name, function_name,
                  complexity_score, lines_of_code, batch_id, output_file_path))
            
            conn.commit()
            return True  # Successfully added
        finally:
            conn.close()
    
    def start_batch(self, target_count: int, repositories: List[str]) -> int:
        """Start a new collection batch and return batch ID."""
        conn = sqlite3.connect(self.index_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO batches (target_count, repositories)
                VALUES (?, ?)
            """, (target_count, json.dumps(repositories)))
            
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()
    
    def finish_batch(self, batch_id: int, actual_count: int, status: str = 'completed'):
        """Mark a batch as completed."""
        conn = sqlite3.connect(self.index_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE batches 
                SET end_time = CURRENT_TIMESTAMP, actual_count = ?, status = ?
                WHERE batch_id = ?
            """, (actual_count, status, batch_id))
            conn.commit()
        finally:
            conn.close()
    
    def get_collection_stats(self) -> Dict:
        """Get overall collection statistics."""
        conn = sqlite3.connect(self.index_path)
        try:
            cursor = conn.cursor()
            
            # Total programs
            cursor.execute("SELECT COUNT(*) FROM programs")
            total_programs = cursor.fetchone()[0]
            
            # Programs by repository
            cursor.execute("""
                SELECT repo_name, COUNT(*) as count 
                FROM programs 
                GROUP BY repo_name 
                ORDER BY count DESC
            """)
            by_repo = dict(cursor.fetchall())
            
            # Recent batches
            cursor.execute("""
                SELECT batch_id, start_time, end_time, target_count, actual_count, status
                FROM batches 
                ORDER BY start_time DESC 
                LIMIT 5
            """)
            recent_batches = [
                {
                    'batch_id': row[0],
                    'start_time': row[1],
                    'end_time': row[2], 
                    'target_count': row[3],
                    'actual_count': row[4],
                    'status': row[5]
                }
                for row in cursor.fetchall()
            ]
            
            return {
                'total_programs': total_programs,
                'programs_by_repo': by_repo,
                'recent_batches': recent_batches
            }
        finally:
            conn.close()
    
    def get_collected_repos(self) -> Set[str]:
        """Get set of repositories that have already been processed."""
        conn = sqlite3.connect(self.index_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT repo_name FROM programs")
            return {row[0] for row in cursor.fetchall()}
        finally:
            conn.close()
    
    def get_repo_program_count(self, repo_name: str) -> int:
        """Get number of programs collected from a specific repository."""
        conn = sqlite3.connect(self.index_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM programs WHERE repo_name = ?", (repo_name,))
            return cursor.fetchone()[0]
        finally:
            conn.close()


class BatchManager:
    """
    Manages collection batches and helps plan incremental collection.
    """
    
    def __init__(self, index: ProgramIndex):
        self.index = index
    
    def plan_next_batch(self, target_total: int, batch_size: int, 
                       available_repos: List[str]) -> Dict:
        """
        Plan the next collection batch based on current progress.
        
        Returns:
            Dictionary with batch plan including repositories to target and counts
        """
        stats = self.index.get_collection_stats()
        current_total = stats['total_programs']
        
        if current_total >= target_total:
            return {
                'status': 'target_reached',
                'current_total': current_total,
                'target_total': target_total,
                'message': f"Target of {target_total} programs already reached"
            }
        
        remaining_needed = target_total - current_total
        batch_target = min(batch_size, remaining_needed)
        
        # Get current collection counts by repo
        collected_repos = stats['programs_by_repo']
        
        # Prioritize repositories with fewer collected programs
        repo_priorities = []
        for repo in available_repos:
            current_count = collected_repos.get(repo, 0)
            repo_priorities.append((repo, current_count))
        
        # Sort by current count (ascending) to balance collection
        repo_priorities.sort(key=lambda x: x[1])
        
        # Plan distribution across repositories
        repos_to_use = repo_priorities[:min(10, len(repo_priorities))]  # Use up to 10 repos
        programs_per_repo = max(1, batch_target // len(repos_to_use))
        
        batch_plan = {
            'status': 'planned',
            'batch_target': batch_target,
            'current_total': current_total,
            'target_total': target_total,
            'remaining_needed': remaining_needed,
            'repositories': [
                {
                    'name': repo,
                    'current_count': count,
                    'target_for_batch': min(programs_per_repo, remaining_needed)
                }
                for repo, count in repos_to_use
            ],
            'estimated_new_programs': min(batch_target, sum(
                min(programs_per_repo, remaining_needed) 
                for _, _ in repos_to_use
            ))
        }
        
        return batch_plan
    
    def execute_batch_plan(self, batch_plan: Dict, collection_func, **kwargs) -> Dict:
        """
        Execute a batch collection plan.
        
        Args:
            batch_plan: Plan from plan_next_batch()
            collection_func: Function to call for collection
            **kwargs: Additional arguments for collection function
        
        Returns:
            Dictionary with batch execution results
        """
        if batch_plan['status'] != 'planned':
            return {'status': 'error', 'message': 'Invalid batch plan'}
        
        # Start batch tracking
        repo_names = [repo['name'] for repo in batch_plan['repositories']]
        batch_id = self.index.start_batch(batch_plan['batch_target'], repo_names)
        
        try:
            # Execute collection
            total_collected = 0
            repo_results = []
            
            for repo_info in batch_plan['repositories']:
                repo_name = repo_info['name']
                target_count = repo_info['target_for_batch']
                
                print(f"\n🎯 Collecting from {repo_name} (target: {target_count})")
                
                collected = collection_func(
                    repo_name=repo_name,
                    max_files=target_count,
                    batch_id=batch_id,
                    **kwargs
                )
                
                total_collected += collected
                repo_results.append({
                    'repo_name': repo_name,
                    'target': target_count,
                    'collected': collected
                })
                
                print(f"✅ Collected {collected} programs from {repo_name}")
            
            # Finish batch tracking
            self.index.finish_batch(batch_id, total_collected, 'completed')
            
            return {
                'status': 'completed',
                'batch_id': batch_id,
                'total_collected': total_collected,
                'target': batch_plan['batch_target'],
                'repo_results': repo_results
            }
            
        except Exception as e:
            # Mark batch as failed
            self.index.finish_batch(batch_id, 0, 'failed')
            return {
                'status': 'failed',
                'batch_id': batch_id,
                'error': str(e)
            }


def print_collection_summary(index: ProgramIndex):
    """Print a summary of the current collection state."""
    stats = index.get_collection_stats()
    
    print("\n" + "="*60)
    print("📊 COLLECTION SUMMARY")
    print("="*60)
    print(f"Total Programs Collected: {stats['total_programs']}")
    
    if stats['programs_by_repo']:
        print(f"\nPrograms by Repository:")
        for repo, count in stats['programs_by_repo'].items():
            print(f"  {repo}: {count}")
    
    if stats['recent_batches']:
        print(f"\nRecent Collection Batches:")
        for batch in stats['recent_batches']:
            status_icon = "✅" if batch['status'] == 'completed' else "❌" if batch['status'] == 'failed' else "⏳"
            print(f"  {status_icon} Batch {batch['batch_id']}: {batch['actual_count'] or 0}/{batch['target_count']} programs ({batch['status']})")
    
    print("="*60)
