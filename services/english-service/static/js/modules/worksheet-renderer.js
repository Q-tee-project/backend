/**
 * 문제지 렌더링 모듈
 */

class WorksheetRenderer {
    constructor() {
        this.renderedPassages = new Set();
    }

    // 메인 문제지 렌더링
    renderWorksheet(data, options = {}) {
        const { showAnswers = true, editMode = false } = options; // 기본값을 true로 변경
        
        let html = this.renderHeader(data, editMode);
        
        // 문제별로 연관된 지문/예문과 함께 렌더링
        this.renderedPassages.clear();
        const renderedExamples = new Set();
        
        if (data.questions && data.questions.length > 0) {
            data.questions.forEach((question, index) => {
                // 해당 문제와 연관된 지문 먼저 렌더링
                if (question.question_passage_id) {
                    const passage = data.passages?.find(p => p.passage_id === question.question_passage_id);
                    if (passage && !this.renderedPassages.has(passage.passage_id)) {
                        html += this.renderPassage(passage, editMode);
                        this.renderedPassages.add(passage.passage_id);
                    }
                }
                
                // 해당 문제와 연관된 예문 먼저 렌더링
                if (question.question_example_id) {
                    const example = data.examples?.find(e => e.example_id === question.question_example_id);
                    if (example && !renderedExamples.has(example.example_id)) {
                        html += this.renderExample(example, editMode);
                        renderedExamples.add(example.example_id);
                    }
                }
                
                // 문제 렌더링 (정답, 해설 포함)
                html += this.renderQuestion(question, index + 1, showAnswers, editMode);
            });
        }

        return html;
    }

    // 문제지 헤더 렌더링
    renderHeader(data, editMode = false) {
        return `
            <div class="worksheet-title ${editMode ? 'editable' : ''}" 
                 ${editMode ? 'data-type="title"' : ''}>
                ${data.worksheet_name || '영어 문제지'}
            </div>
            <div class="worksheet-info">
                <p>
                    <strong>학교급:</strong> ${data.worksheet_level || data.school_level} | 
                    <strong>학년:</strong> ${data.worksheet_grade || data.grade}학년 | 
                    <strong>과목:</strong> ${data.worksheet_subject || data.subject || '영어'} | 
                    <strong>문제 수:</strong> ${data.total_questions}문제 | 
                    <strong>시간:</strong> ${data.worksheet_duration || data.duration}분
                </p>
            </div>
        `;
    }

    // 지문 렌더링
    renderPassage(passage, editMode = false) {
        let html = `
            <div class="passage" data-passage-id="${passage.passage_id}">
                <div class="passage-title">📖 지문 ${passage.passage_id}</div>
                <div class="passage-content ${editMode ? 'editable' : ''}" 
                     ${editMode ? `data-type="passage" data-id="${passage.passage_id}"` : ''}>
        `;

        // passage_content 파싱
        const content = this.parsePassageContent(passage.passage_content);
        html += content;

        html += `
                </div>
        `;
        
        // 한글 번역 표시
        if (passage.korean_translation) {
            html += `
                <div class="passage-translation">
                    <div class="translation-title">🇰🇷 한글 번역</div>
                    <div class="translation-content">
                        ${this.parsePassageContent(passage.korean_translation)}
                    </div>
                </div>
            `;
        }
        
        html += `</div>`;
        return html;
    }

    // 지문 내용 파싱
    parsePassageContent(passageContent) {
        if (!passageContent) return '';

        // JSON 형식 처리
        if (typeof passageContent === 'object' && passageContent.content) {
            const content = passageContent.content;
            
            if (Array.isArray(content)) {
                return content.map(item => {
                    switch (item.type) {
                        case 'title':
                            return `<h3>${this.escapeHtml(item.value)}</h3>`;
                        case 'paragraph':
                            return `<p>${this.escapeHtml(item.value)}</p>`;
                        case 'list':
                            if (Array.isArray(item.value)) {
                                const listItems = item.value.map(li => `<li>${this.escapeHtml(li)}</li>`).join('');
                                return `<ul>${listItems}</ul>`;
                            }
                            return `<p>${this.escapeHtml(item.value)}</p>`;
                        default:
                            return `<p>${this.escapeHtml(item.value)}</p>`;
                    }
                }).join('');
            } else {
                return `<p>${this.escapeHtml(content)}</p>`;
            }
        }

        // 문자열 처리
        if (typeof passageContent === 'string') {
            return `<p>${this.escapeHtml(passageContent)}</p>`;
        }

        return '';
    }

