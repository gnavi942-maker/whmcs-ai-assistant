import os
import logging
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from scraper.crawler import crawl_site

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_ingestion_job():
    """
    Executes the ingestion job: crawls the website, cleans and parses the pages,
    and upserts the data into both PostgreSQL/SQLite and Chroma/FAISS.
    """
    logger.info("Ingestion job started...")
    target_url = os.getenv("SCRAPER_TARGET_URL", "https://whmcsmodules.org/")
    crawl_delay = float(os.getenv("CRAWL_DELAY_SECONDS", "2.0"))
    
    try:
        # 1. Scrape the website
        scraped_data = crawl_site(target_url, crawl_delay)
        logger.info(f"Ingested {len(scraped_data)} documents from {target_url}")
        
        # 2. Update Postgres/SQLite database and vector database
        # We will import these dynamically to avoid circular dependencies
        try:
            from backend.app.rag.vector_store import update_vector_db_with_scraped_data
            from backend.app.database.session import SessionLocal
            from backend.app.database.crud import sync_scraped_data_to_db
            
            db = SessionLocal()
            try:
                # Sync relational data
                sync_scraped_data_to_db(db, scraped_data)
                logger.info("Relational database synchronization complete.")
                
                # Sync vector chunks & embeddings
                update_vector_db_with_scraped_data(scraped_data)
                logger.info("Vector database synchronization complete.")
            finally:
                db.close()
                
        except ImportError as ie:
            logger.warning(f"Relational or vector DB modules not fully initialized yet. Saving data to cache: {ie}")
            # If backend not fully initialized, write to local JSON for later ingestion
            import json
            os.makedirs("scraper/data", exist_ok=True)
            cache_file = f"scraper/data/scraped_cache_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(cache_file, "w") as f:
                json.dump(scraped_data, f, indent=2)
            logger.info(f"Scraped data written to local cache at {cache_file}")

    except Exception as e:
        logger.error(f"Ingestion job failed: {e}")

def start_scheduler():
    """
    Starts the scheduler daemon.
    """
    interval_hours = int(os.getenv("SCRAPING_INTERVAL_HOURS", "24"))
    scheduler = BlockingScheduler()
    scheduler.add_job(run_ingestion_job, 'interval', hours=interval_hours, next_run_time=datetime.now())
    
    logger.info(f"Scraper scheduler started. Running ingestion job every {interval_hours} hours.")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    # Trigger ingestion immediately when run directly
    run_ingestion_job()
