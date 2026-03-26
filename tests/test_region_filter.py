import pytest
from unittest.mock import MagicMock

from src.core.exceptions import FilterError
from src.scraping.region_filter import RegionFilter


class TestRegionFilterApply:
    """Tests for the full region filter application flow."""

    def _make_mock_driver(self):
        mock_driver = MagicMock()
        mock_driver.wait_for.return_value = MagicMock()
        mock_driver.find_all.return_value = [MagicMock()]
        mock_driver.execute_script.return_value = 0
        return mock_driver

    def test_raises_filter_error_when_chip_not_found(self):
        mock_driver = self._make_mock_driver()
        mock_driver.find_all.return_value = []

        rf = RegionFilter(mock_driver)
        with pytest.raises(FilterError):
            rf.apply("Brazil")


class TestRegionFilterRemoveCurrent:
    """Tests for unchecking currently selected regions."""

    def _make_mock_driver(self):
        mock_driver = MagicMock()
        mock_driver.wait_for.return_value = MagicMock()
        mock_driver.find_all.return_value = [MagicMock()]
        mock_driver.execute_script.return_value = 0
        return mock_driver

    def test_remove_current_calls_execute_script(self):
        mock_driver = self._make_mock_driver()
        mock_driver.execute_script.return_value = 1

        rf = RegionFilter(mock_driver)
        rf._remove_current()

        mock_driver.execute_script.assert_called_once()
        js_code = mock_driver.execute_script.call_args[0][0]
        assert "checkbox" in js_code

    def test_remove_current_handles_zero_checked(self):
        mock_driver = self._make_mock_driver()
        mock_driver.execute_script.return_value = 0

        rf = RegionFilter(mock_driver)
        rf._remove_current()

        mock_driver.execute_script.assert_called_once()


class TestRegionFilterTypeAndSelect:
    """Tests for typing region and selecting checkbox."""

    def _make_mock_driver(self):
        mock_driver = MagicMock()
        mock_driver.wait_for.return_value = MagicMock()
        mock_driver.find_all.return_value = [MagicMock()]
        mock_driver.execute_script.return_value = 0
        return mock_driver

    def test_types_and_clicks_via_js(self):
        mock_driver = self._make_mock_driver()
        mock_input = MagicMock()
        mock_driver.wait_for.return_value = mock_input
        mock_driver.execute_script.return_value = "label:Brazil"

        rf = RegionFilter(mock_driver)
        rf._type_and_select("Brazil")

        mock_input.clear.assert_called_once()
        mock_input.send_keys.assert_called_once_with("Brazil")
        mock_driver.execute_script.assert_called_once()

    def test_handles_missing_search_input(self):
        mock_driver = self._make_mock_driver()
        mock_driver.wait_for.side_effect = Exception("timeout")

        rf = RegionFilter(mock_driver)
        rf._type_and_select("Brazil")


class TestRegionFilterClickApply:
    """Tests for clicking the Apply button."""

    def _make_mock_driver(self):
        mock_driver = MagicMock()
        mock_driver.wait_for.return_value = MagicMock()
        mock_driver.find_all.return_value = [MagicMock()]
        mock_driver.execute_script.return_value = 0
        return mock_driver

    def test_uses_click_element(self):
        mock_driver = self._make_mock_driver()
        mock_btn = MagicMock()
        mock_driver.wait_for.return_value = mock_btn

        rf = RegionFilter(mock_driver)
        rf._click_apply()

        mock_driver.click_element.assert_called_once_with(mock_btn)

    def test_falls_back_to_js(self):
        mock_driver = self._make_mock_driver()
        mock_driver.wait_for.side_effect = Exception("timeout")
        mock_driver.execute_script.return_value = "Apply"

        rf = RegionFilter(mock_driver)
        rf._click_apply()

        mock_driver.execute_script.assert_called_once()


class TestRegionFilterFindChip:
    """Tests for finding the region chip button."""

    def _make_mock_driver(self):
        mock_driver = MagicMock()
        mock_driver.wait_for.return_value = MagicMock()
        mock_driver.find_all.return_value = [MagicMock()]
        mock_driver.execute_script.return_value = 0
        return mock_driver

    def test_returns_matching_button(self):
        mock_driver = self._make_mock_driver()
        region_btn = MagicMock()
        region_btn.text = "Region / United States"
        other_btn = MagicMock()
        other_btn.text = "Sector"
        mock_driver.find_all.return_value = [other_btn, region_btn]

        rf = RegionFilter(mock_driver)
        result = rf._find_chip()

        assert result is region_btn

    def test_fallback_searches_all_buttons(self):
        mock_driver = self._make_mock_driver()
        region_btn = MagicMock()
        region_btn.text = "Region / United States"
        mock_driver.find_all.side_effect = [[], [region_btn]]

        rf = RegionFilter(mock_driver)
        result = rf._find_chip()

        assert result is region_btn
        assert mock_driver.find_all.call_count == 2

    def test_returns_none_when_not_found(self):
        mock_driver = self._make_mock_driver()
        mock_driver.find_all.return_value = []

        rf = RegionFilter(mock_driver)
        result = rf._find_chip()

        assert result is None
