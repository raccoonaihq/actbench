from raccoonai import RaccoonAI
from raccoonai.types import fleet_create_params

from .base import BaseBrowser


class FleetBrowser(BaseBrowser):
    def __init__(self, api_key: str):
        self.client = RaccoonAI(secret_key=api_key)
        self.session_id = None

    def get_cdp_url(self, url: str) -> str:
        browser = self.client.fleet.create(
            raccoon_passcode="actbench",
            url=url,
            advanced=fleet_create_params.Advanced(
                block_ads=True,
                solve_captchas=True
            )
        )
        self.session_id = browser.session_id
        cdp_url = browser.websocket_url
        return cdp_url

    def terminate(self):
        self.client.fleet.terminate(self.session_id)
