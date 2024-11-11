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


from woob.browser import LoginBrowser, URL, need_login
from woob.browser.selenium import (
    SeleniumBrowser, IsHereCondition, webdriver,
)
from woob.capabilities.bank import Account
from woob.tools.capabilities.bank.investments import create_french_liquidity

from .pages import HomePage, DashboardPage


class BullionstarBrowser(SeleniumBrowser):
    BASEURL = 'https://www.bullionstar.com'
    HEADLESS = True  # Always change to True for prod
    DRIVER = webdriver.Firefox

    home = URL(r'$', HomePage)
    dashboard = URL(r'/myaccount/dashboard', DashboardPage)

    def __init__(self, username: str, password: str, *args, **kwargs):
        super(BullionstarBrowser, self).__init__(*args, **kwargs)
        self.username = username
        self.password = password

    def deinit(self):
        if self.page and self.page.logged:
            self.location(f"{BASEURL}/deconnexion")
        super(BullionstarBrowser, self).deinit()

    def do_login(self):
        self.home.go()
        if not self.home.is_here():
            print("oops")
        self.page.click_login_button()

        return self.page.fill_login_form(self.username, self.password)

    @need_login
    def iter_accounts(self):# -> Iterable[Account]:
        """
        Iter accounts for a single account `default_account` in aucoffre.

        :rtype: iter[:class:`Account`]
        """
        # Navigate to the dashboard to load account information
        if not self.dashboard.is_here():
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

        if not self.dashboard.is_here():
            self.dashboard.go()
        account = self.page.get_account_info()
        return account

    @need_login
    def iter_investment(self, account: Account):  # -> Iterable[Investment]
        """
        Iterate over investments for a specified account.

        :param account: The account from which investments are to be retrieved
        :rtype: iter[:class:`Investment`]
        """
        if not self.dashboard.is_here():
            self.dashboard.go()

        all_investments = {}

        # Retrieve products on the current page
        raw_investments = self.page.products

        # Accumulate investments across pages
        for raw_inv in raw_investments:
            if raw_inv.label not in all_investments:
                all_investments[raw_inv.label] = raw_inv
            else:
                all_investments[raw_inv.label].quantity += raw_inv.quantity
                all_investments[raw_inv.label].valuation += raw_inv.valuation

        # Yield accumulated investments across all pages
        for inv in all_investments.values():
            if inv.quantity:  # or other conditions
                yield inv

        if account._liquidity > 0:
            yield create_french_liquidity(account._liquidity)
