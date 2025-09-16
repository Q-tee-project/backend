/**
 * 채점 결과 편집 모듈
 */

class GradingResultEditor {
    constructor() {
        this.currentGradingResult = null;
        this.gradingEditMode = false;
    }

    // 채점 결과 상세보기
    async viewGradingResult(id) {
        try {
            console.log('채점 결과 조회:', id);
            
            // 단일 API 호출로 채점 결과와 문제지 데이터를 함께 가져옴
            const gradingResult = await ApiService.getGradingResult(id);
            console.log('채점 결과 데이터:', gradingResult);
            
            this.currentGradingResult = gradingResult;
            
            // worksheet_data에서 문제지 데이터 추출
            const worksheetData = gradingResult.worksheet_data;
            
            if (!worksheetData) {
                throw new Error('문제지 데이터를 찾을 수 없습니다.');
            }
            
            this.renderGradingResultView();
            
        } catch (error) {
            console.error('채점 결과 조회 오류:', error);
            alert('채점 결과를 불러올 수 없습니다.');
        }
    }

    // 채점 결과 뷰 렌더링 (모달 방식)
    renderGradingResultView() {
        const gradingResult = this.currentGradingResult;
        const worksheetData = gradingResult.worksheet_data;

        // 기존 모달이 있으면 제거
        const existingModal = document.querySelector('.grading-result-modal');
        if (existingModal) {
            existingModal.remove();
        }

        // 모달 생성
        const modal = document.createElement('div');
        modal.className = 'grading-result-modal';
        modal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            z-index: 10000;
            overflow-y: auto;
            padding: 20px;
            box-sizing: border-box;
        `;

        const modalContent = document.createElement('div');
        modalContent.className = 'grading-result-modal-content';
        modalContent.style.cssText = `
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 0;
            position: relative;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        `;

        // 스타일 태그를 동적으로 추가 (CSS 클래스 정의)
        const styleTag = document.createElement('style');
        styleTag.innerHTML = `
            .example-content-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-top: 15px;
            }
            .example-part {
                background-color: #f9f9f9;
                border: 1px solid #eee;
                border-radius: 8px;
                padding: 15px;
            }
            .example-part strong {
                display: block;
                margin-bottom: 10px;
                color: #555;
            }
        `;

        let html = `
            <div class="grading-result-header">
                <div class="grading-actions">
                    <button onclick="window.worksheetManager.gradingResultEditor.toggleGradingEditMode()" 
                            class="btn-secondary" id="gradingEditToggleBtn">
                        ${this.gradingEditMode ? '📖 보기 모드' : '✏️ 편집 모드'}
                    </button>
                    <button onclick="window.worksheetManager.gradingResultEditor.closeGradingResultModal()" class="btn-secondary">
                        ← 채점 결과 목록으로 돌아가기
                    </button>
                </div>
                
