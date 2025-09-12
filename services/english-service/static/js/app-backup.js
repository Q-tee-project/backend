// 문제 생성 옵션 설정 페이지 JavaScript

let categories = {};

// 페이지 로드 시 카테고리 데이터 가져오기
async function loadCategories() {
    try {
        categories = await apiService.loadCategories();
        console.log('카테고리 로드됨:', categories);
    } catch (error) {
        console.error('카테고리 로드 실패:', error);
    }
}

// 현재 선택 상태를 저장할 객체
let selectedDetails = {
    reading_types: [],
    grammar_categories: [],
    grammar_topics: {},
    vocabulary_categories: []
};

// 영역 선택에 따른 세부 영역 표시
function updateSubjectDetails() {
    // 현재 선택된 세부 항목들을 저장
    saveCurrentSelections();
    
    const selectedSubjects = [];
    document.querySelectorAll('input[name="subjects"]:checked').forEach(checkbox => {
        selectedSubjects.push(checkbox.value);
    });
    
    const detailsDiv = document.getElementById('subjectDetails');
    
    if (selectedSubjects.length === 0) {
        detailsDiv.innerHTML = '';
        return;
    }

    let html = '<div class="section-title">세부 영역 선택</div>';
    
    // 독해가 선택된 경우
    if (selectedSubjects.includes('독해') && categories.reading_types) {
        html += '<div style="margin-bottom: 20px;">';
        html += '<h4 style="color: #007bff; margin-bottom: 10px;">📖 독해 유형</h4>';
        html += '<div class="checkbox-group">';
        categories.reading_types.forEach(type => {
            const isChecked = selectedDetails.reading_types.includes(type.name) ? 'checked' : '';
            html += `
                <div class="checkbox-item">
                    <input type="checkbox" id="reading_${type.id}" value="${type.name}" name="reading_types" ${isChecked}>
                    <label for="reading_${type.id}">${type.name}</label>
                </div>
            `;
        });
        html += '</div></div>';
    }
    
    // 문법이 선택된 경우
    if (selectedSubjects.includes('문법') && categories.grammar_categories) {
        html += '<div style="margin-bottom: 20px;">';
        html += '<h4 style="color: #007bff; margin-bottom: 10px;">📝 문법 카테고리</h4>';
        categories.grammar_categories.forEach(cat => {
            const isCatChecked = selectedDetails.grammar_categories.includes(cat.name) ? 'checked' : '';
            const topicsVisible = selectedDetails.grammar_categories.includes(cat.name) ? 'block' : 'none';
            
            html += `
                <div style="margin-bottom: 15px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; background: #f9f9f9;">
                    <div class="checkbox-item" style="margin-bottom: 10px;">
                        <input type="checkbox" id="grammar_cat_${cat.id}" value="${cat.name}" name="grammar_categories" onchange="toggleGrammarTopics(${cat.id})" ${isCatChecked}>
                        <label for="grammar_cat_${cat.id}" style="font-weight: bold;">${cat.name}</label>
                    </div>
                    <div id="grammar_topics_${cat.id}" style="margin-left: 20px; display: ${topicsVisible};">
                        <div class="checkbox-group">
            `;
            if (cat.topics && cat.topics.length > 0) {
                cat.topics.forEach(topic => {
                    const isTopicChecked = selectedDetails.grammar_topics.includes(topic.name) ? 'checked' : '';
                    html += `
                        <div class="checkbox-item">
                            <input type="checkbox" id="topic_${topic.id}" value="${topic.name}" name="grammar_topics_${cat.id}" ${isTopicChecked}>
                            <label for="topic_${topic.id}">${topic.name}</label>
                        </div>
                    `;
                });
            }
            html += `
                        </div>
                    </div>
                </div>
            `;
        });
        html += '</div>';
    }
    
    // 어휘가 선택된 경우
    if (selectedSubjects.includes('어휘') && categories.vocabulary_categories) {
        html += '<div style="margin-bottom: 20px;">';
        html += '<h4 style="color: #007bff; margin-bottom: 10px;">📚 어휘 카테고리</h4>';
        html += '<div class="checkbox-group">';
        categories.vocabulary_categories.forEach(cat => {
            const isChecked = selectedDetails.vocabulary_categories.includes(cat.name) ? 'checked' : '';
            html += `
                <div class="checkbox-item">
                    <input type="checkbox" id="vocab_${cat.id}" value="${cat.name}" name="vocabulary_categories" ${isChecked}>
                    <label for="vocab_${cat.id}">${cat.name}</label>
                </div>
            `;
        });
        html += '</div></div>';
    }
    
    detailsDiv.innerHTML = html;
}

// 현재 선택된 세부 항목들을 저장하는 함수
function saveCurrentSelections() {
    // 독해 유형 저장 (텍스트 값으로)
    selectedDetails.reading_types = [];
    document.querySelectorAll('input[name="reading_types"]:checked').forEach(cb => {
        selectedDetails.reading_types.push(cb.value);
    });
    
    // 문법 카테고리 저장 (텍스트 값으로)
    selectedDetails.grammar_categories = [];
    document.querySelectorAll('input[name="grammar_categories"]:checked').forEach(cb => {
        selectedDetails.grammar_categories.push(cb.value);
    });
    
    // 문법 토픽 저장 (텍스트 값으로)
    selectedDetails.grammar_topics = [];
    document.querySelectorAll('input[name^="grammar_topics_"]:checked').forEach(cb => {
        selectedDetails.grammar_topics.push(cb.value);
    });
    
    // 어휘 카테고리 저장 (텍스트 값으로)
    selectedDetails.vocabulary_categories = [];
    document.querySelectorAll('input[name="vocabulary_categories"]:checked').forEach(cb => {
        selectedDetails.vocabulary_categories.push(cb.value);
    });
}

// 문법 카테고리 선택 시 토픽 표시/숨김
function toggleGrammarTopics(categoryId) {
    const checkbox = document.getElementById(`grammar_cat_${categoryId}`);
    const topicsDiv = document.getElementById(`grammar_topics_${categoryId}`);
    
    if (checkbox.checked) {
        topicsDiv.style.display = 'block';
    } else {
        topicsDiv.style.display = 'none';
        // 카테고리 해제 시 해당 토픽들도 모두 해제
        const topicCheckboxes = topicsDiv.querySelectorAll('input[type="checkbox"]');
        topicCheckboxes.forEach(cb => cb.checked = false);
    }
}

// 영역별 비율 업데이트
function updateSubjectRatios() {
    const selectedSubjects = [];
    document.querySelectorAll('input[name="subjects"]:checked').forEach(checkbox => {
        selectedSubjects.push(checkbox.value);
    });
    
    const ratiosDiv = document.getElementById('subjectRatios');
    
    if (selectedSubjects.length === 0) {
        ratiosDiv.innerHTML = '';
        return;
    }

    let html = '';
    const defaultRatio = Math.floor(100 / selectedSubjects.length);
    const remainder = 100 % selectedSubjects.length;
    
    selectedSubjects.forEach((subject, index) => {
        const ratio = index === 0 ? defaultRatio + remainder : defaultRatio;
        html += `
            <div class="ratio-item">
                <label for="ratio${subject}">${subject} 비율</label>
                <input type="range" id="ratio${subject}" min="0" max="100" value="${ratio}" oninput="updateTotalRatio()">
                <input type="number" id="ratio${subject}Num" min="0" max="100" value="${ratio}" oninput="syncSubjectRatio('ratio${subject}')" style="width: 60px; margin-left: 10px;">
                <span class="range-value" id="ratio${subject}Value">${ratio}%</span>
            </div>
        `;
    });
    
    ratiosDiv.innerHTML = html;
    updateTotalRatio();
}

// 총 비율 계산
function updateTotalRatio() {
    const ranges = document.querySelectorAll('#subjectRatios input[type="range"]');
    let total = 0;
    
    ranges.forEach(range => {
        const value = parseInt(range.value);
        total += value;
        
        // 슬라이더 값을 숫자 입력란에 동기화
        const numberInput = document.getElementById(range.id + 'Num');
        if (numberInput) {
            numberInput.value = value;
        }
        
        // 퍼센트 표시 업데이트
        const valueSpan = document.getElementById(range.id + 'Value');
        if (valueSpan) {
            valueSpan.textContent = value + '%';
        }
    });
    
    document.getElementById('totalRatio').textContent = total;
    document.getElementById('totalRatio').style.color = total === 100 ? '#28a745' : '#dc3545';
}

// 숫자 입력에서 영역별 슬라이더로 동기화
function syncSubjectRatio(sliderId) {
    const slider = document.getElementById(sliderId);
    const numberInput = document.getElementById(sliderId + 'Num');
    
    if (slider && numberInput) {
        slider.value = numberInput.value;
        updateTotalRatio();
    }
}

// 문제 형식별 수 업데이트
function updateFormatCounts() {
    const format = document.getElementById('questionFormat').value;
    const countsDiv = document.getElementById('formatCounts');
    const totalQuestions = parseInt(document.getElementById('totalQuestions').value) || 20;
    
    if (!format || format === '전체') {
        countsDiv.innerHTML = `
            <div class="section-title">형식별 문제 비율</div>
            <div class="ratio-group">
                <div class="ratio-item">
                    <label for="ratioMultiple">객관식</label>
                    <input type="range" id="ratioMultiple" min="0" max="100" value="60" oninput="updateFormatRatio()">
                    <input type="number" id="ratioMultipleNum" min="0" max="100" value="60" oninput="syncFormatRatio('ratioMultiple')" style="width: 60px; margin-left: 10px;">
                    <span class="range-value" id="ratioMultipleValue">60%</span>
                </div>
                <div class="ratio-item">
                    <label for="ratioShort">주관식</label>
                    <input type="range" id="ratioShort" min="0" max="100" value="30" oninput="updateFormatRatio()">
                    <input type="number" id="ratioShortNum" min="0" max="100" value="30" oninput="syncFormatRatio('ratioShort')" style="width: 60px; margin-left: 10px;">
                    <span class="range-value" id="ratioShortValue">30%</span>
                </div>
                <div class="ratio-item">
                    <label for="ratioEssay">서술형</label>
                    <input type="range" id="ratioEssay" min="0" max="100" value="10" oninput="updateFormatRatio()">
                    <input type="number" id="ratioEssayNum" min="0" max="100" value="10" oninput="syncFormatRatio('ratioEssay')" style="width: 60px; margin-left: 10px;">
                    <span class="range-value" id="ratioEssayValue">10%</span>
                </div>
            </div>
            <div style="margin-top: 10px; font-size: 14px; color: #666;">
                총 비율: <span id="totalFormatRatio">100</span>% / 100%
            </div>
        `;
    } else {
        countsDiv.innerHTML = `
            <div class="section-title">문제 수</div>
            <div class="ratio-item">
                <label for="countSingle">${format} 문제 수</label>
                <input type="number" id="countSingle" min="0" max="${totalQuestions}" value="${totalQuestions}" readonly>
            </div>
        `;
    }
    updateFormatRatio();
}

// 형식별 비율 업데이트
function updateFormatRatio() {
    const ratioMultiple = parseInt(document.getElementById('ratioMultiple')?.value) || 0;
    const ratioShort = parseInt(document.getElementById('ratioShort')?.value) || 0;
    const ratioEssay = parseInt(document.getElementById('ratioEssay')?.value) || 0;
    
    // 슬라이더 값을 숫자 입력란에 동기화
    const multipleNum = document.getElementById('ratioMultipleNum');
    const shortNum = document.getElementById('ratioShortNum');
    const essayNum = document.getElementById('ratioEssayNum');
    
    if (multipleNum) multipleNum.value = ratioMultiple;
    if (shortNum) shortNum.value = ratioShort;
    if (essayNum) essayNum.value = ratioEssay;
    
    // 퍼센트 표시 업데이트
    const multipleValue = document.getElementById('ratioMultipleValue');
    const shortValue = document.getElementById('ratioShortValue');
    const essayValue = document.getElementById('ratioEssayValue');
    
    if (multipleValue) multipleValue.textContent = ratioMultiple + '%';
    if (shortValue) shortValue.textContent = ratioShort + '%';
    if (essayValue) essayValue.textContent = ratioEssay + '%';
    
    const total = ratioMultiple + ratioShort + ratioEssay;
    
    const totalSpan = document.getElementById('totalFormatRatio');
    if (totalSpan) {
        totalSpan.textContent = total;
        totalSpan.style.color = total === 100 ? '#28a745' : '#dc3545';
    }
}

// 숫자 입력에서 슬라이더로 동기화
function syncFormatRatio(sliderId) {
    const slider = document.getElementById(sliderId);
    const numberInput = document.getElementById(sliderId + 'Num');
    
    if (slider && numberInput) {
        slider.value = numberInput.value;
        updateFormatRatio();
    }
}

// 난이도 비율 업데이트
function updateDifficultyRatio() {
    const high = parseInt(document.getElementById('difficultyHigh').value);
    const medium = parseInt(document.getElementById('difficultyMedium').value);
    const low = parseInt(document.getElementById('difficultyLow').value);
    
    // 슬라이더 값을 숫자 입력란에 동기화
    const highNum = document.getElementById('difficultyHighNum');
    const mediumNum = document.getElementById('difficultyMediumNum');
    const lowNum = document.getElementById('difficultyLowNum');
    
    if (highNum) highNum.value = high;
    if (mediumNum) mediumNum.value = medium;
    if (lowNum) lowNum.value = low;
    
    // 퍼센트 표시 업데이트
    document.getElementById('difficultyHighValue').textContent = high + '%';
    document.getElementById('difficultyMediumValue').textContent = medium + '%';
    document.getElementById('difficultyLowValue').textContent = low + '%';
    
    const total = high + medium + low;
    document.getElementById('totalDifficultyRatio').textContent = total;
    document.getElementById('totalDifficultyRatio').style.color = total === 100 ? '#28a745' : '#dc3545';
}

// 숫자 입력에서 난이도 슬라이더로 동기화
function syncDifficultyRatio(sliderId) {
    const slider = document.getElementById(sliderId);
    const numberInput = document.getElementById(sliderId + 'Num');
    
    if (slider && numberInput) {
        slider.value = numberInput.value;
        updateDifficultyRatio();
    }
}

