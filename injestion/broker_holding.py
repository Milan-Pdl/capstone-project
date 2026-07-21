import time
import pandas as pd
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


def get_all_available_symbols(page) -> list:
    """Extracts all stock symbols by opening the Select2 dropdown and reading the list items."""
    # 1. Click open the Select2 dropdown container to force the list items to render in the DOM
    page.wait_for_selector("span.select2-selection--single")
    page.click("span.select2-selection--single")
    
    # 2. Wait for the options list shown in your screenshot to become visible
    page.wait_for_selector("ul.select2-results__options li.select2-results__option", timeout=15000)
    
    # 3. Extract the text from all available list options
    symbols = page.evaluate("""
        () => {
            const listItems = document.querySelectorAll('ul.select2-results__options li.select2-results__option');
            return Array.from(listItems)
                .map(li => li.textContent.trim())
                .filter(sym => sym && !sym.includes('Select Symbol'));
        }
    """)
    
    # Close the dropdown panel by pressing Escape so we can begin the clean looping process
    page.keyboard.press("Escape")
    return symbols


def get_weekly_holdings_for_all():
    all_data = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)

        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720},
        )

        # Stealth injection to bypass security block
        context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        page = context.new_page()
        page.goto(
            "https://nepsealpha.com/broker-holding",
            wait_until="domcontentloaded",
        )

        # Handle the period dropdown selection (Weekly)
        page.wait_for_selector("#report-types", state="attached", timeout=15000)
        page.select_option("#report-types", value="W")

        # Extract all stock symbols dynamically from the UI list elements
        print("Fetching the complete list of stock symbols...")
        symbols = get_all_available_symbols(page)
        print(f"Found {len(symbols)} symbols to process.")

        # Loop through every symbol discovered
        for index, symbol in enumerate(symbols, start=1):
            print(f"[{index}/{len(symbols)}] Processing symbol: {symbol}...")
            
            try:
                # Open Select2 search dropdown container
                page.wait_for_selector("span.select2-selection--single")
                page.click("span.select2-selection--single")

                # Enter the target symbol into the active search input field
                page.wait_for_selector("input.select2-search__field")
                page.fill("input.select2-search__field", symbol)

                # Wait for Select2 list items and click the exact matching symbol text
                page.wait_for_selector("ul.select2-results__options li")
                page.click(f"ul.select2-results__options li:has-text('{symbol}')")

                # Small delay for DOM state alignment
                time.sleep(0.5)

                # Click the Filter button
                page.click("button:has-text('Filter')", force=True)

                # Wait for both data grids to populate and become fully visible
                page.wait_for_selector(
                    "#broker_holder_buyer_div table", state="visible", timeout=15000
                )
                page.wait_for_selector(
                    "#broker_holder_seller_div table", state="visible", timeout=15000
                )

                # Safely fetch the specific date range text block
                page.wait_for_selector("div.card-header .card-title b")
                date_range_text = (
                    page.locator("div.card-header .card-title b").first.inner_text()
                )

                # Extract DOM data layout strings
                buyer_html = page.locator(
                    "#broker_holder_buyer_div div.table-responsive"
                ).inner_html()
                seller_html = page.locator(
                    "#broker_holder_seller_div div.table-responsive"
                ).inner_html()

                # Parse dynamic collections into structured pandas frames
                df_buyers = parse_dynamic_table(buyer_html, action_type="Buy")
                df_sellers = parse_dynamic_table(seller_html, action_type="Sell")

                # Combine datasets for this symbol
                combined_df = pd.concat([df_buyers, df_sellers], ignore_index=True)

                if not combined_df.empty:
                    combined_df["Symbol"] = symbol
                    combined_df["Period_Range"] = date_range_text.strip()
                    combined_df["Scraped_At"] = pd.Timestamp.now()
                    all_data.append(combined_df)
                
                # Courtesy pause between stocks
                time.sleep(1)

            except Exception as e:
                print(f"Skipping {symbol} due to an error: {e}")
                continue

        context.close()
        browser.close()

    if all_data:
        master_df = pd.concat(all_data, ignore_index=True)
        return master_df
    else:
        return pd.DataFrame()


def parse_dynamic_table(html_content: str, action_type: str) -> pd.DataFrame:
    soup = BeautifulSoup(html_content, "html.parser")
    data_dict = {}

    for row in soup.find_all("tr"):
        header_el = row.find("th")
        if header_el:
            header_name = header_el.get_text(strip=True)
            values = [td.get_text(strip=True) for td in row.find_all("td")]
            data_dict[header_name] = values

    df = pd.DataFrame(data_dict)

    if not df.empty:
        if "Broker" in df.columns:
            df["Broker"] = df["Broker"].astype(str)
        if "Quantity" in df.columns:
            df["Quantity"] = pd.to_numeric(df["Quantity"], errors="coerce")
        df["Type"] = action_type

    return df


if __name__ == "__main__":
    print("Starting full batch broker holding extraction pipeline...")
    master_stock_data = get_weekly_holdings_for_all()

    print("\n--- Final Master Extracted Data ---")
    if not master_stock_data.empty:
        print(f"Total Rows Scraped: {len(master_stock_data)}")
        master_stock_data.to_csv("all_broker_holdings.csv", index=False)
        print("Data successfully saved to 'all_broker_holdings.csv'")
    else:
        print("No data was collected.")