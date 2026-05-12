import pytest
from tools.scraper import _clean_markdown

def test_markdown_cleaner_strips_images():
    """Verify that the markdown cleaner successfully removes image tags."""
    dirty_text = "Here is a picture: ![cute cat](https://example.com/cat.jpg)\nAnd here is text."
    cleaned = _clean_markdown(dirty_text)
    
    assert "cute cat" not in cleaned
    assert "https://example.com/cat.jpg" not in cleaned
    assert "Here is a picture:" in cleaned

def test_markdown_cleaner_strips_urls():
    """Verify that URLs are stripped but the anchor text remains."""
    dirty_text = "Please [click here](https://website.com) to read more."
    cleaned = _clean_markdown(dirty_text)
    
    assert "click here" in cleaned
    assert "https://website.com" not in cleaned

def test_markdown_cleaner_removes_orphaned_lines():
    """Verify that short lines (like nav bars) are removed, but headers stay."""
    dirty_text = (
        "Home | About | Contact\n"
        "# Main Article Title\n"
        "This is a long sentence that has more than four words in it."
    )
    cleaned = _clean_markdown(dirty_text)
    
    assert "Home | About | Contact" not in cleaned
    assert "# Main Article Title" in cleaned
    assert "This is a long sentence" in cleaned
