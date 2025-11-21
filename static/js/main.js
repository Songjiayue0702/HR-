// 全局变量
let currentPage = 1;
let perPage = 10;
let totalPages = 1;
let sortBy = 'upload_time';
let sortOrder = 'desc';
let selectedResumes = new Set();
let currentResumeData = null;
let aiConfigStatus = null; // AI配置状态缓存
let interviewedResumeIds = new Set(); // 已邀约面试的简历ID集合
let selectedInterviews = new Set();   // 面试流程列表中选中的行ID

function escapeHtml(value) {
    if (value === null || value === undefined) {
        return '';
    }
    return String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

// 全局变量
let currentAnalysisResumeId = null;

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    initUpload();
    
    // 检查URL参数，切换到指定模块
    const urlParams = new URLSearchParams(window.location.search);
    const module = urlParams.get('module');
    if (module) {
        switchModule(module);
    } else {
        // 默认显示上传模块
        switchModule('upload');
    }
    
    // 初始化时检查AI状态
    checkAIStatus().then(() => {
        updateAIStatusDisplay();
    });

    // 加载已邀约面试的简历ID
    fetch('/api/interviews/resume-ids')
        .then(response => response.json())
        .then(result => {
            if (result.success && Array.isArray(result.data)) {
                interviewedResumeIds = new Set(result.data);
            }
        })
        .catch(err => {
            console.error('加载已邀约面试简历列表失败:', err);
        });
});

// 初始化上传功能
function initUpload() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    
    uploadArea.addEventListener('click', () => fileInput.click());
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);
    fileInput.addEventListener('change', handleFileSelect);
}

function handleDragOver(e) {
    e.preventDefault();
    e.currentTarget.classList.add('dragover');
}

function handleDragLeave(e) {
    e.currentTarget.classList.remove('dragover');
}

function handleDrop(e) {
    e.preventDefault();
    e.currentTarget.classList.remove('dragover');
    const files = e.dataTransfer.files;
    uploadFiles(files);
}

function handleFileSelect(e) {
    const files = e.target.files;
    if (files && files.length > 0) {
        uploadFiles(files);
    }
    // 清空input，允许重复选择相同文件
    e.target.value = '';
}

// 上传文件
function uploadFiles(files) {
    const formData = new FormData();
    for (let file of files) {
        formData.append('file', file);
    }
    
    // 添加AI配置（从本地存储或表单获取）
    const aiConfig = {
        ai_enabled: document.getElementById('aiEnabled') ? document.getElementById('aiEnabled').checked : false,
        ai_model: document.getElementById('aiModel') ? document.getElementById('aiModel').value : 'gpt-3.5-turbo',
        ai_api_key: document.getElementById('aiApiKey') ? document.getElementById('aiApiKey').value : (localStorage.getItem('ai_api_key') || ''),
        ai_api_base: document.getElementById('aiApiBase') ? document.getElementById('aiApiBase').value : ''
    };
    formData.append('ai_config', JSON.stringify(aiConfig));
    
    const progressDiv = document.getElementById('uploadProgress');
    const progressFill = document.getElementById('progressFill');
    const progressText = document.getElementById('progressText');
    
    progressDiv.style.display = 'block';
    progressFill.style.width = '0%';
    progressText.textContent = '上传中...';
    
    fetch('/api/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            progressFill.style.width = '100%';
            const fileCount = files.length;
            const uploadedCount = data.uploaded_count || fileCount;
            if (fileCount > 1) {
                progressText.textContent = `成功上传 ${uploadedCount}/${fileCount} 个文件，正在解析...`;
            } else {
                progressText.textContent = '上传成功，正在解析...';
            }
            // 立即刷新列表，显示新上传的简历
            loadResumes();
            // 2秒后隐藏进度条，但继续自动刷新直到解析完成
            setTimeout(() => {
                progressDiv.style.display = 'none';
            }, 2000);
        } else {
            alert('上传失败: ' + data.message);
            progressDiv.style.display = 'none';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('上传失败，请重试');
        progressDiv.style.display = 'none';
    });
}

// 加载简历列表
function loadResumes(page = 1) {
    currentPage = page;
    const selectAll = document.getElementById('selectAll');
    if (selectAll) {
        selectAll.checked = false;
    }
    
    const searchInput = document.getElementById('searchInput');
    const genderFilter = document.getElementById('genderFilter');
    const educationFilter = document.getElementById('educationFilter');
    
    if (!searchInput || !genderFilter || !educationFilter) {
        console.warn('Search/filter elements not found, module may not be active');
        return;
    }
    
    const search = searchInput.value;
    const gender = genderFilter.value;
    const education = educationFilter.value;
    
    const params = new URLSearchParams({
        page: page,
        per_page: perPage,
        sort_by: sortBy,
        sort_order: sortOrder
    });
    
    if (search) params.append('search', search);
    if (gender) params.append('gender', gender);
    if (education) params.append('education', education);
    
    fetch(`/api/resumes?${params}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const currentIds = new Set(data.data.map(item => item.id));
                selectedResumes.forEach(id => {
                    if (!currentIds.has(id)) {
                        selectedResumes.delete(id);
                    }
                });
                // 先检查AI状态，然后显示简历列表
                checkAIStatus().then(() => {
                    displayResumes(data.data);
                }).catch(() => {
                    displayResumes(data.data);
                });
                totalPages = Math.ceil(data.total / perPage);
                updatePagination();
            }
        })
        .catch(error => {
            console.error('Error:', error);
            const tbody = document.getElementById('resumeTableBody');
            if (tbody) {
                tbody.innerHTML = '<tr><td colspan="15" class="loading">加载失败，请刷新重试</td></tr>';
            }
        });
}

// 显示简历列表
function displayResumes(resumes) {
    const tbody = document.getElementById('resumeTableBody');
    if (!tbody) {
        console.warn('resumeTableBody element not found');
        return;
    }
    
    if (resumes.length === 0) {
        tbody.innerHTML = '<tr><td colspan="15" class="loading">暂无数据</td></tr>';
        return;
    }
    
    // 检查是否有正在处理的简历，如果有则设置自动刷新
    const hasProcessing = resumes.some(r => r.parse_status === 'pending' || r.parse_status === 'processing');
    if (hasProcessing) {
        // 如果有正在处理的简历，3秒后自动刷新
        if (window.refreshTimer) {
            clearTimeout(window.refreshTimer);
        }
        window.refreshTimer = setTimeout(() => {
            loadResumes(currentPage);
        }, 3000);
    } else {
        // 如果没有正在处理的简历，清除定时器
        if (window.refreshTimer) {
            clearTimeout(window.refreshTimer);
            window.refreshTimer = null;
        }
    }
    
    // 渲染简历行
    tbody.innerHTML = resumes.map(resume => {
        const isSelected = selectedResumes.has(resume.id);
        // 计算工龄：今年-最早工作年份
        const currentYear = new Date().getFullYear();
        let earliestYear = resume.earliest_work_year;
        
        // 如果earliest_work_year为空，从工作经历中计算
        if (!earliestYear && resume.work_experience && resume.work_experience.length > 0) {
            const workYears = resume.work_experience
                .map(exp => exp.start_year)
                .filter(year => year !== null && year !== undefined);
            if (workYears.length > 0) {
                earliestYear = Math.min(...workYears);
            }
        }
        
        const workYears = earliestYear 
            ? (currentYear - earliestYear) 
            : null;
        const workYearsDisplay = workYears !== null && workYears >= 0 ? workYears : '-';
        
        // 计算身份验证码：姓名+手机号后四位
        let identityCode = '-';
        if (resume.name) {
            const phone = resume.phone || '';
            if (phone && phone.length >= 4) {
                identityCode = escapeHtml(resume.name) + phone.slice(-4);
            } else {
                identityCode = escapeHtml(resume.name);
            }
        }
        
        // 查重显示
        let duplicateDisplay = '';
        if (resume.duplicate_status === '重复简历' && resume.duplicate_similarity && resume.duplicate_similarity >= 80) {
            duplicateDisplay = '<span class="duplicate-warning">重复简历</span>';
        }
        
        // 解析状态显示
        let statusDisplay = '';
        const parseStatus = resume.parse_status || 'pending';
        if (parseStatus === 'pending') {
            statusDisplay = '<span class="status-pending">待处理</span>';
        } else if (parseStatus === 'processing') {
            statusDisplay = '<span class="status-processing">处理中</span>';
        } else if (parseStatus === 'success') {
            statusDisplay = '<span class="status-success">已完成</span>';
        } else if (parseStatus === 'failed') {
            statusDisplay = '<span class="status-failed">失败</span>';
        } else {
            statusDisplay = '<span class="status-unknown">未知</span>';
        }
        
        const alreadyInvited = interviewedResumeIds.has(resume.id);
        // 如果状态不是success，禁用查看/编辑按钮
        const viewButtonDisabled = parseStatus !== 'success' ? 'disabled' : '';
        const viewButtonClass = parseStatus !== 'success' ? 'btn btn-small btn-view btn-disabled' : 'btn btn-small btn-view';
        
        return `
        <tr class="${isSelected ? 'selected' : ''}">
            <td><input type="checkbox" value="${resume.id}" ${isSelected ? 'checked' : ''} ${parseStatus !== 'success' ? 'disabled' : ''} onchange="toggleResume(${resume.id}, this)"></td>
            <td>${escapeHtml(resume.applied_position) || '-'}</td>
            <td>${identityCode}</td>
            <td>${escapeHtml(resume.name) || '-'}</td>
            <td>${escapeHtml(resume.gender) || '-'}</td>
            <td>${resume.age || '-'}</td>
            <td>${workYearsDisplay}</td>
            <td>${escapeHtml(resume.phone) || '-'}</td>
            <td>${escapeHtml(resume.email) || '-'}</td>
            <td>${escapeHtml(resume.highest_education) || '-'}</td>
            <td>${escapeHtml(resume.school) || '-'}</td>
            <td>${escapeHtml(resume.major) || '-'}</td>
            <td>${duplicateDisplay}</td>
            <td>${statusDisplay}</td>
            <td>
                <button class="${viewButtonClass}" ${viewButtonDisabled} onclick="viewDetail(${resume.id})">查看/编辑</button>
                <button class="btn btn-small ${alreadyInvited ? 'btn-success' : 'btn-secondary'}" 
                    ${parseStatus !== 'success' || alreadyInvited ? 'disabled' : ''} 
                    onclick="inviteInterview(${resume.id})">
                    ${alreadyInvited ? '已邀约面试' : '邀约面试'}
                </button>
            </td>
        </tr>
    `;
    }).join('');
}

function getStatusIcon(status) {
    if (!status || status === '未校验') return '';
    
    const icons = {
        '完全匹配': '✅',
        '多项选择': '❓',
        '匹配失败': '❌',
        '未校验': '⚪'
    };
    
    return icons[status] || '';
}

// 排序
function sortTable(column) {
    if (sortBy === column) {
        sortOrder = sortOrder === 'asc' ? 'desc' : 'asc';
    } else {
        sortBy = column;
        sortOrder = 'asc';
    }
    loadResumes(currentPage);
}

// 分页
function updatePagination() {
    const pagination = document.getElementById('pagination');
    let html = '';
    
    if (currentPage > 1) {
        html += `<button onclick="loadResumes(${currentPage - 1})">上一页</button>`;
    }
    
    for (let i = 1; i <= totalPages; i++) {
        if (i === currentPage) {
            html += `<button class="active" onclick="loadResumes(${i})">${i}</button>`;
        } else if (i === 1 || i === totalPages || (i >= currentPage - 2 && i <= currentPage + 2)) {
            html += `<button onclick="loadResumes(${i})">${i}</button>`;
        } else if (i === currentPage - 3 || i === currentPage + 3) {
            html += `<button disabled>...</button>`;
        }
    }
    
    if (currentPage < totalPages) {
        html += `<button onclick="loadResumes(${currentPage + 1})">下一页</button>`;
    }
    
    pagination.innerHTML = html;
}

// 选择简历
function toggleResume(id, checkbox) {
    const row = checkbox.closest('tr');
    if (checkbox.checked) {
        selectedResumes.add(id);
        if (row) {
            row.classList.add('selected');
        }
    } else {
        selectedResumes.delete(id);
        if (row) {
            row.classList.remove('selected');
        }
    }
}

function toggleSelectAll() {
    const selectAll = document.getElementById('selectAll');
    const checkboxes = document.querySelectorAll('#resumeTableBody input[type="checkbox"]');
    
    checkboxes.forEach(cb => {
        cb.checked = selectAll.checked;
        if (selectAll.checked) {
            selectedResumes.add(parseInt(cb.value));
            cb.closest('tr')?.classList.add('selected');
        } else {
            selectedResumes.delete(parseInt(cb.value));
            cb.closest('tr')?.classList.remove('selected');
        }
    });
}

// 查看详情
function viewDetail(id) {
    fetch(`/api/resumes/${id}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayDetail(data.data);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('加载详情失败');
        });
}

