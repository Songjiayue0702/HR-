"""
Cloudflare Worker - 智能简历数据库系统
将Flask应用迁移为Cloudflare Worker
"""
import json
import os
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from d1_adapter import D1Adapter
from r2_storage import FileStorageAdapter
# 注意：以下导入的模块需要确保在Workers环境中可用
# 如果某些模块不可用，需要找到替代方案或移除相关功能
try:
    from utils.file_parser import extract_text
    from utils.info_extractor import InfoExtractor
    from utils.ai_extractor import AIExtractor
    from utils.duplicate_checker import check_duplicate
    from utils.export import export_resumes_to_excel, export_interviews_to_excel
    from utils.export_pdf import export_resume_analysis_to_pdf, export_interview_round_analysis_to_pdf
except ImportError as e:
    print(f"警告: 某些工具模块导入失败: {e}")
    # 这些功能可能需要在Workers中重新实现或使用替代方案

try:
    from werkzeug.utils import secure_filename
except ImportError:
    # 如果werkzeug不可用，使用简单的替代方案
    def secure_filename(filename):
        import re
        filename = re.sub(r'[^\w\s-]', '', filename)
        return re.sub(r'[-\s]+', '-', filename).strip('-_')

import secrets
import hashlib


# 配置
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
EDUCATION_LEVELS = ['博士', '硕士', '本科', '大专', '高中', '职高', '初中', '其他']


def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def json_response(data, status=200, headers=None):
    """创建JSON响应"""
    response_headers = {'Content-Type': 'application/json; charset=utf-8'}
    if headers:
        response_headers.update(headers)
    return Response(
        json.dumps(data, ensure_ascii=False),
        status=status,
        headers=response_headers
    )


def error_response(message, status=400):
    """创建错误响应"""
    return json_response({'success': False, 'message': message}, status)


def success_response(data=None, message=None):
    """创建成功响应"""
    response = {'success': True}
    if data is not None:
        response['data'] = data
    if message:
        response['message'] = message
    return json_response(response)


class SessionManager:
    """Session管理器（使用cookie）"""
    
    @staticmethod
    def get_session(request):
        """从请求中获取session"""
        cookies = {}
        cookie_header = request.headers.get('Cookie', '')
        if cookie_header:
            for cookie in cookie_header.split(';'):
                if '=' in cookie:
                    key, value = cookie.strip().split('=', 1)
                    cookies[key] = value
        
        session_id = cookies.get('session_id')
        if not session_id:
            return {}
        
        # 这里应该从KV或D1中获取session数据
        # 为了简化，我们暂时使用cookie直接存储（不安全，仅用于演示）
        # 生产环境应该使用Workers KV或D1存储session
        return cookies
    
    @staticmethod
    def set_session(response, session_data):
        """设置session到响应"""
        # 生成session ID
        session_id = secrets.token_urlsafe(32)
        
        # 设置cookie
        cookie_value = f"session_id={session_id}; Path=/; HttpOnly; SameSite=Lax"
        response.headers['Set-Cookie'] = cookie_value
        
        # 这里应该将session数据存储到KV或D1
        # 为了简化，暂时跳过
        
        return response


async def get_current_user(request, db_adapter):
    """获取当前登录用户"""
    session = SessionManager.get_session(request)
    user_id = session.get('user_id')
    if not user_id:
        return None
    
    try:
        user = await db_adapter.get_user_by_id(int(user_id))
        return user
    except:
        return None


def require_login(func):
    """登录装饰器"""
    async def wrapper(request, env, *args, **kwargs):
        db_adapter = D1Adapter(env.DB)
        user = await get_current_user(request, db_adapter)
        if not user:
            return error_response('请先登录', 401)
        return await func(request, env, user, *args, **kwargs)
    return wrapper


def require_admin(func):
    """管理员权限装饰器"""
    async def wrapper(request, env, *args, **kwargs):
        db_adapter = D1Adapter(env.DB)
        user = await get_current_user(request, db_adapter)
        if not user:
            return error_response('请先登录', 401)
        if user.get('role') != 'admin':
            return error_response('需要管理员权限', 403)
        return await func(request, env, user, *args, **kwargs)
    return wrapper


# ========== 路由处理函数 ==========

