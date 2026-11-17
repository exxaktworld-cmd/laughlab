from src.quality import word_count, validate_script

def test_word_count():
    assert word_count("That's a surprisingly good joke.") == 5

def test_accepts_target_length():
    script = " ".join(["word"] * 90)
    count, issues = validate_script(script, 82, 108)
    assert count == 90
    assert issues == []

def test_rejects_too_short():
    count, issues = validate_script("Only a few words.", 82, 108)
    assert count < 82
    assert issues

def test_rejects_generic_ai_phrase():
    script = "In today's digital age " + " ".join(["word"] * 90)
    _, issues = validate_script(script, 82, 108)
    assert any("generic" in issue.lower() for issue in issues)