function displayDetail(resume) {
    currentResumeData = resume;
    const modal = document.getElementById('detailModal');
    const content = document.getElementById('detailContent');
    const genderOptions = ['', '男', '女']
        .map(g => `<option value="${g}" ${resume.gender === g ? 'selected' : ''}>${g || '未选择'}</option>`).join('');
    const educationOptionsList = ['', '博士', '硕士', '本科', '大专', '专科', '高中', '中专', '职高'];
    const educationOptions = educationOptionsList
        .map(item => `<option value="${item}" ${resume.highest_education === item ? 'selected' : ''}>${item || '未选择'}</option>`).join('');
    const workExperienceText = resume.work_experience && resume.work_experience.length > 0
        ? JSON.stringify(resume.work_experience, null, 2)
        : '';
    const parseStatus = resume.parse_status || '-';
    const errorMessage = resume.error_message || '';
    
    content.innerHTML = `
        <h3>编辑简历信息</h3>
        <div class="form-grid">
            <label>文件名
                <input type="text" value="${escapeHtml(resume.file_name || '')}" disabled>
            </label>
            <label>上传时间
                <input type="text" value="${escapeHtml(resume.upload_time || '')}" disabled>
            </label>
            <label>解析状态
                <input type="text" value="${escapeHtml(parseStatus)}" disabled>
            </label>
            <label>解析时间
                <input type="text" value="${escapeHtml(resume.parse_time || '')}" disabled>
            </label>
            <label>应聘岗位
                <select id="editAppliedPosition" class="form-select">
                    <option value="">请选择岗位</option>
                </select>
            </label>
        </div>
        <div class="form-grid">
            <label>姓名
                <input id="editName" type="text" value="${escapeHtml(resume.name || '')}">
            </label>
            <label>性别
                <select id="editGender">
                    ${genderOptions}
                </select>
            </label>
            <label>出生年份
                <input id="editBirthYear" type="number" value="${resume.birth_year || ''}">
            </label>
            <label>最早工作年份
                <input id="editEarliestWorkYear" type="number" value="${(() => {
                    // 如果数据库中有值，使用数据库的值；否则从工作经历中计算
                    if (resume.earliest_work_year) {
                        return resume.earliest_work_year;
                    }
                    const workExps = resume.work_experience || [];
                    if (workExps.length > 0) {
                        const years = workExps
                            .map(exp => exp.start_year)
                            .filter(year => year !== null && year !== undefined);
                        if (years.length > 0) {
                            return Math.min(...years);
                        }
                    }
                    return '';
                })()}">
            </label>
            <label>手机号
                <input id="editPhone" type="text" value="${escapeHtml(resume.phone || '')}">
            </label>
            <label>邮箱
                <input id="editEmail" type="email" value="${escapeHtml(resume.email || '')}">
            </label>
            <label>最高学历
                <select id="editEducation">
                    ${educationOptions}
                </select>
            </label>
            <label>毕业学校
                <input id="editSchool" type="text" value="${escapeHtml(resume.school || '')}">
            </label>
            <label>专业
                <input id="editMajor" type="text" value="${escapeHtml(resume.major || '')}">
            </label>
        </div>
        <div class="work-experience-section">
            <div class="work-experience-title">最新工作经历（仅显示前2段，只读，自动同步）</div>
            <div class="work-experience-content">
                ${(() => {
                    // 对工作经历按开始时间由近到远排序（降序）
                    const sortedExps = [...(resume.work_experience || [])].sort((a, b) => {
                        const yearA = a.start_year || 0;
                        const yearB = b.start_year || 0;
                        return yearB - yearA; // 降序，最新的在前
                    });
                    const experiences = sortedExps.slice(0, 2);
                    if (!experiences.length) {
                        return '<div class="work-experience-item">暂无数据</div>';
                    }
                    // 确保显示2段（如果不足2段，用空数据填充）
                    while (experiences.length < 2) {
                        experiences.push({ company: '', position: '', start_year: '', end_year: '' });
                    }
                    return experiences.map((exp, idx) => `
                        <div class="work-experience-item">
                            <div class="work-exp-field">
                                <div class="work-exp-label">公司名称</div>
                                <input type="text" id="expCompany${idx}" value="${escapeHtml(exp.company || '')}" readonly>
                            </div>
                            <div class="work-exp-field">
                                <div class="work-exp-label">岗位</div>
                                <input type="text" id="expPosition${idx}" value="${escapeHtml(exp.position || '')}" readonly>
                            </div>
                            <div class="work-exp-field">
                                <div class="work-exp-label">开始年份</div>
                                <input type="number" id="expStart${idx}" value="${exp.start_year || ''}" readonly>
                            </div>
                            <div class="work-exp-field">
                                <div class="work-exp-label">结束年份</div>
                                <input type="number" id="expEnd${idx}" value="${exp.end_year || ''}" readonly>
                            </div>
                        </div>
                    `).join('');
                })()}
            </div>
        </div>
        <div class="work-experience-section">
            <div class="work-experience-title">全部工作经历（可编辑，修改后自动同步至最新工作经历）</div>
            <div class="work-experience-content">
                <div style="margin-bottom: 10px;">
                    <button class="btn btn-primary" onclick="addWorkExperience()" style="padding: 5px 15px; font-size: 13px;">+ 增加工作经历</button>
                </div>
                ${(() => {
                    // 对工作经历按开始时间由近到远排序（降序）
                    const allExps = [...(resume.work_experience || [])].sort((a, b) => {
                        const yearA = a.start_year || 0;
                        const yearB = b.start_year || 0;
                        return yearB - yearA; // 降序，最新的在前
                    });
                    if (!allExps.length) {
                        return '<div class="work-experience-item">暂无数据，点击上方按钮添加</div>';
                    }
                    return `
                        <table class="experience-table">
                            <thead>
                                <tr>
                                    <th>序号</th>
                                    <th>公司名称</th>
                                    <th>岗位</th>
                                    <th>开始年份</th>
                                    <th>结束年份</th>
                                    <th>操作</th>
                                </tr>
                            </thead>
                            <tbody id="allWorkExperienceTable">
                                ${allExps.map((exp, idx) => `
                                    <tr data-row-index="${idx}">
                                        <td>${idx + 1}</td>
                                        <td><input type="text" class="exp-company-input" data-index="${idx}" value="${escapeHtml(exp.company || '')}" placeholder="公司名称"></td>
                                        <td><input type="text" class="exp-position-input" data-index="${idx}" value="${escapeHtml(exp.position || '')}" placeholder="岗位名称"></td>
                                        <td><input type="number" class="exp-start-input" data-index="${idx}" value="${exp.start_year || ''}" placeholder="开始年份"></td>
                                        <td><input type="number" class="exp-end-input" data-index="${idx}" value="${exp.end_year || ''}" placeholder="结束年份（空为至今）"></td>
                                        <td><button class="btn btn-danger" onclick="removeWorkExperience(${idx})" style="padding: 3px 10px; font-size: 12px;">删除</button></td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    `;
                })()}
            </div>
        </div>
        <label class="textarea-label">当前错误信息
            <textarea id="editErrorMessage" rows="3" placeholder="可选">${escapeHtml(errorMessage)}</textarea>
        </label>
        <label class="textarea-label">原始文本（只读）
            <textarea rows="10" readonly>${escapeHtml(resume.raw_text || '')}</textarea>
        </label>
        <div class="modal-actions">
            <div class="modal-actions-row">
                <button class="btn btn-primary" onclick="saveResume()">保存修改</button>
                <button class="btn btn-primary" onclick="exportSingle(${resume.id})">导出Excel</button>
                <button class="btn btn-danger" onclick="deleteResume(${resume.id})">删除简历</button>
                <button class="btn btn-secondary" onclick="closeModal()">关闭</button>
            </div>
            <div class="modal-actions-row">
                <button class="btn btn-primary" onclick="previewResumeFile(${resume.id})">预览简历文件</button>
                <button class="btn btn-primary" onclick="downloadResumeFile(${resume.id})">下载简历文件</button>
            </div>
        </div>
    `;
    modal.style.display = 'block';
    
    // 加载岗位下拉选项
    populatePositionSelect('editAppliedPosition', resume.applied_position || '');
    
    // 添加全部工作经历表格的编辑事件监听
    setupWorkExperienceEditListeners();
}

// 增加工作经历
function addWorkExperience() {
    const table = document.getElementById('allWorkExperienceTable');
    if (!table) {
        // 如果表格不存在，先创建表格
        const workExpSections = document.querySelectorAll('.work-experience-section');
        let detailItem = null;
        for (const section of workExpSections) {
            const title = section.querySelector('.work-experience-title');
            if (title && title.textContent.includes('全部工作经历')) {
                detailItem = section;
                break;
            }
        }
        if (detailItem) {
            const container = detailItem.querySelector('.work-experience-content');
            const existingItem = container ? container.querySelector('.work-experience-item') : null;
            if (existingItem) {
                existingItem.remove();
            }
            const tableHtml = `
                <table class="experience-table">
                    <thead>
                        <tr>
                            <th>序号</th>
                            <th>公司名称</th>
                            <th>岗位</th>
                            <th>开始年份</th>
                            <th>结束年份</th>
                            <th>操作</th>
                        </tr>
                    </thead>
                    <tbody id="allWorkExperienceTable">
                    </tbody>
                </table>
            `;
            detailItem.insertAdjacentHTML('beforeend', tableHtml);
        }
    }
    
    const tbody = document.getElementById('allWorkExperienceTable');
    if (!tbody) return;
    
    // 获取当前行数
    const currentRows = tbody.querySelectorAll('tr');
    const newIndex = currentRows.length;
    
    // 创建新行
    const newRow = document.createElement('tr');
    newRow.setAttribute('data-row-index', newIndex);
    newRow.innerHTML = `
        <td>${newIndex + 1}</td>
        <td><input type="text" class="exp-company-input" data-index="${newIndex}" value="" placeholder="公司名称"></td>
        <td><input type="text" class="exp-position-input" data-index="${newIndex}" value="" placeholder="岗位名称"></td>
        <td><input type="number" class="exp-start-input" data-index="${newIndex}" value="" placeholder="开始年份"></td>
        <td><input type="number" class="exp-end-input" data-index="${newIndex}" value="" placeholder="结束年份（空为至今）"></td>
        <td><button class="btn btn-danger" onclick="removeWorkExperience(${newIndex})" style="padding: 3px 10px; font-size: 12px;">删除</button></td>
    `;
    
    tbody.appendChild(newRow);
    
    // 更新所有行的序号和data-index
    updateWorkExperienceIndices();
    
    // 重新设置事件监听
    setupWorkExperienceEditListeners();
}

// 删除工作经历
function removeWorkExperience(index) {
    const table = document.getElementById('allWorkExperienceTable');
    if (!table) return;
    
    const rows = table.querySelectorAll('tr');
    const rowToRemove = Array.from(rows).find(row => {
        const rowIndex = row.getAttribute('data-row-index');
        return rowIndex && parseInt(rowIndex) === index;
    });
    
    if (rowToRemove) {
        rowToRemove.remove();
        // 更新所有行的序号和data-index
        updateWorkExperienceIndices();
        // 同步到最新工作经历
        syncToLatestWorkExperience();
    }
}

// 更新工作经历表格的序号和索引
function updateWorkExperienceIndices() {
    const table = document.getElementById('allWorkExperienceTable');
    if (!table) return;
    
    const rows = table.querySelectorAll('tr');
    rows.forEach((row, idx) => {
        // 更新序号
        const firstCell = row.querySelector('td:first-child');
        if (firstCell) {
            firstCell.textContent = idx + 1;
        }
        
        // 更新data-index和data-row-index
        row.setAttribute('data-row-index', idx);
        const inputs = row.querySelectorAll('input[data-index]');
        inputs.forEach(input => {
            input.setAttribute('data-index', idx);
        });
        
        // 更新删除按钮的onclick
        const deleteBtn = row.querySelector('button.btn-danger');
        if (deleteBtn) {
            deleteBtn.setAttribute('onclick', `removeWorkExperience(${idx})`);
        }
    });
}

// 设置工作经历编辑监听器
function setupWorkExperienceEditListeners() {
    // 移除之前的事件监听器（如果存在）
    const table = document.getElementById('allWorkExperienceTable');
    if (!table) return;
    
    // 使用事件委托监听所有输入框的变化
    table.addEventListener('input', function(e) {
        if (e.target.classList.contains('exp-company-input') || 
            e.target.classList.contains('exp-position-input') || 
            e.target.classList.contains('exp-start-input') || 
            e.target.classList.contains('exp-end-input')) {
            syncToLatestWorkExperience();
        }
    });
}

// 同步全部工作经历到最新工作经历
function syncToLatestWorkExperience() {
    const table = document.getElementById('allWorkExperienceTable');
    if (!table) return;
    
    const rows = table.querySelectorAll('tr');
    const allExperiences = [];
    
    rows.forEach((row, idx) => {
        const companyInput = row.querySelector('.exp-company-input');
        const positionInput = row.querySelector('.exp-position-input');
        const startInput = row.querySelector('.exp-start-input');
        const endInput = row.querySelector('.exp-end-input');
        
        if (companyInput || positionInput || startInput || endInput) {
            const company = companyInput ? companyInput.value.trim() : '';
            const position = positionInput ? positionInput.value.trim() : '';
            const startYear = startInput && startInput.value ? parseInt(startInput.value, 10) : null;
            const endYear = endInput && endInput.value ? parseInt(endInput.value, 10) : null;
            
            // 如果有任何值，就添加到数组中
            if (company || position || startYear !== null || endYear !== null) {
                allExperiences.push({
                    company: company || null,
                    position: position || null,
                    start_year: startYear,
                    end_year: endYear
                });
            }
        }
    });
    
    // 对工作经历按开始时间由近到远排序（降序）
    allExperiences.sort((a, b) => {
        const yearA = a.start_year || 0;
        const yearB = b.start_year || 0;
        return yearB - yearA; // 降序，最新的在前
    });
    
    // 更新最新工作经历（仅显示前2段）
    // 查找"最新工作经历"的容器
    const workExpSections = document.querySelectorAll('.work-experience-section');
    let latestExpContainer = null;
    for (const section of workExpSections) {
        const title = section.querySelector('.work-experience-title');
        if (title && title.textContent.includes('最新工作经历')) {
            latestExpContainer = section;
            break;
        }
    }
    
    if (latestExpContainer) {
        // 只取前2段工作经历
        const latestExperiences = allExperiences.slice(0, 2);
        // 确保有2段（如果不足，用空数据填充）
        while (latestExperiences.length < 2) {
            latestExperiences.push({ company: '', position: '', start_year: '', end_year: '' });
        }
        
        // 更新显示
        const contentContainer = latestExpContainer.querySelector('.work-experience-content');
        if (contentContainer) {
            contentContainer.innerHTML = latestExperiences.map((exp, idx) => `
                <div class="work-experience-item">
                    <div class="work-exp-field">
                        <div class="work-exp-label">公司名称</div>
                        <input type="text" id="expCompany${idx}" value="${escapeHtml(exp.company || '')}" readonly>
                    </div>
                    <div class="work-exp-field">
                        <div class="work-exp-label">岗位</div>
                        <input type="text" id="expPosition${idx}" value="${escapeHtml(exp.position || '')}" readonly>
                    </div>
                    <div class="work-exp-field">
                        <div class="work-exp-label">开始年份</div>
                        <input type="number" id="expStart${idx}" value="${exp.start_year || ''}" readonly>
                    </div>
                    <div class="work-exp-field">
                        <div class="work-exp-label">结束年份</div>
                        <input type="number" id="expEnd${idx}" value="${exp.end_year || ''}" readonly>
                    </div>
                </div>
            `).join('');
        }
    }
}

function closeModal() {
    document.getElementById('detailModal').style.display = 'none';
    currentResumeData = null;
    const content = document.getElementById('detailContent');
    if (content) {
        content.innerHTML = '';
    }
}

function parseIntegerInput(id) {
    const el = document.getElementById(id);
    if (!el) return null;
    const value = el.value.trim();
    if (!value) return null;
    const num = parseInt(value, 10);
    return Number.isNaN(num) ? null : num;
}

function saveResume() {
    if (!currentResumeData) {
        return;
    }
    const payload = {
        name: document.getElementById('editName').value.trim() || null,
        gender: document.getElementById('editGender').value || null,
        birth_year: parseIntegerInput('editBirthYear'),
        earliest_work_year: parseIntegerInput('editEarliestWorkYear'),
        phone: document.getElementById('editPhone').value.trim() || null,
        email: document.getElementById('editEmail').value.trim() || null,
        applied_position: document.getElementById('editAppliedPosition').value.trim() || null,
        highest_education: document.getElementById('editEducation').value || null,
        school: document.getElementById('editSchool').value.trim() || null,
        major: document.getElementById('editMajor').value.trim() || null,
        error_message: document.getElementById('editErrorMessage').value.trim() || null,
    };

    // 从全部工作经历表格中读取数据
    const table = document.getElementById('allWorkExperienceTable');
    const updatedExperiences = [];
    
    if (table) {
        const rows = table.querySelectorAll('tr');
        rows.forEach((row) => {
            const companyInput = row.querySelector('.exp-company-input');
            const positionInput = row.querySelector('.exp-position-input');
            const startInput = row.querySelector('.exp-start-input');
            const endInput = row.querySelector('.exp-end-input');
            
            if (companyInput || positionInput || startInput || endInput) {
                const company = companyInput ? companyInput.value.trim() : '';
                const position = positionInput ? positionInput.value.trim() : '';
                const startYear = startInput && startInput.value ? parseInt(startInput.value, 10) : null;
                const endYear = endInput && endInput.value ? parseInt(endInput.value, 10) : null;
                
                // 如果有任何值，就添加到数组中
                if (company || position || startYear !== null || endYear !== null) {
                    updatedExperiences.push({
                        company: company || null,
                        position: position || null,
                        start_year: startYear,
                        end_year: endYear
                    });
                }
            }
        });
        
        // 对工作经历按开始时间由近到远排序（降序）
        updatedExperiences.sort((a, b) => {
            const yearA = a.start_year || 0;
            const yearB = b.start_year || 0;
            return yearB - yearA; // 降序，最新的在前
        });
    } else {
        // 如果表格不存在，回退到原来的逻辑（从最新工作经历读取）
        // 动态读取所有工作经历输入框（不再限制为2段）
        let i = 0;
        while (true) {
            const companyInput = document.getElementById(`expCompany${i}`);
            const positionInput = document.getElementById(`expPosition${i}`);
            const startInput = document.getElementById(`expStart${i}`);
            const endInput = document.getElementById(`expEnd${i}`);
            
            // 如果所有输入框都不存在，说明已经读取完所有工作经历
            if (!companyInput && !positionInput && !startInput && !endInput) {
                break;
            }
            
            const company = companyInput ? companyInput.value.trim() : '';
            const position = positionInput ? positionInput.value.trim() : '';
            const startYear = startInput && startInput.value ? parseInt(startInput.value, 10) : null;
            const endYear = endInput && endInput.value ? parseInt(endInput.value, 10) : null;

            const hasValue = company || position || startYear !== null || endYear !== null;

            if (hasValue) {
                updatedExperiences.push({
                    company: company || null,
                    position: position || null,
                    start_year: startYear,
                    end_year: endYear
                });
            }
            i++; // 继续读取下一段工作经历
        }
    }

    payload.work_experience = updatedExperiences;

    fetch(`/api/resumes/${currentResumeData.id}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    })
        .then(response => response.json().then(data => ({ ok: response.ok, data })))
        .then(({ ok, data }) => {
            if (ok && data.success) {
                alert('保存成功');
                closeModal();
                loadResumes(currentPage);
            } else {
                alert(`保存失败：${data.message || '未知错误'}`);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('保存失败，请稍后再试');
        });
}

