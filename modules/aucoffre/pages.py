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

from decimal import Decimal
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from woob.browser.elements import ItemElement, TableElement, method
from woob.browser.filters.html import TableCell
from woob.browser.filters.standard import CleanText, CleanDecimal
from woob.browser.pages import LoggedPage, pagination
from woob.browser.selenium import SeleniumPage
from woob.capabilities.bank.wealth import Investment
from woob.capabilities.bank import Account


class LoginPage(SeleniumPage):

    def login(self, pseudo, identifiant, secret, captcha_response=None):
        try:
            # Fill in the form fields
            pseudo_field = self.driver.find_element(By.NAME, 'usr_pseudo')
            pseudo_field.send_keys(pseudo)

            identifiant_field = self.driver.find_element(By.NAME, 'usr_identifiant')
            identifiant_field.send_keys(identifiant)

            secret_field = self.driver.find_element(By.NAME, 'usr_cle')
            secret_field.send_keys(secret)

            # Fill CAPTCHA if provided
            if captcha_response:
                captcha_field = self.driver.find_element(By.NAME, 'g-recaptcha-response')
                captcha_field.send_keys(captcha_response)

            # Wait until the "Se connecter" button is clickable
            submit_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, '//button[@type="submit" and contains(@class, "btn-primary")]'))
            )

            # Use JavaScript to click the button if .click() doesn't work
            self.driver.execute_script("arguments[0].click();", submit_button)
            print("Form submitted successfully.")

        except Exception as e:
            print("Error during login process:", e)

    def get_error(self):
        # Locate and return error messages if present
        try:
            error_element = self.driver.find_element(By.XPATH, '//div[contains(@class, "errors")]')
            return error_element.text  # Capture and return the text of the error
        except Exception:
            return None  # Return None if no error messages are found

class DashboardPage(LoggedPage, SeleniumPage):
    def get_account_info(self) -> Account:
        """
        Retrieve account information from the dashboard page using Selenium.

        :rtype: :class:`Account`
        """
        account = Account()
        account.id = 'default_account'
        account.label = "My Aucoffre Account"

        # Extract the 'Valorisation moyenne' as the portfolio balance
        try:
            portfolio_value_text = self.driver.find_element(
                By.XPATH, '//h4[contains(text(), "Valeur totale")]/following-sibling::dl[contains(@class, "dl-portefeuille")]/dd[2]'
            ).text
            portfolio_value = Decimal(portfolio_value_text.replace('€', '').replace(',', '.').replace(' ', ''))
        except Exception as e:
            print(f"Error extracting portfolio balance: {e}")
            portfolio_value = Decimal('0')

        # Extract the 'Compte d'attente' as liquidity balance
        try:
            liquidity_text = self.driver.find_element(
                By.XPATH, '//span[contains(@class, "amount_available_input")]'
            ).text
            liquidity_value = Decimal(liquidity_text.replace('€', '').replace(',', '.').replace(' ', ''))
        except Exception as e:
            print(f"Error extracting liquidity balance: {e}")
            liquidity_value = Decimal('0')

        # Calculate the total balance
        total_balance = portfolio_value + liquidity_value
        account.balance = total_balance
        account.currency = u'EUR'
        account._liquidity = liquidity_value

        return account

class ProductListPage(LoggedPage, SeleniumPage):
    @property
    def products(self):
        products = []
        rows = self.browser.driver.find_elements(By.XPATH, '//table[contains(@class, "table-hover")]/tbody/tr')

        # Skip first row that is only title text for each columns
        for row in rows[1:]:
            try:
                product_type = row.find_element(By.XPATH, './td[2]').text.strip()
                #metal = row.find_element(By.XPATH, './td[6]').text.strip()
                price_text = row.find_element(By.XPATH, './td[7]').text.replace('€', '').replace(',', '.').replace(' ', '').strip()
                valuation_text = row.find_element(By.XPATH, './td[8]').text.replace('€', '').replace(',', '.').replace(' ', '').strip()

                # Convert prices and valuations to Decimal
                price = Decimal(price_text) if price_text else Decimal('0')
                valuation = Decimal(valuation_text) if valuation_text else Decimal('0')

                # Create an Investment instance
                investment = Investment()
                investment.label = product_type
                investment.code = "N/A"  # or assign a code if available
                investment.code_type = Investment.CODE_TYPE_ISIN  # or "N/A" if not applicable
                investment.quantity = Decimal('1')  # Adjust as needed
                investment.unitprice = price
                investment.valuation = valuation
                #investment.metal = metal  # Custom field if applicable

                products.append(investment)

            except Exception as e:
                print(f"Error parsing row: {e}")
                continue
        return products

    def has_next_page(self):
        """ Check if 'Suivant' link exists on the current page by partial match """
        try:
            # Search for any link that contains "Suivant" in its text
            self.browser.driver.find_element(By.XPATH, "//a[contains(text(), 'Suivant')]")
            return True
        except NoSuchElementException:
            return False
