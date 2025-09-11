// 문제지 편집 모듈

// 문제지 데이터 검증 함수
function validateWorksheetData(worksheetData, answerData) {
    const errors = [];
    
    // 기본 정보 검증
    if (!worksheetData.worksheet_name) {
        errors.push('문제지 이름이 필요합니다');
    }
    
    if (!worksheetData.worksheet_level) {
        errors.push('학교급 정보가 필요합니다');
    }
    
    if (!worksheetData.grade && !worksheetData.worksheet_grade) {
        errors.push('학년 정보가 필요합니다');
    }
    
    if (!worksheetData.total_questions || worksheetData.total_questions <= 0) {
        errors.push('총 문제 수가 필요합니다');
    }
    
    // 문제 데이터 검증
    if (!worksheetData.questions || worksheetData.questions.length === 0) {
        errors.push('문제가 최소 1개 이상 필요합니다');
    } else {
        worksheetData.questions.forEach((question, index) => {
            if (!question.question_id) {
                errors.push(`${index + 1}번 문제의 ID가 필요합니다`);
            }
            if (!question.question_text) {
                errors.push(`${index + 1}번 문제의 내용이 필요합니다`);
            }
            if (!question.question_type) {
                errors.push(`${index + 1}번 문제의 유형이 필요합니다`);
            }
        });
    }
    
    // 답안 데이터 검증 (있는 경우)
    if (answerData && answerData.questions) {
        answerData.questions.forEach((answer, index) => {
            if (!answer.question_id) {
                errors.push(`${index + 1}번 답안의 문제 ID가 필요합니다`);
            }
            if (!answer.correct_answer) {
                errors.push(`${index + 1}번 답안의 정답이 필요합니다`);
            }
        });
    }
    
    return errors;
}

// 문제지 저장 함수
async function saveWorksheet() {
    const state = window.getGlobalState();
    
    if (!state.currentWorksheetData) {
        alert('저장할 문제지 데이터가 없습니다.');
        return;
    }
    
    const worksheetName = document.getElementById('worksheetNameInput').value.trim();
    if (!worksheetName) {
        alert('문제지 이름을 입력하세요.');
        return;
    }
    
    // 문제지 이름 업데이트
    state.currentWorksheetData.worksheet_name = worksheetName;
    
    // 데이터 검증
    const validationErrors = validateWorksheetData(state.currentWorksheetData, state.currentAnswerData);
    if (validationErrors.length > 0) {
        alert('데이터 검증 실패:\n' + validationErrors.join('\n'));
        return;
    }
    
    try {
        const saveBtn = document.getElementById('saveWorksheetBtn');
        const saveResult = document.getElementById('saveResult');
        
        // 저장 시작
        saveBtn.disabled = true;
        saveBtn.innerHTML = '💾 저장 중...';
        saveResult.style.display = 'block';
        saveResult.innerHTML = '<div style="color: #007bff;">📝 문제지 데이터 검증 완료, 저장 중...</div>';
        
        const saveData = {
            worksheet_data: state.currentWorksheetData,
            answer_data: state.currentAnswerData
        };
        
        // 저장 진행 상황 표시
        saveResult.innerHTML = '<div style="color: #007bff;">🔄 서버에 데이터 전송 중...</div>';
        
        const result = await apiService.saveWorksheet(saveData);
        
        if (result.status === 'success') {
            // 저장 성공
            saveResult.innerHTML = '<div style="color: #28a745;">✅ 문제지가 성공적으로 저장되었습니다!</div>';
            
            // 2초 후 성공 메시지와 함께 목록으로 이동
            setTimeout(() => {
                showTab('worksheets-tab');
                loadWorksheets();
                
                // 전역 상태 초기화
                state.currentWorksheetData = null;
                state.currentAnswerData = null;
                window.setGlobalState(state);
            }, 2000);
            
        } else {
            throw new Error(result.message || '저장 실패');
        }
        
    } catch (error) {
        console.error('문제지 저장 오류:', error);
        
        // 오류 메시지 표시
        const saveResult = document.getElementById('saveResult');
        saveResult.innerHTML = `<div style="color: #dc3545;">❌ 저장 실패: ${error.message}</div>`;
        
        // 3초 후 오류 메시지 숨기기
        setTimeout(() => {
            saveResult.style.display = 'none';
        }, 3000);
        
    } finally {
        const saveBtn = document.getElementById('saveWorksheetBtn');
        saveBtn.disabled = false;
        saveBtn.innerHTML = '📁 문제지 저장하기';
    }
}

