from backend.judge.models import Language

class LanguageValidator:
    @staticmethod
    def validate(language_id):
        if not language_id:
            return False, "Vui lòng chọn ngôn ngữ lập trình.", None
        
        # Support both ID (e.g. 1) and Key (e.g. 'CPP17', 'cpp17', 'PY3')
        lang = None
        if str(language_id).isdigit():
            lang = Language.objects.filter(id=int(language_id), is_active=True).first()
        if not lang:
            lang = Language.objects.filter(key__iexact=str(language_id), is_active=True).first()

        if not lang:
            return False, f"Ngôn ngữ lập trình '{language_id}' không hợp lệ hoặc đã bị vô hiệu hóa.", None
        return True, "", lang
