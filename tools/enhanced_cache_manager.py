#!/usr/bin/env python3
"""
Enhanced Cache Manager Utility

This utility provides commands to manage the enhanced cache system.
"""
import argparse
import sys
from enhanced_cache_system import EnhancedCacheManager

def main():
    parser = argparse.ArgumentParser(description="Enhanced Cache Manager Utility")
    parser.add_argument('command', choices=['sessions', 'export', 'progress', 'stats', 'clear'], 
                       help='Command to execute')
    parser.add_argument('--session-id', help='Session ID for operations')
    parser.add_argument('--output', help='Output file path for export')
    
    args = parser.parse_args()
    
    cache_manager = EnhancedCacheManager()
    
    if args.command == 'sessions':
        # List all sessions
        import sqlite3
        conn = sqlite3.connect(cache_manager.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT session_id, total_programs, model, generation_timestamp FROM generation_metadata ORDER BY created_at DESC')
        sessions = cursor.fetchall()
        conn.close()
        
        print("📋 Available Sessions:")
        print("=" * 60)
        for session in sessions:
            print(f"🆔 {session[0]}")
            print(f"   Programs: {session[1]}, Model: {session[2]}")
            print(f"   Created: {session[3]}")
            print()
    
    elif args.command == 'export':
        if not args.session_id:
            print("❌ Please specify --session-id")
            return
            
        output_path = cache_manager.export_to_json(args.session_id, args.output)
        if output_path:
            print(f"✅ Exported to {output_path}")
        else:
            print("❌ Export failed")
    
    elif args.command == 'progress':
        if not args.session_id:
            print("❌ Please specify --session-id")
            return
            
        progress = cache_manager.get_session_progress(args.session_id)
        print(f"📊 Session Progress: {args.session_id}")
        print("=" * 50)
        for key, value in progress.items():
            print(f"{key}: {value}")
    
    elif args.command == 'stats':
        import sqlite3
        conn = sqlite3.connect(cache_manager.db_path)
        cursor = conn.cursor()
        
        # Get total statistics
        cursor.execute('SELECT COUNT(*) FROM generation_metadata')
        total_sessions = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM enhanced_specifications')
        total_specs = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(total_cost_usd) FROM generation_metadata')
        total_cost = cursor.fetchone()[0] or 0
        
        cursor.execute('SELECT SUM(total_tokens) FROM generation_metadata')
        total_tokens = cursor.fetchone()[0] or 0
        
        conn.close()
        
        print("📊 Enhanced Cache Statistics:")
        print("=" * 40)
        print(f"📋 Total Sessions: {total_sessions}")
        print(f"📄 Total Specifications: {total_specs}")
        print(f"💰 Total Cost: ${total_cost:.6f}")
        print(f"🎯 Total Tokens: {total_tokens:,}")
    
    elif args.command == 'clear':
        confirm = input("⚠️  Are you sure you want to clear all cached data? (yes/no): ")
        if confirm.lower() == 'yes':
            import sqlite3
            conn = sqlite3.connect(cache_manager.db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM enhanced_specifications')
            cursor.execute('DELETE FROM generation_metadata')
            conn.commit()
            conn.close()
            print("✅ Cache cleared")
        else:
            print("❌ Operation cancelled")

if __name__ == "__main__":
    main()