async def handle_login(request, env):
    """处理登录"""
    try:
        data = await request.json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return error_response('用户名和密码不能为空', 400)
        
        db_adapter = D1Adapter(env.DB)
        user = await db_adapter.get_user_by_username(username)
        
        if not user or not db_adapter.check_password(user['password_hash'], password):
            return error_response('用户名或密码错误', 401)
        
        if user.get('is_active') != 1:
            return error_response('账户已被禁用', 403)
        
        # 登录成功，设置session
        response = success_response(data={'user': {
            'id': user['id'],
            'username': user['username'],
            'role': user['role'],
            'real_name': user.get('real_name'),
            'department': user.get('department'),
            'group_name': user.get('group_name')
        }}, message='登录成功')
        
        # 设置session cookie
        session_id = secrets.token_urlsafe(32)
        cookie_value = f"session_id={session_id}; user_id={user['id']}; Path=/; HttpOnly; SameSite=Lax"
        response.headers['Set-Cookie'] = cookie_value
        
        # TODO: 将session存储到KV或D1
        
        return response
    except Exception as e:
        return error_response(f'登录失败: {str(e)}', 500)


async def handle_logout(request, env):
    """处理登出"""
    response = success_response(message='已退出登录')
    # 清除cookie
    response.headers['Set-Cookie'] = 'session_id=; Path=/; HttpOnly; SameSite=Lax; Max-Age=0'
    return response


async def handle_current_user(request, env):
    """获取当前用户信息"""
    db_adapter = D1Adapter(env.DB)
    user = await get_current_user(request, db_adapter)
    if not user:
        return error_response('未登录', 401)
    
    return success_response(data={'user': {
        'id': user['id'],
        'username': user['username'],
        'role': user['role'],
        'real_name': user.get('real_name'),
        'department': user.get('department'),
        'group_name': user.get('group_name')
    }})


async def handle_upload(request, env, user):
    """处理文件上传"""
    try:
        # 获取Content-Type
        content_type = request.headers.get('Content-Type', '')
        
        if 'multipart/form-data' not in content_type:
            return error_response('请求格式错误，需要multipart/form-data', 400)
        
        # 解析multipart表单数据
        # 注意：Cloudflare Workers Python运行时可能需要使用不同的方法
        # 这里假设可以使用formData()方法
        try:
            form_data = await request.formData()
            files = []
            
            # 提取文件
            for key, value in form_data.entries():
                if key == 'file':
                    # 检查是否是文件对象
                    if hasattr(value, 'arrayBuffer') or hasattr(value, 'stream'):
                        files.append(value)
                    elif isinstance(value, (bytes, bytearray)):
                        # 如果已经是字节数据
                        files.append(value)
        except Exception as e:
            print(f"解析表单数据失败: {e}")
            return error_response('解析表单数据失败', 400)
        
        if not files:
            return error_response('没有文件', 400)
        
        storage = FileStorageAdapter(env.UPLOADS_BUCKET, env.EXPORTS_BUCKET)
        db_adapter = D1Adapter(env.DB)
        
        uploaded_count = 0
        failed_files = []
        resume_ids = []
        
        for file in files:
            if not file.name or not allowed_file(file.name):
                failed_files.append(file.name or 'unknown')
                continue
            
            try:
                # 读取文件数据
                if hasattr(file, 'arrayBuffer'):
                    file_data = await file.arrayBuffer()
                    file_bytes = bytes(file_data)
                elif hasattr(file, 'stream'):
                    # 如果是流，读取所有数据
                    chunks = []
                    async for chunk in file.stream():
                        chunks.append(chunk)
                    file_bytes = b''.join(chunks)
                elif isinstance(file, (bytes, bytearray)):
                    file_bytes = bytes(file)
                else:
                    raise ValueError(f"不支持的文件类型: {type(file)}")
                
                # 获取文件名和类型
                file_name = getattr(file, 'name', 'unknown')
                file_type = getattr(file, 'type', 'application/octet-stream')
                
                # 保存到R2
                file_key = await storage.save_upload(
                    file_bytes,
                    file_name,
                    file_type
                )
                
                # 创建数据库记录
                resume_id = await db_adapter.create_resume({
                    'file_name': file.name,
                    'file_path': file_key,  # 存储R2的key而不是本地路径
                    'parse_status': 'pending',
                    'created_by': user['username'],
                    'updated_by': user['username']
                })
                
                # TODO: 异步处理简历解析
                # 在Workers中，可以使用Queue或Durable Objects来处理异步任务
                # 这里暂时标记为pending，后续可以通过定时任务或手动触发处理
                
                uploaded_count += 1
                resume_ids.append(resume_id)
            except Exception as e:
                print(f"文件 {file.name} 上传失败: {e}")
                failed_files.append(file.name)
        
        if uploaded_count > 0:
            return success_response(
                data={
                    'uploaded_count': uploaded_count,
                    'failed_count': len(failed_files),
                    'failed_files': failed_files,
                    'resume_ids': resume_ids
                },
                message=f'成功上传 {uploaded_count} 个文件，正在解析...'
            )
        else:
            return error_response(
                f'所有文件上传失败：{", ".join(failed_files) if failed_files else "不支持的文件格式"}',
                400
            )
    except Exception as e:
        return error_response(f'上传失败: {str(e)}', 500)


