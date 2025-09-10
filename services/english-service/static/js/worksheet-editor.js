/**
 * 문제지 편집기 전용 모듈
 * 문제지 보기, 편집, 삭제 등의 기능을 담당
 */

// 편집 모드 토글 함수
function toggleEditMode() {
    isEditMode = !isEditMode;
    
    if (currentEditingWorksheet) {
        const worksheetsList = document.getElementById('worksheets-list');
        if (worksheetsList) {
            worksheetsList.innerHTML = renderWorksheetEditor(currentEditingWorksheet);
        }
        
        // 편집 모드 변경 알림
        const mode = isEditMode ? '편집' : '보기';
        console.log(`📝 ${mode} 모드로 전환되었습니다.`);
    }
}

// 문제지 편집기 렌더링 함수
function renderWorksheetEditor(worksheetData) {
    const editModeText = isEditMode ? '편집 모드' : '보기 모드';
    const editButtonText = isEditMode ? '📖 보기 모드' : '✏️ 편집 모드';
    const editButtonStyle = isEditMode 
        ? 'background: #6c757d; color: white;' 
        : 'background: #007bff; color: white;';
    
    let html = `
        <!-- 문제지 헤더 -->
        <div style="background: linear-gradient(135deg, #007bff, #0056b3); color: white; padding: 25px; border-radius: 12px; margin-bottom: 25px; box-shadow: 0 4px 15px rgba(0,123,255,0.3);">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
                <div>
                    <h2 style="margin: 0 0 8px 0; font-size: 1.8rem;">📄 ${worksheetData.worksheet_name}</h2>
                    <div style="font-size: 0.95rem; opacity: 0.9;">
                        <span>🗓️ ${new Date(worksheetData.created_at).toLocaleDateString('ko-KR')}</span>
                        <span style="margin-left: 20px;">📊 총 ${worksheetData.total_questions}문제</span>
                        <span style="margin-left: 20px;">🎯 현재 ${editModeText}</span>
                    </div>
                </div>
                <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                    <button onclick="toggleEditMode()" 
                            style="padding: 12px 20px; border: none; border-radius: 8px; font-weight: bold; cursor: pointer; transition: all 0.3s; ${editButtonStyle}">
                        ${editButtonText}
                    </button>
                    ${isEditMode ? `
                        <button onclick="deployWorksheet('${worksheetData.worksheet_id}')" 
                                style="padding: 12px 20px; border: none; border-radius: 8px; font-weight: bold; cursor: pointer; background: #28a745; color: white;">
                            🚀 배포하기
                        </button>
                    ` : ''}
                </div>
            </div>
        </div>
    `;

    // 지문, 예문, 독립 문제들을 그룹별로 표시
    html += renderContentGroups(worksheetData);
    
    return html;
}

// 컨텐츠 그룹별 렌더링 (문제 번호 순서대로)
function renderContentGroups(worksheetData) {
    let html = '';
    let renderedGroups = new Set(); // 이미 렌더링된 그룹 추적
    
    // 문제들을 번호순으로 정렬
    const sortedQuestions = worksheetData.questions.sort((a, b) => {
        const aNum = parseInt(a.question_id);
        const bNum = parseInt(b.question_id);
        return aNum - bNum;
    });
    
    // 문제 순서대로 해당 그룹 렌더링
    sortedQuestions.forEach(question => {
        const questionId = question.question_id;
        const passageId = question.question_passage_id;
        const exampleId = question.question_example_id;
        
        // 지문 그룹 렌더링
        if (passageId && !renderedGroups.has(`passage_${passageId}`)) {
            const passage = worksheetData.passages?.find(p => p.passage_id === passageId);
            if (passage) {
                const relatedQuestions = worksheetData.questions.filter(q => q.question_passage_id === passageId);
                html += renderPassageGroup(passage, relatedQuestions);
                renderedGroups.add(`passage_${passageId}`);
            }
        }
        
        // 예문 그룹 렌더링
        else if (exampleId && !renderedGroups.has(`example_${exampleId}`)) {
            const example = worksheetData.examples?.find(e => e.example_id === exampleId);
            if (example) {
                const relatedQuestions = worksheetData.questions.filter(q => q.question_example_id === exampleId);
                html += renderExampleGroup(example, relatedQuestions);
                renderedGroups.add(`example_${exampleId}`);
            }
        }
        
        // 독립 문제 렌더링
        else if (!passageId && !exampleId && !renderedGroups.has(`standalone_${questionId}`)) {
            html += renderStandaloneQuestion(question);
            renderedGroups.add(`standalone_${questionId}`);
        }
    });
    
    return html;
}

