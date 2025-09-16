/**
 * 문제지 편집 및 관리 모듈
 */

class WorksheetEditor {
    constructor() {
        this.worksheets = [];
        this.gradingResults = [];
        this.currentWorksheet = null;
        this.renderer = new WorksheetRenderer();
        this.startTime = Date.now(); // 문제지 시작 시간
        this.init();
    }

    async init() {
        // ApiService가 로드될 때까지 대기
        await this.waitForApiService();
        this.setupTabNavigation();
        await this.loadWorksheets();
        await this.loadGradingResults();
    }

    // ApiService 로드 대기
    async waitForApiService() {
        return new Promise((resolve) => {
            const checkApiService = () => {
                if (typeof window.ApiService !== 'undefined') {
                    resolve();
                } else {
                    setTimeout(checkApiService, 50);
                }
            };
            checkApiService();
        });
    }

    // 탭 네비게이션 설정
    setupTabNavigation() {
        const tabButtons = document.querySelectorAll('.tab-btn');
        const tabContents = document.querySelectorAll('.tab-content');

        tabButtons.forEach(button => {
            button.addEventListener('click', () => {
                const targetTab = button.dataset.tab;
                
                // 모든 탭 비활성화
                tabButtons.forEach(btn => btn.classList.remove('active'));
                tabContents.forEach(content => content.classList.remove('active'));
                
                // 선택된 탭 활성화
                button.classList.add('active');
                document.getElementById(`${targetTab}-tab`).classList.add('active');
                
                // 탭별 데이터 로드
                this.handleTabSwitch(targetTab);
            });
        });
    }

    // 탭 전환 처리
    async handleTabSwitch(tabName) {
        switch (tabName) {
            case 'worksheets':
                await this.loadWorksheets();
                this.displayWorksheets();
                break;
            case 'results':
                await this.loadGradingResults();
                this.displayGradingResults();
                break;
            case 'generate':
                // 문제 생성 탭은 별도 처리 불필요
                break;
        }
    }

    // 문제지 목록 로드
    async loadWorksheets() {
        try {
            this.worksheets = await window.window.ApiService.getWorksheets();
            console.log('문제지 목록 로드:', this.worksheets);
        } catch (error) {
            console.error('문제지 목록 로드 오류:', error);
            this.showError('문제지 목록을 불러올 수 없습니다.');
        }
    }

    // 채점 결과 목록 로드
    async loadGradingResults() {
        try {
            this.gradingResults = await window.window.ApiService.getGradingResults();
            console.log('채점 결과 로드:', this.gradingResults);
        } catch (error) {
            console.error('채점 결과 로드 오류:', error);
            this.showError('채점 결과를 불러올 수 없습니다.');
        }
    }

    // 문제지 목록 표시
    displayWorksheets() {
        const container = document.getElementById('worksheetsList');
        
        if (!this.worksheets || this.worksheets.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <h3>📝 저장된 문제지가 없습니다</h3>
                    <p>문제 생성 탭에서 새로운 문제지를 만들어보세요.</p>
                </div>
            `;
            return;
        }

        const html = this.worksheets.map(worksheet => 
            this.renderer.renderWorksheetCard(worksheet)
        ).join('');
        
        container.innerHTML = html;
    }

    // 채점 결과 표시
    displayGradingResults() {
        const container = document.getElementById('gradingResults');
        
        if (!this.gradingResults || this.gradingResults.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <h3>📊 채점 결과가 없습니다</h3>
                    <p>문제지를 풀고 답안을 제출하면 채점 결과를 확인할 수 있습니다.</p>
                </div>
            `;
            return;
        }

        const html = this.gradingResults.map(result => 
            this.renderer.renderGradingResultCard(result)
        ).join('');
        
        container.innerHTML = html;
    }

    // 문제지 보기
    async viewWorksheet(worksheetId) {
        try {
            const result = await window.ApiService.getWorksheetForEdit(worksheetId);
            this.currentWorksheet = result.worksheet_data;
            
            this.showWorksheetModal(this.currentWorksheet, { 
                title: '📖 문제지 보기',
                showAnswers: true,
                editMode: false 
            });
        } catch (error) {
            console.error('문제지 조회 오류:', error);
            this.showError('문제지를 불러올 수 없습니다.');
        }
    }