// 폼 데이터 수집
function collectFormData() {
    // 선택된 주요 영역들 수집
    const selectedSubjects = [];
    document.querySelectorAll('input[name="subjects"]:checked').forEach(checkbox => {
        selectedSubjects.push(checkbox.value);
    });

    const data = {
        school_level: document.getElementById('schoolLevel').value,
        grade: parseInt(document.getElementById('grade').value),
        total_questions: parseInt(document.getElementById('totalQuestions').value),
        subjects: selectedSubjects, // 복수 선택 가능
        subject_details: [],
        subject_ratios: [],
        question_format: document.getElementById('questionFormat').value,
        format_counts: [],
        difficulty_distribution: []
    };

    // 세부 영역 수집
    const subjectDetails = {};
    
    // 독해 유형 수집 (텍스트 값으로)
    const selectedReadingTypes = [];
    document.querySelectorAll('input[name="reading_types"]:checked').forEach(cb => {
        selectedReadingTypes.push(cb.value); // ID가 아닌 텍스트 값
    });
    if (selectedReadingTypes.length > 0) {
        subjectDetails.reading_types = selectedReadingTypes;
    }

    // 문법 카테고리 및 토픽 수집 (텍스트 값으로)
    const selectedGrammarCategories = [];
    const selectedGrammarTopics = [];
    document.querySelectorAll('input[name="grammar_categories"]:checked').forEach(cb => {
        selectedGrammarCategories.push(cb.value); // ID가 아닌 텍스트 값
    });
    document.querySelectorAll('input[name^="grammar_topics_"]:checked').forEach(cb => {
        selectedGrammarTopics.push(cb.value); // ID가 아닌 텍스트 값
    });
    if (selectedGrammarCategories.length > 0) {
        subjectDetails.grammar_categories = selectedGrammarCategories;
    }
    if (selectedGrammarTopics.length > 0) {
        subjectDetails.grammar_topics = selectedGrammarTopics;
    }

    // 어휘 카테고리 수집 (텍스트 값으로)
    const selectedVocabCategories = [];
    document.querySelectorAll('input[name="vocabulary_categories"]:checked').forEach(cb => {
        selectedVocabCategories.push(cb.value); // ID가 아닌 텍스트 값
    });
    if (selectedVocabCategories.length > 0) {
        subjectDetails.vocabulary_categories = selectedVocabCategories;
    }

    data.subject_details = subjectDetails;

    // 영역별 비율 수집
    selectedSubjects.forEach(subject => {
        const ratioElement = document.getElementById(`ratio${subject}`);
        if (ratioElement) {
            data.subject_ratios.push({
                subject: subject,
                ratio: parseInt(ratioElement.value)
            });
        }
    });

    // 형식별 문제 비율 수집
    const format = data.question_format;
    if (format === '전체') {
        const multipleElement = document.getElementById('ratioMultiple');
        const shortElement = document.getElementById('ratioShort');
        const essayElement = document.getElementById('ratioEssay');
        
        data.format_ratios = [
            { format: '객관식', ratio: multipleElement ? parseInt(multipleElement.value) : 0 },
            { format: '주관식', ratio: shortElement ? parseInt(shortElement.value) : 0 },
            { format: '서술형', ratio: essayElement ? parseInt(essayElement.value) : 0 }
        ];
    } else {
        data.format_ratios = [
            { format: format, ratio: 100 }
        ];
    }

    // 난이도 분배 수집
    data.difficulty_distribution = [
        { difficulty: '상', ratio: parseInt(document.getElementById('difficultyHigh').value) },
        { difficulty: '중', ratio: parseInt(document.getElementById('difficultyMedium').value) },
        { difficulty: '하', ratio: parseInt(document.getElementById('difficultyLow').value) }
    ];

    // 추가 요구사항 수집
    const additionalRequirements = document.getElementById('additionalRequirements').value.trim();
    if (additionalRequirements) {
        data.additional_requirements = additionalRequirements;
    }

    return data;
}

// 문제지 생성 함수
async function generateExam(event) {
    event.preventDefault(); // 기본 폼 제출 방지
    console.log('🚨 generateExam 함수 시작!');
    
    // 로딩 표시
    document.getElementById('loading').style.display = 'block';
    document.getElementById('examResult').style.display = 'none';
    document.getElementById('error').style.display = 'none';

    try {
        // 폼 데이터 수집
        const formData = collectFormData();
        
        // 브라우저에서 요청 콘솔 출력
        console.log('='.repeat(80));
        console.log('🚀 문제지 생성 요청 시작!');
        console.log('='.repeat(80));
        console.log('📊 요청 데이터:', formData);
        console.log('🏫 학교급:', formData.school_level);
        console.log('📚 학년:', formData.grade);
        console.log('📝 총 문제 수:', formData.total_questions);
        console.log('🎯 선택 영역:', formData.subjects);
        console.log('='.repeat(80));

        // API 호출
        const result = await apiService.generateQuestionOptions(formData);
        
        if (result.status === 'success') {
            // 기존 방식으로 결과 표시 (JSON 파싱 제거만 함)
            displayInputResult(result);
            document.getElementById('examResult').style.display = 'block';
        } else {
            throw new Error(result.message || '서버 오류');
        }

    } catch (error) {
        console.error('='.repeat(80));
        console.error('❌ 문제지 생성 오류 발생:');
        console.error('='.repeat(80));
        console.error('오류 메시지:', error.message);
        console.error('전체 오류 객체:', error);
        if (typeof result !== 'undefined') {
            console.error('서버 응답:', result);
        }
        console.error('='.repeat(80));
        
        document.getElementById('errorData').textContent = error.message;
        document.getElementById('error').style.display = 'block';
    } finally {
        document.getElementById('loading').style.display = 'none';
    }
}



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
            currentWorksheetData = llmResponse;
            
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
        
        // 답안지 데이터 구조 검증 및 변환
        let processedAnswerData = result.answer_sheet;
        
        // answer_sheet 래퍼가 있는 경우 내부 데이터 추출
        if (result.answer_sheet.answer_sheet) {
            processedAnswerData = result.answer_sheet.answer_sheet;
        }
        
        // 전역 변수에 답안지 데이터 저장
        currentAnswerData = processedAnswerData;
        console.log('✅ currentAnswerData 설정 완료:', currentAnswerData);
        
        // 답안지 렌더링
        answerSheetHtml = renderAnswerSheet(processedAnswerData);
    } else {
        // 답안지가 없어도 저장 가능하도록 기본 구조 설정
        currentAnswerData = { questions: [], passages: [], examples: [] };
    }
    
    // 문제지와 답안지가 모두 있으면 저장 버튼 표시
    if (llmResponse && result.answer_sheet) {
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
                
                // 이 지문과 관련된 모든 문제 ID 찾기 (표시용)
                const relatedQuestionIds = sortedQuestions
                    .filter(q => (q.passage_id || q.question_passage_id) === passageId)
                    .map(q => q.question_id)
                    .sort((a, b) => parseInt(a) - parseInt(b));
                
                html += `
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 15px; border-left: 4px solid #17a2b8;">
                        <div style="display: flex; align-items: center; margin-bottom: 15px;">
                            <h3 style="color: #0c5460; margin: 0; margin-right: 15px;">📖 지문 ${relatedPassage.passage_id}</h3>
                            ${relatedPassage.text_type ? `<span style="background: #17a2b8; color: white; padding: 3px 8px; border-radius: 12px; font-size: 12px; font-weight: bold;">${relatedPassage.text_type}</span>` : ''}
                        </div>
                        <div style="font-weight: bold; color: #495057; margin-bottom: 10px;">[${relatedQuestionIds.join('-')}] 다음을 읽고 물음에 답하시오.</div>
                        <div style="background: white; padding: 15px; border-radius: 6px; line-height: 1.6; margin-bottom: 10px; border: 1px solid #dee2e6;">
                            <div style="margin-bottom: 15px;">
                                <div style="font-weight: bold; color: #007bff; margin-bottom: 8px;">📝 영어 원문</div>
                                <div style="line-height: 1.8; font-size: 15px;">${relatedPassage.original_content}</div>
                            </div>
                            ${relatedPassage.korean_translation ? `
                            <div style="padding-top: 15px; border-top: 1px solid #e9ecef;">
                                <div style="font-weight: bold; color: #6c757d; margin-bottom: 8px;">🇰🇷 한글 번역</div>
                                <div style="line-height: 1.8; font-size: 15px; color: #495057;">${relatedPassage.korean_translation}</div>
                            </div>
                            ` : ''}
                        </div>
                    </div>`;
            }
        }

        // 현재 문제의 해설 표시 (지문이 있는 경우)
        if (passageId) {
            html += `
                <div style="background: white; padding: 15px; border-radius: 6px; margin-bottom: 20px; border: 1px solid #dee2e6;">
                    <div style="display: flex; align-items: center; margin-bottom: 10px;">
                        <span style="background: #17a2b8; color: white; padding: 5px 12px; border-radius: 20px; font-weight: bold; margin-right: 15px;">문제 ${question.question_id}</span>
                        <span style="background: #28a745; color: white; padding: 5px 12px; border-radius: 4px; font-weight: bold;">정답: ${question.correct_answer}</span>
                    </div>
                    <div style="margin-bottom: 10px;">
                        <h5 style="color: #495057; margin-bottom: 8px;">📝 해설</h5>
                        <div style="background: #f8f9fa; padding: 15px; border-radius: 4px; line-height: 1.6; color: #212529;">${question.explanation}</div>
                    </div>
                    ${question.learning_point ? `
                        <div>
                            <h5 style="color: #495057; margin-bottom: 8px;">💡 학습 포인트</h5>
                            <div style="background: #e7f3ff; padding: 15px; border-radius: 4px; border-left: 4px solid #007bff; color: #004085;">${question.learning_point}</div>
                        </div>
                    ` : ''}
                </div>`;
        }
        
        // 예문이 있는 문제 처리 (지문이 없는 경우에만)
        else if (question.example_id && !passageId) {
            // 예문을 첫 번째 관련 문제에서만 표시
            if (!processedExamples.has(question.example_id)) {
                const relatedExample = examples.find(e => e.example_id === question.example_id);
                if (relatedExample) {
                    console.log(`💬 예문 ${question.example_id} 첫 번째 표시 (문제 ${question.question_id}에서)`);
                    processedExamples.add(question.example_id);
                    
                    html += `
                        <div style="background: #fff3cd; padding: 20px; border-radius: 8px; margin-bottom: 15px; border-left: 4px solid #ffc107;">
                            <h3 style="color: #856404; margin-bottom: 15px;">💬 예문 ${relatedExample.example_id}</h3>
                            <div style="background: white; padding: 15px; border-radius: 6px; line-height: 1.6; margin-bottom: 10px; border: 1px solid #dee2e6;">
                                <div style="margin-bottom: 15px;">
                                    <div style="font-weight: bold; color: #007bff; margin-bottom: 8px;">📝 영어 원문</div>
                                    <div style="line-height: 1.8; font-size: 15px;">${relatedExample.original_content}</div>
                                </div>
                                ${relatedExample.korean_translation ? `
                                <div style="padding-top: 15px; border-top: 1px solid #e9ecef;">
                                    <div style="font-weight: bold; color: #6c757d; margin-bottom: 8px;">🇰🇷 한글 번역</div>
                                    <div style="line-height: 1.8; font-size: 15px; color: #495057;">${relatedExample.korean_translation}</div>
                                </div>
                                ` : ''}
                            </div>
                        </div>`;
                }
            }
            
            // 현재 문제의 해설 표시 (예문이 있는 경우)
            html += `
                <div style="background: white; padding: 15px; border-radius: 6px; margin-bottom: 20px; border: 1px solid #dee2e6;">
                    <div style="display: flex; align-items: center; margin-bottom: 10px;">
                        <span style="background: #17a2b8; color: white; padding: 5px 12px; border-radius: 20px; font-weight: bold; margin-right: 15px;">문제 ${question.question_id}</span>
                        <span style="background: #28a745; color: white; padding: 5px 12px; border-radius: 4px; font-weight: bold;">정답: ${question.correct_answer}</span>
                    </div>
                    <div style="margin-bottom: 10px;">
                        <h5 style="color: #495057; margin-bottom: 8px;">📝 해설</h5>
                        <div style="background: #f8f9fa; padding: 15px; border-radius: 4px; line-height: 1.6; color: #212529;">${question.explanation}</div>
                    </div>
                    ${question.learning_point ? `
                        <div>
                            <h5 style="color: #495057; margin-bottom: 8px;">💡 학습 포인트</h5>
                            <div style="background: #e7f3ff; padding: 15px; border-radius: 4px; border-left: 4px solid #007bff; color: #004085;">${question.learning_point}</div>
                        </div>
                    ` : ''}
                </div>`;
        }
        
        // 지문도 예문도 없는 독립적인 문제 처리
        else if (!passageId && !question.example_id) {
            html += `
                <div style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 25px; border: 1px solid #dee2e6;">
                    <div style="display: flex; align-items: center; margin-bottom: 15px;">
                        <span style="background: #17a2b8; color: white; padding: 5px 12px; border-radius: 20px; font-weight: bold; margin-right: 15px;">문제 ${question.question_id}</span>
                        <span style="background: #28a745; color: white; padding: 5px 12px; border-radius: 4px; font-weight: bold;">정답: ${question.correct_answer}</span>
                    </div>
                    <div style="margin-bottom: 15px;">
                        <h5 style="color: #495057; margin-bottom: 8px;">📝 해설</h5>
                        <div style="background: #f8f9fa; padding: 15px; border-radius: 4px; line-height: 1.6; color: #212529;">${question.explanation}</div>
                    </div>
                    ${question.learning_point ? `
                        <div>
                            <h5 style="color: #495057; margin-bottom: 8px;">💡 학습 포인트</h5>
                            <div style="background: #e7f3ff; padding: 15px; border-radius: 4px; border-left: 4px solid #007bff; color: #004085;">${question.learning_point}</div>
                        </div>
                    ` : ''}
                </div>`;
        }
    });

    html += `
        <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6;">
            <p style="color: #6c757d; margin: 0;">📚 학습에 도움이 되었기를 바랍니다!</p>
        </div>
    </div>`;

    return html;
}

// 탭 전환 함수
function showTab(tabName) {
    // 모든 탭과 콘텐츠 비활성화
    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    
    // 선택된 탭과 콘텐츠 활성화
    event.target.classList.add('active');
    document.getElementById(tabName).classList.add('active');
    
    // 문제지 목록 탭이 선택되면 목록 로드
    if (tabName === 'worksheets-tab') {
        loadWorksheetsList();
    }
}

// 전역 변수로 생성된 데이터 저장
let currentWorksheetData = null;
let currentAnswerData = null;

// 기본 문제지 이름 생성 함수
function generateDefaultWorksheetName() {
    const schoolLevel = document.getElementById('schoolLevel').value;
    const grade = document.getElementById('grade').value;
    const totalQuestions = document.getElementById('totalQuestions').value;
    
    return `${schoolLevel} ${grade}학년 영어 문제지 (${totalQuestions}문제)`;
}

