from unittest.mock import MagicMock

from src.scraping.consent_handler import ConsentHandler


class TestConsentHandler:
    """Tests for the consent banner dismissal."""

    def test_dismiss_clicks_first_matching_button(self):
        mock_driver = MagicMock()
        mock_btn = MagicMock()
        mock_driver.wait_for.return_value = mock_btn

        handler = ConsentHandler(mock_driver)
        handler.dismiss()

        mock_btn.click.assert_called_once()
        mock_driver.wait_for_invisible.assert_called_once()

    def test_dismiss_handles_no_banner(self):
        mock_driver = MagicMock()
        mock_driver.wait_for.side_effect = Exception("timeout")

        handler = ConsentHandler(mock_driver)
        handler.dismiss()
