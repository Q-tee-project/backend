// 문제지 및 답안지 렌더링 모듈

// 입력 결과 표시 함수
function displayInputResult(result) {
    const examContent = document.getElementById('examContent');
    const llmResponse = result.llm_response;
    const llmError = result.llm_error;
    
    let html = '';
    let worksheetHtml = '';
    let answerSheetHtml = '';
    
    // 제미나이 응답 결과 표시 - 이미 파싱된 객체 사용
    if (llmResponse) {
        // 백엔드에서 이미 파싱된 객체 사용
        console.log('='.repeat(80));
        console.log('🤖 파싱된 문제지 데이터:');
        console.log('='.repeat(80));
        console.log(llmResponse);
        console.log('='.repeat(80));
        
        try {
            // 전역 변수에 문제지 데이터 저장
            const state = window.getGlobalState();
            state.currentWorksheetData = llmResponse;
            window.setGlobalState(state);
            
            // 문제지 형태로 렌더링 (JSON 파싱 없이 바로 사용)
            worksheetHtml = renderExamPaper(llmResponse);
            
        } catch (parseError) {
            console.error('❌ JSON 파싱 실패:', parseError);
            console.error('원본 응답:', llmResponse);
            
            // 파싱 실패시 원본 텍스트 표시
            html += `
                <div style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; border: 2px solid #ffc107;">
                    <h3 style="color: #856404; margin-bottom: 15px; display: flex; align-items: center;">
                        ⚠️ 제미나이 응답 (JSON 파싱 실패)
                        <button onclick="copyResponse()" style="margin-left: auto; padding: 8px 15px; background: #ffc107; color: #856404; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">📋 복사</button>
                    </h3>
                    <div id="responseContent" style="background: #f8f9fa; padding: 15px; border-radius: 6px; border-left: 4px solid #ffc107; font-family: 'Courier New', monospace;  font-size: 13px; line-height: 1.4; max-height: 800px; overflow-y: auto; border: 1px solid #dee2e6;">${llmResponse}</div>
                    <div style="margin-top: 10px; font-size: 12px; color: #856404;">
                        ⚠️ JSON 형식이 올바르지 않아 원본 텍스트로 표시됩니다.
                    </div>
                </div>`;
        }
    }
    
    // 답안지 응답이 있는 경우 처리
    if (result.answer_sheet) {
        console.log('📋 파싱된 답안지 데이터:', result.answer_sheet);
        
        const processedAnswerData = result.answer_sheet;
        
        // 전역 변수에 답안지 데이터 저장
        const state = window.getGlobalState();
        state.currentAnswerData = processedAnswerData;
        window.setGlobalState(state);
        console.log('✅ currentAnswerData 설정 완료:', state.currentAnswerData);
        
        // 답안지 렌더링
        answerSheetHtml = renderAnswerSheet(processedAnswerData);
    } else {
        // 답안지가 없어도 저장 가능하도록 기본 구조 설정
        const state = window.getGlobalState();
        state.currentAnswerData = { questions: [], passages: [], examples: [] };
        window.setGlobalState(state);
    }
    
    // 문제지가 있으면 저장 버튼 표시
    if (llmResponse) {
        html += `
            <div style="text-align: center; margin: 20px 0; padding: 20px; background: #f8f9fa; border-radius: 8px; border: 2px dashed #28a745;">
                <h3 style="color: #28a745; margin-bottom: 15px;">💾 문제지 저장</h3>
                <p style="color: #6c757d; margin-bottom: 15px;">생성된 문제지와 답안지를 데이터베이스에 저장하시겠습니까?</p>
                
                <div style="margin-bottom: 20px;">
                    <label for="worksheetNameInput" style="display: block; margin-bottom: 8px; color: #495057; font-weight: bold;">📝 문제지 이름</label>
                    <input type="text" id="worksheetNameInput" value="${generateDefaultWorksheetName()}" style="
                        width: 300px;
                        max-width: 90%;
                        padding: 12px 15px;
                        border: 2px solid #dee2e6;
                        border-radius: 8px;
                        font-size: 14px;
                        text-align: center;
                        transition: border-color 0.3s ease;
                    " onfocus="this.style.borderColor='#28a745'; this.select()" onblur="this.style.borderColor='#dee2e6'">
                </div>
                
                <button onclick="saveWorksheet()" id="saveWorksheetBtn" style="
                    padding: 12px 30px; 
                    background: linear-gradient(45deg, #28a745, #20c997); 
                    color: white; 
                    border: none; 
                    border-radius: 25px; 
                    font-size: 16px; 
                    font-weight: bold; 
                    cursor: pointer; 
                    box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3);
                    transition: all 0.3s ease;
                " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 20px rgba(40, 167, 69, 0.4)'" 
                   onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 15px rgba(40, 167, 69, 0.3)'">
                    📁 문제지 저장하기
                </button>
                <div id="saveResult" style="margin-top: 15px; display: none;"></div>
            </div>`;
    }
    
    // 2컬럼 레이아웃으로 문제지와 답안지 배치 (전체 너비 확장)
    if (worksheetHtml || answerSheetHtml) {
        html += `
            <div style="width: 100%; max-width: 1800px; margin: 0 auto;">
            <div style="display: grid; grid-template-columns: 3fr 2fr; gap: 25px; margin-bottom: 20px;">
                <div style="background: #f8f9fa; border-radius: 10px; padding: 5px;">
                    <h3 style="color: #28a745; text-align: center; margin: 15px 0; padding: 10px; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        📝 문제지
                    </h3>
                    <div style="padding-right: 10px;">
                        ${worksheetHtml || '<div style="text-align: center; color: #6c757d; padding: 40px;">문제지 없음</div>'}
                    </div>
                </div>
                
                <div style="background: #f0f8ff; border-radius: 10px; padding: 5px;">
                    <h3 style="color: #17a2b8; text-align: center; margin: 15px 0; padding: 10px; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        📋 정답 및 해설
                    </h3>
                    <div style="padding-right: 10px;">
                        ${answerSheetHtml || '<div style="text-align: center; color: #6c757d; padding: 40px;">답안지 없음</div>'}
                    </div>
                </div>
            </div>
            </div>`;
    }
    
    examContent.innerHTML = html;
}