// 문제지 목록 로드
async function loadWorksheets() {
    try {
        const worksheets = await apiService.getWorksheets();
        const content = document.getElementById('worksheets-content');
        
        if (!worksheets || worksheets.length === 0) {
            content.innerHTML = `
                <div style="text-align: center; padding: 40px; color: #6c757d;">
                    <h3>📋 저장된 문제지가 없습니다</h3>
                    <p>아직 저장된 문제지가 없습니다. 문제를 생성해보세요!</p>
                </div>
            `;
            return;
        }
        
        let html = `
            <div style="background: white; padding: 30px; border-radius: 15px; box-shadow: 0 8px 25px rgba(0,0,0,0.1);">
                <h2 style="color: #495057; margin-bottom: 30px; text-align: center;">📚 저장된 문제지 목록</h2>
                <div style="display: grid; gap: 20px;">`;
        
        worksheets.forEach(worksheet => {
            const createdDate = new Date(worksheet.created_at).toLocaleDateString();
            
            html += `
                <div style="border: 2px solid #e9ecef; border-radius: 12px; padding: 20px; background: #f8f9fa; transition: all 0.3s ease;" 
                     onmouseover="this.style.borderColor='#007bff'; this.style.boxShadow='0 4px 15px rgba(0,123,255,0.2)'" 
                     onmouseout="this.style.borderColor='#e9ecef'; this.style.boxShadow='none'">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                        <div>
                            <h3 style="margin: 0; color: #495057;">${worksheet.worksheet_name}</h3>
                            <p style="margin: 5px 0 0 0; color: #6c757d; font-size: 14px;">
                                ${worksheet.school_level} ${worksheet.grade}학년 | ${worksheet.total_questions}문제 | ${worksheet.duration}분
                            </p>
                        </div>
                        <div style="text-align: right;">
                            <div style="color: #6c757d; font-size: 14px;">${createdDate}</div>
                        </div>
                    </div>
                    <div style="display: flex; gap: 10px; margin-top: 15px;">
                        <button onclick="solveWorksheet('${worksheet.worksheet_id}')" class="btn btn-primary" style="padding: 8px 16px; font-size: 14px;">
                            ✏️ 문제 풀기
                        </button>
                        <button onclick="editWorksheet('${worksheet.worksheet_id}')" class="btn btn-secondary" style="padding: 8px 16px; font-size: 14px;">
                            ✏️ 편집
                        </button>
                        <button onclick="deleteWorksheet('${worksheet.worksheet_id}')" class="btn btn-danger" style="padding: 8px 16px; font-size: 14px;">
                            🗑️ 삭제
                        </button>
                    </div>
                </div>`;
        });
        
        html += `
                </div>
            </div>`;
        
        content.innerHTML = html;
        
    } catch (error) {
        console.error('문제지 목록 조회 오류:', error);
        document.getElementById('worksheets-content').innerHTML = `
            <div style="text-align: center; padding: 40px; color: #dc3545;">
                <h3>❌ 오류 발생</h3>
                <p>문제지 목록을 불러오는 중 오류가 발생했습니다.</p>
                <p>${error.message}</p>
            </div>
        `;
    }
}

// 문제지 편집
async function editWorksheet(worksheetId) {
    try {
        const worksheet = await apiService.getWorksheetForEditing(worksheetId);
        
        if (worksheet.status === 'success') {
            // 전역 변수에 저장
            const state = window.getGlobalState();
            state.currentEditingWorksheet = worksheet.worksheet_data;
            state.isEditMode = true;
            window.setGlobalState(state);
            
            // 편집기로 이동
            showTab('edit-tab');
            
            // 편집기 초기화
            if (window.initWorksheetEditor) {
                window.initWorksheetEditor(worksheet.worksheet_data);
            }
        } else {
            throw new Error(worksheet.message || '문제지 조회 실패');
        }
        
    } catch (error) {
        console.error('문제지 편집 오류:', error);
        alert(`문제지 편집 중 오류가 발생했습니다: ${error.message}`);
    }
}

// 문제지 삭제
function deleteWorksheet(worksheetId) {
    if (confirm('정말로 이 문제지를 삭제하시겠습니까?')) {
        alert(`문제지 삭제 기능은 곧 구현됩니다! (문제지 ID: ${worksheetId})`);
    }
}

// 문제 풀기
async function solveWorksheet(worksheetId) {
    try {
        const worksheet = await apiService.getWorksheetForSolving(worksheetId);
        
        if (worksheet.status === 'success') {
            // 전역 변수에 저장
            const state = window.getGlobalState();
            state.currentSolvingWorksheet = worksheet.worksheet_data;
            state.studentAnswers = {};
            state.solveStartTime = new Date();
            window.setGlobalState(state);
            
            // 문제 풀기 탭으로 이동
            showTab('solve-tab');
            
            // 타이머 시작
            startSolveTimer();
            
            // 문제지 렌더링
            renderSolveWorksheet(worksheet.worksheet_data);
        } else {
            throw new Error(worksheet.message || '문제지 조회 실패');
        }
        
    } catch (error) {
        console.error('문제 풀기 오류:', error);
        alert(`문제 풀기 중 오류가 발생했습니다: ${error.message}`);
    }
}

