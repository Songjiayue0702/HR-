# create_req.py
with open('cf-requirements.txt', 'w', encoding='utf-8', newline='\n') as f:
    f.write('Flask\n')
    f.write('Werkzeug\n')
    f.write('pymupdf\n')
    f.write('requests\n')
    f.write('sqlalchemy\n')
    f.write('python-dotenv')
print("已创建符合规范的 cf-requirements.txt 文件。")