    // 예문 렌더링
    renderExample(example, editMode = false) {
        let html = `
            <div class="example" data-example-id="${example.example_id}">
                <div class="example-title">💡 예문 ${example.example_id}</div>
                <div class="example-content ${editMode ? 'editable' : ''}" 
                     ${editMode ? `data-type="example" data-id="${example.example_id}"` : ''}>
                    ${this.escapeHtml(example.example_content || '')}
                </div>
        `;
        
        // 한글 번역 표시
        if (example.korean_translation) {
            html += `
                <div class="example-translation">
                    <div class="translation-title">🇰🇷 한글 번역</div>
                    <div class="translation-content">
                        ${this.escapeHtml(example.korean_translation)}
                    </div>
                </div>
            `;
        }
        
        html += `</div>`;
        return html;
    }

    // 문제 렌더링
    renderQuestion(question, number, showAnswers = false, editMode = false) {
        let html = `
            <div class="question" data-question-id="${question.question_id}">
                <div class="question-header">
                    <span class="question-number">${number}.</span>
                    <span class="question-info">
                        ${question.question_subject} | ${question.question_difficulty} | ${question.question_type}
                    </span>
                </div>
                <div class="question-text ${editMode ? 'editable' : ''}" 
                     ${editMode ? `data-type="question" data-id="${question.question_id}"` : ''}>
                    ${this.escapeHtml(question.question_text || '')}
                </div>
        `;

        // 선택지 렌더링
        if (question.question_choices && question.question_choices.length > 0) {
            html += '<div class="question-choices">';
            question.question_choices.forEach((choice, index) => {
                const marker = ['①', '②', '③', '④', '⑤'][index] || `${index + 1}.`;
                html += `
                    <div class="choice">
                        <span class="choice-marker">${marker}</span>
                        <span class="choice-text ${editMode ? 'editable' : ''}" 
                              ${editMode ? `data-type="choice" data-question-id="${question.question_id}" data-choice-index="${index}"` : ''}>
                            ${this.escapeHtml(choice)}
                        </span>
                    </div>
                `;
            });
            html += '</div>';
        }

        // 정답 및 해설 (편집 모드이거나 답안 표시 모드일 때)
        if (showAnswers || editMode) {
            if (question.correct_answer) {
                html += `
                    <div class="question-answer">
                        <strong>정답:</strong> 
                        <span class="${editMode ? 'editable' : ''}" 
                              ${editMode ? `data-type="answer" data-id="${question.question_id}"` : ''}>
                            ${this.escapeHtml(question.correct_answer)}
                        </span>
                    </div>
                `;
            }
            
            if (question.explanation) {
                html += `
                    <div class="question-explanation">
                        <strong>해설:</strong> 
                        <span class="${editMode ? 'editable' : ''}" 
                              ${editMode ? `data-type="explanation" data-id="${question.question_id}"` : ''}>
                            ${this.escapeHtml(question.explanation)}
                        </span>
                    </div>
                `;
            }

            if (question.learning_point) {
                html += `
                    <div class="question-learning-point">
                        <strong>학습포인트:</strong> 
                        <span class="${editMode ? 'editable' : ''}" 
                              ${editMode ? `data-type="learning_point" data-id="${question.question_id}"` : ''}>
                            ${this.escapeHtml(question.learning_point)}
                        </span>
                    </div>
                `;
            }
        }

        html += '</div>';
        return html;
    }