// 문제지 저장 함수
async function saveWorksheet() {
    const saveBtn = document.getElementById('saveWorksheetBtn');
    const saveResult = document.getElementById('saveResult');
    const worksheetNameInput = document.getElementById('worksheetNameInput');
    
    if (!currentWorksheetData) {
        saveResult.innerHTML = `
            <div style="color: #dc3545; font-weight: bold;">❌ 문제지 데이터가 없습니다.</div>
        `;
        saveResult.style.display = 'block';
        return;
    }
    
    // 답안 데이터가 없으면 기본 구조 설정
    if (!currentAnswerData) {
        console.warn('⚠️ 저장 시 답안 데이터가 없음. 기본 구조 설정');
        currentAnswerData = {
            questions: [],
            passages: [],
            examples: []
        };
        
        saveResult.innerHTML = `
            <div style="color: #ffc107;">⚠️ 답안 데이터가 없습니다. 빈 구조로 저장됩니다.</div>
        `;
        saveResult.style.display = 'block';
        
        // 3초 후 저장 진행
        await new Promise(resolve => setTimeout(resolve, 3000));
    }
    
    // 문제지 이름 검증
    const worksheetName = worksheetNameInput.value.trim();
    if (!worksheetName) {
        saveResult.innerHTML = `
            <div style="color: #dc3545; font-weight: bold;">❌ 문제지 이름을 입력해주세요.</div>
        `;
        saveResult.style.display = 'block';
        worksheetNameInput.focus();
        worksheetNameInput.style.borderColor = '#dc3545';
        return;
    }
    
    // 문제지 데이터에 사용자 입력 이름 추가
    const updatedWorksheetData = {
        ...currentWorksheetData,
        worksheet_name: worksheetName
    };
    
    try {
        // 버튼 비활성화 및 로딩 상태
        saveBtn.disabled = true;
        saveBtn.innerHTML = '💾 저장 중...';
        saveBtn.style.background = '#6c757d';
        
        saveResult.innerHTML = `
            <div style="color: #007bff;">⏳ 데이터베이스에 저장 중입니다...</div>
        `;
        saveResult.style.display = 'block';
        
        console.log('💾 저장 시작...');
        console.log('📄 문제지 데이터:', updatedWorksheetData);
        
        // 답안 데이터 상태 확인
        const hasAnswerQuestions = currentAnswerData.questions > 0;
        const hasAnswerPassages = currentAnswerData.passages > 0; 
        const hasAnswerExamples = currentAnswerData.examples > 0;
        
        if (!hasAnswerQuestions && !hasAnswerPassages && !hasAnswerExamples) {
            console.warn('⚠️ 모든 답안 데이터가 비어있습니다. answer_* 테이블에는 빈 레코드만 저장됩니다.');
        } else {
            console.log(`📊 답안 데이터 현황: 문제 ${currentAnswerData.questions?.length || 0}개, 지문 ${currentAnswerData.passages?.length || 0}개, 예문 ${currentAnswerData.examples?.length || 0}개`);
        }
        
        // API 호출
        const result = await apiService.createWorksheet({
            worksheet_data: updatedWorksheetData,
            answer_data: currentAnswerData
        });
        
        if (result.status === 'success') {
            // 답안 데이터 저장 상태 메시지 생성
            let answerStatusMsg = '';
            if (!hasAnswerQuestions && !hasAnswerPassages && !hasAnswerExamples) {
                answerStatusMsg = '<br><small style="color: #ffc107;">⚠️ 답안 테이블: 빈 데이터로 저장됨</small>';
            } else {
                answerStatusMsg = `<br><small style="color: #28a745;">✅ 답안 테이블: 문제 ${currentAnswerData.questions?.length || 0}개, 지문 ${currentAnswerData.passages?.length || 0}개, 예문 ${currentAnswerData.examples?.length || 0}개 저장됨</small>`;
            }
            
            saveResult.innerHTML = `
                <div style="color: #28a745; font-weight: bold;">
                    ✅ ${result.message}<br>
                    <small style="color: #6c757d;">문제지 ID: ${result.worksheet_id}</small>
                    ${answerStatusMsg}
                </div>
            `;
            
            // 버튼을 성공 상태로 변경
            saveBtn.innerHTML = '✅ 저장 완료';
            saveBtn.style.background = '#28a745';
            
        } else {
            throw new Error(result.detail || '저장에 실패했습니다.');
        }
        
    } catch (error) {
        console.error('문제지 저장 오류:', error);
        
        saveResult.innerHTML = `
            <div style="color: #dc3545; font-weight: bold;">
                ❌ 저장 실패: ${error.message}
            </div>
        `;
        
        // 버튼 복원
        saveBtn.disabled = false;
        saveBtn.innerHTML = '📁 문제지 저장하기';
        saveBtn.style.background = 'linear-gradient(45deg, #28a745, #20c997)';
    }
}

// 문제지 목록 로드 함수
async function loadWorksheetsList() {
    const loadingElement = document.getElementById('worksheets-loading');
    const listElement = document.getElementById('worksheets-list');
    const errorElement = document.getElementById('worksheets-error');
    
    try {
        // 로딩 표시
        loadingElement.style.display = 'block';
        errorElement.style.display = 'none';
        listElement.innerHTML = '';
        
        // API 호출
        const worksheets = await apiService.getWorksheets();
        
        // 문제지 목록 렌더링
        renderWorksheetsList(worksheets);
        
    } catch (error) {
        console.error('문제지 목록 로드 오류:', error);
        document.getElementById('worksheets-error-data').textContent = error.message;
        errorElement.style.display = 'block';
    } finally {
        loadingElement.style.display = 'none';
    }
}