// 지문 그룹 렌더링
function renderPassageGroup(passage, questions) {
    const editActions = isEditMode ? `
        <div style="display: flex; gap: 8px; margin-left: auto;">
            <button onclick="editPassage('${passage.passage_id}')" class="btn btn-sm btn-primary">
                ✏️ 지문편집
            </button>
            <button onclick="aiEditPassage('${passage.passage_id}')" class="btn btn-sm btn-secondary">
                🤖 AI수정
            </button>
        </div>
    ` : '';

    let html = `
        <div style="border: 2px solid #007bff; border-radius: 15px; margin-bottom: 30px; overflow: hidden; background: white; box-shadow: 0 6px 20px rgba(0,123,255,0.1);">
            <!-- 지문 헤더 -->
            <div style="background: linear-gradient(135deg, #007bff, #0056b3); color: white; padding: 20px; display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <h3 style="margin: 0; font-size: 1.4rem;">📄 지문 ${passage.passage_id}</h3>
                    <span style="font-size: 0.9rem; opacity: 0.9;">${questions.length}개 문제 연결됨</span>
                </div>
                ${editActions}
            </div>
            
            <!-- 지문 내용 -->
            <div style="padding: 25px; background: #f8f9ff;">
                <div style="background: white; padding: 20px; border-radius: 10px; border-left: 4px solid #007bff; line-height: 1.8; font-size: 15px;">
                    ${passage.original_content}
                </div>
            </div>
            
            <!-- 연관 문제들 -->
            <div style="padding: 0 25px 25px 25px; background: #f8f9ff;">
                <h4 style="color: #007bff; margin-bottom: 15px; font-size: 1.1rem;">📝 연관 문제들</h4>
                ${questions.map(question => renderQuestionInGroup(question)).join('')}
            </div>
        </div>
    `;
    
    return html;
}

// 예문 그룹 렌더링
function renderExampleGroup(example, questions) {
    const editActions = isEditMode ? `
        <div style="display: flex; gap: 8px; margin-left: auto;">
            <button onclick="editExample('${example.example_id}')" class="btn btn-sm btn-success">
                ✏️ 예문편집
            </button>
            <button onclick="aiEditExample('${example.example_id}')" class="btn btn-sm btn-secondary">
                🤖 AI수정
            </button>
        </div>
    ` : '';

    let html = `
        <div style="border: 2px solid #28a745; border-radius: 15px; margin-bottom: 30px; overflow: hidden; background: white; box-shadow: 0 6px 20px rgba(40,167,69,0.1);">
            <!-- 예문 헤더 -->
            <div style="background: linear-gradient(135deg, #28a745, #1e7e34); color: white; padding: 20px; display: flex; align-items: center; justify-content: space-between;">
                <div>
                    <h3 style="margin: 0; font-size: 1.4rem;">📝 예문 ${example.example_id}</h3>
                    <span style="font-size: 0.9rem; opacity: 0.9;">${questions.length}개 문제 연결됨</span>
                </div>
                ${editActions}
            </div>
            
            <!-- 예문 내용 -->
            <div style="padding: 25px; background: #f8fff8;">
                <div style="background: white; padding: 20px; border-radius: 10px; border-left: 4px solid #28a745; line-height: 1.8; font-size: 15px;">
                    ${example.original_content}
                </div>
            </div>
            
            <!-- 연관 문제들 -->
            <div style="padding: 0 25px 25px 25px; background: #f8fff8;">
                <h4 style="color: #28a745; margin-bottom: 15px; font-size: 1.1rem;">📝 연관 문제들</h4>
                ${questions.map(question => renderQuestionInGroup(question)).join('')}
            </div>
        </div>
    `;
    
    return html;
}

// 개별 독립 문제 렌더링
function renderStandaloneQuestion(question) {
    return `
        <div style="margin-bottom: 20px;">
            ${renderQuestionInGroup(question)}
        </div>
    `;
}

// 독립 문제들 렌더링
function renderStandaloneQuestions(questions) {
    let html = `
        <div style="border: 2px solid #6c757d; border-radius: 15px; margin-bottom: 30px; overflow: hidden; background: white; box-shadow: 0 6px 20px rgba(108,117,125,0.1);">
            <!-- 독립 문제 헤더 -->
            <div style="background: linear-gradient(135deg, #6c757d, #495057); color: white; padding: 20px;">
                <h3 style="margin: 0; font-size: 1.4rem;">🔹 독립 문제들</h3>
                <span style="font-size: 0.9rem; opacity: 0.9;">${questions.length}개 문제</span>
            </div>
            
            <!-- 독립 문제들 -->
            <div style="padding: 25px; background: #f8f9fa;">
                ${questions.map(question => renderQuestionInGroup(question)).join('')}
            </div>
        </div>
    `;
    
    return html;
}