function deleteResume(id) {
    if (!confirm('确定要删除该简历吗？此操作不可撤销。')) {
        return;
    }
    fetch(`/api/resumes/${id}`, {
        method: 'DELETE'
    })
        .then(response => response.json().then(data => ({ ok: response.ok, data })))
        .then(({ ok, data }) => {
            if (ok && data.success) {
                selectedResumes.delete(id);
                if (currentResumeData && currentResumeData.id === id) {
                    closeModal();
                }
                alert('删除成功');
                loadResumes(currentPage);
            } else {
                alert(`删除失败：${data.message || '未知错误'}`);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('删除失败，请稍后再试');
        });
}

// 导出功能
// 预览简历文件
function previewResumeFile(resumeId) {
    // 获取简历信息以确定文件类型
    fetch(`/api/resumes/${resumeId}`)
        .then(response => response.json())
        .then(result => {
            if (!result.success || !result.data) {
                alert('获取简历信息失败');
                return;
            }
            const resume = result.data;
            const fileName = resume.file_name || '';
            const fileExt = fileName.split('.').pop()?.toLowerCase() || '';
            
            const previewModal = document.getElementById('resumePreviewModal');
            const previewContent = document.getElementById('resumePreviewContent');
            
            if (fileExt === 'pdf') {
                // PDF文件：使用iframe预览（不触发下载）
                previewContent.innerHTML = `<iframe src="/api/resumes/${resumeId}/download?download=false" style="width: 100%; height: 100%; border: none;"></iframe>`;
            } else if (fileExt === 'doc' || fileExt === 'docx') {
                // Word文件：提示下载后查看
                previewContent.innerHTML = `
                    <div style="text-align: center; padding: 40px;">
                        <p style="font-size: 16px; margin-bottom: 20px;">Word文档无法在浏览器中直接预览</p>
                        <p style="color: #666; margin-bottom: 30px;">请点击下方按钮下载后查看</p>
                        <button class="btn btn-primary" onclick="downloadResumeFile(${resumeId})">下载文件</button>
                    </div>
                `;
            } else {
                previewContent.innerHTML = `
                    <div style="text-align: center; padding: 40px;">
                        <p style="font-size: 16px; color: #666;">不支持预览此文件类型</p>
                        <button class="btn btn-primary" onclick="downloadResumeFile(${resumeId})" style="margin-top: 20px;">下载文件</button>
                    </div>
                `;
            }
            
            previewModal.style.display = 'block';
        })
        .catch(error => {
            console.error('获取简历信息失败:', error);
            alert('获取简历信息失败，请稍后再试');
        });
}

// 关闭简历预览模态框
function closeResumePreviewModal() {
    const previewModal = document.getElementById('resumePreviewModal');
    if (previewModal) {
        previewModal.style.display = 'none';
        // 清空预览内容
        const previewContent = document.getElementById('resumePreviewContent');
        if (previewContent) {
            previewContent.innerHTML = '';
        }
    }
}

// 下载简历原始文件
function downloadResumeFile(resumeId) {
    window.location.href = `/api/resumes/${resumeId}/download?download=true`;
}

function exportSingle(id) {
    window.location.href = `/api/export/${id}`;
}

function deleteSelected() {
    if (selectedResumes.size === 0) {
        alert('请先选择要删除的简历');
        return;
    }
    if (!confirm(`确定要删除选中的 ${selectedResumes.size} 条简历吗？此操作不可撤销。`)) {
        return;
    }
    fetch('/api/resumes/batch_delete', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            resume_ids: Array.from(selectedResumes)
        })
    })
        .then(response => response.json().then(data => ({ ok: response.ok, data })))
        .then(({ ok, data }) => {
            if (ok && data.success) {
                alert('批量删除成功');
                selectedResumes.clear();
                loadResumes(currentPage);
            } else {
                alert(`批量删除失败：${data.message || '未知错误'}`);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('批量删除失败，请稍后再试');
        });
}

function exportSelected() {
    if (selectedResumes.size === 0) {
        alert('请先选择要导出的简历');
        return;
    }
    
    fetch('/api/export/batch', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            resume_ids: Array.from(selectedResumes)
        })
    })
    .then(response => {
        if (response.ok) {
            return response.blob();
        }
        throw new Error('导出失败');
    })
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `简历批量导出_${new Date().toISOString().split('T')[0]}.xlsx`;
        a.click();
        window.URL.revokeObjectURL(url);
    })
    .catch(error => {
        console.error('Error:', error);
        alert('导出失败，请重试');
    });
}

function exportAll() {
    if (confirm('确定要导出所有简历吗？')) {
        // 获取所有简历ID
        fetch(`/api/resumes?per_page=1000`)
            .then(response => response.json())
            .then(data => {
                if (data.success && data.data.length > 0) {
                    const ids = data.data.map(r => r.id);
                    fetch('/api/export/batch', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            resume_ids: ids
                        })
                    })
                    .then(response => {
                        if (response.ok) {
                            return response.blob();
                        }
                        throw new Error('导出失败');
                    })
                    .then(blob => {
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = `简历全部导出_${new Date().toISOString().split('T')[0]}.xlsx`;
                        a.click();
                        window.URL.revokeObjectURL(url);
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        alert('导出失败，请重试');
                    });
                } else {
                    alert('没有可导出的简历');
                }
            });
    }
}

// =======================
// 面试流程相关功能
// =======================

// 从简历（列表或分析）发起邀约面试
function inviteInterview(resumeId) {
    if (!resumeId) return;
    if (!confirm('确认将该候选人加入"面试流程"吗？')) {
        return;
    }
    // 尝试从匹配度缓存中获取当前岗位的匹配结果
    let match_score = null;
    let match_level = null;
    
    // 从简历分析模块的缓存中获取匹配度结果
    if (typeof matchAnalysisCache !== 'undefined') {
        // 获取当前选择的岗位
        const positionSelect = document.getElementById('analysisPositionSelect');
        const appliedPosition = positionSelect ? positionSelect.value : '';
        if (appliedPosition) {
            const cacheKey = `${resumeId}_${appliedPosition}`;
            const cachedResult = matchAnalysisCache[cacheKey];
            if (cachedResult) {
                match_score = cachedResult.match_score;
                match_level = cachedResult.match_level;
            }
        }
    }

    fetch('/api/interviews', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ resume_id: resumeId, match_score, match_level })
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            alert('已加入面试流程');
            interviewedResumeIds.add(resumeId);
            // 触发当前模块的刷新，以更新按钮状态
            const urlParams = new URLSearchParams(window.location.search);
            const module = urlParams.get('module') || 'upload';
            if (module === 'upload') {
                loadResumes(currentPage);
            } else if (module === 'analysis') {
                loadResumesForAnalysis();
            } else if (module === 'interview') {
                loadInterviews();
            }
            const moduleInterview = document.getElementById('module-interview');
            if (moduleInterview && moduleInterview.classList.contains('active')) {
                loadInterviews();
            }
        } else {
            alert(`操作失败：${result.message || '未知错误'}`);
        }
    })
    .catch(error => {
        console.error('邀约面试失败:', error);
        alert('操作失败，请稍后再试');
    });
}

// 加载面试流程列表
function loadInterviews() {
    const tbody = document.getElementById('interviewTableBody');
    if (!tbody) return;

    tbody.innerHTML = '<tr><td colspan="9" class="loading">加载中...</td></tr>';

    const searchInput = document.getElementById('interviewSearchInput');
    const search = searchInput ? (searchInput.value || '').trim() : '';
    const params = new URLSearchParams();
    if (search) {
        params.append('search', search);
    }

    fetch(`/api/interviews?${params.toString()}`)
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                const list = result.data || [];
                if (list.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="9" class="loading">暂无面试记录</td></tr>';
                    return;
                }
                tbody.innerHTML = list.map(item => {
                    const isSelected = selectedInterviews.has(item.id);
                    const identityCode = escapeHtml(item.identity_code || '-');
                    const name = escapeHtml(item.name || '-');
                    const position = escapeHtml(item.applied_position || '-');
                    const status = escapeHtml(item.status || '待面试');
                    const time = item.update_time ? escapeHtml(item.update_time.replace('T', ' ').slice(0, 19)) : '-';
                    const score = item.match_score !== null && item.match_score !== undefined ? item.match_score : null;
                    const level = escapeHtml(item.match_level || '');
                    const color = getScoreColor(score);
                    const scoreHtml = score !== null
                        ? `<span class="match-score-dot" style="background:${color};"></span><span>${score}${level ? ' 分（' + level + '）' : ''}</span>`
                        : '<span>-</span>';
                    const hasRegistrationForm = item.registration_form_fill_date ? '已填写' : '未填写';
                    const registrationFormStatus = item.registration_form_fill_date 
                        ? `<span style="color: #28a745;">已填写</span>` 
                        : `<span style="color: #999;">未填写</span>`;
                    return `
                        <tr>
                            <td><input type="checkbox" value="${item.id}" ${isSelected ? 'checked' : ''} onchange="toggleInterview(${item.id}, this)"></td>
                            <td>${identityCode}</td>
                            <td>${name}</td>
                            <td>${position}</td>
                            <td>${scoreHtml}</td>
                            <td>${status}</td>
                            <td>${time}</td>
                            <td><button class="btn btn-small btn-primary" onclick="openRegistrationFormModal(${item.id})">${hasRegistrationForm}</button></td>
                            <td><button class="btn btn-small btn-primary" onclick="openInterviewModal(${item.id})">填写/查看</button></td>
                        </tr>
                    `;
                }).join('');
            } else {
                tbody.innerHTML = `<tr><td colspan="9" class="loading">加载失败：${escapeHtml(result.message || '未知错误')}</td></tr>`;
            }
        })
        .catch(error => {
            console.error('加载面试流程失败:', error);
            tbody.innerHTML = '<tr><td colspan="9" class="loading">加载失败，请稍后重试</td></tr>';
        });
}

// 面试流程选择/导出相关
function toggleInterview(id, checkbox) {
    if (checkbox.checked) {
        selectedInterviews.add(id);
    } else {
        selectedInterviews.delete(id);
    }
}

function toggleSelectAllInterviews() {
    const selectAll = document.getElementById('selectAllInterviews');
    const tbody = document.getElementById('interviewTableBody');
    if (!tbody || !selectAll) return;
    const checkboxes = tbody.querySelectorAll('input[type="checkbox"]');
    checkboxes.forEach(cb => {
        cb.checked = selectAll.checked;
        const id = parseInt(cb.value, 10);
        if (selectAll.checked) {
            selectedInterviews.add(id);
        } else {
            selectedInterviews.delete(id);
        }
    });
}

function deleteSelectedInterviews() {
    if (selectedInterviews.size === 0) {
        alert('请先选择要删除的面试记录');
        return;
    }
    if (!confirm(`确定要删除选中的 ${selectedInterviews.size} 条面试记录吗？此操作不可撤销。`)) {
        return;
    }
    fetch('/api/interviews/batch_delete', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            interview_ids: Array.from(selectedInterviews)
        })
    })
    .then(response => response.json().then(data => ({ ok: response.ok, data })))
    .then(({ ok, data }) => {
        if (ok && data.success) {
            alert('批量删除成功');
            selectedInterviews.clear();
            loadInterviews();
        } else {
            alert(`批量删除失败：${data.message || '未知错误'}`);
        }
    })
    .catch(error => {
        console.error('批量删除面试流程失败:', error);
        alert('批量删除失败，请稍后再试');
    });
}

function exportSelectedInterviews() {
    if (selectedInterviews.size === 0) {
        alert('请先选择要导出的面试记录');
        return;
    }
    exportInterviews(Array.from(selectedInterviews));
}

function exportAllInterviews() {
    exportInterviews([]);
}

function exportInterviews(ids) {
    fetch('/api/interviews/export', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ interview_ids: ids })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.message || `导出失败，状态码: ${response.status}`);
            }).catch(() => {
                throw new Error(`导出失败，状态码: ${response.status}`);
            });
        }
        return response.blob();
    })
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `面试流程导出_${new Date().toISOString().split('T')[0]}.xlsx`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
    })
    .catch(error => {
        console.error('导出面试流程失败:', error);
        alert(`导出失败：${error.message || '未知错误'}`);
    });
}

// 下载简历分析PDF报告（简历分析详情页）
function downloadAnalysisPdf(resumeId) {
    fetch(`/api/resumes/${resumeId}/analysis-pdf`, {
        method: 'POST'
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.message || `导出失败，状态码: ${response.status}`);
            }).catch(() => {
                throw new Error(`导出失败，状态码: ${response.status}`);
            });
        }
        return response.blob();
    })
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `简历分析报告_${resumeId}.pdf`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
    })
    .catch(error => {
        console.error('下载简历分析PDF失败:', error);
        alert(`下载失败：${error.message || '未知错误'}`);
    });
}

// 下载单轮面试AI分析PDF
function downloadInterviewAnalysisPdf(interviewId, round) {
    const textarea = document.getElementById(`round${round}_ai_result`);
    const analysisText = textarea ? textarea.value : '';

    fetch(`/api/interviews/${interviewId}/analysis-pdf`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ round, analysis_text: analysisText })
    })
    .then(response => {
        if (!response.ok) {
            return response.json().then(data => {
                throw new Error(data.message || `导出失败，状态码: ${response.status}`);
            }).catch(() => {
                throw new Error(`导出失败，状态码: ${response.status}`);
            });
        }
        return response.blob();
    })
    .then(blob => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        const roundName = round === 1 ? '一面' : round === 2 ? '二面' : '三面';
        a.href = url;
        a.download = `${roundName}面试反馈报告_${interviewId}.pdf`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
    })
    .catch(error => {
        console.error('下载面试AI分析PDF失败:', error);
        alert(`下载失败：${error.message || '未知错误'}`);
    });
}

// 加载岗位列表用于数据统计筛选
function loadPositionsForStats() {
    const select = document.getElementById('statsPosition');
    if (!select) return;

    // 如果已经加载过选项，则不重复加载
    if (select.dataset.loaded === '1') return;

    fetch('/api/positions')
        .then(response => response.json())
        .then(result => {
            if (!result.success) {
                console.error('加载岗位失败:', result.message);
                return;
            }
            const positions = result.data || [];
            positions.forEach(p => {
                const opt = document.createElement('option');
                opt.value = p.position_name;
                opt.textContent = p.position_name;
                select.appendChild(opt);
            });
            select.dataset.loaded = '1';
        })
        .catch(err => {
            console.error('加载岗位失败:', err);
        });
}

