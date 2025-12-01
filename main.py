"""
Main entry point for the financial news scraping and analysis pipeline.

This script orchestrates the daily scraping process, running RSS feeds and/or
Google News scraping, processing articles with AI agents, and storing results
in the database.

Usage:
    python main.py                    # Run both RSS and Google News pipelines
    python main.py --rss-only         # Run only RSS pipeline
    python main.py --google-only      # Run only Google News pipeline
    python main.py --help             # Show help message
"""

import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from run_scraper import main as run_rss_pipeline, main_google as run_google_pipeline


def setup_logging(verbose: bool = False):
    """Set up logging configuration."""
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)


def main():
    """Main entry point for the scraping pipeline."""
    parser = argparse.ArgumentParser(
        description="Financial News Scraping and Analysis Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run both RSS and Google News pipelines
  python main.py
  
  # Run only RSS pipeline
  python main.py --rss-only
  
  # Run only Google News pipeline
  python main.py --google-only
  
  # Enable verbose logging
  python main.py --verbose
        """
    )
    
    parser.add_argument(
        "--rss-only",
        action="store_true",
        help="Run only the RSS scraping pipeline"
    )
    
    parser.add_argument(
        "--google-only",
        action="store_true",
        help="Run only the Google News scraping pipeline"
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose (DEBUG) logging"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.rss_only and args.google_only:
        print("Error: Cannot use --rss-only and --google-only together")
        sys.exit(1)
    
    # Setup logging
    logger = setup_logging(verbose=args.verbose)
    
    start_time = datetime.now()
    logger.info("=" * 80)
    logger.info("Financial News Scraping Pipeline Started")
    logger.info(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)
    
    results = {}
    
    # Run RSS pipeline
    if not args.google_only:
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 1: RSS Feed Scraping")
        logger.info("=" * 80)
        try:
            run_rss_pipeline()
            results['rss'] = True
            logger.info("✓ RSS pipeline completed successfully")
        except Exception as e:
            logger.error(f"✗ RSS pipeline failed: {e}", exc_info=args.verbose)
            results['rss'] = False
    else:
        logger.info("Skipping RSS pipeline (--google-only flag set)")
        results['rss'] = None
    
    # Run Google News pipeline
    if not args.rss_only:
        logger.info("\n" + "=" * 80)
        logger.info("PHASE 2: Google News Scraping")
        logger.info("=" * 80)
        try:
            run_google_pipeline()
            results['google'] = True
            logger.info("✓ Google News pipeline completed successfully")
        except Exception as e:
            logger.error(f"✗ Google News pipeline failed: {e}", exc_info=args.verbose)
            results['google'] = False
    else:
        logger.info("Skipping Google News pipeline (--rss-only flag set)")
        results['google'] = None
    
    # Summary
    end_time = datetime.now()
    duration = end_time - start_time
    
    logger.info("\n" + "=" * 80)
    logger.info("PIPELINE SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Total duration: {duration}")
    
    if results['rss'] is not None:
        status = "✓ SUCCESS" if results['rss'] else "✗ FAILED"
        logger.info(f"RSS Pipeline: {status}")
    
    if results['google'] is not None:
        status = "✓ SUCCESS" if results['google'] else "✗ FAILED"
        logger.info(f"Google News Pipeline: {status}")
    
    # Determine overall success
    all_results = [r for r in results.values() if r is not None]
    overall_success = all(all_results) if all_results else False
    
    logger.info("=" * 80)
    
    if overall_success:
        logger.info("✓ Pipeline completed successfully!")
        return 0
    else:
        logger.error("✗ Pipeline completed with errors!")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

