from src.scraping import stealth


def test_stealth_arguments_include_automation_flag():
    args = stealth.stealth_arguments()
    assert "--disable-blink-features=AutomationControlled" in args
    assert any("--user-agent=" in a for a in args)
    assert any("--lang=pt-BR" == a for a in args)


def test_custom_user_agent_used():
    args = stealth.stealth_arguments(user_agent="MyUA")
    assert "--user-agent=MyUA" in args


def test_excluded_switches():
    assert "enable-automation" in stealth.excluded_switches()


def test_stealth_js_masks_webdriver():
    assert "'webdriver'" in stealth.STEALTH_JS
    assert "pt-BR" in stealth.STEALTH_JS
