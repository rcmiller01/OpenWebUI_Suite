#!/usr/bin/env python3
"""
Proactive Daemon - Agent-initiated nudge system for OpenWebUI Suite

This worker monitors various triggers and sends contextual messages to the
Pipelines Gateway to keep the AI assistant engaged and helpful.
"""

import argparse
import asyncio
import json
import logging
import os
import sqlite3
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

import requests
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IdempotencyManager:
    """Manages idempotency keys to prevent duplicate messages"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database for idempotency keys"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS idempotency_keys (
                    key TEXT PRIMARY KEY,
                    trigger_type TEXT,
                    created_at TIMESTAMP,
                    expires_at TIMESTAMP
                )
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_expires_at
                ON idempotency_keys(expires_at)
            ''')

    def is_duplicate(self, key: str, trigger_type: str, ttl_hours: int = 24) -> bool:
        """Check if a key is duplicate and store it if not"""
        now = datetime.now()
        expires_at = now + timedelta(hours=ttl_hours)

        with sqlite3.connect(self.db_path) as conn:
            # Check if key exists and is not expired
            cursor = conn.execute('''
                SELECT 1 FROM idempotency_keys
                WHERE key = ? AND expires_at > ?
            ''', (key, now))

            if cursor.fetchone():
                return True

            # Store the key
            conn.execute('''
                INSERT OR REPLACE INTO idempotency_keys
                (key, trigger_type, created_at, expires_at)
                VALUES (?, ?, ?, ?)
            ''', (key, trigger_type, now, expires_at))

            return False

    def cleanup_expired(self):
        """Clean up expired idempotency keys"""
        now = datetime.now()
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('DELETE FROM idempotency_keys WHERE expires_at <= ?', (now,))


class BackoffManager:
    """Manages exponential backoff for failed operations"""

    def __init__(self, initial_delay: float = 1.0, max_delay: float = 60.0,
                 multiplier: float = 2.0, max_retries: int = 5):
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.multiplier = multiplier
        self.max_retries = max_retries

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number"""
        if attempt >= self.max_retries:
            return 0  # No more retries

        delay = self.initial_delay * (self.multiplier ** attempt)
        return min(delay, self.max_delay)