// 문제 풀기 화면 렌더링
function renderSolveWorksheet(worksheetData) {
    const content = document.getElementById('solve-content');
    
    let html = `
        <div style="background: white; padding: 30px; border-radius: 15px; box-shadow: 0 8px 25px rgba(0,0,0,0.1);">
            <div style="text-align: center; margin-bottom: 30px; padding: 25px; background: linear-gradient(135deg, #007bff, #0056b3); color: white; border-radius: 12px;">
                <h1 style="margin: 0; font-size: 2rem;">✏️ 문제 풀기</h1>
                <div style="margin-top: 15px; font-size: 1.1rem;">
                    <div><strong>문제지:</strong> ${worksheetData.worksheet_name}</div>
                    <div style="margin-top: 8px;"><strong>총 문제:</strong> ${worksheetData.total_questions}문제</div>
                    <div style="margin-top: 8px;"><strong>소요시간:</strong> ${worksheetData.worksheet_duration}분</div>
                </div>
            </div>
            
            <div id="solve-timer" style="text-align: center; margin-bottom: 30px; padding: 15px; background: #f8f9fa; border-radius: 8px; font-size: 1.2rem; font-weight: bold; color: #007bff;">
                ⏱️ 경과 시간: 00:00
            </div>`;
    
    // 지문과 문제를 연결하여 렌더링
    let renderedPassages = new Set();
    let renderedExamples = new Set();
    
    if (worksheetData.questions && worksheetData.questions.length > 0) {
        worksheetData.questions.forEach((question, index) => {
            // 관련 지문이 있고 아직 렌더링되지 않았다면 먼저 렌더링
            if (question.question_passage_id && !renderedPassages.has(question.question_passage_id)) {
                const passage = worksheetData.passages?.find(p => p.passage_id === question.question_passage_id);
                if (passage) {
                    html += `
                        <div style="background: #f8f9fa; border: 2px solid #007bff; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
                            <h3 style="color: #007bff; margin-bottom: 15px;">📖 지문</h3>
                            <div style="line-height: 1.8; text-align: justify; padding: 15px; background: white; border-radius: 5px;">
                                ${passage.passage_content || '지문 내용 없음'}
                            </div>
                        </div>`;
                    renderedPassages.add(question.question_passage_id);
                }
            }
            
            // 문제 렌더링
            html += `
                <div style="background: white; border: 2px solid #e9ecef; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
                    <div style="display: flex; align-items: center; margin-bottom: 15px;">
                        <span style="background: #dc3545; color: white; padding: 5px 12px; border-radius: 20px; font-weight: bold; margin-right: 15px;">
                            ${question.question_id || (index + 1)}번
                        </span>
                        <div style="display: flex; gap: 10px;">
                            <span style="background: #007bff; color: white; padding: 3px 8px; border-radius: 12px; font-size: 12px;">
                                ${question.question_subject || '영어'}
                            </span>
                            <span style="background: #6f42c1; color: white; padding: 3px 8px; border-radius: 12px; font-size: 12px;">
                                ${question.question_difficulty || '중'}
                            </span>
                            <span style="background: #20c997; color: white; padding: 3px 8px; border-radius: 12px; font-size: 12px;">
                                ${question.question_type || '객관식'}
                            </span>
                        </div>
                    </div>
                    
                    <div style="margin-bottom: 15px;">
                        <p style="font-size: 1.1rem; line-height: 1.6; margin: 0; font-weight: 500;">${question.question_text}</p>
                    </div>`;
            
            // 객관식 선택지 표시
            if (question.question_type === '객관식' && question.question_choices && question.question_choices.length > 0) {
                html += `<div style="margin-left: 20px;">`;
                question.question_choices.forEach((choice, choiceIndex) => {
                    const choiceLabel = String.fromCharCode(9312 + choiceIndex); // ① ② ③ ④ ⑤
                    const choiceId = `choice_${question.question_id}_${choiceIndex}`;
                    html += `
                        <label style="display: block; margin: 8px 0; line-height: 1.5; cursor: pointer;">
                            <input type="radio" name="question_${question.question_id}" value="${choiceIndex + 1}" id="${choiceId}" 
                                   onchange="updateStudentAnswer('${question.question_id}', '${choiceIndex + 1}')" style="margin-right: 8px;">
                            ${choiceLabel} ${choice}
                        </label>`;
                });
                html += `</div>`;
            }
            
            // 주관식/서술형 답안 입력
            if (question.question_type === '단답형' || question.question_type === '주관식') {
                html += `
                    <div style="margin-top: 15px;">
                        <label for="answer_${question.question_id}" style="display: block; margin-bottom: 8px; font-weight: bold;">답:</label>
                        <input type="text" id="answer_${question.question_id}" 
                               onchange="updateStudentAnswer('${question.question_id}', this.value)"
                               style="width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 4px; font-size: 16px;">
                    </div>`;
            } else if (question.question_type === '서술형') {
                html += `
                    <div style="margin-top: 15px;">
                        <label for="answer_${question.question_id}" style="display: block; margin-bottom: 8px; font-weight: bold;">답안:</label>
                        <textarea id="answer_${question.question_id}" 
                                  onchange="updateStudentAnswer('${question.question_id}', this.value)"
                                  style="width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 4px; font-size: 16px; min-height: 100px; resize: vertical;"></textarea>
                    </div>`;
            }
            
            html += `</div>`;
        });
    }
    
    html += `
            <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6;">
                <button onclick="submitAnswers()" class="btn btn-success" style="padding: 12px 30px; font-size: 16px; font-weight: bold;">
                    📝 답안 제출
                </button>
            </div>
        </div>`;
    
    content.innerHTML = html;
}