// 加载数据统计
function loadStatistics() {
    const startInput = document.getElementById('statsStartDate');
    const endInput = document.getElementById('statsEndDate');
    const positionSelect = document.getElementById('statsPosition');
    const statsContent = document.getElementById('statsContent');

    if (!statsContent) return;

    const params = new URLSearchParams();
    if (startInput && startInput.value) params.append('start_date', startInput.value);
    if (endInput && endInput.value) params.append('end_date', endInput.value);
    if (positionSelect && positionSelect.value) params.append('position', positionSelect.value);

    fetch(`/api/statistics?${params.toString()}`)
        .then(response => response.json())
        .then(result => {
            if (!result.success) {
                alert(result.message || '统计失败，请稍后再试');
                return;
            }
            const data = result.data || {};
            
            // 如果选择了岗位，只显示该岗位的数据
            if (data.position) {
                const resumeCount = data.resume_count || 0;
                const interviewCount = data.interview_count || 0;
                const passCount = data.pass_count || 0;
                const offerCount = data.offer_count || 0;
                const onboardCount = data.onboard_count || 0;
                
                // 计算比例（以简历数为100%）
                const interviewRate = resumeCount > 0 ? ((interviewCount / resumeCount) * 100).toFixed(1) : '0.0';
                const passRate = resumeCount > 0 ? ((passCount / resumeCount) * 100).toFixed(1) : '0.0';
                const offerRate = resumeCount > 0 ? ((offerCount / resumeCount) * 100).toFixed(1) : '0.0';
                const onboardRate = resumeCount > 0 ? ((onboardCount / resumeCount) * 100).toFixed(1) : '0.0';
                
                statsContent.innerHTML = `
                    <div class="stats-position-group">
                        <div class="stats-position-title-wrapper">
                            <h3 class="stats-position-title">${escapeHtml(data.position)}</h3>
                            <button class="btn btn-sm btn-funnel" onclick="showFunnelModal('${escapeHtml(data.position)}', {resume_count: ${resumeCount}, interview_count: ${interviewCount}, pass_count: ${passCount}, offer_count: ${offerCount}, onboard_count: ${onboardCount}})">数据漏斗</button>
                        </div>
                        <div class="stats-cards">
                            <div class="stats-card">
                                <div class="stats-card-header">
                                    <div class="stats-card-title">简历数</div>
                                    <div class="stats-card-value">${data.resume_count ?? '-'}</div>
                                </div>
                                <div class="stats-card-desc">按简历上传时间统计</div>
                            </div>
                            <div class="stats-card">
                                <div class="stats-card-header">
                                    <div class="stats-card-title">到面数</div>
                                    <div class="stats-card-value">${data.interview_count ?? '-'}</div>
                                </div>
                                <div class="stats-card-desc">按一面时间统计（有一面时间视为到面）</div>
                            </div>
                            <div class="stats-card">
                                <div class="stats-card-header">
                                    <div class="stats-card-title">通过数</div>
                                    <div class="stats-card-value">${data.pass_count ?? '-'}</div>
                                </div>
                                <div class="stats-card-desc">按状态为通过/已发offer/已入职统计</div>
                            </div>
                            <div class="stats-card">
                                <div class="stats-card-header">
                                    <div class="stats-card-title">Offer数</div>
                                    <div class="stats-card-value">${data.offer_count ?? '-'}</div>
                                </div>
                                <div class="stats-card-desc">按Offer发放日期统计</div>
                            </div>
                            <div class="stats-card">
                                <div class="stats-card-header">
                                    <div class="stats-card-title">入职数</div>
                                    <div class="stats-card-value">${data.onboard_count ?? '-'}</div>
                                </div>
                                <div class="stats-card-desc">按实际入职日期统计</div>
                            </div>
                        </div>
                    </div>
                `;
            } else if (data.by_position && data.by_position.length > 0) {
                // 按岗位分组显示
                let html = '';
                data.by_position.forEach((posData, index) => {
                    const resumeCount = posData.resume_count || 0;
                    const interviewCount = posData.interview_count || 0;
                    const passCount = posData.pass_count || 0;
                    const offerCount = posData.offer_count || 0;
                    const onboardCount = posData.onboard_count || 0;
                    
                    // 计算比例（以简历数为100%）
                    const interviewRate = resumeCount > 0 ? ((interviewCount / resumeCount) * 100).toFixed(1) : '0.0';
                    const passRate = resumeCount > 0 ? ((passCount / resumeCount) * 100).toFixed(1) : '0.0';
                    const offerRate = resumeCount > 0 ? ((offerCount / resumeCount) * 100).toFixed(1) : '0.0';
                    const onboardRate = resumeCount > 0 ? ((onboardCount / resumeCount) * 100).toFixed(1) : '0.0';
                    
                    html += `
                        <div class="stats-position-group">
                            <div class="stats-position-title-wrapper">
                                <h3 class="stats-position-title">${escapeHtml(posData.position)}</h3>
                                <button class="btn btn-sm btn-funnel" onclick="showFunnelModal('${escapeHtml(posData.position)}', {resume_count: ${resumeCount}, interview_count: ${interviewCount}, pass_count: ${passCount}, offer_count: ${offerCount}, onboard_count: ${onboardCount}})">数据漏斗</button>
                            </div>
                            <div class="stats-cards">
                                <div class="stats-card">
                                    <div class="stats-card-header">
                                        <div class="stats-card-title">简历数</div>
                                        <div class="stats-card-value">${posData.resume_count ?? '-'}</div>
                                    </div>
                                    <div class="stats-card-desc">按简历上传时间统计</div>
                                </div>
                                <div class="stats-card">
                                    <div class="stats-card-header">
                                        <div class="stats-card-title">到面数</div>
                                        <div class="stats-card-value">${posData.interview_count ?? '-'}</div>
                                    </div>
                                    <div class="stats-card-desc">按一面时间统计（有一面时间视为到面）</div>
                                </div>
                                <div class="stats-card">
                                    <div class="stats-card-header">
                                        <div class="stats-card-title">通过数</div>
                                        <div class="stats-card-value">${posData.pass_count ?? '-'}</div>
                                    </div>
                                    <div class="stats-card-desc">按状态为通过/已发offer/已入职统计</div>
                                </div>
                                <div class="stats-card">
                                    <div class="stats-card-header">
                                        <div class="stats-card-title">Offer数</div>
                                        <div class="stats-card-value">${posData.offer_count ?? '-'}</div>
                                    </div>
                                    <div class="stats-card-desc">按Offer发放日期统计</div>
                                </div>
                                <div class="stats-card">
                                    <div class="stats-card-header">
                                        <div class="stats-card-title">入职数</div>
                                        <div class="stats-card-value">${posData.onboard_count ?? '-'}</div>
                                    </div>
                                    <div class="stats-card-desc">按实际入职日期统计</div>
                                </div>
                            </div>
                        </div>
                    `;
                });
                
                // 如果有总计数据，也显示总计
                if (data.total) {
                    const totalResumeCount = data.total.resume_count || 0;
                    const totalInterviewCount = data.total.interview_count || 0;
                    const totalPassCount = data.total.pass_count || 0;
                    const totalOfferCount = data.total.offer_count || 0;
                    const totalOnboardCount = data.total.onboard_count || 0;
                    
                    // 计算比例（以简历数为100%）
                    const totalInterviewRate = totalResumeCount > 0 ? ((totalInterviewCount / totalResumeCount) * 100).toFixed(1) : '0.0';
                    const totalPassRate = totalResumeCount > 0 ? ((totalPassCount / totalResumeCount) * 100).toFixed(1) : '0.0';
                    const totalOfferRate = totalResumeCount > 0 ? ((totalOfferCount / totalResumeCount) * 100).toFixed(1) : '0.0';
                    const totalOnboardRate = totalResumeCount > 0 ? ((totalOnboardCount / totalResumeCount) * 100).toFixed(1) : '0.0';
                    
                    html += `
                        <div class="stats-position-group" style="margin-top: 30px; padding-top: 30px; border-top: 2px solid #667eea;">
                            <div class="stats-position-title-wrapper">
                                <h3 class="stats-position-title">总计</h3>
                                <button class="btn btn-sm btn-funnel" onclick="showFunnelModal('总计', {resume_count: ${totalResumeCount}, interview_count: ${totalInterviewCount}, pass_count: ${totalPassCount}, offer_count: ${totalOfferCount}, onboard_count: ${totalOnboardCount}})">数据漏斗</button>
                            </div>
                            <div class="stats-cards">
                                <div class="stats-card">
                                    <div class="stats-card-header">
                                        <div class="stats-card-title">简历数</div>
                                        <div class="stats-card-value">${data.total.resume_count ?? '-'}</div>
                                    </div>
                                    <div class="stats-card-desc">按简历上传时间统计</div>
                                </div>
                                <div class="stats-card">
                                    <div class="stats-card-header">
                                        <div class="stats-card-title">到面数</div>
                                        <div class="stats-card-value">${data.total.interview_count ?? '-'}</div>
                                    </div>
                                    <div class="stats-card-desc">按一面时间统计（有一面时间视为到面）</div>
                                </div>
                                <div class="stats-card">
                                    <div class="stats-card-header">
                                        <div class="stats-card-title">通过数</div>
                                        <div class="stats-card-value">${data.total.pass_count ?? '-'}</div>
                                    </div>
                                    <div class="stats-card-desc">按状态为通过/已发offer/已入职统计</div>
                                </div>
                                <div class="stats-card">
                                    <div class="stats-card-header">
                                        <div class="stats-card-title">Offer数</div>
                                        <div class="stats-card-value">${data.total.offer_count ?? '-'}</div>
                                    </div>
                                    <div class="stats-card-desc">按Offer发放日期统计</div>
                                </div>
                                <div class="stats-card">
                                    <div class="stats-card-header">
                                        <div class="stats-card-title">入职数</div>
                                        <div class="stats-card-value">${data.total.onboard_count ?? '-'}</div>
                                    </div>
                                    <div class="stats-card-desc">按实际入职日期统计</div>
                                </div>
                            </div>
                        </div>
                    `;
                }
                
                statsContent.innerHTML = html;
            } else {
                statsContent.innerHTML = '<div style="text-align: center; padding: 40px; color: #999;">暂无统计数据</div>';
            }
        })
        .catch(err => {
            console.error('加载统计数据失败:', err);
            alert('统计失败，请稍后再试');
        });
}