// 문제지 목록 렌더링 함수
function renderWorksheetsList(worksheets) {
    const listElement = document.getElementById('worksheets-list');
    
    if (worksheets.length === 0) {
        listElement.innerHTML = `
            <div style="text-align: center; padding: 40px; color: #666;">
                <h3>📝 저장된 문제지가 없습니다</h3>
                <p>문제 생성 탭에서 새로운 문제지를 만들어보세요!</p>
            </div>
        `;
        return;
    }
    
    let html = '<div class="worksheets-grid">';
    
    worksheets.forEach(worksheet => {
        const createdDate = new Date(worksheet.created_at).toLocaleDateString('ko-KR');
        const createdTime = new Date(worksheet.created_at).toLocaleTimeString('ko-KR', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
        
        html += `
            <div class="worksheet-card">
                <div class="worksheet-header">
                    <h3 class="worksheet-title">${worksheet.worksheet_name}</h3>
                    <div class="worksheet-badges">
                        <span class="badge badge-level">${worksheet.school_level}</span>
                        <span class="badge badge-grade">${worksheet.grade}학년</span>
                        <span class="badge badge-subject">${worksheet.subject}</span>
                    </div>
                </div>
                
                <div class="worksheet-info">
                    <div class="info-item">
                        <span class="info-label">문제 수:</span>
                        <span class="info-value">${worksheet.total_questions}문제</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">소요 시간:</span>
                        <span class="info-value">${worksheet.duration || 45}분</span>
                    </div>
                    <div class="info-item">
                        <span class="info-label">생성일:</span>
                        <span class="info-value">${createdDate} ${createdTime}</span>
                    </div>
                </div>
                
                <div class="worksheet-actions">
                    <button onclick="viewWorksheet('${worksheet.worksheet_id}')" class="btn btn-primary">
                        📄 문제지 보기
                    </button>
                    <button onclick="solveWorksheet('${worksheet.worksheet_id}')" class="btn btn-success">
                        ✏️ 문제 풀기
                    </button>
                    <button onclick="deleteWorksheet('${worksheet.worksheet_id}')" class="btn btn-danger">
                        🗑️ 삭제
                    </button>
                </div>
            </div>
        `;
    });
    
    html += '</div>';
    listElement.innerHTML = html;
}

// 문제지 편집 관련 전역 변수
let currentEditingWorksheet = null;
let isEditMode = false;

// 문제지 보기 함수
async function viewWorksheet(worksheetId) {
    try {
        console.log(`🔍 문제지 ${worksheetId} 조회 시작...`);
        
        // 먼저 워크시트 목록을 가져와서 실제 ID 확인
        try {
            const worksheetList = await apiService.getWorksheets();
            console.log('📋 사용 가능한 워크시트 목록:', worksheetList);
            
            if (worksheetList.length === 0) {
                alert('저장된 문제지가 없습니다. 먼저 문제지를 생성해주세요.');
                return;
            }
            
            // 실제 워크시트 ID 사용 (첫 번째 워크시트)
            const actualWorksheetId = worksheetList[0].worksheet_id;
            console.log(`🎯 실제 사용할 워크시트 ID: ${actualWorksheetId}`);
            
            // 편집용 엔드포인트로 시도 (정답/해설 포함)
            let worksheetData;
            try {
                console.log('🔄 편집용 엔드포인트로 시도...');
                const editData = await apiService.getWorksheetForEditing(actualWorksheetId);
                worksheetData = editData.worksheet_data;
                console.log('📊 워크시트 데이터 (편집용):', worksheetData);
            } catch (editError) {
                console.log('❌ 편집용 실패, solve 엔드포인트로 시도...');
                try {
                    const solveData = await apiService.getWorksheetForSolving(actualWorksheetId);
                    worksheetData = solveData.worksheet_data;
                    console.log('📊 워크시트 데이터 (solve):', worksheetData);
                } catch (solveError) {
                    console.log('❌ solve도 실패, 일반 엔드포인트 시도...');
                    worksheetData = await apiService.getWorksheet(actualWorksheetId);
                    console.log('📊 워크시트 데이터 (일반):', worksheetData);
                }
            }
            
            currentEditingWorksheet = worksheetData;
            isEditMode = false; // 기본은 보기 모드
            
            // 현재 탭 유지하고 결과 표시
            // showTab('generate-tab'); // 탭 이동 제거
            
            // 문제목록 탭에 편집기 표시
            const worksheetsList = document.getElementById('worksheets-list');
            if (worksheetsList) {
                worksheetsList.innerHTML = renderWorksheetEditor(worksheetData);
            } else {
                alert('문제지 목록 영역을 찾을 수 없습니다.');
            }
            
        } catch (listError) {
            console.error('워크시트 목록 조회 오류:', listError);
            alert(`워크시트 목록을 가져올 수 없습니다: ${listError.message}`);
        }
        
    } catch (error) {
        console.error('문제지 조회 오류:', error);
        alert(`문제지 보기 오류: ${error.message}`);
    }
}

// 문제 풀기 함수
async function solveWorksheet(worksheetId) {
    try {
        // 문제 풀기 탭 버튼 표시
        document.getElementById('solve-tab-btn').style.display = 'block';
        
        // 문제 풀기 탭으로 이동
        showTab('solve-tab');
        
        // 로딩 표시
        document.getElementById('solve-loading').style.display = 'block';
        document.getElementById('solve-error').style.display = 'none';
        document.getElementById('solve-content').innerHTML = '';
        
        // API 호출하여 문제지 로드
        const data = await apiService.getWorksheetForSolving(worksheetId);
        
        // 문제 풀이 시작
        startSolvingWorksheet(data.worksheet_data);
        
    } catch (error) {
        console.error('문제 풀기 오류:', error);
        document.getElementById('solve-error-data').textContent = error.message;
        document.getElementById('solve-error').style.display = 'block';
    } finally {
        document.getElementById('solve-loading').style.display = 'none';
    }
}

// 문제 풀이 관련 전역 변수
let currentSolvingWorksheet = null;
let studentAnswers = {};
let solveStartTime = null;
let solveTimer = null;

// 채점 결과 관련 전역 변수
let currentGradingResult = null;
let currentResultId = null;
let reviewedResults = {}; // 검수된 결과 저장

// 문제 풀이 시작 함수
function startSolvingWorksheet(worksheetData) {
    currentSolvingWorksheet = worksheetData;
    studentAnswers = {};
    solveStartTime = Date.now();
    
    // 헤더 정보 업데이트
    document.getElementById('solve-worksheet-name').textContent = worksheetData.worksheet_name;
    updateSolveProgress();
    
    // 타이머 시작
    startSolveTimer();
    
    // 문제지 렌더링 (답안 입력 폼 포함)
    renderSolvingWorksheet(worksheetData);
    
    // 제출 섹션 표시
    document.getElementById('solve-submit-section').style.display = 'block';
}

// 타이머 시작 함수
function startSolveTimer() {
    if (solveTimer) {
        clearInterval(solveTimer);
    }
    
    solveTimer = setInterval(() => {
        const elapsed = Date.now() - solveStartTime;
        const hours = Math.floor(elapsed / (1000 * 60 * 60));
        const minutes = Math.floor((elapsed % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((elapsed % (1000 * 60)) / 1000);
        
        const timeString = `⏱️ ${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        document.getElementById('solve-timer').textContent = timeString;
    }, 1000);
}

// 진행률 업데이트 함수
function updateSolveProgress() {
    if (!currentSolvingWorksheet) return;
    
    const totalQuestions = currentSolvingWorksheet.total_questions;
    const answeredCount = Object.keys(studentAnswers).length;
    
    document.getElementById('solve-progress').textContent = `📝 ${answeredCount}/${totalQuestions} 완료`;
}

// 문제 풀이용 문제지 렌더링 함수
function renderSolvingWorksheet(worksheetData) {
    let html = `
        <div style="background: white; padding: 25px; border-radius: 10px; margin-bottom: 20px; border: 2px solid #28a745; box-shadow: 0 4px 12px rgba(40, 167, 69, 0.1);">
            <div style="text-align: center; margin-bottom: 30px; border-bottom: 2px solid #28a745; padding-bottom: 20px;">
                <h1 style="color: #28a745; margin: 0; font-size: 1.8rem;">✏️ ${worksheetData.worksheet_name}</h1>
                <div style="margin-top: 10px; color: #6c757d;">
                    <span><strong>총 문제:</strong> ${worksheetData.total_questions}문제</span>
                    <span style="margin-left: 20px;"><strong>제한 시간:</strong> ${worksheetData.worksheet_duration || 45}분</span>
                </div>
            </div>`;

    // 지문과 문제를 연결하여 렌더링
    let renderedPassages = new Set();
    let renderedExamples = new Set();

    if (worksheetData.questions && worksheetData.questions.length > 0) {
        html += `<div style="margin-bottom: 30px;">`;
        
        worksheetData.questions.forEach((question, index) => {
            // 관련 지문이 있고 아직 렌더링되지 않았다면 먼저 렌더링
            if (question.question_passage_id && !renderedPassages.has(question.question_passage_id)) {
                const passage = worksheetData.passages?.find(p => p.passage_id === question.question_passage_id);
                if (passage) {
                    const relatedQuestions = worksheetData.questions
                        .filter(q => q.question_passage_id === question.question_passage_id)
                        .map(q => q.question_id)
                        .sort((a, b) => parseInt(a) - parseInt(b));
                    
                    const questionRange = relatedQuestions.length > 1 
                        ? `[${relatedQuestions[0]}-${relatedQuestions[relatedQuestions.length - 1]}]`
                        : `[${relatedQuestions[0]}]`;
                    
                    html += `
                        <div style="background: #f8f9fa; border: 2px solid #007bff; border-radius: 8px; padding: 20px; margin-bottom: 20px;">
                            <h3 style="color: #007bff; margin-bottom: 15px;">📖 지문</h3>`;
                    
                    if (passage.passage_content) {
                        if (passage.passage_content.title) {
                            html += `<h4 style="text-align: center; margin-bottom: 15px; font-weight: bold;">${passage.passage_content.title}</h4>`;
                        }
                        
                        if (passage.passage_content.paragraphs) {
                            passage.passage_content.paragraphs.forEach(paragraph => {
                                html += `<p style="line-height: 1.6; margin-bottom: 15px; text-align: justify;">${paragraph}</p>`;
                            });
                        }
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
                <div style="background: white; border: 2px solid #e9ecef; border-radius: 8px; padding: 20px; margin-bottom: 20px;" id="question-${question.question_id}">
                    <div style="display: flex; align-items: center; margin-bottom: 15px;">
                        <span style="background: #dc3545; color: white; padding: 5px 12px; border-radius: 20px; font-weight: bold; margin-right: 15px;">
                            ${question.question_id}번
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
            
            // 문제 텍스트 정리
            let cleanQuestionText = question.question_text;
            cleanQuestionText = cleanQuestionText.replace(/지문\s*\[P\d+\]/g, '위 지문');
            cleanQuestionText = cleanQuestionText.replace(/예문\s*\[E\d+\]/g, '다음 예문');
            
            html += `
                <div style="margin-bottom: 15px;">
                    <p style="font-size: 1.1rem; line-height: 1.6; margin: 0; font-weight: 500;">${cleanQuestionText}</p>
                </div>`;
            
            // 관련 예문이 있으면 문제 아래에 표시
            if (question.question_example_id && !renderedExamples.has(question.question_example_id)) {
                const example = worksheetData.examples?.find(e => e.example_id === question.question_example_id);
                if (example) {
                    html += `
                        <div style="background: #fff3cd; border: 2px solid #ffc107; border-radius: 8px; padding: 15px; margin-bottom: 15px;">
                            <div style="font-family: 'Courier New', monospace; line-height: 1.5;">${example.example_content}</div>
                        </div>`;
                    renderedExamples.add(question.question_example_id);
                }
            }
            
            // 답안 입력 영역 렌더링
            html += renderAnswerInput(question);
            
            html += `</div>`;
        });
        
        html += `</div>`;
    }

    html += `
            <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6;">
                <p style="color: #6c757d; margin: 0;">💡 답안을 모두 작성한 후 하단의 "답안 제출하기" 버튼을 클릭하세요!</p>
            </div>
        </div>`;

    document.getElementById('solve-content').innerHTML = html;
}

// 답안 입력 영역 렌더링 함수
function renderAnswerInput(question) {
    const questionId = question.question_id;
    let html = '';
    
    if (question.question_type === '객관식' && question.question_choices && question.question_choices.length > 0) {
        // 객관식 - 라디오 버튼
        html += `
            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; border: 2px solid #28a745;">
                <h4 style="color: #28a745; margin-bottom: 10px;">📝 답안 선택</h4>`;
        
        question.question_choices.forEach((choice, choiceIndex) => {
            const choiceLabel = String.fromCharCode(9312 + choiceIndex); // ① ② ③ ④ ⑤
            const choiceValue = (choiceIndex + 1).toString(); // 1 2 3 4 5 (숫자로 통일)
            
            html += `
                <div style="margin: 8px 0;">
                    <label style="display: flex; align-items: center; cursor: pointer; padding: 8px; border-radius: 4px; transition: background-color 0.2s;" onmouseover="this.style.backgroundColor='#e8f5e8'" onmouseout="this.style.backgroundColor='transparent'">
                        <input type="radio" name="answer_${questionId}" value="${choiceValue}" onchange="saveAnswer('${questionId}', '${choiceValue}')" style="margin-right: 10px;">
                        <span style="line-height: 1.5;">${choiceLabel} ${choice}</span>
                    </label>
                </div>`;
        });
        
        html += `</div>`;
        
    } else if (question.question_type === '단답형' || question.question_type === '주관식') {
        // 단답형/주관식 - 텍스트 입력
        html += `
            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; border: 2px solid #28a745;">
                <h4 style="color: #28a745; margin-bottom: 10px;">📝 답안 작성</h4>
                <input type="text" id="answer_${questionId}" placeholder="답안을 입력하세요" 
                       onchange="saveAnswer('${questionId}', this.value)"
                       style="width: 100%; padding: 12px; border: 2px solid #dee2e6; border-radius: 6px; font-size: 14px;">
            </div>`;
            
    } else if (question.question_type === '서술형') {
        // 서술형 - 텍스트 에어리어
        html += `
            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; border: 2px solid #28a745;">
                <h4 style="color: #28a745; margin-bottom: 10px;">📝 답안 작성</h4>
                <textarea id="answer_${questionId}" placeholder="답안을 자세히 작성하세요" 
                          onchange="saveAnswer('${questionId}', this.value)"
                          style="width: 100%; min-height: 120px; padding: 12px; border: 2px solid #dee2e6; border-radius: 6px; font-size: 14px; resize: vertical;"></textarea>
            </div>`;
    }
    
    return html;
}

// 답안 저장 함수
function saveAnswer(questionId, answer) {
    // 🧹 텍스트 정리 (불필요한 공백/줄바꿈 제거)
    if (typeof answer === 'string' && answer.trim()) {
        // 1. 앞뒤 공백 제거
        answer = answer.trim();
        // 2. 연속된 공백을 하나로 변환
        answer = answer.replace(/\s+/g, ' ');
        // 3. 불필요한 줄바꿈 제거 후 문장 사이 공백 정리
        answer = answer.replace(/\n\s*\n/g, ' ');
        answer = answer.replace(/\n+/g, ' ');
        // 4. 최종 공백 정리
        answer = answer.trim();
    }
    
    studentAnswers[questionId] = answer;
    updateSolveProgress();
    
    // 답안 입력된 문제는 시각적으로 표시
    const questionElement = document.getElementById(`question-${questionId}`);
    if (questionElement) {
        if (answer && answer.trim()) {
            questionElement.style.borderColor = '#28a745';
            questionElement.style.backgroundColor = '#f8fff8';
        } else {
            questionElement.style.borderColor = '#e9ecef';
            questionElement.style.backgroundColor = 'white';
        }
    }
}

// 답안 제출 함수
async function submitAnswers() {
    if (!currentSolvingWorksheet) {
        alert('문제지 정보가 없습니다.');
        return;
    }
    
    const totalQuestions = currentSolvingWorksheet.total_questions;
    const answeredCount = Object.keys(studentAnswers).length;
    
    if (answeredCount < totalQuestions) {
        if (!confirm(`${totalQuestions}문제 중 ${answeredCount}문제만 답했습니다. 정말 제출하시겠습니까?`)) {
            return;
        }
    }
    
    const studentName = document.getElementById('student-name').value.trim() || '익명';
    const completionTime = Math.floor((Date.now() - solveStartTime) / 1000); // 초 단위
    
    try {
        const submitBtn = document.getElementById('submit-answers-btn');
        submitBtn.disabled = true;
        submitBtn.innerHTML = '📤 제출 중...';
        
        // 타이머 정지
        if (solveTimer) {
            clearInterval(solveTimer);
            solveTimer = null;
        }
        
        // 제출 데이터 준비
        const submissionData = {
            worksheet_id: currentSolvingWorksheet.worksheet_id,
            student_name: studentName,
            answers: studentAnswers,
            completion_time: completionTime
        };
        
        console.log('='.repeat(80));
        console.log('📤 답안 제출 시작');
        console.log('='.repeat(80));
        console.log('🎯 요청 URL:', `/worksheets/${currentSolvingWorksheet.worksheet_id}/submit`);
        console.log('📋 제출 데이터:', submissionData);
        console.log('='.repeat(80));
        
        // API 호출하여 답안 제출 및 채점
        const result = await apiService.submitAnswers(currentSolvingWorksheet.worksheet_id, submissionData);
        
        console.log('📡 채점 결과:', result);
        // apiService에서 이미 에러 처리가 완료됨
        
        // 성공 로그 출력
        console.log('='.repeat(80));
        console.log('✅ 답안 제출 및 채점 완료');
        console.log('='.repeat(80));
        console.log('📊 채점 결과:', result.grading_result);
        console.log('📄 지문 그룹 개수:', result.grading_result.passage_groups?.length || 0);
        console.log('📝 예문 그룹 개수:', result.grading_result.example_groups?.length || 0);
        console.log('🔍 독립 문제 개수:', result.grading_result.standalone_questions?.length || 0);
        if (result.grading_result.passage_groups?.length > 0) {
            console.log('📄 지문 그룹:', result.grading_result.passage_groups);
        }
        if (result.grading_result.example_groups?.length > 0) {
            console.log('📝 예문 그룹:', result.grading_result.example_groups);
        }
        console.log('='.repeat(80));
        
        // 성공 메시지 표시
        alert(`답안이 제출되고 채점이 완료되었습니다!\n\n학생: ${result.grading_result.student_name}\n점수: ${result.grading_result.total_score}/${result.grading_result.max_score}점 (${result.grading_result.percentage}%)\n\n채점 결과는 '🎯 채점 결과' 탭에서 확인하실 수 있습니다.`);
        
        // 초기화
        currentSolvingWorksheet = null;
        studentAnswers = {};
        solveStartTime = null;
        
        // 문제지 목록 탭으로 이동
        showTab('worksheets-tab');
        
    } catch (error) {
        console.error('='.repeat(80));
        console.error('❌ 답안 제출 오류 발생');
        console.error('='.repeat(80));
        console.error('🔍 오류 정보:', error);
        console.error('🔍 오류 메시지:', error.message);
        console.error('🔍 오류 스택:', error.stack);
        
        if (error.name) console.error('🔍 오류 타입:', error.name);
        
        // 제출 데이터도 다시 출력 (디버깅용)
        console.error('📤 제출했던 데이터:');
        console.error('  - student_name:', studentName);
        console.error('  - worksheet_id:', currentSolvingWorksheet?.worksheet_id);
        console.error('  - answers 개수:', Object.keys(studentAnswers).length);
        console.error('  - answers 내용:', studentAnswers);
        console.error('  - completion_time:', completionTime);
        console.error('='.repeat(80));
        
        alert(`답안 제출 중 오류가 발생했습니다: ${error.message}\n\n개발자 도구(F12) 콘솔을 확인해주세요.`);
    } finally {
        const submitBtn = document.getElementById('submit-answers-btn');
        submitBtn.disabled = false;
        submitBtn.innerHTML = '📤 답안 제출하기';
    }
}

// 문제 결과 HTML 생성 공통 함수
function generateQuestionResultHTML(result, finalScore, finalFeedback, isCorrect, borderColor, bgColor, iconColor, canReview, isReviewed) {
    return `
        <div style="border: 2px solid ${borderColor}; border-radius: 10px; padding: 20px; margin-bottom: 15px; background: ${bgColor};" id="question-result-${result.question_id}">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 15px;">
                <div style="display: flex; align-items: center; flex: 1;">
                    <span style="font-size: 1.2rem; margin-right: 10px;">${iconColor}</span>
                    <div>
                        <strong>${result.question_id}번 (${result.question_type})</strong>
                        <div style="margin-top: 5px;">
                            <span style="background: ${isCorrect ? '#28a745' : '#dc3545'}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 12px;">
                                <span id="score-${result.question_id}">${finalScore}</span>/${result.max_score}점
                            </span>
                            <span style="background: #6c757d; color: white; padding: 3px 8px; border-radius: 12px; font-size: 12px; margin-left: 5px;">
                                ${result.grading_method === 'ai' ? 'AI 채점' : 'DB 채점'}
                            </span>
                            ${result.is_reviewed ? '<span style="background: #28a745; color: white; padding: 3px 8px; border-radius: 12px; font-size: 12px; margin-left: 5px;">검수 완료</span>' : ''}
                            ${result.needs_review && !result.is_reviewed ? '<span style="background: #ffc107; color: #000; padding: 3px 8px; border-radius: 12px; font-size: 12px; margin-left: 5px;">검수 필요</span>' : ''}
                        </div>
                    </div>
                </div>
                ${canReview ? `
                <div style="display: flex; gap: 10px;">
                    <button onclick="editScore('${result.question_id}')" class="btn btn-primary" style="padding: 5px 10px; font-size: 12px;">
                        ✏️ 점수 수정
                    </button>
                </div>` : ''}
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px;">
                <div style="padding: 10px; background: rgba(255,255,255,0.5); border-radius: 8px;">
                    <strong style="color: #495057;">학생 답안:</strong>
                    <div style="margin-top: 5px; font-family: monospace; background: white; padding: 8px; border-radius: 4px; border: 1px solid #dee2e6;">
                        ${result.student_answer || '(답안 없음)'}
                    </div>
                </div>
                <div style="padding: 10px; background: rgba(255,255,255,0.5); border-radius: 8px;">
                    <strong style="color: #495057;">정답:</strong>
                    <div style="margin-top: 5px; font-family: monospace; background: white; padding: 8px; border-radius: 4px; border: 1px solid #dee2e6;">
                        ${result.correct_answer || '정답 없음'}
                    </div>
                </div>
            </div>
            
            ${finalFeedback ? `
                <div style="background: rgba(255,255,255,0.5); padding: 15px; border-radius: 8px; margin-top: 15px;">
                    <strong style="color: #495057; display: block; margin-bottom: 8px;">해설/피드백:</strong>
                    <div style="line-height: 1.5;" id="feedback-${result.question_id}">
                        ${finalFeedback}
                    </div>
                </div>
            ` : ''}
            
            ${canReview ? `
                <div id="edit-section-${result.question_id}" style="display: none; background: rgba(255,255,255,0.8); padding: 15px; border-radius: 8px; margin-top: 15px; border: 2px dashed #007bff;">
                    <div style="display: grid; grid-template-columns: 1fr 2fr; gap: 15px; align-items: start;">
                        <div>
                            <label style="display: block; margin-bottom: 5px; font-weight: bold; color: #495057;">점수 수정:</label>
                            <input type="number" id="new-score-${result.question_id}" min="0" max="${result.max_score}" value="${finalScore}" 
                                style="width: 100%; padding: 8px; border: 1px solid #ced4da; border-radius: 4px;">
                        </div>
                        <div>
                            <label style="display: block; margin-bottom: 5px; font-weight: bold; color: #495057;">검수 의견:</label>
                            <textarea id="new-feedback-${result.question_id}" placeholder="검수 의견을 입력하세요..." 
                                style="width: 100%; height: 80px; padding: 8px; border: 1px solid #ced4da; border-radius: 4px; resize: vertical;">${result.reviewed_feedback || ''}</textarea>
                        </div>
                    </div>
                    <div style="text-align: right; margin-top: 15px;">
                        <button onclick="cancelEdit('${result.question_id}')" class="btn btn-secondary" style="margin-right: 10px;">
                            취소
                        </button>
                        <button onclick="saveEdit('${result.question_id}')" class="btn btn-success">
                            저장
                        </button>
                    </div>
                </div>
            ` : ''}
        </div>`;
}

// 새로운 그룹핑된 채점 결과 상세보기 표시 함수
function displayGradingResultDetailNew(gradingResult) {
    const content = document.getElementById('result-detail-content');
    
    const timeMinutes = Math.floor(gradingResult.completion_time / 60);
    const timeSeconds = gradingResult.completion_time % 60;
    
    let html = `
        <div style="background: white; padding: 30px; border-radius: 15px; box-shadow: 0 8px 25px rgba(0,0,0,0.1);">
            <!-- 결과 헤더 -->
            <div style="text-align: center; margin-bottom: 30px; padding: 25px; background: linear-gradient(135deg, #dc3545, #c82333); color: white; border-radius: 12px;">
                <h1 style="margin: 0; font-size: 2rem;">🎯 채점 결과 상세</h1>
                <div style="margin-top: 15px; font-size: 1.1rem;">
                    <div><strong>학생:</strong> ${gradingResult.student_name}</div>
                    <div style="margin-top: 8px;"><strong>소요 시간:</strong> ${timeMinutes}분 ${timeSeconds}초</div>
                    <div style="margin-top: 8px;"><strong>결과 ID:</strong> ${gradingResult.result_id}</div>
                </div>
            </div>
            
            <!-- 점수 요약 -->
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px;">
                <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; text-align: center; border: 2px solid #28a745;">
                    <div style="font-size: 2rem; font-weight: bold; color: #28a745;" id="total-score">${gradingResult.total_score}</div>
                    <div style="color: #6c757d;">총 점수</div>
                </div>
                <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; text-align: center; border: 2px solid #007bff;">
                    <div style="font-size: 2rem; font-weight: bold; color: #007bff;">${gradingResult.max_score}</div>
                    <div style="color: #6c757d;">만점</div>
                </div>
                <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; text-align: center; border: 2px solid #6f42c1;">
                    <div style="font-size: 2rem; font-weight: bold; color: #6f42c1;" id="percentage">${gradingResult.percentage}%</div>
                    <div style="color: #6c757d;">정답률</div>
                </div>
                <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; text-align: center; border: 2px solid ${gradingResult.is_reviewed ? '#28a745' : (gradingResult.needs_review ? '#ffc107' : '#6c757d')};">
                    <div style="font-size: 1.5rem; font-weight: bold; color: ${gradingResult.is_reviewed ? '#28a745' : (gradingResult.needs_review ? '#ffc107' : '#6c757d')};">
                        ${gradingResult.is_reviewed ? '✅' : (gradingResult.needs_review ? '⚠️' : '🤖')}
                    </div>
                    <div style="color: #6c757d;">${gradingResult.is_reviewed ? '검수 완료' : (gradingResult.needs_review ? '검수 필요' : '자동 채점')}</div>
                </div>
            </div>`;
    
    // 검수 필요 알림
    if (gradingResult.needs_review && !gradingResult.is_reviewed) {
        html += `
            <div style="background: #fff3cd; border: 2px solid #ffc107; border-radius: 10px; padding: 20px; margin-bottom: 30px;">
                <div style="display: flex; align-items: center; color: #856404;">
                    <span style="font-size: 1.5rem; margin-right: 10px;">⚠️</span>
                    <div>
                        <strong>검수 필요</strong><br>
                        <small>AI가 채점한 주관식 문제가 있어 교사의 검수가 필요합니다. 아래에서 점수를 수정할 수 있습니다.</small>
                    </div>
                </div>
            </div>`;
    }
    
    // 디버깅: 데이터 구조 확인
    console.log('🔍 gradingResult 구조:', gradingResult);
    console.log('📄 passage_groups:', gradingResult.passage_groups);
    console.log('📝 example_groups:', gradingResult.example_groups);
    console.log('📋 standalone_questions:', gradingResult.standalone_questions);
    console.log('🔍 question_results:', gradingResult.question_results);
    console.log('🔍 question_results 개수:', gradingResult.question_results ? gradingResult.question_results.length : 'undefined');
    
    // 새로운 그룹핑된 문제 표시
    html += `
            <div style="margin-bottom: 30px;">
                <h3 style="color: #495057; margin-bottom: 20px; border-bottom: 2px solid #dee2e6; padding-bottom: 10px;">📝 문제별 채점 결과</h3>`;
    
    // 지문 그룹 표시
    if (gradingResult.passage_groups && gradingResult.passage_groups.length > 0) {
        gradingResult.passage_groups.forEach(group => {
            const passage = group.passage;
            const questions = group.questions;
            
            html += `
                <div style="border: 2px solid #007bff; border-radius: 12px; margin-bottom: 25px; overflow: hidden; background: white; box-shadow: 0 4px 15px rgba(0,123,255,0.1);">
                    <!-- 지문 섹션 -->
                    <div style="background: linear-gradient(135deg, #007bff, #0056b3); color: white; padding: 20px;">
                        <h4 style="margin: 0; font-size: 1.3rem;">📄 지문 ${passage.passage_id}${passage.text_type ? ` (${passage.text_type})` : ''}</h4>
                    </div>
                    <div style="padding: 20px; background: #f8f9ff;">
                        <div style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #007bff;">
                            <div style="margin-bottom: 15px;">
                                <div style="font-weight: bold; color: #007bff; margin-bottom: 8px;">📝 영어 원문</div>
                                <div style="line-height: 1.8; font-size: 15px;">
                                    ${passage.original_content}
                                </div>
                            </div>
                            ${passage.korean_translation ? `
                            <div style="padding-top: 15px; border-top: 1px solid #e9ecef;">
                                <div style="font-weight: bold; color: #6c757d; margin-bottom: 8px;">🇰🇷 한글 번역</div>
                                <div style="line-height: 1.8; font-size: 15px; color: #495057;">
                                    ${passage.korean_translation}
                                </div>
                            </div>
                            ` : ''}
                        </div>
                    </div>
                    
                    <!-- 관련 문제들 -->
                    <div style="padding: 0 20px 20px 20px; background: #f8f9ff;">
                        <h5 style="color: #007bff; margin-bottom: 15px; border-bottom: 1px solid #dee2e6; padding-bottom: 8px;">🔗 관련 문제 (${questions.length}개)</h5>`;
            
            questions.forEach(result => {
                const finalScore = result.reviewed_score !== null ? result.reviewed_score : result.score;
                const finalFeedback = result.reviewed_feedback || result.ai_feedback;
                const isCorrect = finalScore === result.max_score;
                const borderColor = isCorrect ? '#28a745' : '#dc3545';
                const bgColor = isCorrect ? '#d4edda' : '#f8d7da';
                const iconColor = isCorrect ? '✅' : '❌';
                const canReview = !gradingResult.is_reviewed && (result.grading_method === 'ai' || result.needs_review);
                
                html += generateQuestionResultHTML(result, finalScore, finalFeedback, isCorrect, borderColor, bgColor, iconColor, canReview, gradingResult.is_reviewed);
            });
            
            html += `
                    </div>
                </div>`;
        });
    }
    
    // 예문 그룹 표시  
    if (gradingResult.example_groups && gradingResult.example_groups.length > 0) {
        gradingResult.example_groups.forEach(group => {
            const example = group.example;
            const questions = group.questions;
            
            html += `
                <div style="border: 2px solid #28a745; border-radius: 12px; margin-bottom: 25px; overflow: hidden; background: white; box-shadow: 0 4px 15px rgba(40,167,69,0.1);">
                    <!-- 예문 섹션 -->
                    <div style="background: linear-gradient(135deg, #28a745, #1e7e34); color: white; padding: 20px;">
                        <h4 style="margin: 0; font-size: 1.3rem;">📝 예문 ${example.example_id}</h4>
                    </div>
                    <div style="padding: 20px; background: #f8fff8;">
                        <div style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #28a745;">
                            <div style="margin-bottom: 15px;">
                                <div style="font-weight: bold; color: #28a745; margin-bottom: 8px;">📝 영어 원문</div>
                                <div style="line-height: 1.8; font-size: 15px;">
                                    ${example.original_content}
                                </div>
                            </div>
                            ${example.korean_translation ? `
                            <div style="padding-top: 15px; border-top: 1px solid #e9ecef;">
                                <div style="font-weight: bold; color: #6c757d; margin-bottom: 8px;">🇰🇷 한글 번역</div>
                                <div style="line-height: 1.8; font-size: 15px; color: #495057;">
                                    ${example.korean_translation}
                                </div>
                            </div>
                            ` : ''}
                        </div>
                    </div>
                    
                    <!-- 관련 문제들 -->
                    <div style="padding: 0 20px 20px 20px; background: #f8fff8;">
                        <h5 style="color: #28a745; margin-bottom: 15px; border-bottom: 1px solid #dee2e6; padding-bottom: 8px;">🔗 관련 문제 (${questions.length}개)</h5>`;
            
            questions.forEach(result => {
                const finalScore = result.reviewed_score !== null ? result.reviewed_score : result.score;
                const finalFeedback = result.reviewed_feedback || result.ai_feedback;
                const isCorrect = finalScore === result.max_score;
                const borderColor = isCorrect ? '#28a745' : '#dc3545';
                const bgColor = isCorrect ? '#d4edda' : '#f8d7da';
                const iconColor = isCorrect ? '✅' : '❌';
                const canReview = !gradingResult.is_reviewed && (result.grading_method === 'ai' || result.needs_review);
                
                html += generateQuestionResultHTML(result, finalScore, finalFeedback, isCorrect, borderColor, bgColor, iconColor, canReview, gradingResult.is_reviewed);
            });
            
            html += `
                    </div>
                </div>`;
        });
    }
    
    // 독립 문제들 표시
    if (gradingResult.standalone_questions && gradingResult.standalone_questions.length > 0) {
        html += `
            <div style="border: 2px solid #6c757d; border-radius: 12px; margin-bottom: 25px; overflow: hidden; background: white; box-shadow: 0 4px 15px rgba(108,117,125,0.1);">
                <div style="background: linear-gradient(135deg, #6c757d, #495057); color: white; padding: 20px;">
                    <h4 style="margin: 0; font-size: 1.3rem;">📋 독립 문제 (${gradingResult.standalone_questions.length}개)</h4>
                </div>
                <div style="padding: 20px; background: #f8f9fa;">`;
        
        gradingResult.standalone_questions.forEach(result => {
            const finalScore = result.reviewed_score !== null ? result.reviewed_score : result.score;
            const finalFeedback = result.reviewed_feedback || result.ai_feedback;
            const isCorrect = finalScore === result.max_score;
            const borderColor = isCorrect ? '#28a745' : '#dc3545';
            const bgColor = isCorrect ? '#d4edda' : '#f8d7da';
            const iconColor = isCorrect ? '✅' : '❌';
            const canReview = !gradingResult.is_reviewed && (result.grading_method === 'ai' || result.needs_review);
            
            html += generateQuestionResultHTML(result, finalScore, finalFeedback, isCorrect, borderColor, bgColor, iconColor, canReview, gradingResult.is_reviewed);
        });
        
        html += `
                </div>
            </div>`;
    }
    
    // Fallback: 그룹 데이터가 없으면 기존 방식으로 표시
    const hasGroupData = (gradingResult.passage_groups && gradingResult.passage_groups.length > 0) ||
                        (gradingResult.example_groups && gradingResult.example_groups.length > 0) ||
                        (gradingResult.standalone_questions && gradingResult.standalone_questions.length > 0);
    
    if (!hasGroupData && gradingResult.question_results && gradingResult.question_results.length > 0) {
        console.log('⚠️ 그룹 데이터가 없습니다. 기존 방식으로 표시합니다.');
        
        html += `
            <div style="border: 2px solid #6c757d; border-radius: 12px; margin-bottom: 25px; overflow: hidden; background: white; box-shadow: 0 4px 15px rgba(108,117,125,0.1);">
                <div style="background: linear-gradient(135deg, #6c757d, #495057); color: white; padding: 20px;">
                    <h4 style="margin: 0; font-size: 1.3rem;">📋 전체 문제 결과 (${gradingResult.question_results.length}개)</h4>
                </div>
                <div style="padding: 20px; background: #f8f9fa;">`;
        
        gradingResult.question_results.forEach(result => {
            const finalScore = result.reviewed_score !== null ? result.reviewed_score : result.score;
            const finalFeedback = result.reviewed_feedback || result.ai_feedback;
            const isCorrect = finalScore === result.max_score;
            const borderColor = isCorrect ? '#28a745' : '#dc3545';
            const bgColor = isCorrect ? '#d4edda' : '#f8d7da';
            const iconColor = isCorrect ? '✅' : '❌';
            const canReview = !gradingResult.is_reviewed && (result.grading_method === 'ai' || result.needs_review);
            
            html += generateQuestionResultHTML(result, finalScore, finalFeedback, isCorrect, borderColor, bgColor, iconColor, canReview, gradingResult.is_reviewed);
        });
        
        html += `
                </div>
            </div>`;
    }
    
    html += `
            </div>
            
            <!-- 하단 액션 버튼 -->
            <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #dee2e6;">
                <button onclick="showResultList()" class="btn btn-secondary" style="margin-right: 15px;">
                    ← 목록으로 돌아가기
                </button>
                ${gradingResult.needs_review && !gradingResult.is_reviewed ? `
                    <button onclick="completeReview()" class="btn btn-success">
                        ✅ 검수 완료
                    </button>
                ` : ''}
            </div>
        </div>`;
    
    content.innerHTML = html;
    
    // 검수 완료 버튼 섹션 표시 여부 결정
    const reviewSection = document.getElementById('review-complete-section');
    if (reviewSection) {
        reviewSection.style.display = gradingResult.needs_review && !gradingResult.is_reviewed ? 'block' : 'none';
    }
}

// 채점 결과 상세보기 표시 함수
function displayGradingResultDetail(gradingResult) {
    const content = document.getElementById('result-detail-content');
    
    const timeMinutes = Math.floor(gradingResult.completion_time / 60);
    const timeSeconds = gradingResult.completion_time % 60;
    
    let html = `
        <div style="background: white; padding: 30px; border-radius: 15px; box-shadow: 0 8px 25px rgba(0,0,0,0.1);">
            <!-- 결과 헤더 -->
            <div style="text-align: center; margin-bottom: 30px; padding: 25px; background: linear-gradient(135deg, #dc3545, #c82333); color: white; border-radius: 12px;">
                <h1 style="margin: 0; font-size: 2rem;">🎯 채점 결과 상세</h1>
                <div style="margin-top: 15px; font-size: 1.1rem;">
                    <div><strong>학생:</strong> ${gradingResult.student_name}</div>
                    <div style="margin-top: 8px;"><strong>소요 시간:</strong> ${timeMinutes}분 ${timeSeconds}초</div>
                    <div style="margin-top: 8px;"><strong>결과 ID:</strong> ${gradingResult.result_id}</div>
                </div>
            </div>
            
            <!-- 점수 요약 -->
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px;">
                <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; text-align: center; border: 2px solid #28a745;">
                    <div style="font-size: 2rem; font-weight: bold; color: #28a745;" id="total-score">${gradingResult.total_score}</div>
                    <div style="color: #6c757d;">총 점수</div>
                </div>
                <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; text-align: center; border: 2px solid #007bff;">
                    <div style="font-size: 2rem; font-weight: bold; color: #007bff;">${gradingResult.max_score}</div>
                    <div style="color: #6c757d;">만점</div>
                </div>
                <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; text-align: center; border: 2px solid #6f42c1;">
                    <div style="font-size: 2rem; font-weight: bold; color: #6f42c1;" id="percentage">${gradingResult.percentage}%</div>
                    <div style="color: #6c757d;">정답률</div>
                </div>
                <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; text-align: center; border: 2px solid ${gradingResult.is_reviewed ? '#28a745' : (gradingResult.needs_review ? '#ffc107' : '#6c757d')};">
                    <div style="font-size: 1.5rem; font-weight: bold; color: ${gradingResult.is_reviewed ? '#28a745' : (gradingResult.needs_review ? '#ffc107' : '#6c757d')};">
                        ${gradingResult.is_reviewed ? '✅' : (gradingResult.needs_review ? '⚠️' : '🤖')}
                    </div>
                    <div style="color: #6c757d;">${gradingResult.is_reviewed ? '검수 완료' : (gradingResult.needs_review ? '검수 필요' : '자동 채점')}</div>
                </div>
            </div>`;
    
    // 검수 필요 알림
    if (gradingResult.needs_review && !gradingResult.is_reviewed) {
        html += `
            <div style="background: #fff3cd; border: 2px solid #ffc107; border-radius: 10px; padding: 20px; margin-bottom: 30px;">
                <div style="display: flex; align-items: center; color: #856404;">
                    <span style="font-size: 1.5rem; margin-right: 10px;">⚠️</span>
                    <div>
                        <strong>검수 필요</strong><br>
                        <small>AI가 채점한 주관식 문제가 있어 교사의 검수가 필요합니다. 아래에서 점수를 수정할 수 있습니다.</small>
                    </div>
                </div>
            </div>`;
    }
    
    // 지문 및 예문 표시
    if ((gradingResult.passages && gradingResult.passages.length > 0) || (gradingResult.examples && gradingResult.examples.length > 0)) {
        html += `
            <div style="margin-bottom: 30px;">
                <h3 style="color: #495057; margin-bottom: 20px; border-bottom: 2px solid #dee2e6; padding-bottom: 10px;">📖 참고 자료</h3>`;
        
        // 지문 표시
        if (gradingResult.passages && gradingResult.passages.length > 0) {
            gradingResult.passages.forEach(passage => {
                const relatedQuestions = gradingResult.question_results.filter(q => q.passage_id === passage.passage_id);
                
                html += `
                    <div style="border: 2px solid #007bff; border-radius: 10px; padding: 20px; margin-bottom: 15px; background: #f8f9ff;">
                        <h4 style="color: #007bff; margin-bottom: 15px;">📄 지문 ${passage.passage_id}${passage.text_type ? ` (${passage.text_type})` : ''}</h4>
                        <div style="background: white; padding: 15px; border-radius: 8px; margin-bottom: 10px; line-height: 1.6;">
                            <div style="margin-bottom: ${passage.korean_translation ? '12px' : '0'}; ">
                                <div style="font-weight: bold; color: #007bff; margin-bottom: 6px;">📝 영어 원문</div>
                                ${passage.original_content}
                            </div>
                            ${passage.korean_translation ? `
                            <div style="padding-top: 12px; border-top: 1px solid #e9ecef;">
                                <div style="font-weight: bold; color: #6c757d; margin-bottom: 6px;">🇰🇷 한글 번역</div>
                                <div style="color: #495057;">${passage.korean_translation}</div>
                            </div>
                            ` : ''}
                        </div>`;
                        
                if (relatedQuestions.length > 0) {
                    html += `
                        <div style="margin-top: 10px;">
                            <small style="color: #6c757d;">🔗 관련 문제: ${relatedQuestions.map(q => q.question_id + '번').join(', ')}</small>
                        </div>`;
                }
                        
                html += `</div>`;
            });
        }
        
        // 예문 표시
        if (gradingResult.examples && gradingResult.examples.length > 0) {
            gradingResult.examples.forEach(example => {
                const relatedQuestions = gradingResult.question_results.filter(q => q.example_id === example.example_id);
                
                html += `
                    <div style="border: 2px solid #28a745; border-radius: 10px; padding: 20px; margin-bottom: 15px; background: #f8fff8;">
                        <h4 style="color: #28a745; margin-bottom: 15px;">📝 예문 ${example.example_id}</h4>
                        <div style="background: white; padding: 15px; border-radius: 8px; margin-bottom: 10px; line-height: 1.6;">
                            <div style="margin-bottom: ${example.korean_translation ? '12px' : '0'}; ">
                                <div style="font-weight: bold; color: #28a745; margin-bottom: 6px;">📝 영어 원문</div>
                                ${example.original_content}
                            </div>
                            ${example.korean_translation ? `
                            <div style="padding-top: 12px; border-top: 1px solid #e9ecef;">
                                <div style="font-weight: bold; color: #6c757d; margin-bottom: 6px;">🇰🇷 한글 번역</div>
                                <div style="color: #495057;">${example.korean_translation}</div>
                            </div>
                            ` : ''}
                        </div>`;
                        
                if (relatedQuestions.length > 0) {
                    html += `
                        <div style="margin-top: 10px;">
                            <small style="color: #6c757d;">🔗 관련 문제: ${relatedQuestions.map(q => q.question_id + '번').join(', ')}</small>
                        </div>`;
                }
                        
                html += `</div>`;
            });
        }
        
        html += `</div>`;
    }
    
    // 문제별 결과 (검수 가능)
    html += `
            <div style="margin-bottom: 30px;">
                <h3 style="color: #495057; margin-bottom: 20px; border-bottom: 2px solid #dee2e6; padding-bottom: 10px;">📝 문제별 채점 결과 및 검수</h3>`;
    
    gradingResult.question_results.forEach((result, index) => {
        const finalScore = result.reviewed_score !== null ? result.reviewed_score : result.score;
        const finalFeedback = result.reviewed_feedback || result.ai_feedback;
        const isCorrect = finalScore === result.max_score;
        const borderColor = isCorrect ? '#28a745' : '#dc3545';
        const bgColor = isCorrect ? '#d4edda' : '#f8d7da';
        const iconColor = isCorrect ? '✅' : '❌';
        const canReview = !gradingResult.is_reviewed && (result.grading_method === 'ai' || result.needs_review);
        
        html += `
                <div style="border: 2px solid ${borderColor}; border-radius: 10px; padding: 20px; margin-bottom: 15px; background: ${bgColor};" id="question-result-${result.question_id}">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 15px;">
                        <div style="display: flex; align-items: center; flex: 1;">
                            <span style="font-size: 1.2rem; margin-right: 10px;">${iconColor}</span>
                            <div>
                                <strong>${result.question_id}번 (${result.question_type})</strong>
                                <div style="margin-top: 5px;">
                                    <span style="background: ${isCorrect ? '#28a745' : '#dc3545'}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 12px;">
                                        <span id="score-${result.question_id}">${finalScore}</span>/${result.max_score}점
                                    </span>
                                    <span style="background: #6c757d; color: white; padding: 3px 8px; border-radius: 12px; font-size: 12px; margin-left: 5px;">
                                        ${result.grading_method === 'ai' ? 'AI 채점' : 'DB 채점'}
                                    </span>
                                    ${result.is_reviewed ? '<span style="background: #28a745; color: white; padding: 3px 8px; border-radius: 12px; font-size: 12px; margin-left: 5px;">검수 완료</span>' : ''}
                                    ${result.needs_review && !result.is_reviewed ? '<span style="background: #ffc107; color: #000; padding: 3px 8px; border-radius: 12px; font-size: 12px; margin-left: 5px;">검수 필요</span>' : ''}
                                </div>
                            </div>
                        </div>
                        ${canReview ? `
                        <div style="display: flex; gap: 10px;">
                            <button onclick="editScore('${result.question_id}')" class="btn btn-primary" style="padding: 5px 10px; font-size: 12px;">
                                ✏️ 점수 수정
                            </button>
                        </div>` : ''}
                    </div>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px;">
                        <div>
                            <strong style="color: #495057;">학생 답안:</strong>
                            <div style="background: white; padding: 10px; border-radius: 5px; margin-top: 5px; border: 1px solid #dee2e6;">
                                ${result.student_answer || '(답안 없음)'}
                            </div>
                        </div>
                        <div>
                            <strong style="color: #495057;">정답:</strong>
                            <div style="background: white; padding: 10px; border-radius: 5px; margin-top: 5px; border: 1px solid #dee2e6;">
                                ${result.correct_answer || '정답 정보 없음'}
                            </div>
                        </div>
                    </div>`;
        
        // AI 피드백이 있는 경우 표시 (수정 가능)
        if (finalFeedback && finalFeedback.trim()) {
            html += `
                    <div style="background: #e3f2fd; border: 1px solid #2196f3; border-radius: 8px; padding: 15px; margin-top: 10px;">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                            <div style="flex: 1;">
                                <strong style="color: #1976d2;">🤖 ${result.is_reviewed ? '검수된 ' : ''}피드백:</strong>
                                <div style="margin-top: 8px; line-height: 1.5;" id="feedback-${result.question_id}">${finalFeedback}</div>
                            </div>
                            ${canReview ? `
                            <button onclick="editFeedback('${result.question_id}')" class="btn btn-secondary" style="padding: 5px 10px; font-size: 12px; margin-left: 10px;">
                                ✏️ 피드백 수정
                            </button>` : ''}
                        </div>
                    </div>`;
        }
        
        html += `</div>`;
    });
    
    html += `</div></div>`;
    
    content.innerHTML = html;
    
    // 검수 완료 섹션 표시 (검수가 필요하고 아직 완료되지 않은 경우)
    if (gradingResult.needs_review && !gradingResult.is_reviewed) {
        document.getElementById('review-complete-section').style.display = 'block';
    } else {
        document.getElementById('review-complete-section').style.display = 'none';
    }
}

// 채점 결과 탭에서 표시하는 함수 (기존 - 사용 안 함)
function displayGradingResultInTab(gradingResult) {
    const content = document.getElementById('result-content');
    
    const timeMinutes = Math.floor(gradingResult.completion_time / 60);
    const timeSeconds = gradingResult.completion_time % 60;
    
    let html = `
        <div style="background: white; padding: 30px; border-radius: 15px; box-shadow: 0 8px 25px rgba(0,0,0,0.1);">
            <!-- 결과 헤더 -->
            <div style="text-align: center; margin-bottom: 30px; padding: 25px; background: linear-gradient(135deg, #dc3545, #c82333); color: white; border-radius: 12px;">
                <h1 style="margin: 0; font-size: 2rem;">🎯 채점 결과</h1>
                <div style="margin-top: 15px; font-size: 1.1rem;">
                    <div><strong>학생:</strong> ${gradingResult.student_name}</div>
                    <div style="margin-top: 8px;"><strong>소요 시간:</strong> ${timeMinutes}분 ${timeSeconds}초</div>
                    <div style="margin-top: 8px;"><strong>문제지:</strong> ${gradingResult.worksheet_id}</div>
                </div>
            </div>
            
            <!-- 점수 요약 -->
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px;">
                <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; text-align: center; border: 2px solid #28a745;">
                    <div style="font-size: 2rem; font-weight: bold; color: #28a745;" id="total-score">${gradingResult.total_score}</div>
                    <div style="color: #6c757d;">총 점수</div>
                </div>
                <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; text-align: center; border: 2px solid #007bff;">
                    <div style="font-size: 2rem; font-weight: bold; color: #007bff;">${gradingResult.max_score}</div>
                    <div style="color: #6c757d;">만점</div>
                </div>
                <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; text-align: center; border: 2px solid #6f42c1;">
                    <div style="font-size: 2rem; font-weight: bold; color: #6f42c1;" id="percentage">${gradingResult.percentage}%</div>
                    <div style="color: #6c757d;">정답률</div>
                </div>
                <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; text-align: center; border: 2px solid #dc3545;">
                    <div style="font-size: 2rem; font-weight: bold; color: #dc3545;">${gradingResult.total_questions}</div>
                    <div style="color: #6c757d;">총 문제</div>
                </div>
            </div>`;
    
    // 검수 필요 알림
    if (gradingResult.needs_review) {
        html += `
            <div style="background: #fff3cd; border: 2px solid #ffc107; border-radius: 10px; padding: 20px; margin-bottom: 30px;">
                <div style="display: flex; align-items: center; color: #856404;">
                    <span style="font-size: 1.5rem; margin-right: 10px;">⚠️</span>
                    <div>
                        <strong>검수 필요</strong><br>
                        <small>AI가 채점한 주관식 문제가 있어 교사의 검수가 필요합니다. 아래에서 점수를 수정할 수 있습니다.</small>
                    </div>
                </div>
            </div>`;
    }
    
    // 지문 및 예문 표시
    if ((gradingResult.passages && gradingResult.passages.length > 0) || (gradingResult.examples && gradingResult.examples.length > 0)) {
        html += `
            <div style="margin-bottom: 30px;">
                <h3 style="color: #495057; margin-bottom: 20px; border-bottom: 2px solid #dee2e6; padding-bottom: 10px;">📖 참고 자료</h3>`;
        
        // 지문 표시
        if (gradingResult.passages && gradingResult.passages.length > 0) {
            gradingResult.passages.forEach(passage => {
                const relatedQuestions = gradingResult.question_results.filter(q => q.passage_id === passage.passage_id);
                
                html += `
                    <div style="border: 2px solid #007bff; border-radius: 10px; padding: 20px; margin-bottom: 15px; background: #f8f9ff;">
                        <h4 style="color: #007bff; margin-bottom: 15px;">📄 지문 ${passage.passage_id}${passage.text_type ? ` (${passage.text_type})` : ''}</h4>
                        <div style="background: white; padding: 15px; border-radius: 8px; margin-bottom: 10px; line-height: 1.6;">
                            <div style="margin-bottom: ${passage.korean_translation ? '12px' : '0'}; ">
                                <div style="font-weight: bold; color: #007bff; margin-bottom: 6px;">📝 영어 원문</div>
                                ${passage.original_content}
                            </div>
                            ${passage.korean_translation ? `
                            <div style="padding-top: 12px; border-top: 1px solid #e9ecef;">
                                <div style="font-weight: bold; color: #6c757d; margin-bottom: 6px;">🇰🇷 한글 번역</div>
                                <div style="color: #495057;">${passage.korean_translation}</div>
                            </div>
                            ` : ''}
                        </div>`;
                        
                if (relatedQuestions.length > 0) {
                    html += `
                        <div style="margin-top: 10px;">
                            <small style="color: #6c757d;">🔗 관련 문제: ${relatedQuestions.map(q => q.question_id + '번').join(', ')}</small>
                        </div>`;
                }
                        
                html += `</div>`;
            });
        }
        
        // 예문 표시
        if (gradingResult.examples && gradingResult.examples.length > 0) {
            gradingResult.examples.forEach(example => {
                const relatedQuestions = gradingResult.question_results.filter(q => q.example_id === example.example_id);
                
                html += `
                    <div style="border: 2px solid #28a745; border-radius: 10px; padding: 20px; margin-bottom: 15px; background: #f8fff8;">
                        <h4 style="color: #28a745; margin-bottom: 15px;">📝 예문 ${example.example_id}</h4>
                        <div style="background: white; padding: 15px; border-radius: 8px; margin-bottom: 10px; line-height: 1.6;">
                            <div style="margin-bottom: ${example.korean_translation ? '12px' : '0'}; ">
                                <div style="font-weight: bold; color: #28a745; margin-bottom: 6px;">📝 영어 원문</div>
                                ${example.original_content}
                            </div>
                            ${example.korean_translation ? `
                            <div style="padding-top: 12px; border-top: 1px solid #e9ecef;">
                                <div style="font-weight: bold; color: #6c757d; margin-bottom: 6px;">🇰🇷 한글 번역</div>
                                <div style="color: #495057;">${example.korean_translation}</div>
                            </div>
                            ` : ''}
                        </div>`;
                        
                if (relatedQuestions.length > 0) {
                    html += `
                        <div style="margin-top: 10px;">
                            <small style="color: #6c757d;">🔗 관련 문제: ${relatedQuestions.map(q => q.question_id + '번').join(', ')}</small>
                        </div>`;
                }
                        
                html += `</div>`;
            });
        }
        
        html += `</div>`;
    }
    
    // 문제별 결과 (검수 가능)
    html += `
            <div style="margin-bottom: 30px;">
                <h3 style="color: #495057; margin-bottom: 20px; border-bottom: 2px solid #dee2e6; padding-bottom: 10px;">📝 문제별 채점 결과 및 검수</h3>`;
    
    gradingResult.question_results.forEach((result, index) => {
        const isCorrect = result.is_correct;
        const borderColor = isCorrect ? '#28a745' : '#dc3545';
        const bgColor = isCorrect ? '#d4edda' : '#f8d7da';
        const iconColor = isCorrect ? '✅' : '❌';
        const canReview = result.grading_method === 'ai' || result.needs_review;
        
        html += `
                <div style="border: 2px solid ${borderColor}; border-radius: 10px; padding: 20px; margin-bottom: 15px; background: ${bgColor};" id="question-result-${result.question_id}">
                    <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 15px;">
                        <div style="display: flex; align-items: center; flex: 1;">
                            <span style="font-size: 1.2rem; margin-right: 10px;">${iconColor}</span>
                            <div>
                                <strong>${result.question_id}번 (${result.question_type})</strong>
                                <div style="margin-top: 5px;">
                                    <span style="background: ${isCorrect ? '#28a745' : '#dc3545'}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 12px;">
                                        <span id="score-${result.question_id}">${result.score}</span>/${result.max_score}점
                                    </span>
                                    <span style="background: #6c757d; color: white; padding: 3px 8px; border-radius: 12px; font-size: 12px; margin-left: 5px;">
                                        ${result.grading_method === 'ai' ? 'AI 채점' : 'DB 채점'}
                                    </span>
                                    ${result.needs_review ? '<span style="background: #ffc107; color: #000; padding: 3px 8px; border-radius: 12px; font-size: 12px; margin-left: 5px;">검수 필요</span>' : ''}
                                </div>
                            </div>
                        </div>
                        ${canReview ? `
                        <div style="display: flex; gap: 10px;">
                            <button onclick="editScore('${result.question_id}')" class="btn btn-primary" style="padding: 5px 10px; font-size: 12px;">
                                ✏️ 점수 수정
                            </button>
                        </div>` : ''}
                    </div>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px;">
                        <div>
                            <strong style="color: #495057;">학생 답안:</strong>
                            <div style="background: white; padding: 10px; border-radius: 5px; margin-top: 5px; border: 1px solid #dee2e6;">
                                ${result.student_answer || '(답안 없음)'}
                            </div>
                        </div>
                        <div>
                            <strong style="color: #495057;">정답:</strong>
                            <div style="background: white; padding: 10px; border-radius: 5px; margin-top: 5px; border: 1px solid #dee2e6;">
                                ${result.correct_answer || '정답 정보 없음'}
                            </div>
                        </div>
                    </div>`;
        
        // AI 피드백이 있는 경우 표시 (수정 가능)
        if (result.ai_feedback && result.ai_feedback.trim()) {
            html += `
                    <div style="background: #e3f2fd; border: 1px solid #2196f3; border-radius: 8px; padding: 15px; margin-top: 10px;">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                            <div style="flex: 1;">
                                <strong style="color: #1976d2;">🤖 AI 피드백:</strong>
                                <div style="margin-top: 8px; line-height: 1.5;" id="feedback-${result.question_id}">${result.ai_feedback}</div>
                            </div>
                            ${canReview ? `
                            <button onclick="editFeedback('${result.question_id}')" class="btn btn-secondary" style="padding: 5px 10px; font-size: 12px; margin-left: 10px;">
                                ✏️ 피드백 수정
                            </button>` : ''}
                        </div>
                    </div>`;
        }
        
        html += `</div>`;
    });
    
    html += `</div></div>`;
    
    content.innerHTML = html;
    
    // 검수 완료 섹션 표시 (검수가 필요한 경우)
    if (gradingResult.needs_review) {
        document.getElementById('review-complete-section').style.display = 'block';
    }
}

// 기존 채점 결과 표시 함수 (solve 탭에서 사용)
function displayGradingResult(gradingResult) {
    const content = document.getElementById('solve-content');
    
    const timeMinutes = Math.floor(gradingResult.completion_time / 60);
    const timeSeconds = gradingResult.completion_time % 60;
    
    let html = `
        <div style="background: white; padding: 30px; border-radius: 15px; box-shadow: 0 8px 25px rgba(0,0,0,0.1);">
            <!-- 결과 헤더 -->
            <div style="text-align: center; margin-bottom: 30px; padding: 25px; background: linear-gradient(135deg, #28a745, #20c997); color: white; border-radius: 12px;">
                <h1 style="margin: 0; font-size: 2rem;">🎯 채점 결과</h1>
                <div style="margin-top: 15px; font-size: 1.1rem;">
                    <div><strong>학생:</strong> ${gradingResult.student_name}</div>
                    <div style="margin-top: 8px;"><strong>소요 시간:</strong> ${timeMinutes}분 ${timeSeconds}초</div>
                </div>
            </div>
            
            <!-- 점수 요약 -->
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px;">
                <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; text-align: center; border: 2px solid #28a745;">
                    <div style="font-size: 2rem; font-weight: bold; color: #28a745;">${gradingResult.total_score}</div>
                    <div style="color: #6c757d;">총 점수</div>
                </div>
                <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; text-align: center; border: 2px solid #007bff;">
                    <div style="font-size: 2rem; font-weight: bold; color: #007bff;">${gradingResult.max_score}</div>
                    <div style="color: #6c757d;">만점</div>
                </div>
                <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; text-align: center; border: 2px solid #6f42c1;">
                    <div style="font-size: 2rem; font-weight: bold; color: #6f42c1;">${gradingResult.percentage}%</div>
                    <div style="color: #6c757d;">정답률</div>
                </div>
                <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; text-align: center; border: 2px solid #dc3545;">
                    <div style="font-size: 2rem; font-weight: bold; color: #dc3545;">${gradingResult.total_questions}</div>
                    <div style="color: #6c757d;">총 문제</div>
                </div>
            </div>`;
    
    // 검수 필요 알림
    if (gradingResult.needs_review) {
        html += `
            <div style="background: #fff3cd; border: 2px solid #ffc107; border-radius: 10px; padding: 20px; margin-bottom: 30px;">
                <div style="display: flex; align-items: center; color: #856404;">
                    <span style="font-size: 1.5rem; margin-right: 10px;">⚠️</span>
                    <div>
                        <strong>검수 필요</strong><br>
                        <small>AI가 채점한 주관식 문제가 있어 교사의 검수가 필요합니다.</small>
                    </div>
                </div>
            </div>`;
    }
    
    // 지문 및 예문 표시
    if ((gradingResult.passages && gradingResult.passages.length > 0) || (gradingResult.examples && gradingResult.examples.length > 0)) {
        html += `
            <div style="margin-bottom: 30px;">
                <h3 style="color: #495057; margin-bottom: 20px; border-bottom: 2px solid #dee2e6; padding-bottom: 10px;">📖 참고 자료</h3>`;
        
        // 지문 표시
        if (gradingResult.passages && gradingResult.passages.length > 0) {
            gradingResult.passages.forEach(passage => {
                const relatedQuestions = gradingResult.question_results.filter(q => q.passage_id === passage.passage_id);
                
                html += `
                    <div style="border: 2px solid #007bff; border-radius: 10px; padding: 20px; margin-bottom: 15px; background: #f8f9ff;">
                        <h4 style="color: #007bff; margin-bottom: 15px;">📄 지문 ${passage.passage_id}${passage.text_type ? ` (${passage.text_type})` : ''}</h4>
                        <div style="background: white; padding: 15px; border-radius: 8px; margin-bottom: 10px; line-height: 1.6;">
                            <div style="margin-bottom: ${passage.korean_translation ? '12px' : '0'}; ">
                                <div style="font-weight: bold; color: #007bff; margin-bottom: 6px;">📝 영어 원문</div>
                                ${passage.original_content}
                            </div>
                            ${passage.korean_translation ? `
                            <div style="padding-top: 12px; border-top: 1px solid #e9ecef;">
                                <div style="font-weight: bold; color: #6c757d; margin-bottom: 6px;">🇰🇷 한글 번역</div>
                                <div style="color: #495057;">${passage.korean_translation}</div>
                            </div>
                            ` : ''}
                        </div>`;
                        
                if (relatedQuestions.length > 0) {
                    html += `
                        <div style="margin-top: 10px;">
                            <small style="color: #6c757d;">🔗 관련 문제: ${relatedQuestions.map(q => q.question_id + '번').join(', ')}</small>
                        </div>`;
                }
                        
                html += `</div>`;
            });
        }
        
        // 예문 표시
        if (gradingResult.examples && gradingResult.examples.length > 0) {
            gradingResult.examples.forEach(example => {
                const relatedQuestions = gradingResult.question_results.filter(q => q.example_id === example.example_id);
                
                html += `
                    <div style="border: 2px solid #28a745; border-radius: 10px; padding: 20px; margin-bottom: 15px; background: #f8fff8;">
                        <h4 style="color: #28a745; margin-bottom: 15px;">📝 예문 ${example.example_id}</h4>
                        <div style="background: white; padding: 15px; border-radius: 8px; margin-bottom: 10px; line-height: 1.6;">
                            <div style="margin-bottom: ${example.korean_translation ? '12px' : '0'}; ">
                                <div style="font-weight: bold; color: #28a745; margin-bottom: 6px;">📝 영어 원문</div>
                                ${example.original_content}
                            </div>
                            ${example.korean_translation ? `
                            <div style="padding-top: 12px; border-top: 1px solid #e9ecef;">
                                <div style="font-weight: bold; color: #6c757d; margin-bottom: 6px;">🇰🇷 한글 번역</div>
                                <div style="color: #495057;">${example.korean_translation}</div>
                            </div>
                            ` : ''}
                        </div>`;
                        
                if (relatedQuestions.length > 0) {
                    html += `
                        <div style="margin-top: 10px;">
                            <small style="color: #6c757d;">🔗 관련 문제: ${relatedQuestions.map(q => q.question_id + '번').join(', ')}</small>
                        </div>`;
                }
                        
                html += `</div>`;
            });
        }
        
        html += `</div>`;
    }
    
    // 문제별 결과
    html += `
            <div style="margin-bottom: 30px;">
                <h3 style="color: #495057; margin-bottom: 20px; border-bottom: 2px solid #dee2e6; padding-bottom: 10px;">📝 문제별 채점 결과</h3>`;
    
    gradingResult.question_results.forEach(result => {
        const isCorrect = result.is_correct;
        const borderColor = isCorrect ? '#28a745' : '#dc3545';
        const bgColor = isCorrect ? '#d4edda' : '#f8d7da';
        const iconColor = isCorrect ? '✅' : '❌';
        
        html += `
                <div style="border: 2px solid ${borderColor}; border-radius: 10px; padding: 20px; margin-bottom: 15px; background: ${bgColor};">
                    <div style="display: flex; justify-content: between; align-items: flex-start; margin-bottom: 15px;">
                        <div style="display: flex; align-items: center; flex: 1;">
                            <span style="font-size: 1.2rem; margin-right: 10px;">${iconColor}</span>
                            <div>
                                <strong>${result.question_id}번 (${result.question_type})</strong>
                                <div style="margin-top: 5px;">
                                    <span style="background: ${isCorrect ? '#28a745' : '#dc3545'}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 12px;">
                                        ${result.score}/${result.max_score}점
                                    </span>
                                    <span style="background: #6c757d; color: white; padding: 3px 8px; border-radius: 12px; font-size: 12px; margin-left: 5px;">
                                        ${result.grading_method === 'ai' ? 'AI 채점' : 'DB 채점'}
                                    </span>
                                    ${result.needs_review ? '<span style="background: #ffc107; color: #000; padding: 3px 8px; border-radius: 12px; font-size: 12px; margin-left: 5px;">검수 필요</span>' : ''}
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 15px;">
                        <div>
                            <strong style="color: #495057;">학생 답안:</strong>
                            <div style="background: white; padding: 10px; border-radius: 5px; margin-top: 5px; border: 1px solid #dee2e6;">
                                ${result.student_answer || '(답안 없음)'}
                            </div>
                        </div>
                        <div>
                            <strong style="color: #495057;">정답:</strong>
                            <div style="background: white; padding: 10px; border-radius: 5px; margin-top: 5px; border: 1px solid #dee2e6;">
                                ${result.correct_answer || '정답 정보 없음'}
                            </div>
                        </div>
                    </div>`;
        
        // AI 피드백이 있는 경우 표시
        if (result.ai_feedback && result.ai_feedback.trim()) {
            html += `
                    <div style="background: #e3f2fd; border: 1px solid #2196f3; border-radius: 8px; padding: 15px; margin-top: 10px;">
                        <strong style="color: #1976d2;">🤖 AI 피드백:</strong>
                        <div style="margin-top: 8px; line-height: 1.5;">${result.ai_feedback}</div>
                    </div>`;
        }
        
        html += `</div>`;
    });
    
    html += `
            </div>
            
            <!-- 액션 버튼 -->
            <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 2px solid #dee2e6;">
                <button onclick="showTab('worksheets-tab')" class="submit-btn" style="margin-right: 15px; background: #007bff;">
                    📋 문제지 목록으로
                </button>
                <button onclick="showTab('generate-tab')" class="submit-btn" style="background: #28a745;">
                    🚀 새 문제 생성
                </button>
            </div>
        </div>`;
    
    content.innerHTML = html;
    
    // 제출 섹션 숨기기
    document.getElementById('solve-submit-section').style.display = 'none';
}

// 점수 수정 함수
function editScore(questionId) {
    if (!currentGradingResult) return;
    
    const result = currentGradingResult.question_results.find(r => r.question_id === questionId);
    if (!result) return;
    
    const currentScore = reviewedResults[questionId]?.score !== undefined ? reviewedResults[questionId].score : result.score;
    const maxScore = result.max_score;
    
    const newScore = prompt(`${questionId}번 문제의 점수를 입력하세요 (0~${maxScore}):`, currentScore);
    
    if (newScore === null) return; // 취소
    
    const score = parseInt(newScore);
    if (isNaN(score) || score < 0 || score > maxScore) {
        alert(`올바른 점수를 입력하세요 (0~${maxScore})`);
        return;
    }
    
    // 검수 결과 저장
    if (!reviewedResults[questionId]) {
        reviewedResults[questionId] = {};
    }
    reviewedResults[questionId].score = score;
    reviewedResults[questionId].is_correct = score === maxScore;
    
    // UI 업데이트
    updateQuestionDisplay(questionId, score, maxScore);
    updateTotalScore();
    
    alert(`${questionId}번 문제의 점수가 ${score}점으로 수정되었습니다.`);
}

// 피드백 수정 함수
function editFeedback(questionId) {
    if (!currentGradingResult) return;
    
    const result = currentGradingResult.question_results.find(r => r.question_id === questionId);
    if (!result) return;
    
    const currentFeedback = reviewedResults[questionId]?.feedback || result.ai_feedback || '';
    
    const newFeedback = prompt(`${questionId}번 문제의 피드백을 수정하세요:`, currentFeedback);
    
    if (newFeedback === null) return; // 취소
    
    // 검수 결과 저장
    if (!reviewedResults[questionId]) {
        reviewedResults[questionId] = {};
    }
    reviewedResults[questionId].feedback = newFeedback;
    
    // UI 업데이트
    const feedbackElement = document.getElementById(`feedback-${questionId}`);
    if (feedbackElement) {
        feedbackElement.textContent = newFeedback;
    }
    
    alert(`${questionId}번 문제의 피드백이 수정되었습니다.`);
}

// 문제 표시 업데이트 함수
function updateQuestionDisplay(questionId, score, maxScore) {
    const scoreElement = document.getElementById(`score-${questionId}`);
    if (scoreElement) {
        scoreElement.textContent = score;
    }
    
    const isCorrect = score === maxScore;
    const questionElement = document.getElementById(`question-result-${questionId}`);
    if (questionElement) {
        const borderColor = isCorrect ? '#28a745' : '#dc3545';
        const bgColor = isCorrect ? '#d4edda' : '#f8d7da';
        questionElement.style.borderColor = borderColor;
        questionElement.style.backgroundColor = bgColor;
        
        // 아이콘 업데이트
        const iconElement = questionElement.querySelector('span');
        if (iconElement) {
            iconElement.textContent = isCorrect ? '✅' : '❌';
        }
    }
}

// 총점 업데이트 함수
function updateTotalScore() {
    if (!currentGradingResult) return;
    
    let totalScore = 0;
    let maxScore = 0;
    
    currentGradingResult.question_results.forEach(result => {
        const questionId = result.question_id;
        const score = reviewedResults[questionId]?.score !== undefined ? reviewedResults[questionId].score : result.score;
        totalScore += score;
        maxScore += result.max_score;
    });
    
    const percentage = maxScore > 0 ? Math.round((totalScore / maxScore) * 100 * 10) / 10 : 0;
    
    // UI 업데이트
    const totalScoreElement = document.getElementById('total-score');
    if (totalScoreElement) {
        totalScoreElement.textContent = totalScore;
    }
    
    const percentageElement = document.getElementById('percentage');
    if (percentageElement) {
        percentageElement.textContent = percentage + '%';
    }
    
    // 전역 결과 업데이트
    currentGradingResult.total_score = totalScore;
    currentGradingResult.percentage = percentage;
}

// 채점 결과 목록 로드 함수
async function loadGradingResults() {
    try {
        document.getElementById('result-loading').style.display = 'block';
        document.getElementById('result-error').style.display = 'none';
        
        const results = await apiService.getGradingResults();
        
        renderGradingResultsList(results);
        
    } catch (error) {
        console.error('채점 결과 로드 오류:', error);
        document.getElementById('result-error-data').textContent = error.message;
        document.getElementById('result-error').style.display = 'block';
    } finally {
        document.getElementById('result-loading').style.display = 'none';
    }
}

// 채점 결과 목록 렌더링 함수
function renderGradingResultsList(results) {
    const listContainer = document.getElementById('result-list');
    
    if (results.length === 0) {
        listContainer.innerHTML = `
            <div style="text-align: center; color: #666; margin: 40px 0;">
                <div style="font-size: 3rem; margin-bottom: 20px;">📝</div>
                <h3>채점 결과가 없습니다</h3>
                <p>학생들이 답안을 제출하면 여기에 채점 결과가 표시됩니다.</p>
            </div>
        `;
        return;
    }
    
    let html = `
        <div class="results-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(400px, 1fr)); gap: 20px; margin-top: 20px;">
    `;
    
    results.forEach(result => {
        const timeMinutes = Math.floor(result.completion_time / 60);
        const timeSeconds = result.completion_time % 60;
        const createdDate = new Date(result.created_at).toLocaleDateString('ko-KR');
        const createdTime = new Date(result.created_at).toLocaleTimeString('ko-KR');
        
        const statusColor = result.is_reviewed ? '#28a745' : (result.needs_review ? '#ffc107' : '#6c757d');
        const statusText = result.is_reviewed ? '검수 완료' : (result.needs_review ? '검수 필요' : '자동 채점');
        const statusIcon = result.is_reviewed ? '✅' : (result.needs_review ? '⚠️' : '🤖');
        
        html += `
            <div class="result-card" style="
                background: white;
                border: 2px solid ${statusColor};
                border-radius: 12px;
                padding: 20px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                transition: transform 0.2s;
                cursor: pointer;
            " onclick="viewGradingResult('${result.result_id}')" onmouseover="this.style.transform='translateY(-2px)'" onmouseout="this.style.transform='translateY(0)'">
                
                <div class="result-header" style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 15px;">
                    <div>
                        <h3 style="margin: 0; color: #333; font-size: 1.1rem;">${result.student_name}</h3>
                        <p style="margin: 5px 0 0 0; color: #666; font-size: 0.9rem;">${result.worksheet_name || 'N/A'}</p>
                    </div>
                    <span style="background: ${statusColor}; color: white; padding: 4px 8px; border-radius: 12px; font-size: 0.8rem;">
                        ${statusIcon} ${statusText}
                    </span>
                </div>
                
                <div class="result-stats" style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-bottom: 15px;">
                    <div style="text-align: center; padding: 10px; background: #f8f9fa; border-radius: 8px;">
                        <div style="font-size: 1.5rem; font-weight: bold; color: #007bff;">${result.total_score}</div>
                        <div style="font-size: 0.8rem; color: #666;">총 점수</div>
                    </div>
                    <div style="text-align: center; padding: 10px; background: #f8f9fa; border-radius: 8px;">
                        <div style="font-size: 1.5rem; font-weight: bold; color: #28a745;">${result.percentage}%</div>
                        <div style="font-size: 0.8rem; color: #666;">정답률</div>
                    </div>
                </div>
                
                <div class="result-info" style="font-size: 0.9rem; color: #666;">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <span>소요 시간:</span>
                        <span>${timeMinutes}분 ${timeSeconds}초</span>
                    </div>
                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <span>제출 일시:</span>
                        <span>${createdDate} ${createdTime}</span>
                    </div>
                    <div style="display: flex; justify-content: space-between;">
                        <span>결과 ID:</span>
                        <span style="font-family: monospace; font-size: 0.8rem;">${result.result_id}</span>
                    </div>
                </div>
            </div>
        `;
    });
    
    html += `</div>`;
    listContainer.innerHTML = html;
}

// 채점 결과 상세보기 함수
async function viewGradingResult(resultId) {
    try {
        document.getElementById('result-loading').style.display = 'block';
        
        const result = await apiService.getGradingResult(resultId);
        
        currentGradingResult = result;
        currentResultId = resultId;
        reviewedResults = {};
        
        // 상세보기 화면으로 전환
        document.getElementById('result-list').style.display = 'none';
        document.getElementById('result-detail').style.display = 'block';
        
        // 상세 내용 렌더링 (새로운 그룹핑된 버전)
        displayGradingResultDetailNew(result);
        
    } catch (error) {
        console.error('채점 결과 상세보기 오류:', error);
        alert(`채점 결과를 불러올 수 없습니다: ${error.message}`);
    } finally {
        document.getElementById('result-loading').style.display = 'none';
    }
}

// 목록으로 돌아가기 함수
function showResultList() {
    document.getElementById('result-detail').style.display = 'none';
    document.getElementById('result-list').style.display = 'block';
    currentGradingResult = null;
    currentResultId = null;
    reviewedResults = {};
}

// 탭 전환 시 채점 결과 목록 로드
function showTab(tabName) {
    // 기존 탭 전환 로직
    const tabs = document.querySelectorAll('.tab');
    const contents = document.querySelectorAll('.tab-content');
    
    tabs.forEach(tab => tab.classList.remove('active'));
    contents.forEach(content => content.classList.remove('active'));
    
    document.querySelector(`[onclick="showTab('${tabName}')"]`).classList.add('active');
    document.getElementById(tabName).classList.add('active');
    
    // 채점 결과 탭 선택 시 목록 로드
    if (tabName === 'result-tab') {
        showResultList(); // 목록 화면으로 초기화
        loadGradingResults();
    }
    
    // 문제지 목록 탭 선택 시 목록 로드
    if (tabName === 'worksheets-tab') {
        loadWorksheetsList();
    }
}

// 결과 내보내기 함수
function exportResults() {
    if (!currentGradingResult) {
        alert('내보낼 결과가 없습니다.');
        return;
    }
    
    // 검수된 결과를 반영한 최종 결과 생성
    const finalResult = JSON.parse(JSON.stringify(currentGradingResult));
    
    finalResult.question_results.forEach(result => {
        const questionId = result.question_id;
        if (reviewedResults[questionId]) {
            if (reviewedResults[questionId].score !== undefined) {
                result.score = reviewedResults[questionId].score;
                result.is_correct = reviewedResults[questionId].is_correct;
            }
            if (reviewedResults[questionId].feedback !== undefined) {
                result.ai_feedback = reviewedResults[questionId].feedback;
            }
        }
    });
    
    // JSON 파일로 다운로드
    const dataStr = JSON.stringify(finalResult, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `grading_result_${finalResult.worksheet_id}_${finalResult.student_name}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
    
    alert('채점 결과가 JSON 파일로 내보내졌습니다.');
}

// 검수 완료 및 저장 함수
async function saveReviewedResults() {
    if (!currentGradingResult || !currentResultId) {
        alert('저장할 결과가 없습니다.');
        return;
    }
    
    try {
        const saveBtn = document.getElementById('save-reviewed-btn');
        saveBtn.disabled = true;
        saveBtn.innerHTML = '💾 저장 중...';
        
        // 검수 데이터 준비
        const reviewData = {
            question_results: reviewedResults,
            reviewed_by: "교사"
        };
        
        // API 호출하여 검수 결과 저장
        const result = await apiService.saveReviewedResult(currentResultId, reviewData);
        
        alert(`검수가 완료되었습니다!\n\n최종 점수: ${result.result.total_score}/${result.result.max_score}점 (${result.result.percentage}%)\n\n결과가 데이터베이스에 저장되었습니다.`);
        
        // 검수 완료 섹션 숨기기
        document.getElementById('review-complete-section').style.display = 'none';
        
        // 결과 다시 로드하여 최신 상태 반영
        await viewGradingResult(currentResultId);
        
    } catch (error) {
        console.error('검수 결과 저장 오류:', error);
        alert(`검수 결과 저장 중 오류가 발생했습니다: ${error.message}`);
    } finally {
        const saveBtn = document.getElementById('save-reviewed-btn');
        saveBtn.disabled = false;
        saveBtn.innerHTML = '💾 검수 완료 및 저장';
    }
}

// 문제지 삭제 함수 (향후 구현)
function deleteWorksheet(worksheetId) {
    if (confirm('정말로 이 문제지를 삭제하시겠습니까?')) {
        alert(`문제지 삭제 기능은 곧 구현됩니다! (문제지 ID: ${worksheetId})`);
    }
}


// 이벤트 리스너 등록
document.addEventListener('DOMContentLoaded', function() {
    loadCategories();
    
    document.querySelectorAll('input[name="subjects"]').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            updateSubjectDetails();
            updateSubjectRatios();
        });
    });
    
    document.getElementById('questionFormat').addEventListener('change', updateFormatCounts);
    document.getElementById('totalQuestions').addEventListener('input', updateFormatCounts);
    
    document.getElementById('questionForm').addEventListener('submit', generateExam);
    
    // 초기 설정
    updateSubjectRatios();
    updateFormatCounts();
});