// 컨텐츠 배열을 HTML로 렌더링하는 헬퍼 함수
function renderContentArray(content) {
    let html = '';
    
    try {
        // JSON이 문자열로 저장되어 있다면 파싱
        const parsedContent = typeof content === 'string' ? JSON.parse(content) : content;
        
        if (parsedContent && parsedContent.content && Array.isArray(parsedContent.content)) {
            parsedContent.content.forEach(item => {
                if (item.type === 'title') {
                    html += `<h4 style="text-align: center; margin-bottom: 20px; font-weight: bold; color: #007bff; font-size: 1.3rem;">${item.value}</h4>`;
                } else if (item.type === 'paragraph') {
                    html += `<p style="line-height: 1.8; margin-bottom: 15px; text-align: justify; text-indent: 20px;">${item.value}</p>`;
                }
            });
        } else if (Array.isArray(parsedContent)) {
            // 직접 배열인 경우
            parsedContent.forEach(item => {
                if (item.type === 'title') {
                    html += `<h4 style="text-align: center; margin-bottom: 20px; font-weight: bold; color: #007bff; font-size: 1.3rem;">${item.value}</h4>`;
                } else if (item.type === 'paragraph') {
                    html += `<p style="line-height: 1.8; margin-bottom: 15px; text-align: justify; text-indent: 20px;">${item.value}</p>`;
                }
            });
        } else {
            // 단순 문자열인 경우
            html = parsedContent.toString();
        }
    } catch (error) {
        console.error('컨텐츠 파싱 오류:', error);
        // 파싱 실패시 원본 내용을 문자열로 변환하여 표시
        if (typeof content === 'object') {
            html = JSON.stringify(content, null, 2).replace(/\n/g, '<br>').replace(/ /g, '&nbsp;');
        } else {
            html = content.toString();
        }
    }
    
    return html;
}