// 显示数据漏斗模态框
function showFunnelModal(positionName, data) {
    const resumeCount = data.resume_count || 0;
    const interviewCount = data.interview_count || 0;
    const passCount = data.pass_count || 0;
    const offerCount = data.offer_count || 0;
    const onboardCount = data.onboard_count || 0;
    
    // 计算比例（以简历数为100%）
    const interviewRate = resumeCount > 0 ? ((interviewCount / resumeCount) * 100).toFixed(1) : '0.0';
    const passRate = resumeCount > 0 ? ((passCount / resumeCount) * 100).toFixed(1) : '0.0';
    const offerRate = resumeCount > 0 ? ((offerCount / resumeCount) * 100).toFixed(1) : '0.0';
    const onboardRate = resumeCount > 0 ? ((onboardCount / resumeCount) * 100).toFixed(1) : '0.0';
    
    const modal = document.getElementById('funnelModal');
    const modalBody = document.getElementById('funnelModalBody');
    if (!modal || !modalBody) return;
    
    modalBody.innerHTML = `
        <div class="funnel-modal-header">
            <h3>${escapeHtml(positionName)} - 数据漏斗</h3>
        </div>
        <div class="funnel-container">
            <div class="funnel-item">
                <div class="funnel-label">简历数</div>
                <div class="funnel-bar-wrapper">
                    <div class="funnel-bar" style="width: 100%; background: #667eea;">
                        <span class="funnel-value">${resumeCount}</span>
                        <span class="funnel-percent">100.0%</span>
                    </div>
                </div>
            </div>
            <div class="funnel-item">
                <div class="funnel-label">到面数</div>
                <div class="funnel-bar-wrapper">
                    <div class="funnel-bar" style="width: ${interviewRate}%; background: #48bb78;">
                        <span class="funnel-value">${interviewCount}</span>
                        <span class="funnel-percent">${interviewRate}%</span>
                    </div>
                </div>
            </div>
            <div class="funnel-item">
                <div class="funnel-label">通过数</div>
                <div class="funnel-bar-wrapper">
                    <div class="funnel-bar" style="width: ${passRate}%; background: #ed8936;">
                        <span class="funnel-value">${passCount}</span>
                        <span class="funnel-percent">${passRate}%</span>
                    </div>
                </div>
            </div>
            <div class="funnel-item">
                <div class="funnel-label">Offer数</div>
                <div class="funnel-bar-wrapper">
                    <div class="funnel-bar" style="width: ${offerRate}%; background: #9f7aea;">
                        <span class="funnel-value">${offerCount}</span>
                        <span class="funnel-percent">${offerRate}%</span>
                    </div>
                </div>
            </div>
            <div class="funnel-item">
                <div class="funnel-label">入职数</div>
                <div class="funnel-bar-wrapper">
                    <div class="funnel-bar" style="width: ${onboardRate}%; background: #38b2ac;">
                        <span class="funnel-value">${onboardCount}</span>
                        <span class="funnel-percent">${onboardRate}%</span>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    modal.style.display = 'block';
}

// 关闭数据漏斗模态框
function closeFunnelModal() {
    const modal = document.getElementById('funnelModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// 根据匹配分数返回颜色
function getScoreColor(score) {
    if (score === null || score === undefined) return '#ccc';
    if (score >= 80) return '#28a745'; // 绿
    if (score >= 60) return '#ffc107'; // 黄
    return '#dc3545'; // 红
}

// 打开面试详情模态框
function openInterviewModal(interviewId) {
    fetch(`/api/interviews/${interviewId}`)
        .then(response => response.json())
        .then(result => {
            if (!result.success) {
                alert(result.message || '加载失败');
                return;
            }
            const data = result.data;
            const modal = document.getElementById('interviewModal');
            const body = document.getElementById('interviewModalBody');
            if (!modal || !body) return;

            const round1Result = data.round1_result || '';
            const round2Result = data.round2_result || '';
            const round3Enabled = !!data.round3_enabled;
            
            // 检查是否已有token，如果有则显示链接
            const baseUrl = window.location.origin;
            const round1Link = data.round1_comment_token ? `${baseUrl}/interview-comment?token=${data.round1_comment_token}` : '';
            const round2Link = data.round2_comment_token ? `${baseUrl}/interview-comment?token=${data.round2_comment_token}` : '';
            const round3Link = data.round3_comment_token ? `${baseUrl}/interview-comment?token=${data.round3_comment_token}` : '';

            body.innerHTML = `
                <div class="form-grid">
                    <div class="detail-item">
                        <label>身份验证码：</label>
                        <span>${escapeHtml(data.identity_code || '-')}</span>
                    </div>
                    <div class="detail-item">
                        <label>候选人姓名：</label>
                        <span>${escapeHtml(data.name || '-')}</span>
                    </div>
                    <div class="detail-item">
                        <label>应聘岗位：</label>
                        <select id="interviewAppliedPosition" class="form-select">
                            <option value="">请选择岗位</option>
                        </select>
                    </div>
                    <div class="detail-item">
                        <label>当前状态：</label>
                        <span id="interviewStatusDisplay">${escapeHtml(data.status || '待面试')}</span>
                    </div>
                </div>
                
                <div class="section-header">
                    <h4>一面</h4>
                    <div>
                        <button class="btn btn-secondary" style="margin-right:8px;" onclick="downloadInterviewAnalysisPdf(${data.id}, 1)">下载面试反馈报告</button>
                        <button class="btn btn-primary" onclick="saveInterview(${data.id})">保存一面</button>
                    </div>
                </div>
                <div class="form-grid">
                    <div class="detail-item">
                        <label>一面面试官：</label>
                        <input type="text" id="round1_interviewer" class="form-input" value="${escapeHtml(data.round1_interviewer || '')}">
                    </div>
                    <div class="detail-item">
                        <label>一面时间：</label>
                        <input type="date" id="round1_time" class="form-input" placeholder="例如：2025-03-10" value="${escapeHtml((data.round1_time || '').slice(0,10))}">
                    </div>
                    <div class="detail-item">
                        <label>一面结果：</label>
                        <select id="round1_result" class="form-select" onchange="onRoundResultChange()">
                            <option value="">未填写</option>
                            <option value="通过" ${round1Result === '通过' ? 'selected' : ''}>通过</option>
                            <option value="未通过" ${round1Result === '未通过' ? 'selected' : ''}>未通过</option>
                        </select>
                    </div>
                </div>
                <div class="form-group">
                    <label>一面评价：</label>
                    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                        <textarea id="round1_comment" class="form-textarea" rows="3" placeholder="请输入一面评价" style="flex: 1;">${escapeHtml(data.round1_comment || '')}</textarea>
                        <button class="btn btn-secondary" onclick="generateCommentLink(${data.id}, 1)" title="生成邀请填写链接">邀请填写</button>
                    </div>
                    <div id="round1_link_display" style="display: ${round1Link ? 'block' : 'none'}; margin-top: 8px; padding: 8px; background: #f0f0f0; border-radius: 4px;">
                        <label style="font-weight: bold;">填写链接：</label>
                        <div style="display: flex; align-items: center; gap: 8px; margin-top: 4px;">
                            <input type="text" id="round1_link" value="${round1Link}" readonly style="flex: 1; padding: 6px; border: 1px solid #ddd; border-radius: 4px;">
                            <button class="btn btn-small" onclick="copyLink('round1_link')">复制</button>
                        </div>
                    </div>
                </div>
                <div class="form-group interview-doc-row">
                    <div class="interview-doc-left">
                        <label>一面文档（录音逐字稿等）：</label>
                        <input type="file" id="round1DocFile" accept=".pdf,.doc,.docx,.txt">
                        <button class="btn btn-secondary" onclick="uploadInterviewDoc(1)">上传</button>
                        <span id="round1DocLink" class="interview-doc-link">${data.round1_doc_path ? `当前文档：<a href="/static/${escapeHtml(data.round1_doc_path)}" target="_blank">查看</a>` : '当前暂无文档'}</span>
                    </div>
                    <div class="interview-doc-right">
                        <button class="btn btn-primary" onclick="analyzeInterviewDoc(${data.id}, 1)">AI分析</button>
                    </div>
                </div>
                <div class="form-group">
                    <label>一面AI分析结果：</label>
                    <textarea id="round1_ai_result" class="form-textarea" rows="4" placeholder="点击上方AI分析后将在此展示结果" readonly>${escapeHtml(data.round1_ai_result || '')}</textarea>
                </div>

                <div class="section-header">
                    <h4>二面</h4>
                    <div>
                        <button class="btn btn-secondary" style="margin-right:8px;" onclick="downloadInterviewAnalysisPdf(${data.id}, 2)">下载面试反馈报告</button>
                        <button class="btn btn-primary" onclick="saveInterview(${data.id})">保存二面</button>
                    </div>
                </div>
                <div class="form-grid">
                    <div class="detail-item">
                        <label>二面面试官：</label>
                        <input type="text" id="round2_interviewer" class="form-input" value="${escapeHtml(data.round2_interviewer || '')}">
                    </div>
                    <div class="detail-item">
                        <label>二面时间：</label>
                        <input type="date" id="round2_time" class="form-input" placeholder="例如：2025-03-12" value="${escapeHtml((data.round2_time || '').slice(0,10))}">
                    </div>
                    <div class="detail-item">
                        <label>二面结果：</label>
                        <select id="round2_result" class="form-select" onchange="onRoundResultChange()">
                            <option value="">未填写</option>
                            <option value="通过" ${round2Result === '通过' ? 'selected' : ''}>通过</option>
                            <option value="未通过" ${round2Result === '未通过' ? 'selected' : ''}>未通过</option>
                        </select>
                    </div>
                </div>
                <div class="form-group">
                    <label>二面评价：</label>
                    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                        <textarea id="round2_comment" class="form-textarea" rows="3" placeholder="请输入二面评价" style="flex: 1;">${escapeHtml(data.round2_comment || '')}</textarea>
                        <button class="btn btn-secondary" onclick="generateCommentLink(${data.id}, 2)" title="生成邀请填写链接">邀请填写</button>
                    </div>
                    <div id="round2_link_display" style="display: ${round2Link ? 'block' : 'none'}; margin-top: 8px; padding: 8px; background: #f0f0f0; border-radius: 4px;">
                        <label style="font-weight: bold;">填写链接：</label>
                        <div style="display: flex; align-items: center; gap: 8px; margin-top: 4px;">
                            <input type="text" id="round2_link" value="${round2Link}" readonly style="flex: 1; padding: 6px; border: 1px solid #ddd; border-radius: 4px;">
                            <button class="btn btn-small" onclick="copyLink('round2_link')">复制</button>
                        </div>
                    </div>
                </div>
                <div class="form-group interview-doc-row">
                    <div class="interview-doc-left">
                        <label>二面文档（录音逐字稿等）：</label>
                        <input type="file" id="round2DocFile" accept=".pdf,.doc,.docx,.txt">
                        <button class="btn btn-secondary" onclick="uploadInterviewDoc(2)">上传</button>
                        <span id="round2DocLink" class="interview-doc-link">${data.round2_doc_path ? `当前文档：<a href="/static/${escapeHtml(data.round2_doc_path)}" target="_blank">查看</a>` : '当前暂无文档'}</span>
                    </div>
                    <div class="interview-doc-right">
                        <button class="btn btn-primary" onclick="analyzeInterviewDoc(${data.id}, 2)">AI分析</button>
                    </div>
                </div>
                <div class="form-group">
                    <label>二面AI分析结果：</label>
                    <textarea id="round2_ai_result" class="form-textarea" rows="4" placeholder="点击上方AI分析后将在此展示结果" readonly>${escapeHtml(data.round2_ai_result || '')}</textarea>
                </div>

                <div class="section-header">
                    <h4>三面</h4>
                    <div>
                        <button class="btn btn-secondary" style="margin-right:8px;" onclick="downloadInterviewAnalysisPdf(${data.id}, 3)">下载面试反馈报告</button>
                        <button class="btn btn-primary" onclick="saveInterview(${data.id})">保存三面</button>
                    </div>
                </div>
                <div class="form-grid">
                    <div class="detail-item">
                        <label>
                            <input type="checkbox" id="round3_enabled" ${round3Enabled ? 'checked' : ''} onchange="onRoundResultChange()">
                            是否有三面
                        </label>
                    </div>
                    <div class="detail-item">
                        <label>三面面试官：</label>
                        <input type="text" id="round3_interviewer" class="form-input" value="${escapeHtml(data.round3_interviewer || '')}">
                    </div>
                    <div class="detail-item">
                        <label>三面时间：</label>
                        <input type="date" id="round3_time" class="form-input" placeholder="例如：2025-03-15" value="${escapeHtml((data.round3_time || '').slice(0,10))}">
                    </div>
                    <div class="detail-item">
                        <label>三面结果：</label>
                        <select id="round3_result" class="form-select" onchange="onRoundResultChange()">
                            <option value="">未填写</option>
                            <option value="通过" ${data.round3_result === '通过' ? 'selected' : ''}>通过</option>
                            <option value="未通过" ${data.round3_result === '未通过' ? 'selected' : ''}>未通过</option>
                        </select>
                    </div>
                </div>
                <div class="form-group">
                    <label>三面评价：</label>
                    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                        <textarea id="round3_comment" class="form-textarea" rows="3" placeholder="请输入三面评价" style="flex: 1;">${escapeHtml(data.round3_comment || '')}</textarea>
                        <button class="btn btn-secondary" onclick="generateCommentLink(${data.id}, 3)" title="生成邀请填写链接">邀请填写</button>
                    </div>
                    <div id="round3_link_display" style="display: ${round3Link ? 'block' : 'none'}; margin-top: 8px; padding: 8px; background: #f0f0f0; border-radius: 4px;">
                        <label style="font-weight: bold;">填写链接：</label>
                        <div style="display: flex; align-items: center; gap: 8px; margin-top: 4px;">
                            <input type="text" id="round3_link" value="${round3Link}" readonly style="flex: 1; padding: 6px; border: 1px solid #ddd; border-radius: 4px;">
                            <button class="btn btn-small" onclick="copyLink('round3_link')">复制</button>
                        </div>
                    </div>
                </div>
                <div class="form-group interview-doc-row">
                    <div class="interview-doc-left">
                        <label>三面文档（录音逐字稿等）：</label>
                        <input type="file" id="round3DocFile" accept=".pdf,.doc,.docx,.txt">
                        <button class="btn btn-secondary" onclick="uploadInterviewDoc(3)">上传</button>
                        <span id="round3DocLink" class="interview-doc-link">${data.round3_doc_path ? `当前文档：<a href="/static/${escapeHtml(data.round3_doc_path)}" target="_blank">查看</a>` : '当前暂无文档'}</span>
                    </div>
                    <div class="interview-doc-right">
                        <button class="btn btn-primary" onclick="analyzeInterviewDoc(${data.id}, 3)">AI分析</button>
                    </div>
                </div>
                <div class="form-group">
                    <label>三面AI分析结果：</label>
                    <textarea id="round3_ai_result" class="form-textarea" rows="4" placeholder="点击上方AI分析后将在此展示结果" readonly>${escapeHtml(data.round3_ai_result || '')}</textarea>
                </div>

                <div class="section-header">
                    <h4>Offer与入职</h4>
                </div>
                <div class="form-grid">
                    <div class="detail-item">
                        <label>
                            <input type="checkbox" id="offer_issued" ${data.offer_issued ? 'checked' : ''}>
                            是否发放Offer
                        </label>
                    </div>
                    <div class="detail-item">
                        <label>Offer发放日期：</label>
                        <input type="date" id="offer_date" class="form-input" placeholder="例如：2025-05-20" value="${escapeHtml((data.offer_date || '').slice(0,10))}">
                    </div>
                    <div class="detail-item">
                        <label>拟入职架构：</label>
                        <input type="text" id="offer_department" class="form-input" value="${escapeHtml(data.offer_department || '')}">
                    </div>
                    <div class="detail-item">
                        <label>拟入职日期：</label>
                        <input type="date" id="offer_onboard_plan_date" class="form-input" placeholder="例如：2025-06-01" value="${escapeHtml((data.offer_onboard_plan_date || '').slice(0,10))}">
                    </div>
                </div>
                <div class="form-grid">
                    <div class="detail-item">
                        <label>
                            <input type="checkbox" id="onboard" ${data.onboard ? 'checked' : ''}>
                            是否已入职
                        </label>
                    </div>
                    <div class="detail-item">
                        <label>实际入职日期：</label>
                        <input type="date" id="onboard_date" class="form-input" placeholder="例如：2025-06-10" value="${escapeHtml((data.onboard_date || '').slice(0,10))}">
                    </div>
                    <div class="detail-item">
                        <label>入职架构：</label>
                        <input type="text" id="onboard_department" class="form-input" value="${escapeHtml(data.onboard_department || '')}">
                    </div>
                </div>

                <div class="modal-actions">
                    <button class="btn btn-primary" onclick="saveInterview(${data.id})">保存</button>
                    <button class="btn btn-secondary" onclick="closeInterviewModal()">关闭</button>
                </div>
            `;

            modal.style.display = 'block';
            // 填充应聘岗位下拉
            populatePositionSelect('interviewAppliedPosition', data.applied_position || '');

            // 将当前 interviewId 存到上传函数可用的位置
            window.currentInterviewIdForUpload = data.id;
            onRoundResultChange(); // 初始化控件启用状态
        })
        .catch(error => {
            console.error('加载面试详情失败:', error);
            alert('加载失败，请稍后再试');
        });
}

function closeInterviewModal() {
    const modal = document.getElementById('interviewModal');
    const body = document.getElementById('interviewModalBody');
    if (modal) modal.style.display = 'none';
    if (body) body.innerHTML = '';
}

// 根据一面/二面结果控制后续字段是否可填
function onRoundResultChange() {
    const r1Result = document.getElementById('round1_result')?.value || '';
    const r2Result = document.getElementById('round2_result')?.value || '';
    const r3Enabled = document.getElementById('round3_enabled')?.checked || false;

    // 二面仅当一面结果为通过时可填
    const r2Fields = ['round2_interviewer', 'round2_time', 'round2_result']
        .map(id => document.getElementById(id))
        .filter(Boolean);
    const r2Disabled = r1Result !== '通过';
    r2Fields.forEach(el => el.disabled = r2Disabled);

    // 三面仅当二面结果为通过且勾选“有三面”时可填
    const r3Fields = ['round3_interviewer', 'round3_time', 'round3_result']
        .map(id => document.getElementById(id))
        .filter(Boolean);
    const r3Disabled = !(r2Result === '通过' && r3Enabled);
    r3Fields.forEach(el => el.disabled = r3Disabled);

    // Offer 与入职信息：
    // 1）仅当最终结果“面试通过”时，Offer部分可填写
    // 2）仅当Offer信息填写完整时，入职部分可填写
    const r3Result = document.getElementById('round3_result')?.value || '';
    const finalPass = (r3Result === '通过') || (r2Result === '通过' && !r3Enabled);

    const offerIssuedEl = document.getElementById('offer_issued');
    const offerDateEl = document.getElementById('offer_date');
    const offerDeptEl = document.getElementById('offer_department');
    const offerPlanDateEl = document.getElementById('offer_onboard_plan_date');

    const onboardEl = document.getElementById('onboard');
    const onboardDateEl = document.getElementById('onboard_date');
    const onboardDeptEl = document.getElementById('onboard_department');

    // Offer部分：只有在最终通过时才可编辑
    const offerDisabled = !finalPass;
    [offerIssuedEl, offerDateEl, offerDeptEl, offerPlanDateEl].forEach(el => {
        if (el) el.disabled = offerDisabled;
    });

    // 判断Offer信息是否完整（用于控制入职部分）
    const offerIssued = offerIssuedEl && offerIssuedEl.checked;
    const offerDate = offerDateEl && offerDateEl.value.trim();
    const offerDept = offerDeptEl && offerDeptEl.value.trim();
    const offerPlanDate = offerPlanDateEl && offerPlanDateEl.value.trim();
    const offerComplete = finalPass && offerIssued && offerDate && offerDept && offerPlanDate;

    // 入职部分：只有在Offer信息完整时才可编辑
    const onboardDisabled = !offerComplete;
    [onboardEl, onboardDateEl, onboardDeptEl].forEach(el => {
        if (el) el.disabled = onboardDisabled;
    });
}

// 保存面试流程详情
function saveInterview(interviewId) {
    const payload = {
        applied_position: document.getElementById('interviewAppliedPosition')?.value || null,
        round1_interviewer: document.getElementById('round1_interviewer')?.value || null,
        round1_time: document.getElementById('round1_time')?.value || null,
        round1_result: document.getElementById('round1_result')?.value || null,
        round2_interviewer: document.getElementById('round2_interviewer')?.value || null,
        round2_time: document.getElementById('round2_time')?.value || null,
        round2_result: document.getElementById('round2_result')?.value || null,
        round3_enabled: document.getElementById('round3_enabled')?.checked || false,
        round3_interviewer: document.getElementById('round3_interviewer')?.value || null,
        round3_time: document.getElementById('round3_time')?.value || null,
        round3_result: document.getElementById('round3_result')?.value || null,
        round1_comment: document.getElementById('round1_comment')?.value || null,
        round2_comment: document.getElementById('round2_comment')?.value || null,
        round3_comment: document.getElementById('round3_comment')?.value || null,
        round1_ai_result: document.getElementById('round1_ai_result')?.value || null,
        round2_ai_result: document.getElementById('round2_ai_result')?.value || null,
        round3_ai_result: document.getElementById('round3_ai_result')?.value || null,
        offer_issued: document.getElementById('offer_issued')?.checked || false,
        offer_date: document.getElementById('offer_date')?.value || null,
        offer_department: document.getElementById('offer_department')?.value || null,
        offer_onboard_plan_date: document.getElementById('offer_onboard_plan_date')?.value || null,
        onboard: document.getElementById('onboard')?.checked || false,
        onboard_date: document.getElementById('onboard_date')?.value || null,
        onboard_department: document.getElementById('onboard_department')?.value || null,
    };

    fetch(`/api/interviews/${interviewId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            alert('保存成功');
            // 刷新列表以同步状态
            loadInterviews();
            // 重新加载详情数据，更新详情页的状态显示
            fetch(`/api/interviews/${interviewId}`)
                .then(response => response.json())
                .then(detailResult => {
                    if (detailResult.success) {
                        // 更新详情页中的状态显示（使用ID选择器）
                        const statusElement = document.getElementById('interviewStatusDisplay');
                        if (statusElement) {
                            statusElement.textContent = detailResult.data.status || '待面试';
                        } else {
                            // 如果ID不存在，尝试通过其他方式更新
                            const allStatusElements = document.querySelectorAll('#interviewModalBody .detail-item');
                            allStatusElements.forEach(item => {
                                const label = item.querySelector('label');
                                if (label && label.textContent.includes('当前状态')) {
                                    const span = item.querySelector('span');
                                    if (span) {
                                        span.textContent = detailResult.data.status || '待面试';
                                    }
                                }
                            });
                        }
                    }
                })
                .catch(err => {
                    console.error('更新详情状态失败:', err);
                });
        } else {
            alert(`保存失败：${result.message || '未知错误'}`);
        }
    })
    .catch(error => {
        console.error('保存面试详情失败:', error);
        alert('保存失败，请稍后再试');
    });
}

// 上传面试文档（按轮次）
function uploadInterviewDoc(round) {
    const fileInput = document.getElementById(`round${round}DocFile`);
    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
        alert('请先选择要上传的文件');
        return;
    }
    const interviewId = window.currentInterviewIdForUpload;
    if (!interviewId) {
        alert('未找到当前面试记录');
        return;
    }

    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('round', String(round));

    fetch(`/api/interviews/${interviewId}/upload-doc`, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            alert('上传成功');
            const data = result.data;
            if (round === 1 && data.round1_doc_path) {
                const linkSpan = document.getElementById('round1DocLink');
                if (linkSpan) {
                    linkSpan.innerHTML = `当前文档：<a href="/static/${escapeHtml(data.round1_doc_path)}" target="_blank">查看</a>`;
                }
            } else if (round === 2 && data.round2_doc_path) {
                const linkSpan = document.getElementById('round2DocLink');
                if (linkSpan) {
                    linkSpan.innerHTML = `当前文档：<a href="/static/${escapeHtml(data.round2_doc_path)}" target="_blank">查看</a>`;
                }
            } else if (round === 3 && data.round3_doc_path) {
                const linkSpan = document.getElementById('round3DocLink');
                if (linkSpan) {
                    linkSpan.innerHTML = `当前文档：<a href="/static/${escapeHtml(data.round3_doc_path)}" target="_blank">查看</a>`;
                }
            }
        } else {
            alert(`上传失败：${result.message || '未知错误'}`);
        }
    })
    .catch(error => {
        console.error('上传失败:', error);
        alert('上传失败，请稍后再试');
    });
}

// 调用AI分析面试文档
function analyzeInterviewDoc(interviewId, round) {
    // 获取按钮和文本域元素
    // 通过查找包含onclick属性的按钮来获取按钮元素
    const buttons = document.querySelectorAll(`button[onclick*="analyzeInterviewDoc(${interviewId}, ${round})"]`);
    const analyzeBtn = buttons.length > 0 ? buttons[0] : null;
    const textarea = document.getElementById(`round${round}_ai_result`);
    const loadingId = `ai_loading_${interviewId}_${round}`;
    
    // 检查是否已有文档
    const docLink = document.getElementById(`round${round}DocLink`);
    if (!docLink || !docLink.textContent.includes('查看')) {
        alert('请先上传面试文档（录音逐字稿等）');
        return;
    }
    
    // 显示加载状态
    if (analyzeBtn) {
        const originalText = analyzeBtn.textContent;
        analyzeBtn.disabled = true;
        analyzeBtn.innerHTML = '<span class="ai-loading-spinner"></span> AI分析中...';
        analyzeBtn.classList.add('analyzing');
    }
    
    // 在文本域上方显示加载提示
    if (textarea) {
        const loadingDiv = document.createElement('div');
        loadingDiv.id = loadingId;
        loadingDiv.className = 'ai-analysis-loading';
        loadingDiv.innerHTML = `
            <div class="ai-loading-content">
                <div class="ai-loading-spinner-large"></div>
                <p class="ai-loading-text">AI正在分析面试文档，请稍候...</p>
                <p class="ai-loading-hint">这可能需要几秒钟到一分钟的时间</p>
            </div>
        `;
        textarea.parentNode.insertBefore(loadingDiv, textarea);
        textarea.value = '';
        textarea.style.display = 'none';
    }
    
    fetch(`/api/interviews/${interviewId}/analyze-doc`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ round })
    })
    .then(response => response.json())
    .then(result => {
        // 移除加载状态
        if (analyzeBtn) {
            analyzeBtn.disabled = false;
            analyzeBtn.textContent = 'AI分析';
            analyzeBtn.classList.remove('analyzing');
        }
        
        const loadingDiv = document.getElementById(loadingId);
        if (loadingDiv) {
            loadingDiv.remove();
        }
        
        if (textarea) {
            textarea.style.display = 'block';
        }
        
        if (result.success) {
            const data = result.data || {};
            const summary = data.summary || '';
            const strengths = (data.strengths || []).join('\n- ');
            const weaknesses = (data.weaknesses || []).join('\n- ');
            const conclusion = data.conclusion || '';
            const nextQuestions = (data.next_questions || []).join('\n- ');
            let msg = '';
            if (summary) msg += `【整体概括】\n${summary}\n\n`;
            if (strengths) msg += `【优势】\n- ${strengths}\n\n`;
            if (weaknesses) msg += `【不足】\n- ${weaknesses}\n\n`;
            if (conclusion) msg += `【综合结论】\n${conclusion}\n\n`;
            if (nextQuestions) msg += `【下一轮推荐追问问题】\n- ${nextQuestions}`;
            
            if (textarea) {
                textarea.value = msg || '分析完成，但未返回可用内容';
                // 添加成功提示动画
                textarea.classList.add('analysis-success');
                setTimeout(() => {
                    textarea.classList.remove('analysis-success');
                }, 2000);
            } else {
                alert(msg || '分析完成，但未返回可用内容');
            }
        } else {
            if (textarea) {
                textarea.value = `分析失败：${result.message || '未知错误'}`;
            }
            alert(result.message || 'AI分析失败');
        }
    })
    .catch(error => {
        console.error('AI分析文档失败:', error);
        
        // 移除加载状态
        if (analyzeBtn) {
            analyzeBtn.disabled = false;
            analyzeBtn.textContent = 'AI分析';
            analyzeBtn.classList.remove('analyzing');
        }
        
        const loadingDiv = document.getElementById(loadingId);
        if (loadingDiv) {
            loadingDiv.remove();
        }
        
        if (textarea) {
            textarea.style.display = 'block';
            textarea.value = '分析失败，请稍后再试';
        }
        
        alert('AI分析失败，请稍后再试');
    });
}