    // 문제지 편집
    async editWorksheet(worksheetId) {
        try {
            const result = await window.ApiService.getWorksheetForEdit(worksheetId);
            this.currentWorksheet = result.worksheet_data;
            
            this.showWorksheetModal(this.currentWorksheet, { 
                title: '✏️ 문제지 편집',
                showAnswers: true,
                editMode: true 
            });
        } catch (error) {
            console.error('문제지 조회 오류:', error);
            this.showError('문제지를 불러올 수 없습니다.');
        }
    }

    // 문제지 풀이
    async solveWorksheet(worksheetId) {
        try {
            const result = await window.ApiService.getWorksheetForSolve(worksheetId);
            const worksheetData = result.worksheet_data;
            
            this.showSolveModal(worksheetData);
        } catch (error) {
            console.error('문제지 조회 오류:', error);
            this.showError('문제지를 불러올 수 없습니다.');
        }
    }

    // 문제지 삭제
    async deleteWorksheet(worksheetId) {
        if (!confirm('정말로 이 문제지를 삭제하시겠습니까?')) {
            return;
        }

        try {
            await window.ApiService.deleteWorksheet(worksheetId);
            this.showSuccess('문제지가 삭제되었습니다.');
            await this.loadWorksheets();
            this.displayWorksheets();
        } catch (error) {
            console.error('문제지 삭제 오류:', error);
            this.showError('문제지 삭제에 실패했습니다.');
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
                            <button class="btn btn-success" onclick="saveWorksheetChanges()">
                                💾 저장
                            </button>
                        ` : ''}
                        <button class="btn btn-secondary" onclick="printWorksheet()">
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

        // 전역 함수 설정
        window.saveWorksheetChanges = () => this.saveWorksheetChanges();
        window.printWorksheet = () => this.printWorksheet();
    }

    // 문제지 풀이 모달
    showSolveModal(worksheetData) {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content solve-modal">
                <div class="modal-header">
                    <h2>✍️ 문제지 풀이</h2>
                    <div class="timer" id="solveTimer">
                        ⏱️ ${worksheetData.worksheet_duration || 45}:00
                    </div>
                    <button class="btn btn-outline modal-close">❌ 닫기</button>
                </div>
                <div class="modal-body">
                    <div class="solve-content">
                        <div class="worksheet-section">
                            ${this.renderer.renderWorksheet(worksheetData, { showAnswers: false, editMode: false })}
                        </div>
                        <div class="answer-section">
                            ${this.renderer.renderAnswerSheet(worksheetData)}
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // 타이머 시작
        this.startSolveTimer(worksheetData.worksheet_duration || 45);

        // 모달 닫기 이벤트
        modal.querySelector('.modal-close').addEventListener('click', () => {
            if (confirm('풀이를 종료하시겠습니까? 작성한 답안은 저장되지 않습니다.')) {
                modal.remove();
            }
        });

        // 답안 제출 함수 설정
        window.submitAnswers = () => this.submitAnswers(worksheetData.worksheet_id);
    }

    // 풀이 타이머
    startSolveTimer(minutes) {
        let timeLeft = minutes * 60;
        const timerElement = document.getElementById('solveTimer');
        
        const timer = setInterval(() => {
            const mins = Math.floor(timeLeft / 60);
            const secs = timeLeft % 60;
            timerElement.textContent = `⏱️ ${mins}:${secs.toString().padStart(2, '0')}`;
            
            if (timeLeft <= 0) {
                clearInterval(timer);
                alert('시간이 종료되었습니다!');
                this.submitAnswers();
            }
            
            timeLeft--;
        }, 1000);
    }

    // 답안 제출
    async submitAnswers(worksheetId) {
        const answers = {};
        const inputs = document.querySelectorAll('.answer-input');
        
        inputs.forEach(input => {
            const questionId = input.dataset.questionId;
            const answer = input.value.trim();
            if (answer) {
                answers[questionId] = answer;
            }
        });

        if (Object.keys(answers).length === 0) {
            alert('답안을 입력해주세요.');
            return;
        }

        if (!confirm('답안을 제출하시겠습니까?')) {
            return;
        }

        try {
            // 소요 시간 계산 (초 단위)
            const completionTime = Math.floor((Date.now() - this.startTime) / 1000) || 60; // 기본 60초
            
            const result = await window.ApiService.submitAnswers(worksheetId, {
                answers: answers,
                completion_time: completionTime
            });

            this.showSuccess('답안이 제출되었습니다!');
            
            // 모달 닫기
            document.querySelector('.modal-overlay').remove();
            
            // 채점 결과 새로고침
            await this.loadGradingResults();
            if (document.querySelector('.tab-btn[data-tab="results"]').classList.contains('active')) {
                this.displayGradingResults();
            }

        } catch (error) {
            console.error('답안 제출 오류:', error);
            this.showError('답안 제출에 실패했습니다.');
        }
    }

    // 편집 이벤트 리스너 추가
    attachEditListeners(container) {
        const editables = container.querySelectorAll('.editable');
        editables.forEach(element => {
            element.contentEditable = true;
            element.addEventListener('blur', (e) => this.handleEdit(e));
            element.addEventListener('keydown', (e) => this.handleEditKeydown(e));
        });
    }

    // 편집 처리
    async handleEdit(event) {
        const element = event.target;
        const type = element.dataset.type;
        const id = element.dataset.id;
        const newContent = element.textContent.trim();

        try {
            element.style.backgroundColor = '#fff3cd';
            
            const worksheetId = this.currentWorksheet.worksheet_id;
            
            switch (type) {
                case 'title':
                    await window.ApiService.updateWorksheetTitle(worksheetId, newContent);
                    this.currentWorksheet.worksheet_name = newContent;
                    break;
                    
                case 'question':
                    await window.ApiService.updateQuestionText(worksheetId, id, newContent);
                    break;
                    
                case 'choice':
                    const choiceIndex = parseInt(element.dataset.choiceIndex);
                    const questionId = element.dataset.questionId;
                    await window.ApiService.updateQuestionChoice(worksheetId, questionId, choiceIndex, newContent);
                    break;
                    
                case 'answer':
                    await window.ApiService.updateQuestionAnswer(worksheetId, id, newContent);
                    break;
                    
                case 'passage':
                    const passageContent = this.parsePassageContent(element);
                    await window.ApiService.updatePassage(worksheetId, id, passageContent);
                    break;
                    
                case 'example':
                    await window.ApiService.updateExample(worksheetId, id, newContent);
                    break;
            }

            element.style.backgroundColor = '#d4edda';
            setTimeout(() => {
                element.style.backgroundColor = '';
            }, 1000);

        } catch (error) {
            console.error('편집 저장 오류:', error);
            element.style.backgroundColor = '#f8d7da';
            setTimeout(() => {
                element.style.backgroundColor = '';
            }, 2000);
            this.showError('편집 내용 저장에 실패했습니다.');
        }
    }

    // 편집 키보드 이벤트
    handleEditKeydown(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            event.target.blur();
        }
    }

    // 지문 내용 파싱 (JSON 형식 유지)
    parsePassageContent(element) {
        const content = [];
        const children = element.children;
        
        for (let child of children) {
            if (child.tagName === 'H3') {
                content.push({ type: 'title', value: child.textContent });
            } else if (child.tagName === 'P') {
                content.push({ type: 'paragraph', value: child.textContent });
            }
        }
        
        return { 
            content: content.length > 0 ? content : [{ type: 'paragraph', value: element.textContent }] 
        };
    }

    // 문제지 변경사항 저장
    async saveWorksheetChanges() {
        try {
            // 현재 편집된 내용을 currentWorksheet에 반영
            const result = await window.ApiService.saveWorksheet(this.currentWorksheet);
            this.showSuccess('변경사항이 저장되었습니다.');
        } catch (error) {
            console.error('저장 오류:', error);
            this.showError('저장에 실패했습니다.');
        }
    }

    // 문제지 인쇄
    printWorksheet() {
        const printContent = this.renderer.renderForPrint(this.currentWorksheet);
        const printWindow = window.open('', '_blank');
        printWindow.document.write(`
            <!DOCTYPE html>
            <html>
            <head>
                <title>문제지 인쇄</title>
                <link rel="stylesheet" href="/static/css/style.css">
            </head>
            <body>
                ${printContent}
                <script>window.print(); window.close();</script>
            </body>
            </html>
        `);
        printWindow.document.close();
    }

    // 채점 결과 보기
    async viewGradingResult(resultId) {
        try {
            const result = await window.ApiService.getGradingResult(resultId);
            this.showGradingResultModal(result);
        } catch (error) {
            console.error('채점 결과 조회 오류:', error);
            this.showError('채점 결과를 불러올 수 없습니다.');
        }
    }

    // 채점 결과 모달
    showGradingResultModal(result) {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content grading-modal">
                <div class="modal-header">
                    <h2>📊 채점 결과</h2>
                    <button class="btn btn-outline modal-close">❌ 닫기</button>
                </div>
                <div class="modal-body">
                    <div class="result-summary">
                        <h3>${result.student_name}님의 답안</h3>
                        <p><strong>점수:</strong> ${result.total_score}/${result.max_score}점</p>
                        <p><strong>제출일:</strong> ${this.renderer.formatDate(result.submitted_at)}</p>
                    </div>
                    <div class="result-details">
                        <!-- 상세 채점 결과 표시 -->
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        modal.querySelector('.modal-close').addEventListener('click', () => {
            modal.remove();
        });
    }

    // 성공 메시지
    showSuccess(message) {
        this.showMessage(message, 'success');
    }

    // 오류 메시지
    showError(message) {
        this.showMessage(message, 'error');
    }

    // 메시지 표시
    showMessage(message, type) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type}`;
        alertDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            z-index: 1000;
            max-width: 400px;
            word-wrap: break-word;
            ${type === 'success' ? 'background: #28a745;' : 'background: #dc3545;'}
        `;
        alertDiv.textContent = message;
        
        document.body.appendChild(alertDiv);
        
        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }

    // 채점 결과 보기
    async viewGradingResult(resultId) {
        try {
            console.log('채점 결과 조회:', resultId);
            
            // 채점 결과 데이터 가져오기
            const gradingResult = await window.ApiService.getGradingResult(resultId);
            console.log('채점 결과 데이터:', gradingResult);
            
            // 해당 문제지 데이터도 가져오기
            const worksheetData = await window.ApiService.getWorksheetForSolving(gradingResult.worksheet_id);
            console.log('문제지 데이터:', worksheetData);
            
            // 채점 결과 렌더링
            this.renderGradingResult(gradingResult, worksheetData);
            
        } catch (error) {
            console.error('채점 결과 조회 오류:', error);
            this.showError('채점 결과를 불러오는데 실패했습니다.');
        }
    }

    // 채점 결과 렌더링
    renderGradingResult(gradingResult, worksheetData) {
        const content = document.getElementById('worksheetContent');
        
        // 헤더 정보
        let html = `
            <div class="grading-result-header">
                <h2>📊 채점 결과</h2>
                <div class="score-summary">
                    <div class="score-item">
                        <span class="label">학생:</span>
                        <span class="value">${gradingResult.student_name}</span>
                    </div>
                    <div class="score-item">
                        <span class="label">총점:</span>
                        <span class="value score">${gradingResult.total_score}/${gradingResult.max_score}점</span>
                    </div>
                    <div class="score-item">
                        <span class="label">정답률:</span>
                        <span class="value percentage">${gradingResult.percentage.toFixed(1)}%</span>
                    </div>
                    <div class="score-item">
                        <span class="label">소요시간:</span>
                        <span class="value">${Math.floor(gradingResult.completion_time / 60)}분 ${gradingResult.completion_time % 60}초</span>
                    </div>
                </div>
            </div>
        `;

        // 문제지 정보
        html += `
            <div class="worksheet-info">
                <h3>${worksheetData.worksheet_name}</h3>
                <p><strong>학교급:</strong> ${worksheetData.worksheet_level} | 
                   <strong>학년:</strong> ${worksheetData.worksheet_grade}학년 | 
                   <strong>문제 수:</strong> ${worksheetData.total_questions}문제</p>
            </div>
        `;

        // 문제별 채점 결과와 함께 문제지 렌더링
        html += this.renderWorksheetWithGradingResult(worksheetData, gradingResult);
        
        content.innerHTML = html;
        
        // 결과 화면 표시
        document.getElementById('generatedWorksheet').style.display = 'block';
        document.getElementById('generatedWorksheet').scrollIntoView({ behavior: 'smooth' });
    }

    // 채점 결과와 함께 문제지 렌더링
    renderWorksheetWithGradingResult(worksheetData, gradingResult) {
        let html = '';
        
        // 문제별로 연관된 지문/예문과 함께 렌더링
        const renderedPassages = new Set();
        const renderedExamples = new Set();
        
        if (worksheetData.questions && worksheetData.questions.length > 0) {
            worksheetData.questions.forEach((question, index) => {
                // 해당 문제와 연관된 지문 먼저 렌더링
                if (question.question_passage_id) {
                    const passage = worksheetData.passages?.find(p => p.passage_id === question.question_passage_id);
                    if (passage && !renderedPassages.has(passage.passage_id)) {
                        html += this.renderer.renderPassage(passage, false);
                        renderedPassages.add(passage.passage_id);
                    }
                }
                
                // 해당 문제와 연관된 예문 먼저 렌더링
                if (question.question_example_id) {
                    const example = worksheetData.examples?.find(e => e.example_id === question.question_example_id);
                    if (example && !renderedExamples.has(example.example_id)) {
                        html += this.renderer.renderExample(example, false);
                        renderedExamples.add(example.example_id);
                    }
                }
                
                // 문제 렌더링 (채점 결과 포함)
                html += this.renderQuestionWithResult(question, index + 1, gradingResult);
            });
        }
        
        return html;
    }

    // 채점 결과와 함께 문제 렌더링
    renderQuestionWithResult(question, number, gradingResult) {
        const questionResult = gradingResult.question_results?.find(qr => qr.question_id === question.question_id);
        const studentAnswer = gradingResult.student_answers?.[question.question_id];
        const isCorrect = questionResult?.is_correct || false;
        const score = questionResult?.score || 0;
        const maxScore = questionResult?.max_score || 1;
        
        let html = `
            <div class="question grading-result-question ${isCorrect ? 'correct' : 'incorrect'}">
                <div class="question-header">
                    <span class="question-number">${number}.</span>
                    <span class="question-info">
                        ${question.question_subject} | ${question.question_difficulty} | ${question.question_type}
                    </span>
                    <span class="question-score ${isCorrect ? 'correct' : 'incorrect'}">
                        ${score}/${maxScore}점 ${isCorrect ? '✅' : '❌'}
                    </span>
                </div>
                <div class="question-text">
                    ${this.renderer.escapeHtml(question.question_text || '')}
                </div>
        `;

        // 선택지 렌더링 (학생 답안과 정답 표시)
        if (question.question_choices && question.question_choices.length > 0) {
            html += '<div class="question-choices">';
            question.question_choices.forEach((choice, index) => {
                const marker = ['①', '②', '③', '④', '⑤'][index] || `${index + 1}.`;
                const isStudentChoice = studentAnswer === (index + 1).toString() || studentAnswer === marker;
                const isCorrectChoice = question.correct_answer === (index + 1).toString() || question.correct_answer === marker;
                
                let choiceClass = 'choice';
                if (isStudentChoice && isCorrectChoice) {
                    choiceClass += ' student-correct'; // 학생이 선택하고 정답
                } else if (isStudentChoice && !isCorrectChoice) {
                    choiceClass += ' student-wrong'; // 학생이 선택했지만 틀림
                } else if (!isStudentChoice && isCorrectChoice) {
                    choiceClass += ' correct-answer'; // 정답이지만 학생이 선택 안함
                }
                
                html += `
                    <div class="${choiceClass}">
                        <span class="choice-marker">${marker}</span>
                        <span class="choice-text">
                            ${this.renderer.escapeHtml(choice)}
                        </span>
                        ${isStudentChoice ? '<span class="student-mark">👤</span>' : ''}
                        ${isCorrectChoice ? '<span class="correct-mark">✅</span>' : ''}
                    </div>
                `;
            });
            html += '</div>';
        } else {
            // 주관식/서술형 답안
            html += `
                <div class="answer-comparison">
                    <div class="student-answer">
                        <strong>학생 답안:</strong> 
                        <span class="answer-text ${isCorrect ? 'correct' : 'incorrect'}">
                            ${this.renderer.escapeHtml(studentAnswer || '미작성')}
                        </span>
                    </div>
                    <div class="correct-answer">
                        <strong>정답:</strong> 
                        <span class="answer-text">
                            ${this.renderer.escapeHtml(question.correct_answer || '')}
                        </span>
                    </div>
                </div>
            `;
        }

        // 해설 표시
        if (question.explanation) {
            html += `
                <div class="question-explanation">
                    <strong>해설:</strong> 
                    <span>${this.renderer.escapeHtml(question.explanation)}</span>
                </div>
            `;
        }

        // AI 피드백 (있는 경우)
        if (questionResult?.ai_feedback) {
            html += `
                <div class="ai-feedback">
                    <strong>AI 피드백:</strong> 
                    <span>${this.renderer.escapeHtml(questionResult.ai_feedback)}</span>
                </div>
            `;
        }

        html += '</div>';
        return html;
    }
}

// 전역 함수들
window.viewWorksheet = (id) => window.worksheetEditor.viewWorksheet(id);
window.editWorksheet = (id) => window.worksheetEditor.editWorksheet(id);
window.solveWorksheet = (id) => window.worksheetEditor.solveWorksheet(id);
window.deleteWorksheet = (id) => window.worksheetEditor.deleteWorksheet(id);
window.viewGradingResult = (id) => window.worksheetEditor.viewGradingResult(id);

// 전역으로 노출
window.WorksheetEditor = WorksheetEditor;