// 글의 종류별 지문 렌더링 함수 (실제 AI 생성 구조에 맞춤)
function renderPassageByType(passage) {
    let html = '';
    const content = passage.passage_content;
    const passageType = passage.passage_type || 'article';

    try {
        // JSON이 문자열로 저장되어 있다면 파싱
        const parsedContent = typeof content === 'string' ? JSON.parse(content) : content;
        console.log(`🎯 [${passageType}] 지문 파싱:`, parsedContent);

        switch(passageType) {
            case 'article':
                // 일반 글: content 배열에서 type별로 처리
                console.log(`🔍 [article] content:`, parsedContent.content);
                
                if (parsedContent.content && Array.isArray(parsedContent.content)) {
                    parsedContent.content.forEach((item, index) => {
                        console.log(`   항목 ${index + 1}:`, item.type, item.value?.substring(0, 30) + '...');
                        
                        if (item.type === 'title') {
                            html += `<h4 style="text-align: center; margin-bottom: 20px; font-weight: bold; color: #007bff; font-size: 1.3rem;">${item.value}</h4>`;
                        } else if (item.type === 'paragraph') {
                            html += `<p style="line-height: 1.8; margin-bottom: 15px; text-align: justify; padding: 0 10px; text-indent: 20px;">${item.value}</p>`;
                        }
                    });
                } else {
                    console.warn(`⚠️ [article] content가 배열이 아님:`, parsedContent.content);
                }
                break;

            case 'correspondence':
                // 서신/소통: metadata + content 배열
                if (parsedContent.metadata) {
                    const meta = parsedContent.metadata;
                    html += `<div style="background: #f8f9fa; padding: 15px; margin-bottom: 15px; border-radius: 5px; border-left: 4px solid #007bff; font-family: 'Courier New', monospace;">`;
                    if (meta.sender) html += `<div style="margin-bottom: 5px;"><strong>From:</strong> ${meta.sender}</div>`;
                    if (meta.recipient) html += `<div style="margin-bottom: 5px;"><strong>To:</strong> ${meta.recipient}</div>`;
                    if (meta.subject) html += `<div style="margin-bottom: 5px;"><strong>Subject:</strong> ${meta.subject}</div>`;
                    if (meta.date) html += `<div style="margin-bottom: 5px;"><strong>Date:</strong> ${meta.date}</div>`;
                    html += `</div>`;
                }
                // content 배열에서 paragraph 처리
                if (parsedContent.content && Array.isArray(parsedContent.content)) {
                    parsedContent.content.forEach(item => {
                        if (item.type === 'paragraph') {
                            html += `<p style="line-height: 1.8; margin-bottom: 15px; text-align: justify; padding: 0 10px;">${item.value}</p>`;
                        }
                    });
                }
                break;

            case 'dialogue':
                // 대화문: participants + content 배열
                if (parsedContent.metadata && parsedContent.metadata.participants) {
                    html += `<div style="background: #f0f8ff; padding: 10px; margin-bottom: 15px; border-radius: 5px; font-size: 14px; color: #666; text-align: center;">💬 ${parsedContent.metadata.participants.join(' & ')}</div>`;
                }
                if (parsedContent.content && Array.isArray(parsedContent.content)) {
                    parsedContent.content.forEach((dialogue, index) => {
                        const bgColor = index % 2 === 0 ? '#e3f2fd' : '#f3e5f5';
                        const borderColor = index % 2 === 0 ? '#2196f3' : '#9c27b0';
                        html += `<div style="margin-bottom: 12px; padding: 12px 18px; background: ${bgColor}; border-radius: 20px; border-left: 4px solid ${borderColor}; max-width: 80%; ${index % 2 === 0 ? 'margin-right: auto;' : 'margin-left: auto;'}">`;
                        html += `<strong style="color: ${borderColor}; font-size: 14px;">${dialogue.speaker}:</strong><br>`;
                        html += `<span style="margin-top: 5px; display: inline-block;">${dialogue.line}</span>`;
                        html += `</div>`;
                    });
                }
                break;

            case 'informational':
                // 정보성 양식: content 배열에서 type별로 처리
                console.log(`🔍 [informational] content:`, parsedContent.content);
                
                if (parsedContent.content && Array.isArray(parsedContent.content)) {
                    parsedContent.content.forEach((item, index) => {
                        console.log(`   항목 ${index + 1}:`, item.type, item.value?.substring(0, 30) || item.items || item.pairs);
                        
                        if (item.type === 'title') {
                            html += `<h4 style="text-align: center; margin-bottom: 20px; font-weight: bold; color: #dc3545; padding: 12px; background: #fff3cd; border-radius: 8px; border: 2px dashed #ffc107;">${item.value}</h4>`;
                        } else if (item.type === 'paragraph') {
                            html += `<p style="line-height: 1.8; margin-bottom: 15px; text-align: justify; padding: 0 10px;">${item.value}</p>`;
                        } else if (item.type === 'list' && item.items && Array.isArray(item.items)) {
                            html += `<div style="background: #f8f9fa; padding: 15px; margin-bottom: 15px; border-radius: 5px; border-left: 4px solid #28a745;">`;
                            html += `<ul style="margin: 0; padding-left: 20px;">`;
                            item.items.forEach(listItem => {
                                html += `<li style="margin-bottom: 8px; line-height: 1.6;">${listItem}</li>`;
                            });
                            html += `</ul></div>`;
                        } else if (item.type === 'key_value' && item.pairs && Array.isArray(item.pairs)) {
                            html += `<div style="background: #e8f4fd; padding: 15px; margin-bottom: 15px; border-radius: 8px; border: 1px solid #bee5eb;">`;
                            html += `<div style="display: grid; grid-template-columns: auto 1fr; gap: 10px 20px;">`;
                            item.pairs.forEach(pair => {
                                html += `<div style="font-weight: bold; color: #0c5460; white-space: nowrap;">${pair.key}:</div>`;
                                html += `<div style="color: #212529;">${pair.value}</div>`;
                            });
                            html += `</div></div>`;
                        }
                    });
                } else {
                    console.warn(`⚠️ [informational] content가 배열이 아님:`, parsedContent.content);
                }
                break;

            case 'review':
                // 리뷰/후기: metadata + content 배열
                if (parsedContent.metadata) {
                    const meta = parsedContent.metadata;
                    html += `<div style="background: #fff8e1; padding: 15px; margin-bottom: 15px; border-radius: 8px; border-left: 4px solid #ffc107;">`;
                    if (meta.product_name) html += `<div style="margin-bottom: 8px; font-size: 16px;"><strong>📦 ${meta.product_name}</strong></div>`;
                    if (meta.reviewer) html += `<div style="margin-bottom: 5px; color: #666;"><strong>reviewer:</strong> ${meta.reviewer}</div>`;
                    if (meta.rating) {
                        const stars = '★'.repeat(Math.floor(meta.rating)) + '☆'.repeat(5 - Math.floor(meta.rating));
                        html += `<div style="margin-bottom: 5px; color: #ff9800; font-size: 18px;"><strong>rating:</strong> ${stars} (${meta.rating})</div>`;
                    }
                    if (meta.date) html += `<div style="color: #888; font-size: 14px;"><strong>date:</strong> ${meta.date}</div>`;
                    html += `</div>`;
                }
                // content 배열에서 paragraph 처리
                if (parsedContent.content && Array.isArray(parsedContent.content)) {
                    parsedContent.content.forEach(item => {
                        if (item.type === 'paragraph') {
                            html += `<p style="line-height: 1.8; margin-bottom: 15px; text-align: justify; padding: 0 10px; font-style: italic;">${item.value}</p>`;
                        }
                    });
                }
                break;

            default:
                console.warn(`알 수 없는 지문 타입: ${passageType}`);
                // 기본 처리: 데이터 구조에 따라 유연하게 표시
                if (parsedContent.title) {
                    html += `<h4 style="text-align: center; margin-bottom: 15px; font-weight: bold; color: #6c757d;">${parsedContent.title}</h4>`;
                }
                if (parsedContent.paragraphs && Array.isArray(parsedContent.paragraphs)) {
                    parsedContent.paragraphs.forEach(paragraph => {
                        html += `<p style="line-height: 1.8; margin-bottom: 15px; text-align: justify; padding: 0 10px;">${paragraph}</p>`;
                    });
                } else {
                    // 복잡한 구조는 JSON으로 표시
                    html += `<div style="line-height: 1.8; text-align: justify; padding: 15px; background: #f8f9fa; border-radius: 5px; font-family: 'Courier New', monospace; font-size: 12px;">`;
                    html += JSON.stringify(parsedContent, null, 2).replace(/\n/g, '<br>').replace(/ /g, '&nbsp;');
                    html += `</div>`;
                }
        }
        
    } catch (error) {
        console.error('🚫 지문 파싱 오류:', error, parsedContent);
        // 파싱 실패시 원본 내용 표시
        if (content && typeof content === 'object') {
            html = `<div style="line-height: 1.8; text-align: justify; padding: 15px; background: #f8f9fa; border-radius: 5px;">`;
            html += `<div style="color: #dc3545; margin-bottom: 10px; font-weight: bold;">⚠️ 파싱 실패 - 원본 데이터 표시:</div>`;
            html += JSON.stringify(content, null, 2).replace(/\n/g, '<br>').replace(/ /g, '&nbsp;');
            html += `</div>`;
        } else {
            html = `<div style="line-height: 1.8; text-align: justify; padding: 15px; background: white; border-radius: 5px;">지문을 표시할 수 없습니다.</div>`;
        }
    }

    return html;
}