// 统一的模态框点击外部关闭处理
// 当点击模态框外部（背景）时关闭模态框，点击模态框内容区域不会关闭
document.addEventListener('click', function(event) {
    // 检查是否点击在模态框背景上（而不是模态框内容上）
    // event.target是.modal元素，且不是.modal-content或其子元素
    if (event.target.classList.contains('modal')) {
        const modalId = event.target.id;
        
        switch(modalId) {
            case 'detailModal':
                closeModal();
                break;
            case 'resumePreviewModal':
                closeResumePreviewModal();
                break;
            case 'editModal':
                closeEditModal();
                break;
            case 'interviewModal':
                closeInterviewModal();
                break;
            case 'funnelModal':
                closeFunnelModal();
                break;
            case 'positionModal':
                closePositionModal();
                break;
        }
    }
});

// AI配置相关函数
function toggleAIConfig() {
    const content = document.getElementById('aiConfigContent');
    const btn = document.getElementById('toggleAIConfigBtn');
    if (content.style.display === 'none') {
        content.style.display = 'block';
        btn.textContent = '收起配置';
    } else {
        content.style.display = 'none';
        btn.textContent = '展开配置';
    }
}

function loadAIConfig() {
    fetch('/api/ai/config')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const config = data.data;
                document.getElementById('aiEnabled').checked = config.ai_enabled;
                document.getElementById('aiModel').value = config.ai_model;
                if (config.ai_api_base) {
                    document.getElementById('aiApiBase').value = config.ai_api_base;
                }
                
                // 从本地存储加载API密钥（如果存在）
                const savedKey = localStorage.getItem('ai_api_key');
                if (savedKey) {
                    document.getElementById('aiApiKey').value = savedKey;
                }
                
                // 更新模型选项
                if (config.ai_models && config.ai_models.length > 0) {
                    updateModelOptions(config.ai_models);
                }
            }
        })
        .catch(error => {
            console.error('加载AI配置失败:', error);
        });
}

function updateModelOptions(models) {
    const select = document.getElementById('aiModel');
    if (models && models.length > 0) {
        select.innerHTML = '';
        models.forEach(model => {
            const option = document.createElement('option');
            option.value = model.value;
            option.textContent = model.label;
            select.appendChild(option);
        });
    }
}

function updateAIConfig() {
    // 实时更新配置到本地存储
    const config = {
        ai_enabled: document.getElementById('aiEnabled').checked,
        ai_model: document.getElementById('aiModel').value,
        ai_api_key: document.getElementById('aiApiKey').value,
        ai_api_base: document.getElementById('aiApiBase').value
    };
    
    // 保存API密钥到本地存储
    if (config.ai_api_key) {
        localStorage.setItem('ai_api_key', config.ai_api_key);
    }
    
    // 保存其他配置到本地存储
    localStorage.setItem('ai_config', JSON.stringify({
        ai_enabled: config.ai_enabled,
        ai_model: config.ai_model,
        ai_api_base: config.ai_api_base
    }));
}

function saveAIConfig() {
    const config = {
        ai_enabled: document.getElementById('aiEnabled').checked,
        ai_model: document.getElementById('aiModel').value,
        ai_api_key: document.getElementById('aiApiKey').value,
        ai_api_base: document.getElementById('aiApiBase').value
    };
    
    fetch('/api/ai/config', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(config)
    })
    .then(response => response.json())
    .then(data => {
        const statusDiv = document.getElementById('aiConfigStatus');
        if (data.success) {
            statusDiv.innerHTML = '<span style="color: green;">✓ ' + data.message + '，配置已自动生效</span>';
            // 保存到本地存储
            if (config.ai_api_key) {
                localStorage.setItem('ai_api_key', config.ai_api_key);
            }
            localStorage.setItem('ai_config', JSON.stringify({
                ai_enabled: config.ai_enabled,
                ai_model: config.ai_model,
                ai_api_base: config.ai_api_base
            }));
            // 保存后自动使用，不需要重新连接
            updateAIConfig();
            // 更新简历列表中的AI状态显示
            checkAIStatus().then(() => {
                updateAIStatusDisplay();
            });
        } else {
            statusDiv.innerHTML = '<span style="color: red;">✗ ' + data.message + '</span>';
        }
        setTimeout(() => {
            statusDiv.innerHTML = '';
        }, 3000);
    })
    .catch(error => {
        console.error('保存AI配置失败:', error);
        const statusDiv = document.getElementById('aiConfigStatus');
        statusDiv.innerHTML = '<span style="color: red;">✗ 保存失败，请重试</span>';
        setTimeout(() => {
            statusDiv.innerHTML = '';
        }, 3000);
    });
}

function testAIConnection() {
    const config = {
        api_key: document.getElementById('aiApiKey').value,
        api_base: document.getElementById('aiApiBase').value,
        model: document.getElementById('aiModel').value
    };
    
    if (!config.api_key) {
        alert('请先输入API密钥');
        return;
    }
    
    const statusDiv = document.getElementById('aiConfigStatus');
    statusDiv.innerHTML = '<span style="color: blue;">测试连接中...</span>';
    
    fetch('/api/ai/test', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(config)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            statusDiv.innerHTML = '<span style="color: green;">✓ ' + data.message + '</span>';
        } else {
            statusDiv.innerHTML = '<span style="color: red;">✗ ' + data.message + '</span>';
        }
        setTimeout(() => {
            statusDiv.innerHTML = '';
        }, 5000);
    })
    .catch(error => {
        console.error('测试AI连接失败:', error);
        statusDiv.innerHTML = '<span style="color: red;">✗ 测试失败，请检查网络连接</span>';
        setTimeout(() => {
            statusDiv.innerHTML = '';
        }, 5000);
    });
}

// 模块切换功能
function switchModule(moduleName) {
    // 隐藏所有模块
    document.querySelectorAll('.module').forEach(module => {
        module.classList.remove('active');
        module.style.display = 'none';
    });
    
    // 移除所有导航项的active状态
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    
    // 显示选中的模块
    const targetModule = document.getElementById(`module-${moduleName}`);
    if (targetModule) {
        targetModule.classList.add('active');
        targetModule.style.display = 'block';
        
        // 激活对应的导航项
        const navItem = document.querySelector(`[data-module="${moduleName}"]`);
        if (navItem) {
            navItem.classList.add('active');
        }
        
        // 更新URL（不刷新页面）
        const newUrl = window.location.pathname + `?module=${moduleName}`;
        window.history.pushState({module: moduleName}, '', newUrl);
        
        // 根据模块加载相应数据
        if (moduleName === 'analysis') {
            loadResumesForAnalysis();
        } else if (moduleName === 'upload') {
            loadResumes();
            // 更新AI状态显示
            checkAIStatus().then(() => {
                updateAIStatusDisplay();
            });
        } else if (moduleName === 'settings') {
            loadAIConfig();
        } else if (moduleName === 'positions') {
            loadPositions();
        } else if (moduleName === 'interview') {
            loadInterviews();
        } else if (moduleName === 'stats') {
            loadPositionsForStats();
            loadStatistics();
        }
    }
}

// 加载简历列表用于分析模块
function loadResumesForAnalysis(searchTerm = '') {
    const listElement = document.getElementById('resumeSelectorList');
    if (!listElement) {
        console.warn('resumeSelectorList element not found');
        return;
    }
    
    const params = new URLSearchParams({
        page: 1,
        per_page: 1000,
        sort_by: 'upload_time',
        sort_order: 'desc'
    });
    
    if (searchTerm) {
        params.append('search', searchTerm);
    }
    
    fetch(`/api/resumes?${params}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayResumeSelector(data.data);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            if (listElement) {
                listElement.innerHTML = '<div class="loading">加载失败，请刷新重试</div>';
            }
        });
}

// 显示简历选择器列表
function displayResumeSelector(resumes) {
    const list = document.getElementById('resumeSelectorList');
    if (!list) {
        console.warn('resumeSelectorList element not found');
        return;
    }
    
    if (resumes.length === 0) {
        list.innerHTML = '<div class="empty-state">暂无简历</div>';
        return;
    }
    
    list.innerHTML = resumes.map(resume => {
        const identityCode = (() => {
            if (!resume.name) return '-';
            const phone = resume.phone || '';
            if (phone && phone.length >= 4) {
                return escapeHtml(resume.name + phone.slice(-4));
            }
            return escapeHtml(resume.name);
        })();
        const name = escapeHtml(resume.name || '未命名');
        const school = escapeHtml(resume.school || '未知学校');
        const major = escapeHtml(resume.major || '未知专业');
        const appliedPosition = escapeHtml(resume.applied_position || '未填写');
        const status = resume.parse_status || 'pending';
        const statusClass = status === 'success' ? 'success' : status === 'processing' ? 'processing' : 'pending';
        const alreadyInvited = interviewedResumeIds.has(resume.id);
        
        // 获取匹配度色块
        let matchBadgeHtml = '';
        if (resume.applied_position) {
            const cacheKey = `${resume.id}_${resume.applied_position}`;
            const matchAnalysis = matchAnalysisCache[cacheKey];
            if (matchAnalysis && matchAnalysis.match_score !== undefined) {
                const score = matchAnalysis.match_score;
                let colorClass = 'match-gray';
                if (score >= 80) {
                    colorClass = 'match-green';
                } else if (score >= 60) {
                    colorClass = 'match-orange';
                } else {
                    colorClass = 'match-red';
                }
                matchBadgeHtml = `<span class="match-badge ${colorClass}" title="匹配度: ${score}分"></span>`;
            } else {
                // 未解析
                matchBadgeHtml = '<span class="match-badge match-gray" title="未解析"></span>';
            }
        } else {
            // 未填写应聘岗位
            matchBadgeHtml = '<span class="match-badge match-gray" title="未填写应聘岗位"></span>';
        }
        
        return `
            <div class="resume-selector-item" onclick="selectResumeForAnalysis(${resume.id})" data-resume-id="${resume.id}">
                <div class="resume-selector-item-header">
                    <div class="resume-selector-item-name">${identityCode}</div>
                    ${matchBadgeHtml}
                </div>
                <div class="resume-selector-item-info">${school} | ${major}</div>
                <div class="resume-selector-item-info">应聘岗位：${appliedPosition}</div>
                <div class="resume-selector-item-info" style="margin-top: 4px;">
                    <span class="status-${statusClass}">${getStatusText(status)}</span>
                    <button class="btn btn-link btn-small" 
                        ${alreadyInvited ? 'disabled' : ''}
                        onclick="event.stopPropagation(); ${alreadyInvited ? '' : `inviteInterview(${resume.id})`}"
                        style="color: ${alreadyInvited ? '#28a745' : '#007bff'};">
                        ${alreadyInvited ? '已邀约面试' : '邀约面试'}
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

function getStatusText(status) {
    const statusMap = {
        'pending': '待处理',
        'processing': '处理中',
        'success': '已完成',
        'failed': '失败'
    };
    return statusMap[status] || '未知';
}

function searchResumesForAnalysis(searchTerm) {
    loadResumesForAnalysis(searchTerm);
}

// 选择简历进行分析
function selectResumeForAnalysis(resumeId) {
    currentAnalysisResumeId = resumeId;
    
    // 更新选中状态
    document.querySelectorAll('.resume-selector-item').forEach(item => {
        item.classList.remove('active');
    });
    const selectedItem = document.querySelector(`[data-resume-id="${resumeId}"]`);
    if (selectedItem) {
        selectedItem.classList.add('active');
    }
    
    // 加载简历详情
    fetch(`/api/resumes/${resumeId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayAnalysisDetail(data.data);
            } else {
                const detailDiv = document.getElementById('analysisDetail');
                if (detailDiv) {
                    detailDiv.innerHTML = '<div class="empty-state"><p>加载失败，请重试</p></div>';
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
            const detailDiv = document.getElementById('analysisDetail');
            if (detailDiv) {
                detailDiv.innerHTML = '<div class="empty-state"><p>加载失败，请重试</p></div>';
            }
        });
}

// 显示分析详情
function displayAnalysisDetail(resume) {
    const detailDiv = document.getElementById('analysisDetail');
    if (!detailDiv) {
        console.warn('analysisDetail element not found');
        return;
    }
    
    // 计算工龄
    const currentYear = new Date().getFullYear();
    let earliestYear = resume.earliest_work_year;
    if (!earliestYear && resume.work_experience && resume.work_experience.length > 0) {
        const workYears = resume.work_experience
            .map(exp => exp.start_year)
            .filter(year => year !== null && year !== undefined);
        if (workYears.length > 0) {
            earliestYear = Math.min(...workYears);
        }
    }
    const workYears = earliestYear ? (currentYear - earliestYear) : null;
    
    // 格式化工作经历
    let workExpHtml = '<p>暂无工作经历</p>';
    if (resume.work_experience && resume.work_experience.length > 0) {
        workExpHtml = '<ul>';
        resume.work_experience.forEach(exp => {
            const startYear = exp.start_year || '未知';
            const endYear = exp.end_year || '至今';
            const company = escapeHtml(exp.company || '未知公司');
            const position = escapeHtml(exp.position || '未知岗位');
            workExpHtml += `<li><strong>${startYear}-${endYear}</strong> ${company} | ${position}</li>`;
        });
        workExpHtml += '</ul>';
    }
    
    // 加载岗位列表用于下拉选择
    loadPositionsForAnalysis().then(positions => {
        const positionOptions = positions.map(pos => 
            `<option value="${escapeHtml(pos.position_name)}" ${resume.applied_position === pos.position_name ? 'selected' : ''}>${escapeHtml(pos.position_name)}</option>`
        ).join('');
        const positionSelectHtml = `
            <option value="">请选择岗位</option>
            ${positionOptions}
        `;
        
        detailDiv.innerHTML = `
        <div class="analysis-detail-content">
            <div class="detail-section">
                <h3>应聘岗位</h3>
                <div class="detail-grid">
                    <div class="detail-item" style="grid-column: 1 / -1;">
                        <label>应聘岗位：</label>
                        <select id="analysisAppliedPosition" class="form-select" style="width: 300px; padding: 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px;" onchange="onAppliedPositionChange(${resume.id})">
                            ${positionSelectHtml}
                        </select>
                        <button class="btn btn-primary" onclick="saveAppliedPosition(${resume.id})" style="margin-left: 10px; padding: 8px 15px;">保存</button>
                    </div>
                </div>
            </div>
            
            <div class="detail-section">
                <h3>简历匹配度分析</h3>
                <div id="matchAnalysisResult" class="match-analysis-result">
                    <div class="loading">正在分析中...</div>
                </div>
            </div>
            
            <div class="detail-section">
                <h3>基本信息</h3>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>姓名：</label>
                        <span>${escapeHtml(resume.name || '-')}</span>
                    </div>
                    <div class="detail-item">
                        <label>性别：</label>
                        <span>${escapeHtml(resume.gender || '-')}</span>
                    </div>
                    <div class="detail-item">
                        <label>年龄：</label>
                        <span>${resume.age || '-'}</span>
                    </div>
                    <div class="detail-item">
                        <label>出生年份：</label>
                        <span>${resume.birth_year || '-'}</span>
                    </div>
                    <div class="detail-item">
                        <label>手机号：</label>
                        <span>${escapeHtml(resume.phone || '-')}</span>
                    </div>
                    <div class="detail-item">
                        <label>邮箱：</label>
                        <span>${escapeHtml(resume.email || '-')}</span>
                    </div>
                </div>
            </div>
            
            <div class="detail-section">
                <h3>教育信息</h3>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>最高学历：</label>
                        <span>${escapeHtml(resume.highest_education || '-')}</span>
                    </div>
                    <div class="detail-item">
                        <label>毕业学校：</label>
                        <span>${escapeHtml(resume.school || '-')}</span>
                    </div>
                    <div class="detail-item">
                        <label>专业：</label>
                        <span>${escapeHtml(resume.major || '-')}</span>
                    </div>
                </div>
            </div>
            
            <div class="detail-section">
                <h3>工作经历</h3>
                <div class="work-experience-list">
                    ${workExpHtml}
                </div>
                <div class="detail-item" style="margin-top: 15px;">
                    <label>工龄：</label>
                    <span>${workYears !== null && workYears >= 0 ? workYears + '年' : '-'}</span>
                </div>
            </div>

            <div class="detail-section">
                <h3>下载分析报告</h3>
                <div class="detail-item" style="display: flex; gap: 10px; flex-wrap: wrap;">
                    <button class="btn btn-primary" onclick="downloadAnalysisPdf(${resume.id})">下载PDF报告</button>
                    <button class="btn btn-primary" onclick="downloadResumeFile(${resume.id})">下载原简历文件</button>
                </div>
            </div>
            
            <div class="detail-section">
                <h3>原始文本</h3>
                <div class="raw-text-container">
                    <pre class="raw-text">${escapeHtml(resume.raw_text || '无原始文本')}</pre>
                </div>
            </div>
        </div>
    `;
        
        // 如果有应聘岗位，检查是否有缓存的分析结果
        if (resume.applied_position) {
            const cacheKey = `${resume.id}_${resume.applied_position}`;
            if (matchAnalysisCache[cacheKey]) {
                // 使用缓存的分析结果
                displayMatchAnalysis(matchAnalysisCache[cacheKey]);
            } else {
                // 没有缓存，进行新的分析
                analyzeResumeMatch(resume.id, resume.applied_position);
            }
        } else {
            document.getElementById('matchAnalysisResult').innerHTML = '<div class="empty-state"><p>请先选择应聘岗位，然后系统将自动进行匹配度分析</p></div>';
        }
    });
}

// 加载岗位列表用于分析模块 / 通用下拉
function loadPositionsForAnalysis() {
    return fetch('/api/positions')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                return data.data;
            } else {
                return [];
            }
        })
        .catch(error => {
            console.error('加载岗位列表失败:', error);
            return [];
        });
}

// 通用：填充岗位下拉选项
function populatePositionSelect(selectId, selectedName) {
    const select = document.getElementById(selectId);
    if (!select) return;
    loadPositionsForAnalysis().then(positions => {
        const current = selectedName || '';
        let optionsHtml = '<option value="">请选择岗位</option>';
        positions.forEach(pos => {
            const name = pos.position_name || '';
            const selected = name === current ? 'selected' : '';
            optionsHtml += `<option value="${escapeHtml(name)}" ${selected}>${escapeHtml(name)}</option>`;
        });
        select.innerHTML = optionsHtml;
    });
}

// 应聘岗位变化时的处理
function onAppliedPositionChange(resumeId) {
    const select = document.getElementById('analysisAppliedPosition');
    const appliedPosition = select.value;
    
    if (appliedPosition) {
        // 检查是否有缓存的分析结果
        const cacheKey = `${resumeId}_${appliedPosition}`;
        if (matchAnalysisCache[cacheKey]) {
            // 使用缓存的分析结果
            displayMatchAnalysis(matchAnalysisCache[cacheKey]);
        } else {
            // 没有缓存，进行新的分析
            analyzeResumeMatch(resumeId, appliedPosition);
        }
    } else {
        document.getElementById('matchAnalysisResult').innerHTML = '<div class="empty-state"><p>请选择应聘岗位后，系统将自动进行匹配度分析</p></div>';
    }
}

// 保存应聘岗位
function saveAppliedPosition(resumeId) {
    const select = document.getElementById('analysisAppliedPosition');
    const appliedPosition = select.value.trim();
    
    fetch(`/api/resumes/${resumeId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            applied_position: appliedPosition || null
        })
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            alert('应聘岗位保存成功');
            // 如果有岗位，检查是否有缓存的分析结果
            if (appliedPosition) {
                const cacheKey = `${resumeId}_${appliedPosition}`;
                if (matchAnalysisCache[cacheKey]) {
                    // 使用缓存的分析结果
                    displayMatchAnalysis(matchAnalysisCache[cacheKey]);
                } else {
                    // 没有缓存，进行新的分析
                    analyzeResumeMatch(resumeId, appliedPosition);
                }
            }
        } else {
            alert('保存失败: ' + (result.message || '未知错误'));
        }
    })
    .catch(error => {
        console.error('保存应聘岗位失败:', error);
        alert('保存失败，请重试');
    });
}