                <h2>${worksheetData.worksheet_name}</h2>
                <div class="grading-summary">
                    <div class="student-info">
                        <span><strong>학생:</strong> ${gradingResult.student_name}</span>
                        <span><strong>소요시간:</strong> ${Math.floor(gradingResult.completion_time / 60)}분 ${gradingResult.completion_time % 60}초</span>
                    </div>
                    <div class="score-info">
                        <span class="total-score">${gradingResult.total_score} / ${gradingResult.max_score}</span>
                        <span class="percentage">(${gradingResult.percentage.toFixed(1)}%)</span>
                    </div>
                </div>
            </div>
        `;

        // 문제들과 채점 결과 렌더링 (새로운 구조)
        if (worksheetData.questions && worksheetData.questions.length > 0) {
            console.log('📊 워크시트 데이터 구조:', worksheetData);
            console.log('📖 지문 데이터:', worksheetData.passages);
            console.log('💡 예문 데이터:', worksheetData.examples);
            
            const usedPassages = new Set(); // 이미 표시된 지문 추적
            
            worksheetData.questions.forEach((question, index) => {
                console.log(`🔍 문제 ${index + 1} 분석:`, question);
                
                const questionResult = gradingResult.question_results.find(
                    qr => qr.question_id === question.question_id
                );
                
                let questionHtml = '';
                
                // 1. 지문 렌더링 (연계된 첫 문제에서만, 중복 제거)
                let passage = null;
                if (question.passage_id && worksheetData.passages) {
                    passage = worksheetData.passages.find(p => p.passage_id === question.passage_id);
                } else if (worksheetData.passages && worksheetData.passages[index]) {
                    passage = worksheetData.passages[index];
                }
                
                if (passage && !usedPassages.has(passage.passage_id || index)) {
                    console.log(`📖 지문 표시: 문제 ${index + 1}에 지문 추가`);
                    questionHtml += this.renderPassageForGrading(passage, index);
                    usedPassages.add(passage.passage_id || index);
                }
                
                // 2. 문제 질문 + 3. 예문 + 4. 객관식 보기 + 5. 학생답 + 6. 정답 + 7. 해설 + 8. AI피드백
                questionHtml += this.renderQuestionWithResultNewStructure(question, questionResult, index + 1, worksheetData);
                
                html += questionHtml;
            });
        }

        // 모달 닫기 버튼 추가
        const closeButton = document.createElement('button');
        closeButton.innerHTML = '✕';
        closeButton.style.cssText = `
            position: absolute;
            top: 15px;
            right: 20px;
            background: #dc3545;
            color: white;
            border: none;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            font-size: 20px;
            cursor: pointer;
            z-index: 10001;
            transition: all 0.3s ease;
        `;
        closeButton.onmouseover = () => closeButton.style.background = '#c82333';
        closeButton.onmouseout = () => closeButton.style.background = '#dc3545';
        closeButton.onclick = () => this.closeGradingResultModal();

        // HTML을 모달에 넣기
        modalContent.innerHTML = html;
        modalContent.appendChild(closeButton);
        modalContent.prepend(styleTag); // 스타일 태그를 모달 컨텐츠 맨 앞에 추가
        
        // 모달을 페이지에 추가
        modal.appendChild(modalContent);
        document.body.appendChild(modal);
        
        // 모달 배경 클릭시 닫기
        modal.onclick = (e) => {
            if (e.target === modal) {
                this.closeGradingResultModal();
            }
        };
        
        // ESC 키로 닫기
        const handleKeyPress = (e) => {
            if (e.key === 'Escape') {
                this.closeGradingResultModal();
                document.removeEventListener('keydown', handleKeyPress);
            }
        };
        document.addEventListener('keydown', handleKeyPress);
    }

    // 채점 결과 모달 닫기
    closeGradingResultModal() {
        const modal = document.querySelector('.grading-result-modal');
        if (modal) {
            modal.remove();
        }
    }

    // 지문 렌더링 (채점용)
    renderPassageForGrading(passage, index) {
        const content = this.formatPassageContent(passage.original_content);
        const translation = this.formatPassageContent(passage.korean_translation);
            
        return `
            <div class="passage-section">
                <h3>📖 지문 ${index + 1}</h3>
                <div class="passage-content">
                    <div class="passage-text">${content}</div>
                    ${translation ? `
                        <div class="passage-translation">
                            <strong>번역:</strong> ${translation}
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    // 지문 내용 형식화 함수 (글 종류별 처리)
    formatPassageContent(content) {
        if (!content) return '';
        
        // 문자열인 경우 그대로 반환
        if (typeof content === 'string') return content;
        
        // 객체인 경우 글 종류에 따라 처리
        if (typeof content === 'object') {
            try {
                let html = '';
                
                // 1. article (일반 글) 형식: {"content": [{"type": "title", "value": "글의 제목"}, {"type": "paragraph", "value": "첫 번째 문단 내용"}]}
                if (content.content && Array.isArray(content.content) && !content.metadata) {
                    content.content.forEach(item => {
                        if (item.type === 'title') {
                            html += `<h4 class="passage-title">${item.value}</h4>`;
                        } else if (item.type === 'paragraph') {
                            html += `<p class="passage-paragraph">${item.value}</p>`;
                        } else if (item.type === 'list' && item.items) {
                            html += '<ul class="passage-list">';
                            item.items.forEach(listItem => {
                                html += `<li>${listItem}</li>`;
                            });
                            html += '</ul>';
                        } else if (item.type === 'key_value' && item.pairs) {
                            html += '<div class="passage-info">';
                            item.pairs.forEach(pair => {
                                html += `<div class="info-item"><strong>${pair.key}:</strong> ${pair.value}</div>`;
                            });
                            html += '</div>';
                        }
                    });
                    return html;
                }
                
                // 2. correspondence (서신/소통) 형식: {"metadata": {"sender": "발신자", "recipient": "수신자", "subject": "제목", "date": "2025-01-01"}, "content": [{"type": "paragraph", "value": "서신 내용"}]}
                else if (content.metadata && (content.metadata.sender || content.metadata.recipient || content.metadata.subject)) {
                    const meta = content.metadata;
                    html += '<div class="correspondence-header">';
                    if (meta.sender) html += `<div><strong>📤 발신자:</strong> ${meta.sender}</div>`;
                    if (meta.recipient) html += `<div><strong>📥 수신자:</strong> ${meta.recipient}</div>`;
                    if (meta.subject) html += `<div><strong>📋 제목:</strong> ${meta.subject}</div>`;
                    if (meta.date) html += `<div><strong>📅 날짜:</strong> ${meta.date}</div>`;
                    html += '</div>';
                    
                    // content 부분 처리
                    if (content.content && Array.isArray(content.content)) {
                        html += '<div class="correspondence-content">';
                        content.content.forEach(item => {
                            if (item.type === 'paragraph') {
                                html += `<p class="passage-paragraph">${item.value}</p>`;
                            }
                        });
                        html += '</div>';
                    }
                    return html;
                }
                
                // 3. dialogue (대화문) 형식: {"metadata": {"participants": ["참여자1", "참여자2"]}, "content": [{"speaker": "참여자1", "line": "첫 번째 대사"}, {"speaker": "참여자2", "line": "두 번째 대사"}]}
                else if (content.metadata && content.metadata.participants && Array.isArray(content.metadata.participants)) {
                    html += '<div class="dialogue-participants"><strong>👥 참여자:</strong> ' + 
                          content.metadata.participants.join(', ') + '</div>';
                    
                    // content 부분 처리
                    if (content.content && Array.isArray(content.content)) {
                        html += '<div class="dialogue-content">';
                        content.content.forEach(dialogue => {
                            if (dialogue.speaker && dialogue.line) {
                                html += `<div class="dialogue-line"><strong>${dialogue.speaker}:</strong> ${dialogue.line}</div>`;
                            }
                        });
                        html += '</div>';
                    }
                    return html;
                }
                
                // 4. informational (정보성 양식) 형식: {"content": [{"type": "title", "value": "안내문 제목"}, {"type": "paragraph", "value": "설명 내용"}, {"type": "list", "items": ["항목1", "항목2", "항목3"]}, {"type": "key_value", "pairs": [{"key": "장소", "value": "시청 앞"}, {"key": "시간", "value": "오후 2시"}]}]}
                else if (content.content && Array.isArray(content.content) && 
                        content.content.some(item => item.type === 'list' || item.type === 'key_value')) {
                    html += '<div class="informational-content">';
                    content.content.forEach(item => {
                        if (item.type === 'title') {
                            html += `<h4 class="passage-title">📢 ${item.value}</h4>`;
                        } else if (item.type === 'paragraph') {
                            html += `<p class="passage-paragraph">${item.value}</p>`;
                        } else if (item.type === 'list' && item.items) {
                            html += '<ul class="passage-list">';
                            item.items.forEach(listItem => {
                                html += `<li>• ${listItem}</li>`;
                            });
                            html += '</ul>';
                        } else if (item.type === 'key_value' && item.pairs) {
                            html += '<div class="passage-info">';
                            item.pairs.forEach(pair => {
                                html += `<div class="info-item"><strong>${pair.key}:</strong> ${pair.value}</div>`;
                            });
                            html += '</div>';
                        }
                    });
                    html += '</div>';
                    return html;
                }
                
                // 5. review (리뷰/후기) 형식: {"metadata": {"rating": 4.5, "product_name": "상품명", "reviewer": "리뷰어명", "date": "2025-01-01"}, "content": [{"type": "paragraph", "value": "리뷰 내용"}]}
                else if (content.metadata && (content.metadata.rating || content.metadata.product_name || content.metadata.reviewer)) {
                    const meta = content.metadata;
                    html += '<div class="review-header">';
                    if (meta.product_name) html += `<div><strong>🛍️ 상품:</strong> ${meta.product_name}</div>`;
                    if (meta.reviewer) html += `<div><strong>👤 리뷰어:</strong> ${meta.reviewer}</div>`;
                    if (meta.rating) {
                        const stars = '★'.repeat(Math.floor(meta.rating)) + (meta.rating % 1 ? '☆' : '');
                        html += `<div><strong>⭐ 평점:</strong> ${stars} (${meta.rating}/5.0)</div>`;
                    }
                    if (meta.date) html += `<div><strong>📅 날짜:</strong> ${meta.date}</div>`;
                    html += '</div>';
                    
                    // content 부분 처리
                    if (content.content && Array.isArray(content.content)) {
                        html += '<div class="review-content">';
                        content.content.forEach(item => {
                            if (item.type === 'paragraph') {
                                html += `<p class="passage-paragraph">${item.value}</p>`;
                            }
                        });
                        html += '</div>';
                    }
                    return html;
                }
                
                // 단순 객체인 경우 JSON으로 표시
                return JSON.stringify(content, null, 2);
            } catch (e) {
                return JSON.stringify(content);
            }
        }
        
        return content.toString();
    }

    // 예문 렌더링 (채점용)
    renderExampleForGrading(example, index) {
        // 1. 세 가지 데이터를 모두 가져옵니다.
        const studentContent = this.formatPassageContent(example.example_content);
        const originalContent = this.formatPassageContent(example.original_content);
        const translation = this.formatPassageContent(example.korean_translation);
        
        // 2. 새로운 HTML 구조로 렌더링합니다.
        return `
            <div class="example-section">
                <h3>💡 예문 ${index + 1}</h3>
                <div class="example-content-grid">
                    ${studentContent ? `
                        <div class="example-part">
                            <strong>학생용 예문 (문제)</strong>
                            <div class="example-text">${studentContent}</div>
                        </div>
                    ` : ''}
                    ${originalContent ? `
                        <div class="example-part">
                            <strong>원본 예문 (정답)</strong>
                            <div class="example-text original">${originalContent}</div>
                        </div>
                    ` : ''}
                    ${translation ? `
                        <div class="example-part">
                            <strong>번역</strong>
                            <div class="example-translation">${translation}</div>
                        </div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    // 새로운 구조로 문제와 채점 결과 렌더링
    renderQuestionWithResultNewStructure(question, questionResult, questionNum, worksheetData) {
        if (!questionResult) {
            console.warn(`문제 ${question.question_id}에 대한 채점 결과를 찾을 수 없습니다.`);
            return '';
        }

        const isCorrect = questionResult.is_correct;
        const score = questionResult.score;
        const maxScore = questionResult.max_score;
        const gradingMethod = questionResult.grading_method;
        
        // 학생 답안과 정답 정보
        const studentAnswer = this.currentGradingResult.student_answers[question.question_id] || '';
        const correctAnswer = questionResult.correct_answer || question.correct_answer || '';
        
        // 문제 유형을 한국어로 변환
        const questionTypeKorean = {
            'multiple_choice': '객관식',
            'short_answer': '단답형', 
            'essay': '서술형'
        }[question.question_type] || question.question_type;

        let html = `
            <div class="grading-result-question ${isCorrect ? 'correct' : 'incorrect'}">
                <div class="question-header">
                    <div class="question-info">
                        <span class="question-number">문제 ${questionNum}</span>
                        <span class="question-type-badge ${question.question_type}">${questionTypeKorean}</span>
                    </div>
                    <div class="question-score">
                        <div class="score-badge">${score} / ${maxScore}점</div>
                        <span class="grading-method ${gradingMethod}">${gradingMethod === 'ai' ? 'AI' : 'DB'}</span>
                        ${this.gradingEditMode ? `
                            <label class="correct-toggle">
                                <input type="checkbox" 
                                       data-question-id="${question.question_id}"
                                       ${isCorrect ? 'checked' : ''}
                                       onchange="window.worksheetManager.gradingResultEditor.toggleQuestionCorrect('${question.question_id}', this.checked)">
                                <span class="correct-label">정답 인정</span>
                            </label>
                        ` : ''}
                    </div>
                </div>
                
                <!-- 2. 문제 질문 -->
                <div class="question-content">
                    <div class="question-text">${question.question_text}</div>
                </div>
        `;

        // 3. 예문 렌더링 (해당 문제와 연관된 예문)
        let example = null;
        if (question.example_id && worksheetData.examples) {
            example = worksheetData.examples.find(e => e.example_id === question.example_id);
        } else if (worksheetData.examples && worksheetData.examples[questionNum - 1]) {
            example = worksheetData.examples[questionNum - 1];
        }
        
        if (example) {
            html += this.renderExampleForGrading(example, questionNum - 1);
        }

        // 4. 객관식 보기가 있는 경우 보기
        if (question.question_type === 'multiple_choice' && question.choices) {
            html += '<div class="choices">';
            question.choices.forEach((choice, index) => {
                const choiceNum = ['①', '②', '③', '④', '⑤'][index];
                const choiceValue = (index + 1).toString();
                const isStudentChoice = studentAnswer === choiceValue;
                const isCorrectChoice = correctAnswer === choiceValue;
                
                let choiceClass = 'choice';
                if (isStudentChoice && isCorrectChoice) {
                    choiceClass += ' student-correct';
                } else if (isStudentChoice) {
                    choiceClass += ' student-wrong';
                } else if (isCorrectChoice) {
                    choiceClass += ' correct-answer';
                }
                
                html += `
                    <div class="${choiceClass}">
                        <span class="choice-number">${choiceNum}</span>
                        <span class="choice-text">${choice}</span>
                        ${isStudentChoice ? '<span class="student-mark">학생 선택</span>' : ''}
                        ${isCorrectChoice ? '<span class="correct-mark">정답</span>' : ''}
                    </div>
                `;
            });
            html += '</div>';
        }

        // 5. 학생 답 + 6. 정답
        html += `
            <div class="answer-comparison">
                <div class="student-answer">
                    <strong>👤 학생 답안:</strong> 
                    <span class="answer-text ${isCorrect ? 'correct' : 'incorrect'}">${studentAnswer || '답안 없음'}</span>
                </div>
                <div class="correct-answer">
                    <strong>✅ 정답:</strong> 
                    <span class="answer-text correct">${correctAnswer}</span>
                </div>
            </div>
        `;

        // 7. 문제 해설 (있는 경우)
        if (question.explanation && question.explanation.trim()) {
            html += `
                <div class="question-explanation">
                    <div class="explanation-header">
                        <strong>💡 해설</strong>
                    </div>
                    <div class="explanation-content">
                        ${question.explanation}
                    </div>
                </div>
            `;
        }

        // 학습 포인트 (있는 경우)
        if (question.learning_points && question.learning_points.length > 0) {
            html += `
                <div class="learning-points">
                    <div class="points-header">
                        <strong>📚 학습 포인트</strong>
                    </div>
                    <ul class="points-list">
                        ${question.learning_points.map(point => `<li>${point}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        // 8. AI 피드백 (있는 경우)
        if (questionResult.ai_feedback && gradingMethod === 'ai') {
            html += `
                <div class="ai-feedback">
                    <strong>🤖 AI 피드백:</strong> ${questionResult.ai_feedback}
                    ${this.gradingEditMode && gradingMethod === 'ai' ? `
                        <div class="edit-feedback">
                            <textarea placeholder="피드백 수정..." 
                                      onblur="window.worksheetManager.gradingResultEditor.saveFeedback('${question.question_id}', this.value)"
                                      style="width: 100%; min-height: 60px; margin-top: 8px;">${questionResult.ai_feedback || ''}</textarea>
                        </div>
                    ` : ''}
                </div>
            `;
        }

        html += '</div>';
        return html;
    }

    // 기존 함수 (호환성 유지)
    renderQuestionWithResult(question, questionResult, questionNum) {
        if (!questionResult) {
            console.warn(`문제 ${question.question_id}에 대한 채점 결과를 찾을 수 없습니다.`);
            return '';
        }

        const isCorrect = questionResult.is_correct;
        const score = questionResult.score;
        const maxScore = questionResult.max_score;
        const gradingMethod = questionResult.grading_method;
        
        // 학생 답안과 정답 정보
        const studentAnswer = this.currentGradingResult.student_answers[question.question_id] || '';
        const correctAnswer = questionResult.correct_answer || question.correct_answer || '';
        
        console.log(`문제 ${questionNum} - 학생답안: "${studentAnswer}", 정답: "${correctAnswer}"`);

        // 문제 유형을 한국어로 변환
        const questionTypeKorean = {
            'multiple_choice': '객관식',
            'short_answer': '단답형', 
            'essay': '서술형'
        }[question.question_type] || question.question_type;

        let html = `
            <div class="grading-result-question ${isCorrect ? 'correct' : 'incorrect'}">
                <div class="question-header">
                    <div class="question-info">
                        <span class="question-number">문제 ${questionNum}</span>
                        <span class="question-type-badge ${question.question_type}">${questionTypeKorean}</span>
                    </div>
                    <div class="question-score">
                        <div class="score-badge">${score} / ${maxScore}점</div>
                        <span class="grading-method ${gradingMethod}">${gradingMethod === 'ai' ? 'AI' : 'DB'}</span>
                        ${this.gradingEditMode ? `
                            <label class="correct-toggle">
                                <input type="checkbox" 
                                       data-question-id="${question.question_id}"
                                       ${isCorrect ? 'checked' : ''}
                                       onchange="window.worksheetManager.gradingResultEditor.toggleQuestionCorrect('${question.question_id}', this.checked)">
                                <span class="correct-label">정답 인정</span>
                            </label>
                        ` : ''}
                    </div>
                </div>
                
                <div class="question-content">
                    <div class="question-text">${question.question_text}</div>
                </div>
        `;

        // 객관식 문제인 경우
        if (question.question_type === 'multiple_choice' && question.choices) {
            html += '<div class="choices">';
            question.choices.forEach((choice, index) => {
                const choiceNum = ['①', '②', '③', '④', '⑤'][index];
                const choiceValue = (index + 1).toString();
                const isStudentChoice = studentAnswer === choiceValue;
                const isCorrectChoice = correctAnswer === choiceValue;
                
                let choiceClass = 'choice';
                if (isStudentChoice && isCorrectChoice) {
                    choiceClass += ' student-correct';
                } else if (isStudentChoice) {
                    choiceClass += ' student-wrong';
                } else if (isCorrectChoice) {
                    choiceClass += ' correct-answer';
                }
                
                html += `
                    <div class="${choiceClass}">
                        <span class="choice-number">${choiceNum}</span>
                        <span class="choice-text">${choice}</span>
                        ${isStudentChoice ? '<span class="student-mark">학생 선택</span>' : ''}
                        ${isCorrectChoice ? '<span class="correct-mark">정답</span>' : ''}
                    </div>
                `;
            });
            html += '</div>';
        }

        // 답안 비교 섹션
        html += `
            <div class="answer-comparison">
                <div class="student-answer">
                    <strong>학생 답안:</strong> 
                    <span class="answer-text ${isCorrect ? 'correct' : 'incorrect'}">${studentAnswer || '답안 없음'}</span>
                </div>
                <div class="correct-answer">
                    <strong>정답:</strong> 
                    <span class="answer-text correct">${correctAnswer}</span>
                </div>
            </div>
        `;

        // AI 피드백 (있는 경우)
        if (questionResult.ai_feedback && gradingMethod === 'ai') {
            html += `
                <div class="ai-feedback">
                    <strong>🤖 AI 피드백:</strong> ${questionResult.ai_feedback}
                    ${this.gradingEditMode && gradingMethod === 'ai' ? `
                        <div class="edit-feedback">
                            <textarea placeholder="피드백 수정..." 
                                      onblur="window.worksheetManager.gradingResultEditor.saveFeedback('${question.question_id}', this.value)"
                                      style="width: 100%; min-height: 60px; margin-top: 8px;">${questionResult.ai_feedback || ''}</textarea>
                        </div>
                    ` : ''}
                </div>
            `;
        }

        // 문제 해설 (있는 경우)
        if (question.explanation && question.explanation.trim()) {
            html += `
                <div class="question-explanation">
                    <div class="explanation-header">
                        <strong>💡 해설</strong>
                    </div>
                    <div class="explanation-content">
                        ${question.explanation}
                    </div>
                </div>
            `;
        }

        // 학습 포인트 (있는 경우)
        if (question.learning_points && question.learning_points.length > 0) {
            html += `
                <div class="learning-points">
                    <div class="points-header">
                        <strong>📚 학습 포인트</strong>
                    </div>
                    <ul class="points-list">
                        ${question.learning_points.map(point => `<li>${point}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        html += '</div>';
        return html;
    }

    // 편집 모드 토글
    toggleGradingEditMode() {
        this.gradingEditMode = !this.gradingEditMode;
        console.log('채점 편집 모드 토글:', this.gradingEditMode);
        
        if (this.currentGradingResult) {
            this.renderGradingResultView();
        }
    }

    // 정답 인정 토글 기능
    async toggleQuestionCorrect(questionId, isCorrect) {
        try {
            if (!this.currentGradingResult) {
                console.error('현재 채점 결과가 없습니다.');
                return;
            }

            console.log(`문제 ${questionId} 정답 인정 상태 변경: ${isCorrect}`);

            // API 호출
            const reviewData = {
                question_results: {
                    [questionId]: {
                        is_correct: isCorrect
                    }
                }
            };

            const response = await ApiService.updateGradingReview(
                this.currentGradingResult.result_id, 
                reviewData
            );

            if (response) {
                console.log('정답 인정 상태 업데이트 성공:', response);
                
                // 현재 채점 결과 업데이트
                const questionResult = this.currentGradingResult.question_results.find(
                    qr => qr.question_id === questionId
                );
                
                if (questionResult) {
                    questionResult.is_correct = isCorrect;
                    // 점수도 업데이트 (백엔드에서 계산된 값 반영)
                    if (response.total_score !== undefined) {
                        this.currentGradingResult.total_score = response.total_score;
                        this.currentGradingResult.percentage = response.percentage;
                    }
                }

                // UI 새로고침
                this.renderGradingResultView();
                
                // 성공 피드백
                this.showNotification('정답 인정 상태가 업데이트되었습니다.', 'success');
            }

        } catch (error) {
            console.error('정답 인정 상태 업데이트 오류:', error);
            this.showNotification('정답 인정 상태 업데이트 중 오류가 발생했습니다.', 'error');
            
            // 체크박스 상태 되돌리기
            const checkbox = document.querySelector(`input[data-question-id="${questionId}"]`);
            if (checkbox) {
                checkbox.checked = !isCorrect;
            }
        }
    }

    // 피드백 저장
    async saveFeedback(questionId, feedback) {
        try {
            const reviewData = {
                question_results: {
                    [questionId]: {
                        feedback: feedback
                    }
                }
            };

            const response = await ApiService.updateGradingReview(
                this.currentGradingResult.result_id, 
                reviewData
            );

            if (response) {
                console.log('피드백 업데이트 성공:', response);
                
                // 현재 채점 결과 업데이트
                const questionResult = this.currentGradingResult.question_results.find(
                    qr => qr.question_id === questionId
                );
                
                if (questionResult) {
                    questionResult.ai_feedback = feedback;
                }

                this.showNotification('피드백이 업데이트되었습니다.', 'success');
            }

        } catch (error) {
            console.error('피드백 업데이트 오류:', error);
            this.showNotification('피드백 업데이트 중 오류가 발생했습니다.', 'error');
        }
    }

    // 알림 표시 함수
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 12px 20px;
            border-radius: 4px;
            color: white;
            font-weight: bold;
            z-index: 1000;
            transition: all 0.3s ease;
        `;
        
        if (type === 'success') {
            notification.style.backgroundColor = '#28a745';
        } else if (type === 'error') {
            notification.style.backgroundColor = '#dc3545';
        } else {
            notification.style.backgroundColor = '#007bff';
        }
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    // 채점 결과 목록으로 돌아가기
    showGradingResultsList() {
        // 워크시트 콘텐츠 숨기기
        const worksheetContent = document.getElementById('worksheetContent');
        if (worksheetContent) {
            worksheetContent.innerHTML = '';
        }

        // 탭 전환
        document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
        
        const resultsTab = document.querySelector('[data-tab="results"]');
        const resultsContent = document.getElementById('results-tab');
        
        if (resultsTab) resultsTab.classList.add('active');
        if (resultsContent) resultsContent.classList.add('active');
    }
}

// 전역으로 노출
window.GradingResultEditor = GradingResultEditor;