    // 답안지 렌더링
    renderAnswerSheet(data) {
        let html = `
            <div class="answer-sheet">
                <h3>📝 답안지</h3>
                <div class="answer-grid">
        `;

        if (data.questions && data.questions.length > 0) {
            data.questions.forEach((question, index) => {
                html += `
                    <div class="answer-item">
                        <span class="answer-number">${index + 1}.</span>
                        <input type="text" class="answer-input" 
                               data-question-id="${question.question_id}"
                               placeholder="답안 입력">
                    </div>
                `;
            });
        }

        html += `
                </div>
                <div class="answer-sheet-actions">
                    <button class="btn btn-primary" onclick="submitAnswers()">
                        📤 답안 제출
                    </button>
                </div>
            </div>
        `;

        return html;
    }

    // HTML 이스케이프
    escapeHtml(text) {
        if (typeof text !== 'string') return text;
        
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // 문제지 출력용 렌더링
    renderForPrint(data) {
        return `
            <div class="print-worksheet">
                <style>
                    @media print {
                        .worksheet-actions, .btn { display: none !important; }
                        .passage, .question { page-break-inside: avoid; }
                        body { font-size: 12pt; line-height: 1.4; }
                    }
                </style>
                ${this.renderWorksheet(data, { showAnswers: false, editMode: false })}
            </div>
        `;
    }

    // 문제지 목록 카드 렌더링
    renderWorksheetCard(worksheet) {
        return `
            <div class="worksheet-card" data-worksheet-id="${worksheet.worksheet_id}">
                <h3>${this.escapeHtml(worksheet.worksheet_name)}</h3>
                <div class="worksheet-meta">
                    <p><strong>학교급:</strong> ${worksheet.school_level} ${worksheet.grade}학년</p>
                    <p><strong>문제 수:</strong> ${worksheet.total_questions}문제 | 
                       <strong>시간:</strong> ${worksheet.duration}분</p>
                    <p><strong>생성일:</strong> ${this.formatDate(worksheet.created_at)}</p>
                </div>
                <div class="worksheet-actions">
                    <button class="btn btn-primary" onclick="viewWorksheet('${worksheet.worksheet_id}')">
                        📖 보기
                    </button>
                    <button class="btn btn-secondary" onclick="editWorksheet('${worksheet.worksheet_id}')">
                        ✏️ 편집
                    </button>
                    <button class="btn btn-success" onclick="solveWorksheet('${worksheet.worksheet_id}')">
                        ✍️ 풀이
                    </button>
                    <button class="btn btn-danger" onclick="deleteWorksheet('${worksheet.worksheet_id}')">
                        🗑️ 삭제
                    </button>
                </div>
            </div>
        `;
    }

    // 날짜 포맷팅
    formatDate(dateString) {
        if (!dateString) return '';
        
        const date = new Date(dateString);
        return date.toLocaleDateString('ko-KR', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    // 채점 결과 카드 렌더링
    renderGradingResultCard(result) {
        const scorePercentage = Math.round((result.total_score / result.max_score) * 100);
        const scoreClass = scorePercentage >= 80 ? 'excellent' : 
                          scorePercentage >= 60 ? 'good' : 'needs-improvement';

        return `
            <div class="grading-result-card ${scoreClass}" data-result-id="${result.id}">
                <h3>${this.escapeHtml(result.student_name)}</h3>
                <div class="result-meta">
                    <p><strong>문제지:</strong> ${this.escapeHtml(result.worksheet_name)}</p>
                    <p><strong>점수:</strong> ${result.total_score}/${result.max_score}점 (${scorePercentage}%)</p>
                    <p><strong>제출일:</strong> ${this.formatDate(result.submitted_at)}</p>
                </div>
                <div class="result-actions">
                    <button class="btn btn-primary" onclick="viewGradingResult('${result.id}')">
                        📊 상세보기
                    </button>
                    <button class="btn btn-secondary" onclick="reviewGrading('${result.id}')">
                        🔍 검수
                    </button>
                </div>
            </div>
        `;
    }
}

// 전역으로 노출
window.WorksheetRenderer = WorksheetRenderer;