// 分析简历匹配度
function analyzeResumeMatch(resumeId, appliedPosition) {
    const resultDiv = document.getElementById('matchAnalysisResult');
    if (!resultDiv) {
        return;
    }
    
    resultDiv.innerHTML = '<div class="loading">正在分析中，请稍候...</div>';
    
    fetch(`/api/resumes/${resumeId}/match-analysis`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            applied_position: appliedPosition
        })
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            // 缓存分析结果
            const cacheKey = `${resumeId}_${appliedPosition}`;
            matchAnalysisCache[cacheKey] = result.data;
            // 显示分析结果
            displayMatchAnalysis(result.data);
            // 更新简历选择卡片中的匹配度色块
            updateResumeSelectorMatchBadge(resumeId, appliedPosition, result.data.match_score);
        } else {
            resultDiv.innerHTML = `<div class="error">分析失败: ${result.message || '未知错误'}</div>`;
        }
    })
    .catch(error => {
        console.error('分析简历匹配度失败:', error);
        resultDiv.innerHTML = '<div class="error">分析失败，请检查AI配置是否正确</div>';
    });
}

// 显示匹配度分析结果
function displayMatchAnalysis(analysisData) {
    const resultDiv = document.getElementById('matchAnalysisResult');
    if (!resultDiv) {
        return;
    }
    
    const matchScore = analysisData.match_score || 0;
    const matchLevel = analysisData.match_level || '未知';
    const strengths = analysisData.strengths || [];
    const weaknesses = analysisData.weaknesses || [];
    const suggestions = analysisData.suggestions || [];
    const detailedAnalysis = analysisData.detailed_analysis || '';
    
    let html = `
        <div class="match-analysis-content">
            <div class="match-score-section">
                <div class="match-score-circle" style="background: ${getScoreColor(matchScore)}">
                    <div class="match-score-value">${matchScore}</div>
                    <div class="match-score-label">匹配度</div>
                </div>
                <div class="match-level-badge match-level-${matchLevel.toLowerCase()}">${matchLevel}</div>
            </div>
            
            ${detailedAnalysis ? `
            <div class="match-analysis-text">
                <h4>详细分析</h4>
                <div class="analysis-text-content">${escapeHtml(detailedAnalysis).replace(/\n/g, '<br>')}</div>
            </div>
            ` : ''}
            
            ${strengths.length > 0 ? `
            <div class="match-strengths">
                <h4>优势匹配点</h4>
                <ul>
                    ${strengths.map(s => `<li>${escapeHtml(s)}</li>`).join('')}
                </ul>
            </div>
            ` : ''}
            
            ${weaknesses.length > 0 ? `
            <div class="match-weaknesses">
                <h4>不足匹配点</h4>
                <ul>
                    ${weaknesses.map(w => `<li>${escapeHtml(w)}</li>`).join('')}
                </ul>
            </div>
            ` : ''}
            
            ${suggestions.length > 0 ? `
            <div class="match-suggestions">
                <h4>改进建议</h4>
                <ul>
                    ${suggestions.map(s => `<li>${escapeHtml(s)}</li>`).join('')}
                </ul>
            </div>
            ` : ''}
        </div>
    `;
    
    resultDiv.innerHTML = html;
}

// 根据分数获取颜色
function getScoreColor(score) {
    if (score >= 80) return '#52c41a'; // 绿色
    if (score >= 60) return '#faad14'; // 橙色
    return '#ff4d4f'; // 红色
}

// 根据分数获取颜色类名
function getScoreColorClass(score) {
    if (score >= 80) return 'match-green';
    if (score >= 60) return 'match-orange';
    return 'match-red';
}

// 更新简历选择卡片中的匹配度色块
function updateResumeSelectorMatchBadge(resumeId, appliedPosition, matchScore) {
    const resumeItem = document.querySelector(`[data-resume-id="${resumeId}"]`);
    if (!resumeItem) {
        return; // 如果简历卡片不在当前显示的列表中，不更新
    }
    
    const header = resumeItem.querySelector('.resume-selector-item-header');
    if (!header) {
        return;
    }
    
    // 查找或创建匹配度色块
    let badge = header.querySelector('.match-badge');
    if (!badge) {
        // 如果没有色块，创建一个
        badge = document.createElement('span');
        badge.className = 'match-badge';
        header.appendChild(badge);
    }
    
    // 更新色块样式和提示
    if (matchScore !== undefined && matchScore !== null) {
        badge.className = `match-badge ${getScoreColorClass(matchScore)}`;
        badge.title = `匹配度: ${matchScore}分`;
    } else {
        badge.className = 'match-badge match-gray';
        badge.title = '未解析';
    }
}

// 检查AI配置状态
function checkAIStatus() {
    return new Promise((resolve) => {
        // 先从本地存储获取
        const localConfig = localStorage.getItem('ai_config');
        const localApiKey = localStorage.getItem('ai_api_key');
        
        // 然后从后端获取最新状态
        fetch('/api/ai/config')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    const config = data.data;
                    // 使用后端返回的ai_available状态，或检查本地存储
                    const isEnabled = config.ai_available !== undefined 
                        ? config.ai_available 
                        : (config.ai_enabled && (localApiKey || config.ai_enabled));
                    
                    aiConfigStatus = {
                        enabled: isEnabled,
                        hasApiKey: !!localApiKey || config.ai_available,
                        aiEnabled: config.ai_enabled
                    };
                    
                    resolve();
                } else {
                    // 使用本地存储的状态
                    const isEnabled = localConfig && localApiKey;
                    aiConfigStatus = {
                        enabled: isEnabled,
                        hasApiKey: !!localApiKey,
                        aiEnabled: false
                    };
                    resolve();
                }
            })
            .catch(error => {
                console.error('检查AI配置状态失败:', error);
                // 使用本地存储的状态
                const isEnabled = localConfig && localApiKey;
                aiConfigStatus = {
                    enabled: isEnabled,
                    hasApiKey: !!localApiKey,
                    aiEnabled: false
                };
                resolve();
            });
    });
}

// 获取AI状态显示
function getAIStatusDisplay() {
    if (aiConfigStatus === null) {
        // 如果还没有检查，先使用本地存储判断
        const localConfig = localStorage.getItem('ai_config');
        const localApiKey = localStorage.getItem('ai_api_key');
        const isEnabled = localConfig && localApiKey;
        return isEnabled 
            ? '<span class="ai-status-enabled">AI解析已启动</span>'
            : '<span class="ai-status-disabled">AI解析未启动</span>';
    }
    
    return aiConfigStatus.enabled
        ? '<span class="ai-status-enabled">AI解析已启动</span>'
        : '<span class="ai-status-disabled">AI解析未启动</span>';
}

// 更新标题行的AI状态显示
function updateAIStatusDisplay() {
    const statusHeader = document.getElementById('aiStatusHeader');
    if (statusHeader) {
        statusHeader.innerHTML = getAIStatusDisplay();
    }
}

// 处理浏览器前进后退
window.addEventListener('popstate', function(event) {
    const urlParams = new URLSearchParams(window.location.search);
    const module = urlParams.get('module') || 'upload';
    switchModule(module);
});

// ==================== 岗位目录功能 ====================
let currentPositionId = null;

// ==================== 简历匹配度分析缓存 ====================
let matchAnalysisCache = {}; // 缓存格式: { 'resumeId_positionName': analysisData }

// 加载岗位列表
function loadPositions() {
    const listElement = document.getElementById('positionsList');
    if (!listElement) {
        console.warn('positionsList element not found');
        return;
    }
    
    listElement.innerHTML = '<div class="loading">加载中...</div>';
    
    fetch('/api/positions')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayPositions(data.data);
            } else {
                listElement.innerHTML = '<div class="error">加载失败: ' + (data.message || '未知错误') + '</div>';
            }
        })
        .catch(error => {
            console.error('加载岗位列表失败:', error);
            listElement.innerHTML = '<div class="error">加载失败，请刷新重试</div>';
        });
}

// 显示岗位列表
function displayPositions(positions) {
    const listElement = document.getElementById('positionsList');
    if (!listElement) {
        return;
    }
    
    if (!positions || positions.length === 0) {
        listElement.innerHTML = '<div class="empty-state"><p>暂无岗位信息，点击"新增岗位"按钮添加</p></div>';
        return;
    }
    
    let html = '<div class="positions-list-container">';
    positions.forEach(position => {
        const createTime = position.create_time ? new Date(position.create_time).toLocaleString('zh-CN') : '-';
        const updateTime = position.update_time ? new Date(position.update_time).toLocaleString('zh-CN') : '-';
        
        html += `
            <div class="position-group">
                <div class="position-name-header">
                    <h4 class="position-name">${escapeHtml(position.position_name || '未命名岗位')}</h4>
                </div>
                <div style="flex: 1; display: flex; flex-direction: column;">
                    <div class="position-cards">
                        <div class="position-info-card">
                            <div class="position-info-title">工作内容</div>
                            <div class="position-info-content">${escapeHtml(position.work_content || '未填写')}</div>
                        </div>
                        <div class="position-info-card">
                            <div class="position-info-title">任职资格</div>
                            <div class="position-info-content">${escapeHtml(position.job_requirements || '未填写')}</div>
                        </div>
                        <div class="position-info-card">
                            <div class="position-info-title">核心需求</div>
                            <div class="position-info-content">${escapeHtml(position.core_requirements || '未填写')}</div>
                        </div>
                        <div class="position-actions">
                            <button class="btn btn-sm btn-edit" onclick="editPosition(${position.id})" title="编辑">✏️</button>
                            <button class="btn btn-sm btn-delete" onclick="deletePosition(${position.id})" title="删除">🗑️</button>
                        </div>
                    </div>
                    <div class="position-footer">
                        <span class="position-time">创建: ${createTime}</span>
                        <span class="position-time">更新: ${updateTime}</span>
                    </div>
                </div>
            </div>
        `;
    });
    html += '</div>';
    
    listElement.innerHTML = html;
}

// 显示新增岗位表单
function showAddPositionForm() {
    currentPositionId = null;
    const modal = document.getElementById('positionModal');
    const form = document.getElementById('positionForm');
    const title = document.getElementById('positionModalTitle');
    
    if (!modal || !form || !title) {
        console.error('岗位表单元素未找到');
        return;
    }
    
    title.textContent = '新增岗位';
    form.reset();
    modal.style.display = 'block';
}

// 编辑岗位
function editPosition(positionId) {
    currentPositionId = positionId;
    const modal = document.getElementById('positionModal');
    const form = document.getElementById('positionForm');
    const title = document.getElementById('positionModalTitle');
    
    if (!modal || !form || !title) {
        console.error('岗位表单元素未找到');
        return;
    }
    
    title.textContent = '编辑岗位';
    
    fetch(`/api/positions/${positionId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const position = data.data;
                document.getElementById('positionName').value = position.position_name || '';
                document.getElementById('workContent').value = position.work_content || '';
                document.getElementById('jobRequirements').value = position.job_requirements || '';
                document.getElementById('coreRequirements').value = position.core_requirements || '';
                modal.style.display = 'block';
            } else {
                alert('加载岗位信息失败: ' + (data.message || '未知错误'));
            }
        })
        .catch(error => {
            console.error('加载岗位信息失败:', error);
            alert('加载岗位信息失败，请重试');
        });
}

// 保存岗位
function savePosition(event) {
    event.preventDefault();
    
    const positionName = document.getElementById('positionName').value.trim();
    const workContent = document.getElementById('workContent').value.trim();
    const jobRequirements = document.getElementById('jobRequirements').value.trim();
    const coreRequirements = document.getElementById('coreRequirements').value.trim();
    
    // 验证所有字段
    if (!positionName) {
        alert('请输入岗位名称');
        return;
    }
    if (!workContent) {
        alert('请输入工作内容');
        return;
    }
    if (!jobRequirements) {
        alert('请输入任职资格');
        return;
    }
    if (!coreRequirements) {
        alert('请输入核心需求');
        return;
    }
    
    const data = {
        position_name: positionName,
        work_content: workContent,
        job_requirements: jobRequirements,
        core_requirements: coreRequirements
    };
    
    const url = currentPositionId ? `/api/positions/${currentPositionId}` : '/api/positions';
    const method = currentPositionId ? 'PUT' : 'POST';
    
    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            closePositionModal();
            loadPositions();
            alert(currentPositionId ? '岗位更新成功' : '岗位创建成功');
        } else {
            alert('保存失败: ' + (result.message || '未知错误'));
        }
    })
    .catch(error => {
        console.error('保存岗位失败:', error);
        alert('保存失败，请重试');
    });
}

// 删除岗位
function deletePosition(positionId) {
    if (!confirm('确定要删除这个岗位吗？此操作不可恢复。')) {
        return;
    }
    
    fetch(`/api/positions/${positionId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            loadPositions();
            alert('岗位删除成功');
        } else {
            alert('删除失败: ' + (result.message || '未知错误'));
        }
    })
    .catch(error => {
        console.error('删除岗位失败:', error);
        alert('删除失败，请重试');
    });
}

