/**
 * 문제지 뷰어 모듈
 */

class WorksheetViewer {
    constructor() {
        this.renderer = new WorksheetRenderer();
        this.editMode = false;
    }

    // 문제지 상세보기 (모달로 표시)
    async viewWorksheet(id) {
        try {
            console.log('문제지 보기:', id);
            
            const response = await ApiService.getWorksheetForEdit(id);
            console.log('📋 API 응답:', response);
            
            // API 응답에서 worksheet_data 추출
            const worksheet = response.worksheet_data || response;
            this.currentWorksheet = worksheet;
            
            console.log('📄 파싱된 문제지 데이터:', worksheet);
            
            this.showWorksheetModal(worksheet, { 
                title: worksheet.worksheet_name || '문제지', 
                showAnswers: true, 
                editMode: false 
            });
            
        } catch (error) {
            console.error('문제지 조회 오류:', error);
            alert('문제지를 불러올 수 없습니다.');
        }
    }

    // 문제지 모달 표시
    showWorksheetModal(worksheetData, options = {}) {
        const { title = '문제지', showAnswers = false, editMode = false } = options;
        
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content worksheet-modal">
                <div class="modal-header">
                    <h2>${title}</h2>
                    <div class="modal-actions">
                        ${editMode ? `
                            <button class="btn btn-secondary" onclick="window.worksheetManager.worksheetViewer.toggleWorksheetEditMode()">
                                ${this.editMode ? '📖 보기 모드' : '✏️ 편집 모드'}
                            </button>
                        ` : `
                            <button class="btn btn-secondary" onclick="window.worksheetManager.editWorksheet('${worksheetData.worksheet_id}')">
                                ✏️ 편집
                            </button>
                        `}
                        <button class="btn btn-secondary" onclick="window.worksheetManager.worksheetViewer.printWorksheet()">
                            🖨️ 인쇄
                        </button>
                        <button class="btn btn-outline modal-close">
                            ❌ 닫기
                        </button>
                    </div>
                </div>
                <div class="modal-body ${editMode ? 'edit-mode' : ''}">
                    ${this.renderer.renderWorksheet(worksheetData, { showAnswers, editMode })}
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // 편집 모드 설정
        if (editMode) {
            this.attachEditListeners(modal);
        }

        // 모달 닫기 이벤트
        modal.querySelector('.modal-close').addEventListener('click', () => {
            modal.remove();
        });

        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });

        // ESC 키로 모달 닫기
        const handleKeyDown = (e) => {
            if (e.key === 'Escape') {
                modal.remove();
                document.removeEventListener('keydown', handleKeyDown);
            }
        };
        document.addEventListener('keydown', handleKeyDown);
    }

    // 편집 리스너 연결
    attachEditListeners(modal) {
        // 편집 가능한 요소들에 이벤트 리스너 추가
        modal.querySelectorAll('[contenteditable="true"]').forEach(element => {
            element.addEventListener('blur', (e) => {
                // 자동 저장 로직
                this.handleAutoSave(e.target);
            });
            
            element.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    e.target.blur();
                }
            });
        });
    }

    // 자동 저장 처리
    async handleAutoSave(element) {
        // 여기에 자동 저장 로직 구현
        console.log('자동 저장:', element.textContent);
    }

    // 인쇄 기능
    printWorksheet() {
        window.print();
    }

    // 보기용 문제지 렌더링 (편집 가능)
    renderWorksheetForViewing(worksheet) {
        const worksheetContent = document.getElementById('worksheetContent');
        if (!worksheetContent) return;

        let html = `
            <div class="worksheet-header">
                <div class="worksheet-actions">
                    <button onclick="window.worksheetManager.worksheetViewer.toggleWorksheetEditMode()" 
                            class="btn-secondary edit-toggle-btn" id="editToggleBtn">
                        ${this.editMode ? '📖 보기 모드' : '✏️ 편집 모드'}
                    </button>
                    <button onclick="window.worksheetManager.showWorksheetsList()" class="btn-secondary">
                        ← 문제지 목록으로 돌아가기
                    </button>
                </div>
                <h2 class="worksheet-title ${this.editMode ? 'editable' : ''}" 
                    ${this.editMode ? `contenteditable="true" 
                    onblur="window.worksheetManager.worksheetViewer.saveWorksheetTitle('${worksheet.worksheet_id}', this.textContent)"` : ''}>
                    ${worksheet.worksheet_name || '문제지 제목'}
                </h2>
                <div class="worksheet-info">
                    <span>📚 ${worksheet.worksheet_level} ${worksheet.worksheet_grade}</span>
                    <span>📝 총 ${worksheet.total_questions}문제</span>
                    <span>⏱️ ${worksheet.worksheet_duration}분</span>
                </div>
            </div>
        `;

        // 지문들 렌더링
        if (worksheet.passages && worksheet.passages.length > 0) {
            worksheet.passages.forEach((passage, index) => {
                html += this.renderPassage(passage, index);
            });
        }

        // 예문들 렌더링
        if (worksheet.examples && worksheet.examples.length > 0) {
            worksheet.examples.forEach((example, index) => {
                html += this.renderExample(example, index);
            });
        }

        // 문제들 렌더링
        if (worksheet.questions && worksheet.questions.length > 0) {
            worksheet.questions.forEach((question, index) => {
                html += this.renderQuestion(question, index + 1);
            });
        }

        worksheetContent.innerHTML = html;
        
        if (this.editMode) {
            this.attachEditModeListeners();
        }
    }

    // 지문 렌더링
    renderPassage(passage, index) {
        const isEditable = this.editMode;
        return `
            <div class="passage-section" data-passage-id="${passage.passage_id}">
                <h3>📖 지문 ${index + 1}</h3>
                <div class="passage-content">
                    <div class="passage-text ${isEditable ? 'editable' : ''}" 
                         ${isEditable ? `contenteditable="true"
                         onblur="window.worksheetManager.worksheetViewer.savePassageContent('${passage.passage_id}', this.innerHTML)"` : ''}>
                        ${passage.original_content || ''}
                    </div>
                    ${passage.korean_translation ? `
                        <div class="passage-translation ${isEditable ? 'editable' : ''}" 
                             ${isEditable ? `contenteditable="true"
                             onblur="window.worksheetManager.worksheetViewer.savePassageTranslation('${passage.passage_id}', this.innerHTML)"` : ''}>
                            <strong>번역:</strong> ${passage.korean_translation}
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    // 예문 렌더링
    renderExample(example, index) {
        const isEditable = this.editMode;
        return `
            <div class="example-section" data-example-id="${example.example_id}">
                <h3>💡 예문 ${index + 1}</h3>
                <div class="example-content">
                    <div class="example-text ${isEditable ? 'editable' : ''}" 
                         ${isEditable ? `contenteditable="true"
                         onblur="window.worksheetManager.worksheetViewer.saveExampleContent('${example.example_id}', this.innerHTML)"` : ''}>
                        ${example.original_content || ''}
                    </div>
                    ${example.korean_translation ? `
                        <div class="example-translation ${isEditable ? 'editable' : ''}" 
                             ${isEditable ? `contenteditable="true"
                             onblur="window.worksheetManager.worksheetViewer.saveExampleTranslation('${example.example_id}', this.innerHTML)"` : ''}>
                            <strong>번역:</strong> ${example.korean_translation}
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    // 문제 렌더링
    renderQuestion(question, questionNum) {
        const isEditable = this.editMode;
        let html = `
            <div class="question-item" data-question-id="${question.question_id}">
                <div class="question-header">
                    <span class="question-number">${questionNum}</span>
                    <span class="question-type">[${question.question_type}]</span>
                </div>
                
                <div class="question-text ${isEditable ? 'editable' : ''}" 
                     ${isEditable ? `contenteditable="true"
                     onblur="window.worksheetManager.worksheetViewer.saveQuestionText('${question.question_id}', this.innerHTML)"` : ''}>
                    ${question.question_text}
                </div>
        `;

        // 객관식 문제인 경우 선택지 추가
        if (question.question_type === 'multiple_choice' && question.choices) {
            html += '<div class="choices">';
            question.choices.forEach((choice, index) => {
                const choiceNum = ['①', '②', '③', '④', '⑤'][index];
                html += `
                    <div class="choice" data-choice-index="${index}">
                        <span class="choice-number">${choiceNum}</span>
                        <span class="choice-text ${isEditable ? 'editable' : ''}" 
                              ${isEditable ? `contenteditable="true"
                              onblur="window.worksheetManager.worksheetViewer.saveChoice('${question.question_id}', ${index}, this.textContent)"` : ''}>${choice}</span>
                    </div>
                `;
            });
            html += '</div>';
        }

        // 정답 표시
        html += `
            <div class="answer-section">
                <strong>정답: </strong>
                <span class="correct-answer ${isEditable ? 'editable' : ''}" 
                      ${isEditable ? `contenteditable="true"
                      onblur="window.worksheetManager.worksheetViewer.saveAnswer('${question.question_id}', this.textContent)"` : ''}>${question.correct_answer || ''}</span>
            </div>
        `;

        // 해설
        if (question.explanation) {
            html += `
                <div class="explanation-section">
                    <strong>해설:</strong>
                    <div class="explanation-text ${isEditable ? 'editable' : ''}" 
                         ${isEditable ? `contenteditable="true"
                         onblur="window.worksheetManager.worksheetViewer.saveExplanation('${question.question_id}', this.innerHTML)"` : ''}>${question.explanation}</div>
                </div>
            `;
        }

        // 학습포인트
        if (question.learning_points && question.learning_points.length > 0) {
            html += `
                <div class="learning-points-section">
                    <strong>학습포인트:</strong>
                    <div class="learning-points">
            `;
            question.learning_points.forEach((point, index) => {
                html += `
                    <div class="learning-point ${isEditable ? 'editable' : ''}" 
                         ${isEditable ? `contenteditable="true"
                         onblur="window.worksheetManager.worksheetViewer.saveLearningPoint('${question.question_id}', ${index}, this.textContent)"` : ''}>• ${point}</div>
                `;
            });
            html += `
                    </div>
                </div>
            `;
        }

        html += '</div>';
        return html;
    }

    // 편집 모드 토글
    toggleWorksheetEditMode() {
        this.editMode = !this.editMode;
        console.log('편집 모드 토글:', this.editMode);
        
        if (this.currentWorksheet) {
            this.renderWorksheetForViewing(this.currentWorksheet);
        }
    }

    // 편집 모드 이벤트 리스너 설정
    attachEditModeListeners() {
        document.querySelectorAll('.editable').forEach(element => {
            // 포커스시 스타일 적용
            element.addEventListener('focus', () => {
                element.style.outline = '2px solid #007bff';
                element.style.backgroundColor = '#f8f9fa';
            });
            
            // 블러시 스타일 제거
            element.addEventListener('blur', () => {
                element.style.outline = 'none';
                element.style.backgroundColor = 'transparent';
            });
            
            // Enter 키로 저장
            element.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    element.blur();
                }
            });
        });
    }

    // 저장 함수들 (WorksheetEditor와 동일)
    async saveWorksheetTitle(worksheetId, title) {
        try {
            await ApiService.updateWorksheet(worksheetId, { worksheet_name: title });
            this.showSaveStatus(true);
        } catch (error) {
            console.error('제목 저장 오류:', error);
            this.showSaveStatus(false);
        }
    }

    async savePassageContent(passageId, content) {
        try {
            await ApiService.updatePassage(passageId, { original_content: content });
            this.showSaveStatus(true);
        } catch (error) {
            console.error('지문 저장 오류:', error);
            this.showSaveStatus(false);
        }
    }

    async savePassageTranslation(passageId, translation) {
        try {
            await ApiService.updatePassage(passageId, { korean_translation: translation });
            this.showSaveStatus(true);
        } catch (error) {
            console.error('지문 번역 저장 오류:', error);
            this.showSaveStatus(false);
        }
    }

    async saveExampleContent(exampleId, content) {
        try {
            await ApiService.updateExample(exampleId, { original_content: content });
            this.showSaveStatus(true);
        } catch (error) {
            console.error('예문 저장 오류:', error);
            this.showSaveStatus(false);
        }
    }

    async saveExampleTranslation(exampleId, translation) {
        try {
            await ApiService.updateExample(exampleId, { korean_translation: translation });
            this.showSaveStatus(true);
        } catch (error) {
            console.error('예문 번역 저장 오류:', error);
            this.showSaveStatus(false);
        }
    }

    async saveQuestionText(questionId, text) {
        try {
            await ApiService.updateQuestion(questionId, { question_text: text });
            this.showSaveStatus(true);
        } catch (error) {
            console.error('문제 텍스트 저장 오류:', error);
            this.showSaveStatus(false);
        }
    }

    async saveChoice(questionId, choiceIndex, choiceText) {
        try {
            await ApiService.updateQuestionChoice(questionId, choiceIndex, choiceText);
            this.showSaveStatus(true);
        } catch (error) {
            console.error('선택지 저장 오류:', error);
            this.showSaveStatus(false);
        }
    }

    async saveAnswer(questionId, answer) {
        try {
            await ApiService.updateQuestion(questionId, { correct_answer: answer });
            this.showSaveStatus(true);
        } catch (error) {
            console.error('정답 저장 오류:', error);
            this.showSaveStatus(false);
        }
    }

    async saveExplanation(questionId, explanation) {
        try {
            await ApiService.updateQuestion(questionId, { explanation: explanation });
            this.showSaveStatus(true);
        } catch (error) {
            console.error('해설 저장 오류:', error);
            this.showSaveStatus(false);
        }
    }

    async saveLearningPoint(questionId, pointIndex, pointText) {
        try {
            await ApiService.updateQuestionLearningPoint(questionId, pointIndex, pointText);
            this.showSaveStatus(true);
        } catch (error) {
            console.error('학습포인트 저장 오류:', error);
            this.showSaveStatus(false);
        }
    }

    // 저장 상태 표시
    showSaveStatus(success) {
        const status = document.createElement('div');
        status.className = `save-status ${success ? 'success' : 'error'}`;
        status.textContent = success ? '저장됨' : '저장 실패';
        status.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 8px 16px;
            border-radius: 4px;
            color: white;
            font-weight: bold;
            z-index: 1000;
            background-color: ${success ? '#28a745' : '#dc3545'};
        `;
        
        document.body.appendChild(status);
        
        setTimeout(() => {
            status.remove();
        }, 2000);
    }

    // 문제지 목록으로 돌아가기
    showWorksheetsList() {
        // 워크시트 콘텐츠 숨기기
        const worksheetContent = document.getElementById('worksheetContent');
        if (worksheetContent) {
            worksheetContent.innerHTML = '';
        }

        // 탭 전환
        document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
        
        const worksheetTab = document.querySelector('[data-tab="worksheets"]');
        const worksheetTabContent = document.getElementById('worksheets-tab');
        
        if (worksheetTab) worksheetTab.classList.add('active');
        if (worksheetTabContent) worksheetTabContent.classList.add('active');
    }
}

// 전역으로 노출
window.WorksheetViewer = WorksheetViewer;