class ProactiveDaemon:
    """Main proactive daemon class"""

    def __init__(self, config_path: str, dry_run: bool = False):
        self.config = self._load_config(config_path)
        self.dry_run = dry_run
        self.idempotency = IdempotencyManager(self.config['global']['database_path'])
        self.backoff = BackoffManager(
            initial_delay=self.config['backoff']['initial_delay_seconds'],
            max_delay=self.config['backoff']['max_delay_seconds'],
            multiplier=self.config['backoff']['multiplier'],
            max_retries=self.config['backoff']['max_retries']
        )

        # Override dry_run from config if set via command line
        if dry_run:
            self.config['global']['dry_run'] = True

        logger.info(f"Proactive Daemon initialized (dry_run: {self.dry_run})")

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)

        # Expand environment variables
        def expand_env_vars(obj):
            if isinstance(obj, dict):
                return {k: expand_env_vars(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [expand_env_vars(item) for item in obj]
            elif isinstance(obj, str) and obj.startswith('${') and obj.endswith('}'):
                env_var = obj[2:-1]
                return os.getenv(env_var, obj)
            else:
                return obj

        return expand_env_vars(config)

    async def send_nudge(self, trigger_type: str, message: str,
                        context: Optional[Dict[str, Any]] = None) -> bool:
        """Send a nudge message to Pipelines Gateway"""
        if self.dry_run:
            logger.info(f"[DRY RUN] Would send nudge: {trigger_type} - {message}")
            return True

        # Create idempotency key
        key_data = {
            'trigger_type': trigger_type,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'context': context or {}
        }
        key = f"{trigger_type}:{hash(json.dumps(key_data, sort_keys=True))}"

        if self.idempotency.is_duplicate(key, trigger_type):
            logger.info(f"Skipping duplicate nudge: {trigger_type}")
            return True

        # Prepare request
        url = f"{self.config['global']['pipelines_url']}/v1/chat/completions"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f"Bearer {self.config['global']['system_token']}"
        }

        payload = {
            'messages': [
                {
                    'role': 'system',
                    'content': f"[PROACTIVE NUDGE - {trigger_type.upper()}] {message}"
                }
            ],
            'stream': False,
            'idempotency_key': key
        }

        # Send with backoff
        for attempt in range(self.backoff.max_retries):
            try:
                logger.info(f"Sending nudge (attempt {attempt + 1}): {trigger_type}")
                response = requests.post(url, json=payload, headers=headers, timeout=30)

                if response.status_code == 200:
                    logger.info(f"Nudge sent successfully: {trigger_type}")
                    return True
                else:
                    logger.error(f"Nudge failed with status {response.status_code}: {response.text}")

            except Exception as e:
                logger.error(f"Nudge failed (attempt {attempt + 1}): {e}")

            if attempt < self.backoff.max_retries - 1:
                delay = self.backoff.get_delay(attempt)
                logger.info(f"Retrying in {delay} seconds...")
                await asyncio.sleep(delay)

        logger.error(f"Failed to send nudge after {self.backoff.max_retries} attempts")
        return False

    async def check_time_of_day_triggers(self):
        """Check time-of-day triggers"""
        config = self.config['triggers']['time_of_day']
        if not config['enabled']:
            return

        now = datetime.now()
        current_time = now.strftime("%H:%M")

        for scheduled_time in config['schedule']:
            if current_time == scheduled_time:
                if scheduled_time == "08:00":
                    message = config['messages']['morning']
                elif scheduled_time == "18:00":
                    message = config['messages']['evening']
                else:
                    message = f"Scheduled nudge at {scheduled_time}"

                await self.send_nudge('time_of_day', message, {'scheduled_time': scheduled_time})

    async def check_inactivity_triggers(self):
        """Check inactivity gap triggers"""
        config = self.config['triggers']['inactivity_gap']
        if not config['enabled']:
            return

        # This would typically check user activity logs
        # For now, we'll implement a simple time-based check
        # In a real implementation, this would query user activity from a database

        # Placeholder: check if it's been more than threshold minutes since last activity
        # This is a simplified implementation
        message = config['message']
        await self.send_nudge('inactivity_gap', message, {'threshold_minutes': config['threshold_minutes']})

    async def check_openbb_alerts(self):
        """Check OpenBB market alerts"""
        config = self.config['triggers']['openbb_alerts']
        if not config['enabled']:
            return

        # This would integrate with OpenBB API
        # For now, we'll simulate market checking
        try:
            # Simulate checking market data
            # In real implementation: call OpenBB API for price changes
            for symbol in config['symbols']:
                # Simulate price change detection
                price_change = 0.0  # Would be actual price change percentage

                if abs(price_change) >= config['thresholds']['price_change_percent']:
                    message = config['message'].format(
                        symbol=symbol,
                        change=price_change,
                        interval=config['check_interval_minutes']
                    )
                    await self.send_nudge('openbb_alert', message, {
                        'symbol': symbol,
                        'price_change': price_change
                    })

        except Exception as e:
            logger.error(f"OpenBB alert check failed: {e}")

    async def check_tandoor_gaps(self):
        """Check Tandoor meal planning gaps"""
        config = self.config['triggers']['tandoor_gaps']
        if not config['enabled']:
            return

        try:
            # This would check Tandoor API for meal planning status
            # For now, we'll simulate checking meal plans

            # Simulate meal planning gap detection
            needs_planning = True  # Would check actual meal plan status

            if needs_planning:
                message = config['meal_planning_reminder']
                await self.send_nudge('tandoor_gap', message, {
                    'check_interval_hours': config['check_interval_hours']
                })

        except Exception as e:
            logger.error(f"Tandoor gap check failed: {e}")

    async def check_drive_anomalies(self):
        """Check drive state anomalies"""
        config = self.config['triggers']['drive_anomalies']
        if not config['enabled']:
            return

        try:
            # This would check drive state API for anomalies
            # For now, we'll simulate anomaly detection

            # Simulate drive anomaly detection
            has_anomaly = False  # Would check actual drive data

            if has_anomaly:
                message = config['message'].format(anomaly_type="speeding")
                await self.send_nudge('drive_anomaly', message, {
                    'check_interval_minutes': config['check_interval_minutes']
                })

        except Exception as e:
            logger.error(f"Drive anomaly check failed: {e}")

    async def run_once(self):
        """Run all trigger checks once"""
        logger.info("Running proactive daemon checks...")

        await self.check_time_of_day_triggers()
        await self.check_inactivity_triggers()
        await self.check_openbb_alerts()
        await self.check_tandoor_gaps()
        await self.check_drive_anomalies()

        # Cleanup expired idempotency keys
        self.idempotency.cleanup_expired()

        logger.info("Proactive daemon checks completed")

    async def run_continuous(self):
        """Run continuously with scheduling"""
        logger.info("Starting proactive daemon in continuous mode...")

        while True:
            await self.run_once()
            await asyncio.sleep(60)  # Check every minute


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Proactive Daemon")
    parser.add_argument("--config", default="config/triggers.yaml",
                       help="Path to configuration file")
    parser.add_argument("--once", action="store_true",
                       help="Run checks once and exit")
    parser.add_argument("--dry-run", action="store_true",
                       help="Dry run mode - log actions without sending")
    parser.add_argument("--verbose", action="store_true",
                       help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Check if config file exists
    if not os.path.exists(args.config):
        logger.error(f"Configuration file not found: {args.config}")
        sys.exit(1)

    # Initialize daemon
    daemon = ProactiveDaemon(args.config, args.dry_run)

    if args.once:
        # Run once and exit
        asyncio.run(daemon.run_once())
    else:
        # Run continuously
        asyncio.run(daemon.run_continuous())


if __name__ == "__main__":
    main()
