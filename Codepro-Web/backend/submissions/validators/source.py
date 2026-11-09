class SourceCodeValidator:
    MAX_SIZE = 65536 # 64 KB

    @classmethod
    def validate(cls, source_code: str):
        if not isinstance(source_code, str) or not source_code.strip():
            return False, "Mã nguồn không được để trống."
        if len(source_code.encode('utf-8')) > cls.MAX_SIZE:
            return False, f"Dung lượng mã nguồn vượt quá giới hạn cho phép ({cls.MAX_SIZE // 1024} KB)."
        if '\x00' in source_code:
            return False, "Mã nguồn chứa ký tự không hợp lệ (null byte)."
        return True, ""