// 문제지 렌더링 함수
function renderExamPaper(examData) {
    let html = `
        <div style="background: white; padding: 25px; border-radius: 10px; margin-bottom: 20px; border: 2px solid #28a745; box-shadow: 0 4px 12px rgba(40, 167, 69, 0.1);">
            <div style="text-align: center; margin-bottom: 30px; border-bottom: 2px solid #28a745; padding-bottom: 20px;">
                <h1 style="color: #28a745; margin: 0; font-size: 1.8rem;">🎓 ${examData.worksheet_name || '영어 시험 문제지'}</h1>
                <div style="margin-top: 10px; color: #6c757d; display: flex; justify-content: center; gap: 20px; flex-wrap: wrap;">
                    <span><strong>시험일:</strong> ${examData.worksheet_date || '미정'}</span>
                    <span><strong>시간:</strong> ${examData.worksheet_time || '미정'}</span>
                    <span><strong>소요시간:</strong> ${examData.worksheet_duration || '45'}분</span>
                    <span><strong>총 문제:</strong> ${examData.total_questions || '10'}문제</span>
                </div>
            </div>`;

    // 지문과 문제를 연결하여 렌더링
    let renderedPassages = new Set();
    let renderedExamples = new Set();

    // 문제 섹션
    if (examData.questions && examData.questions.length > 0) {
        html += `<div style="margin-bottom: 30px;">`;
        
        examData.questions.forEach((question, index) => {
            // 관련 지문이 있고 아직 렌더링되지 않았다면 먼저 렌더링
            if (question.question_passage_id && !renderedPassages.has(question.question_passage_id)) {
                const passage = examData.passages?.find(p => p.passage_id === question.question_passage_id);
                if (passage) {
                    // 이 지문을 사용하는 모든 문제 번호 찾기
                    const relatedQuestions = examData.questions
                        .filter(q => q.question_passage_id === question.question_passage_id)
                        .map(q => q.question_id)
                        .sort((a, b) => parseInt(a) - parseInt(b));
                    
                    const questionRange = relatedQuestions.length > 1 
                        ? `[${relatedQuestions[0]}-${relatedQuestions[relatedQuestions.length - 1]}]`
                        : `[${relatedQuestions[0]}]`;
                    
                    html += `
                        <div style="background: #f8f9fa; border: 2px solid #007bff; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
                            <h3 style="color: #007bff; margin-bottom: 15px;">📖 지문</h3>`;
                    
                    // JSON 지문 파싱 및 표시
                    if (passage.passage_content) {
                        html += renderPassageByType(passage);
                    } else {
                        // fallback: 단순 텍스트 표시
                        html += `<div style="line-height: 1.8; text-align: justify; padding: 15px; background: white; border-radius: 5px;">${passage.passage_text || '지문 내용 없음'}</div>`;
                    }
                    
                    html += `
                            <div style="text-align: center; margin-top: 20px; padding: 10px; background: #e3f2fd; border-radius: 5px;">
                                <strong style="color: #1976d2;">${questionRange} 다음을 읽고 물음에 답하시오.</strong>
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
                    </div>`;
            
            // 문제 텍스트에서 [E?], [P?] 참조 제거
            let cleanQuestionText = question.question_text;
            cleanQuestionText = cleanQuestionText.replace(/지문\s*\[P\d+\]/g, '위 지문');
            cleanQuestionText = cleanQuestionText.replace(/예문\s*\[E\d+\]/g, '다음 예문');
            
            html += `
                <div style="margin-bottom: 15px;">
                    <p style="font-size: 1.1rem; line-height: 1.6; margin: 0; font-weight: 500;">${cleanQuestionText}</p>
                </div>`;
            
            // 관련 예문이 있으면 문제 아래에 표시
            if (question.question_example_id && !renderedExamples.has(question.question_example_id)) {
                const example = examData.examples?.find(e => e.example_id === question.question_example_id);
                if (example) {
                    html += `
                        <div style="background: #fff3cd; border: 2px solid #ffc107; border-radius: 8px; padding: 15px; margin-bottom: 15px;">
                            <div style="font-family: 'Courier New', monospace; line-height: 1.5;">${example.example_content}</div>
                        </div>`;
                    renderedExamples.add(question.question_example_id);
                }
            }
            
            // 객관식 선택지 표시 (객관식인 경우에만)
            if (question.question_type === '객관식' && question.question_choices && question.question_choices.length > 0) {
                html += `<div style="margin-left: 20px;">`;
                question.question_choices.forEach((choice, choiceIndex) => {
                    const choiceLabel = String.fromCharCode(9312 + choiceIndex); // ① ② ③ ④ ⑤
                    html += `<p style="margin: 8px 0; line-height: 1.5;">${choiceLabel} ${choice}</p>`;
                });
                html += `</div>`;
            }
            
            // 주관식/서술형 답안 공간
            if (question.question_type === '단답형' || question.question_type === '주관식') {
                html += `
                    <div style="margin-top: 15px; padding: 15px; border: 1px dashed #ccc; border-radius: 4px; background: #fafafa;">
                        <span style="color: #666; font-size: 14px;">답: </span>
                        <span style="display: inline-block; width: 200px; border-bottom: 1px solid #333; margin-left: 10px;"></span>
                    </div>`;
            } else if (question.question_type === '서술형') {
                html += `
                    <div style="margin-top: 15px; padding: 15px; border: 1px dashed #ccc; border-radius: 4px; background: #fafafa; min-height: 100px;">
                        <span style="color: #666; font-size: 14px;">답안 작성란:</span>
                        <div style="margin-top: 10px; min-height: 80px; border-bottom: 1px solid #ddd;"></div>
                    </div>`;
            }
            
            html += `</div>`;
        });
        
        html += `</div>`;
    }

    html += `
            <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6;">
                <p style="color: #6c757d; margin: 0;">🎯 시험 완료 후 답안을 다시 한번 확인하세요!</p>
            </div>
        </div>`;

    return html;
}

// 답안지 렌더링 함수 (문제지와 동일한 형태로 지문/예문과 함께 표시)
function renderAnswerSheet(answerData) {
    let html = `
        <div style="background: white; padding: 30px; border-radius: 8px; margin-bottom: 20px; border: 2px solid #17a2b8; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <h2 style="color: #0c5460; margin-bottom: 25px; text-align: center; border-bottom: 3px solid #17a2b8; padding-bottom: 15px;">
                📋 정답 및 해설
            </h2>`;

    if (!answerData || !answerData.questions) {
        html += `<p style="text-align: center; color: #6c757d;">답안지 데이터가 없습니다.</p></div>`;
        return html;
    }

    const passages = answerData.passages || [];
    const examples = answerData.examples || [];
    const questions = answerData.questions || [];

    // 문제를 번호 순으로 정렬
    const sortedQuestions = [...questions].sort((a, b) => parseInt(a.question_id) - parseInt(b.question_id));
    
    // 이미 표시된 지문/예문을 추적
    const processedPassages = new Set();
    const processedExamples = new Set();
    
    console.log('📋 답안지 렌더링 시작:', { 
        passages: passages.length, 
        examples: examples.length, 
        questions: questions.length 
    });
    
    sortedQuestions.forEach(question => {
        console.log(`📝 처리 중인 문제 ${question.question_id}:`, {
            passage_id: question.passage_id,
            question_passage_id: question.question_passage_id,
            example_id: question.example_id
        });

        // 지문이 있는 문제 처리
        const passageId = question.passage_id || question.question_passage_id;
        
        // 지문을 첫 번째 관련 문제에서만 표시
        if (passageId && !processedPassages.has(passageId)) {
            const relatedPassage = passages.find(p => p.passage_id === passageId);
            if (relatedPassage) {
                console.log(`📖 지문 ${passageId} 첫 번째 표시 (문제 ${question.question_id}에서)`);
                processedPassages.add(passageId);
                
                // 이 지문을 사용하는 모든 문제 번호 찾기
                const relatedQuestions = questions
                    .filter(q => (q.passage_id === passageId || q.question_passage_id === passageId))
                    .map(q => q.question_id)
                    .sort((a, b) => parseInt(a) - parseInt(b));
                
                const questionRange = relatedQuestions.length > 1 
                    ? `[${relatedQuestions[0]}-${relatedQuestions[relatedQuestions.length - 1]}]`
                    : `[${relatedQuestions[0]}]`;
                
                html += `
                    <div style="background: #f8f9fa; border: 2px solid #007bff; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
                        <h3 style="color: #007bff; margin-bottom: 15px;">📖 지문 (원문)</h3>`;
                
                // 원문 지문 표시
                if (relatedPassage.original_content) {
                    html += `<div style="line-height: 1.8; text-align: justify; padding: 15px; background: white; border-radius: 5px; margin-bottom: 15px;">`;
                    html += renderContentArray(relatedPassage.original_content);
                    html += `</div>`;
                }
                
                // 한글 번역 표시
                if (relatedPassage.korean_translation) {
                    html += `
                        <div style="background: #e8f5e8; border: 1px solid #28a745; border-radius: 5px; padding: 15px;">
                            <h4 style="color: #155724; margin-bottom: 10px;">🇰🇷 한글 번역</h4>
                            <div style="line-height: 1.8; text-align: justify;">`;
                    html += renderContentArray(relatedPassage.korean_translation);
                    html += `</div>
                        </div>`;
                }
                
                html += `
                        <div style="text-align: center; margin-top: 20px; padding: 10px; background: #e3f2fd; border-radius: 5px;">
                            <strong style="color: #1976d2;">${questionRange} 다음을 읽고 물음에 답하시오.</strong>
                        </div>
                    </div>`;
            }
        }
        
        // 예문이 있는 문제 처리
        const exampleId = question.example_id;
        if (exampleId && !processedExamples.has(exampleId)) {
            const relatedExample = examples.find(e => e.example_id === exampleId);
            if (relatedExample) {
                console.log(`📝 예문 ${exampleId} 표시 (문제 ${question.question_id}에서)`);
                processedExamples.add(exampleId);
                
                html += `
                    <div style="background: #fff3cd; border: 2px solid #ffc107; border-radius: 8px; padding: 15px; margin-bottom: 20px;">
                        <h4 style="color: #856404; margin-bottom: 10px;">📝 예문</h4>`;
                
                // 원문 예문 표시
                if (relatedExample.original_content) {
                    html += `<div style="font-family: 'Courier New', monospace; line-height: 1.5; margin-bottom: 10px;">`;
                    html += renderContentArray(relatedExample.original_content);
                    html += `</div>`;
                }
                
                // 한글 번역 표시
                if (relatedExample.korean_translation) {
                    html += `
                        <div style="background: #e8f5e8; border: 1px solid #28a745; border-radius: 5px; padding: 10px;">
                            <div style="font-size: 14px; color: #155724; margin-bottom: 5px;">🇰🇷 한글 번역:</div>
                            <div style="line-height: 1.5;">`;
                    html += renderContentArray(relatedExample.korean_translation);
                    html += `</div>
                        </div>`;
                }
                
                html += `</div>`;
            }
        }
        
        // 문제와 정답/해설 표시
        html += `
            <div style="background: white; border: 2px solid #e9ecef; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
                <div style="display: flex; align-items: center; margin-bottom: 15px;">
                    <span style="background: #dc3545; color: white; padding: 5px 12px; border-radius: 20px; font-weight: bold; margin-right: 15px;">
                        ${question.question_id}번
                    </span>
                    <div style="display: flex; gap: 10px;">
                        <span style="background: #28a745; color: white; padding: 3px 8px; border-radius: 12px; font-size: 12px;">
                            정답: ${question.correct_answer || 'N/A'}
                        </span>
                    </div>
                </div>`;
        
        // 해설 표시
        if (question.explanation) {
            html += `
                <div style="background: #f8f9fa; border-left: 4px solid #17a2b8; padding: 15px; margin-bottom: 15px; border-radius: 0 5px 5px 0;">
                    <h4 style="color: #0c5460; margin-bottom: 10px;">💡 해설</h4>
                    <div style="line-height: 1.6;">${question.explanation}</div>
                </div>`;
        }
        
        // 학습 포인트 표시
        if (question.learning_point) {
            html += `
                <div style="background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; border-radius: 0 5px 5px 0;">
                    <h4 style="color: #856404; margin-bottom: 10px;">🎯 학습 포인트</h4>
                    <div style="line-height: 1.6;">${question.learning_point}</div>
                </div>`;
        }
        
        html += `</div>`;
    });

    html += `</div>`;
    return html;
}

// 기본 문제지 이름 생성 함수
function generateDefaultWorksheetName() {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    
    return `영어문제지_${year}${month}${day}_${hours}${minutes}`;
}

// 전역 함수로 노출
window.displayInputResult = displayInputResult;
window.renderContentArray = renderContentArray;
window.renderPassageByType = renderPassageByType;
window.renderExamPaper = renderExamPaper;
window.renderAnswerSheet = renderAnswerSheet;
window.generateDefaultWorksheetName = generateDefaultWorksheetName;