// 그룹 내 개별 문제 렌더링
function renderQuestionInGroup(question) {
    const questionId = Array.isArray(question.question_id) ? question.question_id[0] : question.question_id;
    const questionType = Array.isArray(question.question_type) ? question.question_type[0] : question.question_type;
    
    const editActions = isEditMode ? `
        <div style="display: flex; gap: 5px; flex-wrap: wrap;">
            <button onclick="editQuestion('${questionId}')" class="btn btn-sm btn-outline-primary">
                ✏️ 문제편집
            </button>
            <button onclick="editAnswer('${questionId}')" class="btn btn-sm btn-outline-success">
                📝 정답편집
            </button>
            <button onclick="deleteQuestion('${questionId}')" class="btn btn-sm btn-outline-danger">
                🗑️ 삭제
            </button>
            <button onclick="aiEditQuestion('${questionId}')" class="btn btn-sm btn-outline-secondary">
                🤖 AI수정
            </button>
        </div>
    ` : '';

    let questionContent = '';
    
    // 문제 내용 렌더링
    questionContent += `
        <div style="background: white; border: 1px solid #dee2e6; border-radius: 8px; padding: 20px; margin-bottom: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 15px;">
                <div style="font-weight: bold; color: #495057; font-size: 1.1rem;">
                    ${questionId}번. ${questionType}
                </div>
                ${editActions}
            </div>
            
            <!-- 문제 텍스트 -->
            <div style="margin-bottom: 15px; line-height: 1.6; padding: 10px; background: #f8f9fa; border-radius: 6px; border-left: 4px solid #007bff;">
                <strong style="color: #007bff;">📝 문제:</strong>
                <div style="margin-top: 8px;">${question.question_text}</div>
            </div>
    `;
    
    // 선택지 표시 (객관식인 경우)
    if (questionType === '객관식' && question.choices) {
        questionContent += `
            <div style="margin-bottom: 15px; padding: 10px; background: #f0f8ff; border-radius: 6px; border-left: 4px solid #6c757d;">
                <strong style="color: #6c757d;">📋 선택지:</strong>
                <div style="margin-top: 8px; margin-left: 15px;">
        `;
        question.choices.forEach((choice, index) => {
            const choiceLabel = String.fromCharCode(9312 + index); // ① ② ③ ④ ⑤
            questionContent += `<div style="margin: 5px 0;">${choiceLabel} ${choice}</div>`;
        });
        questionContent += '</div></div>';
    }
    
    // 정답 표시 (항상 표시)
    questionContent += `
        <div style="margin-bottom: 15px; padding: 10px; background: #e8f5e8; border-radius: 6px; border-left: 4px solid #28a745;">
            <strong style="color: #28a745;">✅ 정답:</strong>
            <div style="margin-top: 8px; font-weight: 600; color: #155724;">
                ${question.correct_answer || '정답 정보 없음'}
            </div>
        </div>
    `;
    
    // 해설 표시 (항상 표시)
    if (question.explanation) {
        questionContent += `
            <div style="margin-bottom: 15px; padding: 10px; background: #fff3cd; border-radius: 6px; border-left: 4px solid #ffc107;">
                <strong style="color: #856404;">💡 해설:</strong>
                <div style="margin-top: 8px; line-height: 1.6; color: #856404;">
                    ${question.explanation}
                </div>
            </div>
        `;
    } else {
        questionContent += `
            <div style="margin-bottom: 15px; padding: 10px; background: #f8d7da; border-radius: 6px; border-left: 4px solid #dc3545;">
                <strong style="color: #721c24;">💡 해설:</strong>
                <div style="margin-top: 8px; color: #721c24; font-style: italic;">
                    해설이 없습니다.
                </div>
            </div>
        `;
    }
    
    // 학습 포인트 표시 (있는 경우)
    if (question.learning_point) {
        questionContent += `
            <div style="margin-bottom: 15px; padding: 10px; background: #e2e3e5; border-radius: 6px; border-left: 4px solid #6c757d;">
                <strong style="color: #495057;">🎯 학습 포인트:</strong>
                <div style="margin-top: 8px; line-height: 1.6; color: #495057;">
                    ${question.learning_point}
                </div>
            </div>
        `;
    }
    
    questionContent += '</div>';
    
    return questionContent;
}

// 편집 액션 함수들 (기본 구조만)
function editPassage(passageId) {
    alert(`지문 ${passageId} 편집 기능 (구현 예정)`);
}

function editExample(exampleId) {
    alert(`예문 ${exampleId} 편집 기능 (구현 예정)`);
}

function editQuestion(questionId) {
    alert(`문제 ${questionId} 편집 기능 (구현 예정)`);
}

function editAnswer(questionId) {
    alert(`문제 ${questionId} 정답/해설 편집 기능 (구현 예정)`);
}

function deleteQuestion(questionId) {
    const confirmMessage = `문제 ${questionId}를 삭제하시겠습니까?\n\n⚠️ 주의: 연관된 정답, 해설, 학습포인트도 함께 삭제됩니다.`;
    
    if (confirm(confirmMessage)) {
        alert(`문제 ${questionId} 및 연관 데이터 삭제 기능 (구현 예정)\n\n삭제될 데이터:\n- 문제 텍스트\n- 선택지 (객관식인 경우)\n- 정답\n- 해설\n- 학습 포인트`);
    }
}

function aiEditPassage(passageId) {
    alert(`지문 ${passageId} AI 수정 기능 (구현 예정)`);
}

function aiEditExample(exampleId) {
    alert(`예문 ${exampleId} AI 수정 기능 (구현 예정)`);
}

function aiEditQuestion(questionId) {
    alert(`문제 ${questionId} AI 수정 기능 (구현 예정)`);
}

function deployWorksheet(worksheetId) {
    alert(`문제지 ${worksheetId} 배포 기능 (구현 예정)`);
}
