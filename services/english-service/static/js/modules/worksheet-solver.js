/**
 * 문제지 풀이 모듈
 */

class WorksheetSolver {
    constructor() {
        this.currentWorksheet = null;
        this.answers = {};
        this.startTime = null;
        this.timerInterval = null;
        this.renderer = new WorksheetRenderer();
    }

    // 문제지 풀이 시작 (모달로 표시)
    async solveWorksheet(id) {
        try {
            console.log('문제지 풀이 시작:', id);
            
            const response = await ApiService.getWorksheetForSolve(id);
            console.log('📋 풀이용 API 응답:', response);
            
            // API 응답에서 worksheet_data 추출
            const worksheet = response.worksheet_data || response;
            this.currentWorksheet = worksheet;
            this.answers = {};
            this.startTime = Date.now();
            
            console.log('📄 풀이용 문제지 데이터:', worksheet);
            
            this.showSolveModal(worksheet);
            
        } catch (error) {
            console.error('문제지 풀이 시작 오류:', error);
            alert('문제지를 불러올 수 없습니다.');
        }
    }

    // 문제지 풀이 모달
    showSolveModal(worksheetData) {
        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal-content solve-modal">
                <div class="modal-header">
                    <h2>✍️ 문제지 풀이: ${worksheetData.worksheet_name || '문제지'}</h2>
                    <div class="solve-info">
                        <div class="timer" id="solveTimer">⏱️ 00:00</div>
                        <div class="progress">
                            <span id="progress-text">0/${worksheetData.total_questions} 문제 완료</span>
                        </div>
                    </div>
                    <div class="solve-actions">
                        <button class="btn btn-primary" onclick="window.worksheetManager.worksheetSolver.submitAnswers()" id="submitBtn">
                            제출하기
                        </button>
                        <button class="btn btn-outline modal-close">❌ 취소</button>
                    </div>
                </div>
                <div class="modal-body">
                    <div class="solve-content">
                        ${this.renderer.renderWorksheet(worksheetData, { showAnswers: false, editMode: false, solveMode: true })}
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // 타이머 시작
        this.startTimer();
        
        // 답안 입력 이벤트 연결
        this.attachSolveEventListeners(modal);
        
        // 객관식 선택지 클릭 기능 추가
        this.setupMultipleChoiceClickHandlers(modal);
        
        // 단답형/서술형 문제에 답란 추가
        this.addAnswerInputsToQuestions(modal, worksheetData);
        
        // 객관식 문제의 기존 답안 입력란 완전 제거
        this.removeUnnecessaryAnswerInputs(modal, worksheetData);

        // 모달 닫기 이벤트
        modal.querySelector('.modal-close').addEventListener('click', () => {
            if (confirm('풀이를 종료하시겠습니까? 작성한 답안은 저장되지 않습니다.')) {
                this.stopTimer();
                modal.remove();
            }
        });

        // ESC 키로 모달 닫기
        const handleKeyDown = (e) => {
            if (e.key === 'Escape') {
                if (confirm('풀이를 종료하시겠습니까? 작성한 답안은 저장되지 않습니다.')) {
                    this.stopTimer();
                    modal.remove();
                    document.removeEventListener('keydown', handleKeyDown);
                }
            }
        };
        document.addEventListener('keydown', handleKeyDown);
    }

    // 답안 입력 필드 렌더링 (기존 방식)
    renderAnswerInputs(worksheetData) {
        return '';
    }