// 학생 답안 업데이트
function updateStudentAnswer(questionId, answer) {
    const state = window.getGlobalState();
    state.studentAnswers[questionId] = answer;
    window.setGlobalState(state);
}

// 타이머 시작
function startSolveTimer() {
    const state = window.getGlobalState();
    
    if (state.solveTimer) {
        clearInterval(state.solveTimer);
    }
    
    state.solveTimer = setInterval(() => {
        const now = new Date();
        const elapsed = Math.floor((now - state.solveStartTime) / 1000);
        const minutes = Math.floor(elapsed / 60);
        const seconds = elapsed % 60;
        
        const timerElement = document.getElementById('solve-timer');
        if (timerElement) {
            timerElement.innerHTML = `⏱️ 경과 시간: ${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }
    }, 1000);
    
    window.setGlobalState(state);
}

// 답안 제출
async function submitAnswers() {
    const state = window.getGlobalState();
    
    if (!state.currentSolvingWorksheet) {
        alert('제출할 문제지가 없습니다.');
        return;
    }
    
    if (!state.studentAnswers || Object.keys(state.studentAnswers).length === 0) {
        alert('답안을 입력해주세요.');
        return;
    }
    
    // 학생 이름 입력
    const studentName = prompt('학생 이름을 입력하세요:');
    if (!studentName || studentName.trim() === '') {
        alert('학생 이름을 입력해주세요.');
        return;
    }
    
    try {
        // 제출 버튼 비활성화
        const submitBtn = document.querySelector('button[onclick="submitAnswers()"]');
        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '📤 제출 중...';
        }
        
        const submitData = {
            worksheet_id: state.currentSolvingWorksheet.worksheet_id,
            student_name: studentName.trim(),
            answers: state.studentAnswers,
            completion_time: Math.floor((new Date() - state.solveStartTime) / 1000)
        };
        
        console.log('답안 제출 데이터:', submitData);
        
        const result = await apiService.submitAnswers(submitData);
        
        if (result.status === 'success') {
            // 성공 메시지
            alert(`답안이 제출되었습니다!\n\n결과 ID: ${result.result_id}\n\n채점 결과를 확인하세요.`);
            
            // 타이머 정지
            if (state.solveTimer) {
                clearInterval(state.solveTimer);
                state.solveTimer = null;
            }
            
            // 상태 초기화
            state.currentSolvingWorksheet = null;
            state.studentAnswers = {};
            state.solveStartTime = null;
            window.setGlobalState(state);
            
            // 채점 결과 탭으로 이동
            showTab('result-tab');
            displayGradingResults();
        } else {
            throw new Error(result.message || '답안 제출 실패');
        }
        
    } catch (error) {
        console.error('답안 제출 오류:', error);
        alert(`답안 제출 중 오류가 발생했습니다: ${error.message}`);
    } finally {
        // 제출 버튼 복원
        const submitBtn = document.querySelector('button[onclick="submitAnswers()"]');
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '📝 답안 제출';
        }
    }
}

// 전역 함수로 노출
window.saveWorksheet = saveWorksheet;
window.loadWorksheets = loadWorksheets;
window.editWorksheet = editWorksheet;
window.deleteWorksheet = deleteWorksheet;
window.solveWorksheet = solveWorksheet;
window.renderSolveWorksheet = renderSolveWorksheet;
window.updateStudentAnswer = updateStudentAnswer;
window.startSolveTimer = startSolveTimer;
window.submitAnswers = submitAnswers;
