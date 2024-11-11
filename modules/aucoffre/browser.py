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


from functools import wraps
import time

from woob.browser.selenium import (
    SeleniumBrowser, IsHereCondition, webdriver,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

from woob.tools.capabilities.bank.investments import create_french_liquidity
from woob.browser import LoginBrowser, URL, need_login
from woob.capabilities.bank import Account
from .pages import LoginPage, DashboardPage, ProductListPage


class AucoffreBrowser(SeleniumBrowser):
    BASEURL = 'https://www.aucoffre.com'

    login = URL(r'/connexion', LoginPage)
    dashboard = URL(r'/transactions/tableau-de-bord', DashboardPage)
    products_list = URL(r'/pieces/desc-piecelibre/pageNum-(?P<pagenum>\d+)/displayMode-3/liste-par-utilisateur', ProductListPage)

    HEADLESS = True  # Always change to True for prod

    #WINDOW_SIZE = (1800, 1000)
    WINDOW_SIZE = (1264, 596)
    DRIVER = webdriver.Firefox

    def __init__(self, pseudo: str, username: str, password: str, *args, **kwargs):
        super(AucoffreBrowser, self).__init__(*args, **kwargs)
        self.pseudo = pseudo
        self.username = username
        self.password = password

    def deinit(self):
        if self.page and self.page.logged:
            self.location(f"{BASEURL}/deconnexion")
        super(AucoffreBrowser, self).deinit()

    def accept_cookies(self):
        ActionChains(self.driver).move_by_offset(700, 400).click().perform()
        ActionChains(self.driver).move_by_offset(-700, -400).perform()

    def do_login(self):
        self.login.go()
        self.accept_cookies()
        self.wait_until(IsHereCondition(self.login))
        self.page.login(self.pseudo, self.username, self.password)

        if self.login.is_here():
            error = self.page.get_error()
            #raise AssertionError('Unhandled behavior at login: error is "{}"'.format(error))

        if self.dashboard.is_here():
            print("in dashboard. Jump to product list")
            #self.products_list.go()

    @need_login
    def iter_investment(self, account: Account):  # -> Iterable[Investment]
        """
        Iterate over investments for a specified account.

        :param account: The account from which investments are to be retrieved
        :rtype: iter[:class:`Investment`]
        """
        page_url = self.products_list
        pagenum=1
        if not page_url.is_here():
            self.products_list.go(pagenum=pagenum)

        all_investments = {}

        while True:
            # Retrieve products on the current page
            raw_investments = self.page.products

            # Accumulate investments across pages
            for raw_inv in raw_investments:
                if raw_inv.label not in all_investments:
                    all_investments[raw_inv.label] = raw_inv
                else:
                    all_investments[raw_inv.label].quantity += raw_inv.quantity
                    all_investments[raw_inv.label].valuation += raw_inv.valuation

            # Check if there's a next page and navigate if available
            if self.page.has_next_page():
                pagenum = pagenum + 1
                self.products_list.go(pagenum=pagenum)
            else:
                break

        # Yield accumulated investments across all pages
        for inv in all_investments.values():
            if inv.quantity:  # or other conditions
                yield inv

        if account._liquidity > 0:
            yield create_french_liquidity(account._liquidity)

    @need_login
    def iter_accounts(self):# -> Iterable[Account]:
        """
        Iter accounts for a single account `default_account` in aucoffre.

        :rtype: iter[:class:`Account`]
        """
        # Navigate to the dashboard to load account information
        self.dashboard.go()

        # Assuming the DashboardPage parses account info into a list of Account objects
        account = self.page.get_account_info()
        if account:
            yield account

    @need_login
    def get_account(self, account_id: str) -> Account:
        """
        Get account information by ID.

        :param account_id: The ID of the account to retrieve
        :rtype: :class:`Account`
        """
        if account_id != 'default_account':
            raise ValueError("Only 'default_account' is supported for aucoffre")

        self.dashboard.go()
        account = self.page.get_account_info()
        return account
