"""检查两个简历的解析结果"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import get_db_session, Resume

db = get_db_session()

# 查找两个简历
r1 = db.query(Resume).filter_by(name='邱曙光').first()
r2 = db.query(Resume).filter(Resume.file_name.like('%李宜隆%')).order_by(Resume.id.desc()).first()

print("=" * 60)
print("邱曙光:")
print("=" * 60)
if r1:
    print(f"姓名: {r1.name}")
    print(f"专业: {r1.major}")
    print(f"工作经历: {len(r1.work_experience) if r1.work_experience else 0}条")
    if r1.work_experience:
        for i, exp in enumerate(r1.work_experience[:3], 1):
            print(f"  {i}. {exp.get('company')} - {exp.get('position')} ({exp.get('start_year')}-{exp.get('end_year')})")
else:
    print("未找到")

print("\n" + "=" * 60)
print("李宜隆:")
print("=" * 60)
if r2:
    print(f"姓名: {r2.name}")
    print(f"专业: {r2.major}")
    print(f"工作经历: {len(r2.work_experience) if r2.work_experience else 0}条")
    if r2.work_experience:
        for i, exp in enumerate(r2.work_experience[:3], 1):
            print(f"  {i}. {exp.get('company')} - {exp.get('position')} ({exp.get('start_year')}-{exp.get('end_year')})")
else:
    print("未找到")

db.close()