    // 단답형/서술형 문제에 답란 추가
    addAnswerInputsToQuestions(modal, worksheetData) {
        if (!worksheetData.questions) return;
        
        console.log('🔍 문제 타입 디버깅:', worksheetData.questions.map(q => ({
            id: q.question_id, 
            type: q.question_type,
            hasChoices: (q.choices && q.choices.length > 0) || (q.question_choices && q.question_choices.length > 0),
            choicesLength: q.question_choices ? q.question_choices.length : 'undefined'
        })));
        
        worksheetData.questions.forEach((question, index) => {
            // 선택지가 없는 문제(주관식)에만 답란 추가
            const isMultipleChoice = (question.choices && question.choices.length > 0) || (question.question_choices && question.question_choices.length > 0);
            if (!isMultipleChoice) {
                const questionElement = modal.querySelector(`.question[data-question-id="${question.question_id}"]`);
                if (questionElement) {
                    // 답안 입력 영역 생성
                    const answerSection = document.createElement('div');
                    answerSection.className = 'answer-input-section';
                    answerSection.setAttribute('data-question-id', question.question_id);
                    
                    answerSection.innerHTML = `
                        <div class="answer-header">
                            <strong>📝 답안</strong>
                        </div>
                        <textarea class="answer-textarea" 
                                  placeholder="답안을 입력하세요..." 
                                  data-question-id="${question.question_id}"
                                  rows="3"></textarea>
                    `;
                    
                    // 문제 요소 바로 뒤에 답안 섹션 삽입
                    questionElement.appendChild(answerSection);
                    
                    // 이벤트 리스너 추가
                    const textarea = answerSection.querySelector('.answer-textarea');
                    textarea.addEventListener('blur', (e) => {
                        this.selectAnswer(question.question_id, e.target.value);
                    });
                    textarea.addEventListener('input', (e) => {
                        this.updateAnswerStatus(question.question_id, e.target.value);
                    });
                }
            }
        });
    }

    // 불필요한 답안 입력란 제거 (객관식용)
    removeUnnecessaryAnswerInputs(modal, worksheetData) {
        // 기존의 모든 답안 입력 관련 요소 제거
        const answerSheets = modal.querySelectorAll('.answer-sheet, .answer-inputs, .solving-answer-inputs');
        answerSheets.forEach(sheet => sheet.remove());
        
        // 객관식 문제의 불필요한 답안 입력란 제거
        if (worksheetData.questions) {
            worksheetData.questions.forEach(question => {
                const isMultipleChoice = (question.choices && question.choices.length > 0) || (question.question_choices && question.question_choices.length > 0);
                if (isMultipleChoice) {
                    // 객관식 문제와 연관된 답안 입력 요소들 제거
                    const inputElements = modal.querySelectorAll(`
                        [data-question-id="${question.question_id}"].answer-input-group,
                        [data-question-id="${question.question_id}"].answer-input-section,
                        textarea[data-question-id="${question.question_id}"],
                        input[data-question-id="${question.question_id}"].answer-input
                    `);
                    inputElements.forEach(element => element.remove());
                }
            });
        }
        
        console.log('불필요한 답안 입력란 제거 완료');
    }

    // 풀이 이벤트 리스너 연결
    attachSolveEventListeners(modal) {
        // 키보드 단축키
        const handleKeyDown = (e) => {
            if (e.ctrlKey && e.key === 'Enter') {
                e.preventDefault();
                this.submitAnswers();
            }
        };
        modal.addEventListener('keydown', handleKeyDown);
    }

    // 객관식 선택지 클릭 기능 추가
    setupMultipleChoiceClickHandlers(modal) {
        // 모든 객관식 선택지(.choice)에 클릭 이벤트 추가
        const choices = modal.querySelectorAll('.choice');
        choices.forEach(choice => {
            choice.style.cursor = 'pointer';
            choice.addEventListener('click', (e) => {
                // 클릭된 선택지의 문제 ID와 선택지 번호 찾기
                const questionElement = choice.closest('.question');
                if (!questionElement) return;
                
                const questionId = questionElement.getAttribute('data-question-id');
                const choiceIndex = Array.from(questionElement.querySelectorAll('.choice')).indexOf(choice);
                const choiceValue = (choiceIndex + 1).toString();
                
                // 같은 문제의 다른 선택지 선택 해제
                questionElement.querySelectorAll('.choice').forEach(c => {
                    c.classList.remove('selected');
                    c.style.backgroundColor = '';
                    c.style.borderColor = '';
                });
                
                // 현재 선택지 선택 표시
                choice.classList.add('selected');
                choice.style.backgroundColor = '#e3f2fd';
                choice.style.border = '2px solid #007bff';
                
                // 답안 저장
                this.selectAnswer(questionId, choiceValue);
                
                console.log(`문제 ${questionId}에서 선택지 ${choiceValue} 선택`);
            });
        });
    }


    // 답안 선택
    selectAnswer(questionId, answer) {
        this.answers[questionId] = answer;
        this.updateAnswerStatus(questionId, answer);
        this.updateProgress();
        console.log('답안 선택:', questionId, answer);
    }

