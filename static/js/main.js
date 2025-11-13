// 全局变量
let currentPage = 1;
let perPage = 10;
let totalPages = 1;
let sortBy = 'upload_time';
let sortOrder = 'desc';
let selectedResumes = new Set();
let currentResumeData = null;

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

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    initUpload();
    loadResumes();
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
    uploadFiles(files);
}

// 上传文件
function uploadFiles(files) {
    const formData = new FormData();
    for (let file of files) {
        formData.append('file', file);
    }
    
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
            progressText.textContent = '上传成功，正在解析...';
            setTimeout(() => {
                progressDiv.style.display = 'none';
                loadResumes();
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
    
    const search = document.getElementById('searchInput').value;
    const gender = document.getElementById('genderFilter').value;
    const education = document.getElementById('educationFilter').value;
    
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
                displayResumes(data.data);
                totalPages = Math.ceil(data.total / perPage);
                updatePagination();
            }
        })
        .catch(error => {
            console.error('Error:', error);
            document.getElementById('resumeTableBody').innerHTML = 
                '<tr><td colspan="11" class="loading">加载失败，请刷新重试</td></tr>';
        });
}

// 显示简历列表
function displayResumes(resumes) {
    const tbody = document.getElementById('resumeTableBody');
    
    if (resumes.length === 0) {
        tbody.innerHTML = '<tr><td colspan="14" class="loading">暂无数据</td></tr>';
        return;
    }
    
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
        
        return `
        <tr class="${isSelected ? 'selected' : ''}">
            <td><input type="checkbox" value="${resume.id}" ${isSelected ? 'checked' : ''} onchange="toggleResume(${resume.id}, this)"></td>
            <td>${escapeHtml(resume.applied_position) || '-'}</td>
            <td>${identityCode}</td>
            <td>${duplicateDisplay}</td>
            <td>${escapeHtml(resume.name) || '-'}</td>
            <td>${escapeHtml(resume.gender) || '-'}</td>
            <td>${resume.age || '-'}</td>
            <td>${workYearsDisplay}</td>
            <td>${escapeHtml(resume.phone) || '-'}</td>
            <td>${escapeHtml(resume.email) || '-'}</td>
            <td>${escapeHtml(resume.highest_education) || '-'}</td>
            <td>
                ${escapeHtml(resume.school) || '-'}
                ${getStatusIcon(resume.school_match_status)}
            </td>
            <td>
                ${escapeHtml(resume.major) || '-'}
                ${getStatusIcon(resume.major_match_status)}
            </td>
            <td>
                <button class="btn btn-small btn-view" onclick="viewDetail(${resume.id})">查看/编辑</button>
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
    const schoolMatch = resume.school_match_status || '未校验';
    const majorMatch = resume.major_match_status || '未校验';
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
                <input id="editAppliedPosition" type="text" value="${escapeHtml(resume.applied_position || '')}">
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
            <label>学校（标准化）
                <input id="editSchool" type="text" value="${escapeHtml(resume.school || '')}">
            </label>
            <label>学校（原始）
                <input id="editSchoolOriginal" type="text" value="${escapeHtml(resume.school_original || '')}">
            </label>
            <label>专业（标准化）
                <input id="editMajor" type="text" value="${escapeHtml(resume.major || '')}">
            </label>
            <label>专业（原始）
                <input id="editMajorOriginal" type="text" value="${escapeHtml(resume.major_original || '')}">
            </label>
        </div>
        <div class="form-grid">
            <label>学校匹配状态
                <input type="text" value="${escapeHtml(schoolMatch)}" disabled>
            </label>
            <label>专业匹配状态
                <input type="text" value="${escapeHtml(majorMatch)}" disabled>
            </label>
            <label>学校置信度
                <input type="text" value="${escapeHtml(resume.school_confidence ?? '')}" disabled>
            </label>
            <label>专业置信度
                <input type="text" value="${escapeHtml(resume.major_confidence ?? '')}" disabled>
            </label>
        </div>
        <div class="detail-item">
            <div class="detail-label">最新工作经历（最多两段，只读，自动同步）</div>
            ${(() => {
                const experiences = (resume.work_experience || []).slice(0, 2);
                while (experiences.length < 2) {
                    experiences.push({ company: '', position: '', start_year: '', end_year: '' });
                }
                return experiences.map((exp, idx) => `
                    <div class="work-experience-item">
                        <label>公司
                            <input type="text" id="expCompany${idx}" value="${escapeHtml(exp.company || '')}" readonly>
                        </label>
                        <label>岗位
                            <input type="text" id="expPosition${idx}" value="${escapeHtml(exp.position || '')}" readonly>
                        </label>
                        <label>开始年份
                            <input type="number" id="expStart${idx}" value="${exp.start_year || ''}" readonly>
                        </label>
                        <label>结束年份
                            <input type="number" id="expEnd${idx}" value="${exp.end_year || ''}" readonly>
                        </label>
                    </div>
                `).join('');
            })()}
        </div>
        <div class="detail-item">
            <div class="detail-label">全部工作经历（可编辑，修改后自动同步至最新工作经历）</div>
            ${(() => {
                const allExps = resume.work_experience || [];
                if (!allExps.length) {
                    return '<div class="work-experience-item">暂无数据</div>';
                }
                return `
                    <table class="experience-table">
                        <thead>
                            <tr>
                                <th>序号</th>
                                <th>公司</th>
                                <th>岗位</th>
                                <th>开始年份</th>
                                <th>结束年份</th>
                            </tr>
                        </thead>
                        <tbody id="allWorkExperienceTable">
                            ${allExps.map((exp, idx) => `
                                <tr>
                                    <td>${idx + 1}</td>
                                    <td><input type="text" class="exp-company-input" data-index="${idx}" value="${escapeHtml(exp.company || '')}" placeholder="公司名称"></td>
                                    <td><input type="text" class="exp-position-input" data-index="${idx}" value="${escapeHtml(exp.position || '')}" placeholder="岗位名称"></td>
                                    <td><input type="number" class="exp-start-input" data-index="${idx}" value="${exp.start_year || ''}" placeholder="开始年份"></td>
                                    <td><input type="number" class="exp-end-input" data-index="${idx}" value="${exp.end_year || ''}" placeholder="结束年份（空为至今）"></td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                `;
            })()}
        </div>
        <label class="textarea-label">当前错误信息
            <textarea id="editErrorMessage" rows="3" placeholder="可选">${escapeHtml(errorMessage)}</textarea>
        </label>
        <label class="textarea-label">原始文本（只读）
            <textarea rows="10" readonly>${escapeHtml(resume.raw_text || '')}</textarea>
        </label>
        <div class="modal-actions">
            <button class="btn btn-primary" onclick="saveResume()">保存修改</button>
            <button class="btn btn-secondary" onclick="exportSingle(${resume.id})">导出Excel</button>
            <button class="btn btn-danger" onclick="deleteResume(${resume.id})">删除简历</button>
            <button class="btn btn-secondary" onclick="closeModal()">关闭</button>
        </div>
    `;
    modal.style.display = 'block';
    
    // 添加全部工作经历表格的编辑事件监听
    setupWorkExperienceEditListeners();
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
    
    // 更新最新工作经历（最多两条）
    const latestExperiences = allExperiences.slice(0, 2);
    for (let i = 0; i < 2; i++) {
        const exp = latestExperiences[i] || { company: '', position: '', start_year: '', end_year: '' };
        const companyInput = document.getElementById(`expCompany${i}`);
        const positionInput = document.getElementById(`expPosition${i}`);
        const startInput = document.getElementById(`expStart${i}`);
        const endInput = document.getElementById(`expEnd${i}`);
        
        if (companyInput) companyInput.value = exp.company || '';
        if (positionInput) positionInput.value = exp.position || '';
        if (startInput) startInput.value = exp.start_year || '';
        if (endInput) endInput.value = exp.end_year || '';
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
        school_original: document.getElementById('editSchoolOriginal').value.trim() || null,
        major: document.getElementById('editMajor').value.trim() || null,
        major_original: document.getElementById('editMajorOriginal').value.trim() || null,
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
    } else {
        // 如果表格不存在，回退到原来的逻辑（从最新工作经历读取）
        for (let i = 0; i < 2; i++) {
            const company = document.getElementById(`expCompany${i}`).value.trim();
            const position = document.getElementById(`expPosition${i}`).value.trim();
            const startInput = document.getElementById(`expStart${i}`).value;
            const endInput = document.getElementById(`expEnd${i}`).value;
            const startYear = startInput ? parseInt(startInput, 10) : null;
            const endYear = endInput ? parseInt(endInput, 10) : null;

            const hasValue = company || position || startYear !== null || endYear !== null;

            if (hasValue) {
                updatedExperiences.push({
                    company: company || null,
                    position: position || null,
                    start_year: startYear,
                    end_year: endYear,
                });
            }
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

// 点击模态框外部关闭
window.onclick = function(event) {
    const modal = document.getElementById('detailModal');
    if (event.target === modal) {
        closeModal();
    }
}

