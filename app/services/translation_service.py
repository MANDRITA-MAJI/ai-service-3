from deep_translator import GoogleTranslator

def translate_to_english(text: str, source_lang: str = 'auto') -> str:
    """
    Translates text to English. 
    source_lang can be 'hi' (Hindi), 'bn' (Bengali), etc., or 'auto' to detect automatically.
    """
    if not text or text.strip() == "":
        return ""
        
    try:
        # Use deep-translator to route through Google's free endpoint
        translator = GoogleTranslator(source=source_lang, target='en')
        return translator.translate(text)
    except Exception as e:
        print(f"[translation_service] Translation failed: {e}")
        # Fallback to returning the original text if the translation fails
        return text