    // 답안 상태 업데이트
    updateAnswerStatus(questionId, answer) {
        const statusElement = document.getElementById(`status-${questionId}`);
        if (statusElement) {
            if (answer && answer.trim()) {
                statusElement.textContent = '완료';
                statusElement.className = 'answer-status completed';
            } else {
                statusElement.textContent = '미완료';
                statusElement.className = 'answer-status incomplete';
            }
        }
    }

    // 진행률 업데이트
    updateProgress() {
        const totalQuestions = this.currentWorksheet?.total_questions || 0;
        const completedAnswers = Object.keys(this.answers).filter(
            key => this.answers[key] && this.answers[key].trim()
        ).length;
        
        const progressText = document.getElementById('progress-text');
        const progressFill = document.getElementById('progress-fill');
        
        if (progressText) {
            progressText.textContent = `${completedAnswers}/${totalQuestions} 문제 완료`;
        }
        
        if (progressFill) {
            const percentage = totalQuestions > 0 ? (completedAnswers / totalQuestions) * 100 : 0;
            progressFill.style.width = `${percentage}%`;
        }
    }

    // 타이머 시작
    startTimer() {
        this.timerInterval = setInterval(() => {
            const elapsed = Math.floor((Date.now() - this.startTime) / 1000);
            const minutes = Math.floor(elapsed / 60);
            const seconds = elapsed % 60;
            
            const timerElement = document.getElementById('timer');
            if (timerElement) {
                timerElement.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
            }
        }, 1000);
    }

    // 타이머 정지
    stopTimer() {
        if (this.timerInterval) {
            clearInterval(this.timerInterval);
            this.timerInterval = null;
        }
    }

    // 답안 제출
    async submitAnswers() {
        try {
            const totalQuestions = this.currentWorksheet?.total_questions || 0;
            const completedAnswers = Object.keys(this.answers).filter(
                key => this.answers[key] && this.answers[key].trim()
            ).length;
            
            // 미완료 문제가 있는 경우 확인
            if (completedAnswers < totalQuestions) {
                const confirmed = confirm(
                    `${totalQuestions - completedAnswers}개의 문제가 미완료입니다. 정말 제출하시겠습니까?`
                );
                if (!confirmed) return;
            }
            
            this.stopTimer();
            
            const completionTime = Math.floor((Date.now() - this.startTime) / 1000);
            
            console.log('답안 제출:', {
                worksheetId: this.currentWorksheet.worksheet_id,
                answers: this.answers,
                completionTime: completionTime
            });
            
            // 학생 이름 입력 받기
            const studentName = prompt('학생 이름을 입력하세요:');
            if (!studentName) {
                this.startTimer(); // 취소시 타이머 재시작
                return;
            }
            
            const submitData = {
                student_name: studentName,
                answers: this.answers,
                completion_time: completionTime
            };
            
            const result = await ApiService.submitAnswers(
                this.currentWorksheet.worksheet_id, 
                submitData
            );
            
            console.log('제출 결과:', result);
            
            if (result) {
                const percentage = result.percentage ? result.percentage.toFixed(1) : '0.0';
                const totalScore = result.total_score || 0;
                const maxScore = result.max_score || 0;
                
                alert(`제출이 완료되었습니다!\n점수: ${totalScore}/${maxScore} (${percentage}%)`);
                
                // 채점 결과 보기로 이동
                if (result.result_id) {
                    window.gradingResultEditor = window.gradingResultEditor || new GradingResultEditor();
                    await window.gradingResultEditor.viewGradingResult(result.result_id);
                }
            }
            
        } catch (error) {
            console.error('답안 제출 오류:', error);
            alert('답안 제출 중 오류가 발생했습니다.');
            this.startTimer(); // 오류시 타이머 재시작
        }
    }

    // 풀이 취소
    cancelSolving() {
        const confirmed = confirm('정말 풀이를 취소하시겠습니까? 입력한 답안이 모두 사라집니다.');
        if (confirmed) {
            this.stopTimer();
            this.showWorksheetsList();
        }
    }

    // 이벤트 리스너 설정
    attachSolvingEventListeners() {
        // 키보드 단축키
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'Enter') {
                e.preventDefault();
                this.submitAnswers();
            }
        });
    }

    // 문제지 목록으로 돌아가기
    showWorksheetsList() {
        this.stopTimer();
        
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
window.WorksheetSolver = WorksheetSolver;
