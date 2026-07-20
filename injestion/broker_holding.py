import time
import pandas as pd
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


def get_weekly_holdings(symbol: str):
    with sync_playwright() as p:
        # Keep headless=False for now so you can verify the spinner goes away
        browser = p.chromium.launch(headless=False)

        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720},
        )

        # CRUCIAL STEALTH FIX: Hide the automation footprint to break the infinite spinner
        context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        page = context.new_page()
        page.goto(
            "https://nepsealpha.com/broker-holding",
            wait_until="domcontentloaded",
        )

        # 1. Handle the period dropdown selection
        page.wait_for_selector("#report-types", state="attached", timeout=15000)
        page.select_option("#report-types", value="W")

        # 2. Open Select2 search dropdown container
        page.wait_for_selector("span.select2-selection--single")
        page.click("span.select2-selection--single")

        # 3. Enter the target symbol into the active search input field
        page.wait_for_selector("input.select2-search__field")
        page.fill("input.select2-search__field", symbol)

        # 4. Wait for Select2 list items and click the exact matching symbol
        page.wait_for_selector("ul.select2-results__options li")
        page.click(f"ul.select2-results__options li:has-text('{symbol}')")

        # Small delay for DOM synchronization
        time.sleep(0.5)

        # 5. Click the Filter button
        page.wait_for_selector("button:has-text('Filter')")
        page.click("button:has-text('Filter')", force=True)

        # 6. Wait for the tables to load into view (Spinner should clear now)
        page.wait_for_selector(
            "#broker_holder_buyer_div table", state="visible", timeout=30000
        )
        page.wait_for_selector(
            "#broker_holder_seller_div table", state="visible", timeout=30000
        )

        # Extract DOM data strings
        buyer_html = page.locator(
            "#broker_holder_buyer_div div.table-responsive"
        ).inner_html()
        seller_html = page.locator(
            "#broker_holder_seller_div div.table-responsive"
        ).inner_html()

        context.close()
        browser.close()

        # Parse dataframes
        df_buyers = parse_dynamic_table(buyer_html, action_type="Buy")
        df_sellers = parse_dynamic_table(seller_html, action_type="Sell")

        combined_df = pd.concat([df_buyers, df_sellers], ignore_index=True)
        return combined_df


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
    target_symbol = "UNHPL"
    print(f"Running stealth extraction pipeline for: {target_symbol}...")
    stock_data = get_weekly_holdings(target_symbol)
    print("\n--- Final Extracted Data ---")
    print(stock_data)