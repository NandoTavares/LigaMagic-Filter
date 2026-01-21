
import time
import re
from collections import Counter
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


START_URL = "https://www.ligamagic.com.br/?view=cards/card&card=Squee,%20the%20Immortal"
DECK_FILE = "deck.txt"
OUTPUT_FILE = "store_ranking.txt"
WAIT_TIME_INITIAL = 20  
MAX_STORES_PER_CARD = 10 

def clean_card_name(line):

    return re.sub(r'^\d+\s+', '', line).strip()

def main():

    print("Setting up WebDriver...")
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service)
    except Exception as e:
        print(f"Error setting up WebDriver: {e}")
        return

    store_counter = Counter()
    processed_cards = 0

    try:

        print(f"Navigating to start URL: {START_URL}")
        driver.get(START_URL)
        
        print(f"Waiting {WAIT_TIME_INITIAL} seconds for manual interaction/loading...")
        time.sleep(WAIT_TIME_INITIAL)

        with open(DECK_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        total_cards = len(lines)
        print(f"Found {total_cards} cards in {DECK_FILE}")


        for index, line in enumerate(lines):
            card_name = clean_card_name(line)
            if not card_name:
                continue

            print(f"\nProcessing [{index+1}/{total_cards}]: {card_name}")


            if index > 0:

                try:
                    search_input = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, "mainsearch"))
                    )
                    search_input.clear()
                    search_input.send_keys(card_name)
                    

                    time.sleep(2) 
                    try:

                        first_item = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, ".autocomplete > div"))
                        )
                        first_item.click()
                    except Exception as e:
                        print(f"Autocomplete click failed, trying Enter: {e}")
                        search_input.send_keys(Keys.RETURN)

                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.ID, "marketplace-stores"))
                    )
                    
                except Exception as e:
                    print(f"Error navigating to {card_name}: {e}")
                    continue

            try:

                container = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, "marketplace-stores"))
                )
                

                rows = container.find_elements(By.CSS_SELECTOR, ".store")
                
                print(f"Found {len(rows)} store offers.")
                
                count = 0
                for row in rows:
                    if count >= MAX_STORES_PER_CARD:
                        break
                    
                    try:
                        store_link = row.find_element(By.CSS_SELECTOR, "a.link-store")
                        href = store_link.get_attribute("href")
                        

                        store_id_match = re.search(r"[?&]id=(\d+)", href)
                        
                        price_element = row.find_element(By.CSS_SELECTOR, ".price")
                        price_text = price_element.text
                        
                        if store_id_match:
                            store_id = store_id_match.group(1)
                            store_counter[store_id] += 1
                            count += 1
                            print(f"  - Captured ID: {store_id} ({price_text})")
                        else:
                            print(f"  - Warning: Store ID not found in href: {href}")
                            
                    except Exception as row_error:
                        continue
                        
            except Exception as e:
                print(f"Error scraping data for {card_name}: {e}")

            processed_cards += 1

            time.sleep(1)

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        print("\nClosing WebDriver...")
        driver.quit()


    print("\n" + "="*40)
    print("FINAL STORE RANKING (Top 30)")
    print("="*40)
    
    ranking = store_counter.most_common()
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as out:
        out.write("Ranking de Lojas (ID)\n")
        out.write("="*60 + "\n")
        
        for rank, (store_id, count) in enumerate(ranking, 1):
            link = f"https://www.ligamagic.com.br/?view=mp/showcase/home&id={store_id}"
            line_out = f"{rank}. ID: {store_id} | Aparições: {count} | Link: {link}"
            print(line_out)
            out.write(line_out + "\n")
            
            if rank >= 100: 
                pass

    print(f"\nResults saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