async def handle_get_resumes(request, env):
    """获取简历列表"""
    try:
        db_adapter = D1Adapter(env.DB)
        
        # 获取查询参数
        url = urlparse(request.url)
        params = parse_qs(url.query)
        
        page = int(params.get('page', [1])[0])
        per_page = int(params.get('per_page', [10])[0])
        search = params.get('search', [''])[0]
        status = params.get('status', [''])[0]
        
        filters = {}
        if status:
            filters['parse_status'] = status
        
        offset = (page - 1) * per_page
        resumes = await db_adapter.list_resumes(filters=filters, limit=per_page, offset=offset)
        
        # TODO: 实现搜索功能
        # 目前D1适配器的list_resumes方法支持基本的筛选
        
        return success_response(data={
            'resumes': resumes,
            'page': page,
            'per_page': per_page,
            'total': len(resumes)  # TODO: 实现总数统计
        })
    except Exception as e:
        return error_response(f'获取简历列表失败: {str(e)}', 500)


async def handle_get_resume(request, env, resume_id):
    """获取简历详情"""
    try:
        db_adapter = D1Adapter(env.DB)
        resume = await db_adapter.get_resume(resume_id)
        
        if not resume:
            return error_response('简历不存在', 404)
        
        return success_response(data={'resume': resume})
    except Exception as e:
        return error_response(f'获取简历详情失败: {str(e)}', 500)


async def handle_get_education_levels(request, env):
    """获取教育层级选项"""
    return success_response(data=EDUCATION_LEVELS)


# ========== 主路由处理 ==========

async def handle_route(request, env):
    """处理路由"""
    url = urlparse(request.url)
    path = url.path
    method = request.method
    
    # 静态文件（CSS、JS、图片等）
    if path.startswith('/static/'):
        # 在Workers中，静态文件通常通过Pages或R2提供
        # 这里返回404，实际应该配置Pages或使用R2
        return Response('Not Found', status=404)
    
    # 首页和登录页
    if path == '/' or path == '/login':
        # 返回HTML模板
        # 在Workers中，可以使用HTML模板或通过Pages提供
        return Response('<!DOCTYPE html><html><body><h1>智能简历数据库系统</h1><p>请配置Pages或使用R2提供静态文件</p></body></html>', 
                       headers={'Content-Type': 'text/html; charset=utf-8'})
    
    # API路由
    if path.startswith('/api/'):
        # 登录相关
        if path == '/api/login' and method == 'POST':
            return await handle_login(request, env)
        elif path == '/api/logout' and method == 'POST':
            return await handle_logout(request, env)
        elif path == '/api/current-user' and method == 'GET':
            return await handle_current_user(request, env)
        
        # 教育层级
        elif path == '/api/education-levels' and method == 'GET':
            return await handle_get_education_levels(request, env)
        
        # 简历相关
        elif path == '/api/upload' and method == 'POST':
            user = await get_current_user(request, D1Adapter(env.DB))
            if not user:
                return error_response('请先登录', 401)
            return await handle_upload(request, env, user)
        elif path == '/api/resumes' and method == 'GET':
            return await handle_get_resumes(request, env)
        elif path.startswith('/api/resumes/') and method == 'GET':
            try:
                resume_id = int(path.split('/')[-1])
                return await handle_get_resume(request, env, resume_id)
            except ValueError:
                return error_response('无效的简历ID', 400)
        
        # 其他API路由...
        # TODO: 实现更多路由
        
        return error_response('路由不存在', 404)
    
    return error_response('路由不存在', 404)


# ========== Worker入口 ==========

async def on_fetch(request, env):
    """
    Cloudflare Worker入口函数
    
    Args:
        request: Request对象
        env: 环境变量（包含DB、UPLOADS_BUCKET、EXPORTS_BUCKET等）
    """
    try:
        # 处理CORS预检请求
        if request.method == 'OPTIONS':
            return Response(None, headers={
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization',
                'Access-Control-Max-Age': '86400'
            })
        
        # 处理路由
        response = await handle_route(request, env)
        
        # 添加CORS头
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        
        return response
    except Exception as e:
        print(f"Worker错误: {e}")
        import traceback
        traceback.print_exc()
        return error_response(f'服务器错误: {str(e)}', 500)


# 导出Worker入口
# 注意：Cloudflare Workers Python运行时使用不同的导出方式
# 这里使用标准的Python函数，实际部署时可能需要根据Workers Python运行时调整

# 如果使用Workers Python运行时，可能需要这样导出：
# export default on_fetch

# 或者使用Cloudflare Workers的Python绑定：
if __name__ == '__main__':
    # 本地测试
    print("Worker已加载，请在Cloudflare Workers环境中运行")

