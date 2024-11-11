# Copyright(C) 2024      Uncaged Coder
#
# This file is part of a woob module.
#
# This woob module is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This woob module is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this woob module. If not, see <http://www.gnu.org/licenses/>.

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from decimal import Decimal
from woob.browser.pages import LoggedPage
from woob.browser.selenium import SeleniumPage
import time
from woob.capabilities.bank import Account
from woob.capabilities.bank.wealth import Investment


class HomePage(LoggedPage, SeleniumPage):
    def click_login_button(self):
        # Locate and click the login button to open the popup
        login_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.ID, 'btn-login'))
        )
        if login_button:
            login_button.click()
        else:
            raise ValueError("Login button not found")

    def fill_login_form(self, _id, password):
        # Wait for and locate email, password fields, and login button
        email_field = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//input[@data-param="email"]'))
        )
        password_field = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//input[@data-param="hashedPassword"]'))
        )

        if email_field and password_field:
            # Enter email and password, then click login
            email_field.send_keys(_id)
            password_field.send_keys(password)
        else:
            raise ValueError("Login form elements not found")

        login_button = self.driver.find_element(By.ID, 'btn-popup-login')
        if login_button:
            login_button.click()
        else:
            raise ValueError("Login form elements not found")

        self._wait_tobe_fully_logged()

    def _wait_tobe_fully_logged(self):
        for _ in range(10):
            is_login = self.driver.execute_script("return localStorage.getItem('isLogin');")
            if is_login == 'true':
                return
            time.sleep(1)
        print("Login failed or timed out.")


class DashboardPage(LoggedPage, SeleniumPage):
    def get_account_info(self) -> Account:
        """
        Retrieve account information from the dashboard page using Selenium.

        :rtype: :class:`Account`
        """
        account = Account()

        # Extract account number
        try:
            account_number = self.driver.find_element(
                By.XPATH, '//td[contains(text(), "BullionStar Account Number")]/span[@class="account-number"]'
            ).text
            account.id = account_number.strip()
        except Exception as e:
            print(f"Error extracting account number: {e}")
            account.id = "Unknown Account"

        # Extract account name
        try:
            account_name = self.driver.find_element(
                By.XPATH, '//td[@class="account-name -bold"]'
            ).text
            account.label = account_name.strip()
        except Exception as e:
            print(f"Error extracting account name: {e}")
            account.label = "Unnamed Account"

        # Extract total assets
        try:
            total_assets_text = self.driver.find_element(
                By.XPATH, '//td[@class="text-right total-assets-amount -bold"]/span[contains(@class, "valuation") and not(contains(@class, "hide"))]'
            ).text
            total_assets = Decimal(total_assets_text.replace('€', '').replace(',', '').strip())
        except Exception as e:
            print(f"Error extracting total assets: {e}")
            total_assets = Decimal('0')

        # Extract cash balance
        try:
            cash_balance_text = self.driver.find_element(
                By.XPATH, '//div[@class="cash-balance"]/header/p[@class="pull-right"]/span[@class="-bold total"]'
            ).text
            cash_balance = Decimal(cash_balance_text.replace('€', '').replace(',', '').strip())
        except Exception as e:
            print(f"Error extracting cash balance: {e}")
            cash_balance = Decimal('0')

        # Set account balance and currency
        account.balance = total_assets
        account.currency = 'EUR'
        account._liquidity = cash_balance

        return account

    @property
    def products(self):
        products = []

        try:
            # Wait until the bullion portfolio table is visible
            table = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//div[@class="bullion-portfolio-wrap"]//table[@class="bullion-portfolio"]/tbody'))
            )

            # Locate all rows within the product table's tbody
            rows = table.find_elements(By.XPATH, './tr')
            num_rows = len(rows)

            # Iterate through each row to extract product details
            i = 0
            while i < num_rows:
                try:
                    # First row for label or metal type
                    product_info = rows[i].text.strip()
                    # Extract product type/label from the first row
                    if product_info:
                        # This might be the product label or type
                        investment_label = product_info

                    # Check if there's a next row for details
                    if i + 1 < num_rows:
                        details_row = rows[i + 1]
                        # Extract quantity, buy price, today's price, and market value
                        quantity_text = details_row.find_element(By.XPATH, './td[1]').text.strip()
                        quantity = Decimal(quantity_text.replace(',', '').strip()) if quantity_text else Decimal('0')

                        buy_price_text = details_row.find_element(By.XPATH, './td[2]').text.strip()
                        buy_price = Decimal(buy_price_text.replace('€', '').replace(',', '').strip()) if buy_price_text else Decimal('0')

                        todays_price_text = details_row.find_element(By.XPATH, './td[3]').text.strip()
                        todays_price = Decimal(todays_price_text.replace('€', '').replace(',', '').strip()) if todays_price_text else Decimal('0')

                        mkt_value_text = details_row.find_element(By.XPATH, './td[5]').text.strip()
                        mkt_value = Decimal(mkt_value_text.replace('€', '').replace(',', '').strip()) if mkt_value_text else Decimal('0')

                        # Initialize an Investment object for the product
                        investment = Investment()
                        investment.label = investment_label  # Set the label from the first row
                        investment.code = "N/A"  # Placeholder for code
                        investment.code_type = Investment.CODE_TYPE_ISIN  # Placeholder for code type
                        investment.quantity = quantity
                        investment.unitprice = buy_price
                        investment.valuation = mkt_value

                        products.append(investment)

                    # Move to the next investment, which spans two rows
                    i += 2

                except Exception as e:
                    print(f"Error parsing product row: {e}")
                    i += 1  # Move to the next row in case of error

        except Exception as e:
            print(f"Error locating product table rows: {e}")

        return products


