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


from woob.capabilities.bank import Account, CapBankWealth
from woob.tools.backend import Module, BackendConfig
from woob.tools.value import ValueBackendPassword

from .browser import BullionstarBrowser


__all__ = ['BullionstarModule']


class BullionstarModule(Module, CapBankWealth):
    NAME = 'bullionstar'
    DESCRIPTION = 'Bullionstar'
    MAINTAINER = 'Uncaged Coder'
    EMAIL = 'uncaged-coder@proton.me'
    LICENSE = 'LGPLv3+'
    CONFIG = BackendConfig(
        ValueBackendPassword('login', label='login', masked=False),
        ValueBackendPassword('password', label='password', masked=True),
    )

    BROWSER = BullionstarBrowser

    def create_default_browser(self):
        login = self.config['login'].get()
        password = self.config['password'].get()
        browser = self.create_browser(login, password)
        return browser

    def iter_accounts(self):
        return self.browser.iter_accounts()

    def iter_history(self, account):
        return self.browser.iter_history(account)

    def iter_investment(self, account):
        return self.browser.iter_investment(account)

    def iter_market_orders(self, account):
        return self.browser.iter_market_orders(account)