// 生成面试评价填写链接
function generateCommentLink(interviewId, round) {
    fetch(`/api/interviews/${interviewId}/comment-link/${round}`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            const linkInput = document.getElementById(`round${round}_link`);
            const linkDisplay = document.getElementById(`round${round}_link_display`);
            if (linkInput && linkDisplay) {
                const baseUrl = window.location.origin;
                linkInput.value = `${baseUrl}/interview-comment?token=${result.data.token}`;
                linkDisplay.style.display = 'block';
            }
        } else {
            alert('生成链接失败：' + (result.message || '未知错误'));
        }
    })
    .catch(error => {
        console.error('生成链接失败:', error);
        alert('生成链接失败，请重试');
    });
}

// 复制链接
function copyLink(inputId) {
    const input = document.getElementById(inputId);
    if (input) {
        input.select();
        input.setSelectionRange(0, 99999); // 兼容移动设备
        try {
            document.execCommand('copy');
            alert('链接已复制到剪贴板');
        } catch (err) {
            // 使用现代API
            navigator.clipboard.writeText(input.value).then(() => {
                alert('链接已复制到剪贴板');
            }).catch(() => {
                alert('复制失败，请手动复制');
            });
        }
    }
}

// 关闭岗位表单模态框
function closePositionModal() {
    const modal = document.getElementById('positionModal');
    if (modal) {
        modal.style.display = 'none';
        currentPositionId = null;
    }
}

// 点击模态框外部关闭（已合并到统一的处理函数中）

// 面试登记表相关函数
function openRegistrationFormModal(interviewId) {
    fetch(`/api/interviews/${interviewId}`)
        .then(response => response.json())
        .then(result => {
            if (result.success) {
                const data = result.data;
                const modal = document.getElementById('registrationFormModal');
                const body = document.getElementById('registrationFormModalBody');
                if (!modal || !body) return;

                // 获取关联的简历信息
                fetch(`/api/resumes/${data.resume_id}`)
                    .then(res => res.json())
                    .then(resumeResult => {
                        const resume = resumeResult.success ? resumeResult.data : null;
                        
                        // 构建表单HTML
                        const baseUrl = window.location.origin;
                        const inviteLink = data.registration_form_token 
                            ? `${baseUrl}/registration-form?token=${data.registration_form_token}` 
                            : '';
                        
                        body.innerHTML = `
                            <form id="registrationForm" onsubmit="saveRegistrationForm(${data.id}); return false;">
                                <div class="form-group">
                                    <label>邀请填写链接</label>
                                    <div style="display: flex; gap: 8px;">
                                        <input type="text" id="reg_invite_link" class="form-input" value="${inviteLink}" readonly>
                                        <button type="button" class="btn btn-secondary" onclick="generateRegistrationFormLink(${data.id})">生成链接</button>
                                        <button type="button" class="btn btn-secondary" onclick="copyLink('reg_invite_link')">复制链接</button>
                                    </div>
                                </div>
                                
                                <div class="form-group">
                                    <label>姓名 <span class="required">*</span></label>
                                    <input type="text" id="reg_name" class="form-input" value="${escapeHtml(data.name || '')}" readonly>
                                </div>
                                
                                <div class="form-group">
                                    <label>填写日期 <span class="required">*</span></label>
                                    <input type="text" id="reg_fill_date" class="form-input" value="${escapeHtml(data.registration_form_fill_date || new Date().toISOString().split('T')[0])}" readonly>
                                </div>
                                
                                <div class="form-group">
                                    <label>联系方式 <span class="required">*</span></label>
                                    <input type="text" id="reg_contact" class="form-input" value="${escapeHtml(data.registration_form_contact || (resume ? resume.phone || '' : ''))}" required>
                                </div>
                                
                                <div class="form-group">
                                    <label>邮箱 <span class="required">*</span></label>
                                    <input type="email" id="reg_email" class="form-input" value="${escapeHtml(data.registration_form_email || (resume ? resume.email || '' : ''))}" required>
                                </div>
                                
                                <div class="form-group">
                                    <label>出生日期 <span class="required">*</span></label>
                                    <input type="date" id="reg_birth_date" class="form-input" value="${escapeHtml(data.registration_form_birth_date || (resume && resume.birth_year ? resume.birth_year + '-01-01' : ''))}" required>
                                </div>
                                
                                <div class="form-group">
                                    <label>民族 <span class="required">*</span></label>
                                    <input type="text" id="reg_ethnicity" class="form-input" value="${escapeHtml(data.registration_form_ethnicity || '')}" required>
                                </div>
                                
                                <div class="form-group">
                                    <label>婚姻状况 <span class="required">*</span></label>
                                    <select id="reg_marital_status" class="form-select" required>
                                        <option value="">请选择</option>
                                        <option value="未婚" ${data.registration_form_marital_status === '未婚' ? 'selected' : ''}>未婚</option>
                                        <option value="已婚" ${data.registration_form_marital_status === '已婚' ? 'selected' : ''}>已婚</option>
                                        <option value="离异" ${data.registration_form_marital_status === '离异' ? 'selected' : ''}>离异</option>
                                    </select>
                                </div>
                                
                                <div class="form-group">
                                    <label>有无子女 <span class="required">*</span></label>
                                    <select id="reg_has_children" class="form-select" required>
                                        <option value="">请选择</option>
                                        <option value="有" ${data.registration_form_has_children === '有' ? 'selected' : ''}>有</option>
                                        <option value="无" ${data.registration_form_has_children === '无' ? 'selected' : ''}>无</option>
                                    </select>
                                </div>
                                
                                <div class="form-group">
                                    <label>籍贯 <span class="required">*</span></label>
                                    <input type="text" id="reg_origin" class="form-input" value="${escapeHtml(data.registration_form_origin || '')}" required>
                                </div>
                                
                                <div class="form-group">
                                    <label>身份证号（选填）</label>
                                    <input type="text" id="reg_id_card" class="form-input" value="${escapeHtml(data.registration_form_id_card || '')}">
                                </div>
                                
                                <div class="form-group">
                                    <label>首次工作时间 <span class="required">*</span></label>
                                    <input type="date" id="reg_first_work_date" class="form-input" value="${escapeHtml(data.registration_form_first_work_date || '')}" required>
                                </div>
                                
                                <div class="form-group">
                                    <label>近两份工作经历 <span class="required">*</span></label>
                                    <div class="work-exp-header" style="display: flex; gap: 8px; margin-bottom: 8px; font-weight: bold; font-size: 14px;">
                                        <span style="flex: 1;">公司名称</span>
                                        <span style="flex: 1;">岗位</span>
                                        <span style="flex: 1;">开始时间</span>
                                        <span style="flex: 1;">结束时间</span>
                                    </div>
                                    <div id="reg_work_experience_container">
                                        ${renderWorkExperienceInputs(parseWorkExperiences(data.registration_form_recent_work_experience || (resume && resume.work_experience ? resume.work_experience.slice(0, 2) : [])))}
                                    </div>
                                </div>
                                
                                <div class="form-group">
                                    <label>最高学历院校及专业及起始时间 <span class="required">*</span></label>
                                    <textarea id="reg_education" class="form-textarea" rows="3" required>${escapeHtml(data.registration_form_education || (resume ? `${resume.school || ''} ${resume.major || ''}` : ''))}</textarea>
                                </div>
                                
                                <div class="form-group">
                                    <label>个人爱好及特长 <span class="required">*</span></label>
                                    <textarea id="reg_hobbies" class="form-textarea" rows="3" required>${escapeHtml(data.registration_form_hobbies || '')}</textarea>
                                </div>
                                
                                <div class="form-group">
                                    <label>原月薪 <span class="required">*</span></label>
                                    <input type="text" id="reg_current_salary" class="form-input" value="${escapeHtml(data.registration_form_current_salary || '')}" required>
                                </div>
                                
                                <div class="form-group">
                                    <label>期望月薪 <span class="required">*</span></label>
                                    <input type="text" id="reg_expected_salary" class="form-input" value="${escapeHtml(data.registration_form_expected_salary || '')}" required>
                                </div>
                                
                                <div class="form-group">
                                    <label>最快到岗时间 <span class="required">*</span></label>
                                    <input type="date" id="reg_available_date" class="form-input" value="${escapeHtml(data.registration_form_available_date || '')}" required>
                                </div>
                                
                                <div class="form-group">
                                    <label>现住址 <span class="required">*</span></label>
                                    <div class="address-row">
                                        <select id="reg_address_province" class="form-select" required></select>
                                        <select id="reg_address_city" class="form-select" required></select>
                                        <select id="reg_address_district" class="form-select" required></select>
                                    </div>
                                    <input type="text" id="reg_address_detail" class="form-input" value="${escapeHtml(data.registration_form_address_detail || '')}" required placeholder="详细地址">
                                </div>
                                
                                <div class="form-group">
                                    <label>能否出差 <span class="required">*</span></label>
                                    <select id="reg_can_travel" class="form-select" required>
                                        <option value="">请选择</option>
                                        <option value="是" ${data.registration_form_can_travel === '是' ? 'selected' : ''}>是</option>
                                        <option value="否" ${data.registration_form_can_travel === '否' ? 'selected' : ''}>否</option>
                                    </select>
                                </div>
                                
                                <div class="form-group">
                                    <label>考虑新公司的主要因素（请按重要性排序，拖拽调整顺序） <span class="required">*</span></label>
                                    <ul id="reg_consideration_factors" class="sortable-list" style="font-size: 12px;">
                                        ${renderConsiderationFactors(data.registration_form_consideration_factors)}
                                    </ul>
                                </div>
                                
                                <div class="form-actions">
                                    <button type="submit" class="btn btn-primary">保存</button>
                                    <button type="button" class="btn btn-secondary" onclick="closeRegistrationFormModal()">关闭</button>
                                </div>
                            </form>
                        `;
                        
                        if (typeof Sortable !== 'undefined') {
                            new Sortable(document.getElementById('reg_consideration_factors'), {
                                animation: 150,
                                handle: '.sortable-item'
                            });
                        }
                        initAddressSelects('reg_', data.registration_form_address_province || '', data.registration_form_address_city || '', data.registration_form_address_district || '');
                        modal.style.display = 'block';
                    })
                    .catch(error => {
                        console.error('获取简历信息失败:', error);
                        alert('获取简历信息失败');
                    });
            } else {
                alert('获取面试记录失败：' + (result.message || '未知错误'));
            }
        })
        .catch(error => {
            console.error('获取面试记录失败:', error);
            alert('获取面试记录失败，请稍后再试');
        });
}

function parseWorkExperiences(value) {
    if (!value) return [];
    if (Array.isArray(value)) return value;
    if (typeof value === 'string') {
        try {
            const parsed = JSON.parse(value);
            if (Array.isArray(parsed)) {
                return parsed;
            }
        } catch (e) {
            console.error('解析工作经历失败:', e);
        }
    }
    return [];
}

function renderWorkExperienceInputs(workExperiences) {
    if (!workExperiences || workExperiences.length === 0) {
        return '<div class="work-exp-item" style="display: flex; gap: 8px; margin-bottom: 8px;"><input type="text" placeholder="公司名称" class="form-input" style="flex: 1;"><input type="text" placeholder="岗位" class="form-input" style="flex: 1;"><input type="date" placeholder="开始时间" class="form-input" style="flex: 1;"><input type="date" placeholder="结束时间" class="form-input" style="flex: 1;"></div>';
    }
    return workExperiences.map(exp => {
        const company = escapeHtml(exp.company || '');
        const position = escapeHtml(exp.position || '');
        const startYear = exp.start_year ? (exp.start_year + '-01-01') : '';
        const endYear = exp.end_year ? (exp.end_year + '-01-01') : '';
        return `<div class="work-exp-item" style="display: flex; gap: 8px; margin-bottom: 8px;"><input type="text" placeholder="公司名称" class="form-input" value="${company}" style="flex: 1;"><input type="text" placeholder="岗位" class="form-input" value="${position}" style="flex: 1;"><input type="date" placeholder="开始时间" class="form-input" value="${startYear}" style="flex: 1;"><input type="date" placeholder="结束时间" class="form-input" value="${endYear}" style="flex: 1;"></div>`;
    }).join('');
}

function renderConsiderationFactors(factorsJson) {
    const defaultFactors = [
        '公司前景',
        '团队氛围',
        '薪酬福利',
        '人际关系',
        '文化价值观',
        '晋升机会',
        '领导风格'
    ];
    
    let factors = defaultFactors;
    if (factorsJson) {
        try {
            const parsed = JSON.parse(factorsJson);
            if (Array.isArray(parsed)) {
                factors = parsed;
            }
        } catch (e) {
            // 如果解析失败，使用默认顺序
        }
    }
    
    return factors.map((factor, index) => 
        `<li class="sortable-item" data-factor="${escapeHtml(factor)}" style="font-size: 12px; padding: 8px; margin: 5px 0; background: #f8f9fa; border: 1px solid #ddd; border-radius: 4px; cursor: move;">${index + 1}. ${escapeHtml(factor)}</li>`
    ).join('');
}

function closeRegistrationFormModal() {
    const modal = document.getElementById('registrationFormModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

function saveRegistrationForm(interviewId) {
    const form = document.getElementById('registrationForm');
    if (!form) return;
    
    // 收集工作经历
    const workExpItems = form.querySelectorAll('.work-exp-item');
    const workExperiences = Array.from(workExpItems).map(item => {
        const inputs = item.querySelectorAll('input');
        return {
            company: inputs[0]?.value || '',
            position: inputs[1]?.value || '',
            start_year: inputs[2]?.value ? parseInt(inputs[2].value.split('-')[0]) : null,
            end_year: inputs[3]?.value ? parseInt(inputs[3].value.split('-')[0]) : null
        };
    }).filter(exp => exp.company || exp.position);
    
    // 收集考虑因素排序
    const factorItems = form.querySelectorAll('#reg_consideration_factors .sortable-item');
    const factors = Array.from(factorItems).map(item => item.getAttribute('data-factor'));
    
    const data = {
        registration_form_fill_date: document.getElementById('reg_fill_date')?.value || new Date().toISOString().split('T')[0],
        registration_form_contact: document.getElementById('reg_contact')?.value || '',
        registration_form_email: document.getElementById('reg_email')?.value || '',
        registration_form_birth_date: document.getElementById('reg_birth_date')?.value || '',
        registration_form_ethnicity: document.getElementById('reg_ethnicity')?.value || '',
        registration_form_marital_status: document.getElementById('reg_marital_status')?.value || '',
        registration_form_has_children: document.getElementById('reg_has_children')?.value || '',
        registration_form_origin: document.getElementById('reg_origin')?.value || '',
        registration_form_id_card: document.getElementById('reg_id_card')?.value || '',
        registration_form_first_work_date: document.getElementById('reg_first_work_date')?.value || '',
        registration_form_recent_work_experience: workExperiences,
        registration_form_education: document.getElementById('reg_education')?.value || '',
        registration_form_hobbies: document.getElementById('reg_hobbies')?.value || '',
        registration_form_current_salary: document.getElementById('reg_current_salary')?.value || '',
        registration_form_expected_salary: document.getElementById('reg_expected_salary')?.value || '',
        registration_form_available_date: document.getElementById('reg_available_date')?.value || '',
        registration_form_address_province: document.getElementById('reg_address_province')?.value || '',
        registration_form_address_city: document.getElementById('reg_address_city')?.value || '',
        registration_form_address_district: document.getElementById('reg_address_district')?.value || '',
        registration_form_address_detail: document.getElementById('reg_address_detail')?.value || '',
        registration_form_can_travel: document.getElementById('reg_can_travel')?.value || '',
        registration_form_consideration_factors: JSON.stringify(factors)
    };
    
    fetch(`/api/interviews/${interviewId}/registration-form`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            alert('保存成功');
            loadInterviews();
            closeRegistrationFormModal();
        } else {
            alert('保存失败：' + (result.message || '未知错误'));
        }
    })
    .catch(error => {
        console.error('保存失败:', error);
        alert('保存失败，请稍后再试');
    });
}

function generateRegistrationFormLink(interviewId) {
    fetch(`/api/interviews/${interviewId}/registration-form-link`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            const baseUrl = window.location.origin;
            const linkInput = document.getElementById('reg_invite_link');
            if (linkInput) {
                linkInput.value = `${baseUrl}/registration-form?token=${result.data.token}`;
            }
            alert('链接生成成功');
        } else {
            alert('生成链接失败：' + (result.message || '未知错误'));
        }
    })
    .catch(error => {
        console.error('生成链接失败:', error);
        alert('生成链接失败，请重试');
    });
}


