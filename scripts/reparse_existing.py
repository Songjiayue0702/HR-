"""重新解析已存在的简历记录"""
from datetime import datetime
from models import get_db_session, Resume
from utils.info_extractor import InfoExtractor
from utils.file_parser import extract_text


def reparse_all(batch_size: int = 50) -> None:
    """重新解析所有保存的 raw_text，并更新数据库字段"""
    session = get_db_session()
    extractor = InfoExtractor()

    try:
        query = session.query(Resume).order_by(Resume.id.asc())
        total = query.count()
        print(f"待重新解析的简历数量: {total}")

        processed = 0
        for resume in query.yield_per(batch_size):
            text = resume.raw_text
            if not text:
                try:
                    text = extract_text(resume.file_path)
                    resume.raw_text = text
                except Exception as err:
                    resume.parse_status = 'failed'
                    resume.error_message = str(err)
                continue

            info = extractor.extract_all(text)
            resume.name = info.get('name')
            resume.gender = info.get('gender')
            resume.birth_year = info.get('birth_year')
            resume.age = info.get('age')
            resume.phone = info.get('phone')
            resume.email = info.get('email')
            resume.earliest_work_year = info.get('earliest_work_year')
            resume.work_experience_years = info.get('work_experience_years')
            resume.work_experience = info.get('work_experience')
            resume.highest_education = info.get('highest_education')
            resume.school = info.get('school')
            resume.major = info.get('major')
            resume.parse_status = 'success'
            resume.parse_time = datetime.now()
            resume.error_message = None

            processed += 1
            if processed % batch_size == 0:
                session.commit()
                print(f"已更新 {processed}/{total} 条记录")

        session.commit()
        print("重新解析完成")
    finally:
        session.close()


if __name__ == "__main__":
    reparse_all()
