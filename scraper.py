import json
import logging
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import config

class NepaliPatroVegetableScraper:
    def __init__(self):
        self.driver = None
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(config.LOG_FILE),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def setup_driver(self):
        """Setup Chrome driver with Arc browser compatibility"""
        chrome_options = Options()
        
        # Add options for Arc browser compatibility
        for option in config.CHROME_OPTIONS:
            chrome_options.add_argument(option)
            
        if config.HEADLESS:
            chrome_options.add_argument("--headless")
            
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(config.IMPLICIT_WAIT)
            self.logger.info("Chrome driver initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Chrome driver: {e}")
            raise
            
    def load_page(self):
        """Load the vegetables page"""
        try:
            self.logger.info(f"Loading page: {config.URL}")
            self.driver.get(config.URL)
            
            # Wait for page to load completely
            WebDriverWait(self.driver, config.WAIT_TIME).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # Additional wait for JavaScript content to load
            time.sleep(5)
            self.logger.info("Page loaded successfully")
            
        except TimeoutException:
            self.logger.error("Page load timeout")
            raise
        except Exception as e:
            self.logger.error(f"Error loading page: {e}")
            raise
            
    def extract_price_from_text(self, text):
        """Extract numeric price values from text"""
        import re
        # Look for price patterns: numbers followed by common Nepali currency indicators
        price_patterns = [
            r'(\d+(?:\.\d+)?)\s*(?:रु|रुपैयाँ|Rs|₹)',  # Nepali rupees
            r'(\d+(?:\.\d+)?)',  # Just numbers
        ]
        
        prices = []
        for pattern in price_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                try:
                    prices.append(float(match))
                except ValueError:
                    continue
        return prices
    
    def scrape_vegetables_data(self):
        """Scrape vegetables data with focus on price extraction"""
        vegetables_data = []
        
        try:
            # Wait for content to be present
            self.logger.info("Waiting for vegetable price content to load...")
            
            # Specific selectors for vegetable price data
            price_selectors = [
                "table tr",  # Table rows (most likely format)
                ".price-table tr",
                ".vegetable-price-row",
                ".market-price tr",
                "[class*='price'] tr",
                "[class*='vegetable'] tr",
                ".table-responsive tr",
                "tbody tr",
                ".price-item",
                ".vegetable-item",
                "[data-vegetable]",
                "[data-price]"
            ]
            
            elements_found = False
            raw_data = []
            
            for selector in price_selectors:
                try:
                    elements = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                    )
                    if elements and len(elements) > 1:  # Need multiple rows for meaningful data
                        self.logger.info(f"Found {len(elements)} price elements with selector: {selector}")
                        elements_found = True
                        
                        # Extract data from each element
                        for i, element in enumerate(elements):
                            try:
                                text_content = element.text.strip()
                                if text_content and len(text_content.split()) > 1:  # Skip headers with single words
                                    
                                    # Try to extract from table cells if it's a table row
                                    cells = element.find_elements(By.TAG_NAME, "td")
                                    if not cells:
                                        cells = element.find_elements(By.TAG_NAME, "th")
                                    
                                    if cells:
                                        cell_texts = [cell.text.strip() for cell in cells]
                                        raw_info = {
                                            'row_index': i,
                                            'full_text': text_content,
                                            'cells': cell_texts,
                                            'selector_used': selector,
                                            'timestamp': datetime.now().isoformat()
                                        }
                                    else:
                                        # Not a table, just extract text
                                        raw_info = {
                                            'row_index': i,
                                            'full_text': text_content,
                                            'selector_used': selector,
                                            'timestamp': datetime.now().isoformat()
                                        }
                                    
                                    raw_data.append(raw_info)
                                    
                            except Exception as e:
                                self.logger.warning(f"Error extracting element {i}: {e}")
                                continue
                        break
                        
                except TimeoutException:
                    continue
                except Exception as e:
                    self.logger.warning(f"Error with selector {selector}: {e}")
                    continue
            
            # Process raw data to extract vegetable prices
            if raw_data:
                vegetables_data = self.process_price_data(raw_data)
            
            if not elements_found:
                # Fallback: get page source for manual inspection
                self.logger.warning("No vegetable price elements found")
                self.logger.info("Capturing page content for analysis...")
                
                # Try to find any table or structured content
                try:
                    tables = self.driver.find_elements(By.TAG_NAME, "table")
                    if tables:
                        for i, table in enumerate(tables):
                            table_html = table.get_attribute('outerHTML')[:500]
                            debug_info = {
                                'table_index': i,
                                'table_html_preview': table_html,
                                'table_text_preview': table.text[:200],
                                'timestamp': datetime.now().isoformat()
                            }
                            vegetables_data.append(debug_info)
                    else:
                        # No tables found, get general page info
                        page_title = self.driver.title
                        body_text = self.driver.find_element(By.TAG_NAME, "body").text[:500]
                        
                        debug_info = {
                            'page_title': page_title,
                            'body_text_preview': body_text,
                            'current_url': self.driver.current_url,
                            'timestamp': datetime.now().isoformat(),
                            'message': 'No table structure found for vegetable prices'
                        }
                        vegetables_data.append(debug_info)
                        
                except Exception as e:
                    self.logger.error(f"Error in fallback data extraction: {e}")
                
        except Exception as e:
            self.logger.error(f"Error scraping vegetables price data: {e}")
            error_info = {
                'error': str(e),
                'timestamp': datetime.now().isoformat(),
                'url': config.URL
            }
            vegetables_data.append(error_info)
            
        return vegetables_data
    
    def process_price_data(self, raw_data):
        """Process raw scraped data to extract vegetable names and prices"""
        processed_vegetables = {}
        
        self.logger.info(f"Processing {len(raw_data)} raw data entries for price extraction")
        
        for entry in raw_data:
            try:
                if 'cells' in entry and entry['cells']:
                    # Table format - try to identify vegetable name and prices
                    cells = entry['cells']
                    
                    # Skip header rows (common header keywords)
                    if any(keyword in ' '.join(cells).lower() for keyword in 
                           ['vegetable', 'price', 'min', 'max', 'average', 'market', 'तरकारी', 'मूल्य']):
                        continue
                    
                    # Try different table structures
                    if len(cells) >= 4:  # Expected: [vegetable, min_price, max_price, avg_price] or similar
                        vegetable_name = cells[0]
                        price_cells = cells[1:]
                        
                        # Extract all prices from remaining cells
                        all_prices = []
                        for cell in price_cells:
                            prices = self.extract_price_from_text(cell)
                            all_prices.extend(prices)
                        
                        if vegetable_name and all_prices:
                            if vegetable_name not in processed_vegetables:
                                processed_vegetables[vegetable_name] = []
                            processed_vegetables[vegetable_name].extend(all_prices)
                    
                    elif len(cells) >= 2:  # Minimum: [vegetable, price]
                        vegetable_name = cells[0]
                        price_text = ' '.join(cells[1:])
                        prices = self.extract_price_from_text(price_text)
                        
                        if vegetable_name and prices:
                            if vegetable_name not in processed_vegetables:
                                processed_vegetables[vegetable_name] = []
                            processed_vegetables[vegetable_name].extend(prices)
                
                else:
                    # Non-table format - try to extract from full text
                    full_text = entry.get('full_text', '')
                    # This is more complex and might need manual inspection of data first
                    pass
                    
            except Exception as e:
                self.logger.warning(f"Error processing entry {entry.get('row_index', 'unknown')}: {e}")
                continue
        
        # Calculate min, max, average for each vegetable
        final_vegetables_data = []
        for vegetable_name, prices in processed_vegetables.items():
            if prices:  # Only if we have price data
                price_stats = {
                    'vegetable_name': vegetable_name,
                    'min_price': min(prices),
                    'max_price': max(prices),
                    'average_price': round(sum(prices) / len(prices), 2),
                    'price_count': len(prices),
                    'all_prices': prices,
                    'timestamp': datetime.now().isoformat()
                }
                final_vegetables_data.append(price_stats)
        
        self.logger.info(f"Processed price data for {len(final_vegetables_data)} vegetables")
        return final_vegetables_data
        
    def save_data(self, data):
        """Save scraped vegetable price data to JSON file"""
        try:
            # Load existing data if file exists
            existing_data = []
            if config.OUTPUT_FILE.exists():
                with open(config.OUTPUT_FILE, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    
            # Add new data with timestamp
            new_entry = {
                'scrape_timestamp': datetime.now().isoformat(),
                'vegetables_count': len(data),
                'vegetables_price_data': data
            }
            existing_data.append(new_entry)
            
            # Save updated data
            with open(config.OUTPUT_FILE, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2, ensure_ascii=False)
                
            self.logger.info(f"Vegetable price data saved to {config.OUTPUT_FILE}")
            self.logger.info(f"Scraped price data for {len(data)} vegetables")
            
            # Print summary to console
            if data and isinstance(data[0], dict) and 'vegetable_name' in data[0]:
                print("\n" + "="*60)
                print("VEGETABLE PRICE SUMMARY")
                print("="*60)
                for item in data:
                    if 'vegetable_name' in item:
                        print(f"Vegetable: {item['vegetable_name']}")
                        print(f"  Min Price: Rs. {item['min_price']}")
                        print(f"  Max Price: Rs. {item['max_price']}")
                        print(f"  Average Price: Rs. {item['average_price']}")
                        print(f"  Price Points: {item['price_count']}")
                        print("-" * 40)
                print("="*60)
            
        except Exception as e:
            self.logger.error(f"Error saving data: {e}")
            raise
            
    def run(self):
        """Run the complete scraping process"""
        try:
            self.logger.info("Starting Nepali Patro vegetable scraper...")
            
            # Setup and run scraper
            self.setup_driver()
            self.load_page()
            vegetables_data = self.scrape_vegetables_data()
            self.save_data(vegetables_data)
            
            self.logger.info("Scraping completed successfully!")
            
        except Exception as e:
            self.logger.error(f"Scraping failed: {e}")
            raise
        finally:
            if self.driver:
                self.driver.quit()
                self.logger.info("Browser closed")

def main():
    scraper = NepaliPatroVegetableScraper()
    scraper.run()

if __name__ == "__main__":
    main()