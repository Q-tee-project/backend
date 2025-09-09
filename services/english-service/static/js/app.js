// 문제 생성 옵션 설정 페이지 JavaScript

let categories = {};

// 페이지 로드 시 카테고리 데이터 가져오기
async function loadCategories() {
    try {
        const response = await fetch('/categories');
        categories = await response.json();
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
        console.log('🔍 collectFormData 호출 시작...');
        const formData = collectFormData();
        console.log('✅ collectFormData 완료!');
        console.log('문제지 생성 요청 데이터:', formData);

        // API 호출
        const response = await fetch('/question-options', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        });

        const result = await response.json();
        
        // 응답 데이터를 콘솔에 출력 (개발자 도구에서 확인 가능)
        console.log('='.repeat(80));
        console.log('🎉 옵션 입력 완료! 응답 데이터:');
        console.log('='.repeat(80));
        console.log('📊 전체 응답:', result);
        console.log('📝 입력 데이터:', result.request_data);
        console.log('='.repeat(80));
        
        if (response.ok && result.status === 'success') {
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

// 프롬프트 복사 함수
function copyPrompt() {
    const promptContent = document.getElementById('promptContent');
    if (promptContent) {
        const textArea = document.createElement('textarea');
        textArea.value = promptContent.textContent;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        
        // 복사 완료 알림
        const button = event.target;
        const originalText = button.textContent;
        button.textContent = '✅ 복사됨!';
        button.style.background = '#28a745';
        setTimeout(() => {
            button.textContent = originalText;
            button.style.background = '#007bff';
        }, 2000);
    }
}

// 제미나이 응답 복사 함수
function copyResponse() {
    const responseContent = document.getElementById('responseContent');
    if (responseContent) {
        const textArea = document.createElement('textarea');
        textArea.value = responseContent.textContent;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        
        // 복사 완료 알림
        const button = event.target;
        const originalText = button.textContent;
        button.textContent = '✅ 복사됨!';
        button.style.background = '#198754';
        setTimeout(() => {
            button.textContent = originalText;
            button.style.background = '#28a745';
        }, 2000);
    }
}

// 입력 결과 표시 함수
function displayInputResult(result) {
    const examContent = document.getElementById('examContent');
    const requestData = result.request_data;
    const distributionSummary = result.distribution_summary;
    const prompt = result.prompt;
    const llmResponse = result.llm_response;
    const llmError = result.llm_error;
    const subjectTypesValidation = result.subject_types_validation;
    
    let html = `
        <div style="padding: 20px; background: #f8f9fa; border-radius: 8px; margin-bottom: 20px;">
            <h2 style="color: #28a745; margin-bottom: 15px;">✅ ${result.message}</h2>`;
    
    // 분배 결과가 있으면 표시
    if (distributionSummary) {
        html += `
            <div style="background: white; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
                <h4 style="color: #007bff;">📊 문제 분배 결과</h4>
                <p><strong>총 문제 수:</strong> ${distributionSummary.total_questions}문제</p>
                <p><strong>검증 통과:</strong> ${distributionSummary.validation_passed ? '✅ 통과' : '❌ 실패'}</p>
                
                <h5 style="margin-top: 15px;">영역별 분배:</h5>
                ${distributionSummary.subject_distribution.map(item => 
                    `<p>• <strong>${item.subject}:</strong> ${item.count}문제 (${item.ratio}%)</p>`
                ).join('')}
                
                <h5 style="margin-top: 15px;">형식별 분배:</h5>
                ${distributionSummary.format_distribution.map(item => 
                    `<p>• <strong>${item.format}:</strong> ${item.count}문제 (${item.ratio}%)</p>`
                ).join('')}
                
                <h5 style="margin-top: 15px;">난이도별 분배:</h5>
                ${distributionSummary.difficulty_distribution.map(item => 
                    `<p>• <strong>${item.difficulty}:</strong> ${item.count}문제 (${item.ratio}%)</p>`
                ).join('')}
            </div>`;
    }
    
    // 영역별 출제 유형 검증 결과
    if (subjectTypesValidation) {
        html += `
            <div style="background: white; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
                <h4 style="color: #007bff;">🎯 영역별 출제 유형 확인</h4>
                ${subjectTypesValidation.reading_types.length > 0 ? 
                    `<p><strong>📖 독해 유형:</strong> ${subjectTypesValidation.reading_types.join(', ')}</p>` : ''}
                ${subjectTypesValidation.grammar_categories.length > 0 ? 
                    `<p><strong>📝 문법 카테고리:</strong> ${subjectTypesValidation.grammar_categories.join(', ')}</p>` : ''}
                ${subjectTypesValidation.grammar_topics.length > 0 ? 
                    `<p><strong>📝 문법 토픽:</strong> ${subjectTypesValidation.grammar_topics.join(', ')}</p>` : ''}
                ${subjectTypesValidation.vocabulary_categories.length > 0 ? 
                    `<p><strong>📚 어휘 카테고리:</strong> ${subjectTypesValidation.vocabulary_categories.join(', ')}</p>` : ''}
            </div>`;
    }
    
    // 제미나이 응답 결과 표시 - JSON 파싱하여 문제지 형태로 렌더링
    if (llmResponse) {
        // 콘솔에 원본 JSON 출력
        console.log('='.repeat(80));
        console.log('🤖 제미나이 원본 JSON 응답:');
        console.log('='.repeat(80));
        console.log(llmResponse);
        console.log('='.repeat(80));
        
        try {
            // 마크다운 코드 블록 제거 (```json ... ```)
            let cleanJsonString = llmResponse.trim();
            
            // ```json으로 시작하고 ```로 끝나는 경우 제거
            if (cleanJsonString.startsWith('```json')) {
                cleanJsonString = cleanJsonString.replace(/^```json\s*/, '').replace(/\s*```$/, '');
            } else if (cleanJsonString.startsWith('```')) {
                // ```만으로 시작하는 경우도 처리
                cleanJsonString = cleanJsonString.replace(/^```\s*/, '').replace(/\s*```$/, '');
            }
            
            console.log('🧹 정제된 JSON 문자열:');
            console.log(cleanJsonString);
            
            // JSON 파싱 시도
            const examData = JSON.parse(cleanJsonString);
            
            // 파싱된 JSON 객체도 콘솔에 출력
            console.log('📋 파싱된 문제지 데이터:');
            console.log(examData);
            
            // 전역 변수에 문제지 데이터 저장
            currentWorksheetData = examData;
            
            // 문제지 형태로 렌더링
            html += renderExamPaper(examData);
            
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
                    <div id="responseContent" style="background: #f8f9fa; padding: 15px; border-radius: 6px; border-left: 4px solid #ffc107; font-family: 'Courier New', monospace; white-space: pre-wrap; font-size: 13px; line-height: 1.4; max-height: 800px; overflow-y: auto; border: 1px solid #dee2e6;">${llmResponse}</div>
                    <div style="margin-top: 10px; font-size: 12px; color: #856404;">
                        ⚠️ JSON 형식이 올바르지 않아 원본 텍스트로 표시됩니다.
                    </div>
                </div>`;
        }
    }
    
    // 답안지 응답이 있는 경우 표시
    if (result.answer_sheet) {
        console.log('📋 답안지 원본 응답:');
        console.log(result.answer_sheet);
        
        try {
            // 마크다운 코드 블록 제거
            let cleanAnswerString = result.answer_sheet.trim();
            if (cleanAnswerString.startsWith('```json')) {
                cleanAnswerString = cleanAnswerString.replace(/^```json\s*/, '').replace(/\s*```$/, '');
            } else if (cleanAnswerString.startsWith('```')) {
                cleanAnswerString = cleanAnswerString.replace(/^```\s*/, '').replace(/\s*```$/, '');
            }
            
            console.log('🧹 정제된 답안지 JSON:');
            console.log(cleanAnswerString);
            
            // JSON 파싱 시도
            const answerData = JSON.parse(cleanAnswerString);
            console.log('📋 파싱된 답안지 데이터:');
            console.log(answerData);
            
            // 전역 변수에 답안지 데이터 저장
            currentAnswerData = answerData;
            
            // 답안지 렌더링
            html += renderAnswerSheet(answerData);
            
        } catch (parseError) {
            console.error('❌ 답안지 JSON 파싱 실패:', parseError);
            
            // 파싱 실패시 원본 텍스트 표시
            html += `
                <div style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; border: 2px solid #17a2b8;">
                    <h3 style="color: #0c5460; margin-bottom: 15px;">📋 답안지 (JSON 파싱 실패)</h3>
                    <div style="background: #d1ecf1; padding: 15px; border-radius: 6px; border-left: 4px solid #17a2b8; font-family: 'Courier New', monospace; white-space: pre-wrap; font-size: 13px; line-height: 1.4; max-height: 600px; overflow-y: auto; border: 1px solid #bee5eb;">${result.answer_sheet}</div>
                    <div style="margin-top: 10px; font-size: 12px; color: #0c5460;">
                        ⚠️ JSON 형식이 올바르지 않아 원본 텍스트로 표시됩니다.
                    </div>
                </div>`;
        }
    }
    
    // LLM 오류 표시
    if (llmError) {
        html += `
            <div style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; border: 2px solid #dc3545;">
                <h3 style="color: #dc3545; margin-bottom: 15px;">❌ AI 응답 오류</h3>
                <div style="background: #f8d7da; padding: 15px; border-radius: 6px; border-left: 4px solid #dc3545; color: #721c24;">${llmError}</div>
                <div style="margin-top: 10px; font-size: 12px; color: #6c757d;">
                    💡 API 키를 확인하거나 나중에 다시 시도해주세요.
                </div>
            </div>`;
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
    
    // 생성된 프롬프트 표시
    if (prompt) {
        html += `
            <div style="background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; border: 2px solid #007bff;">
                <h3 style="color: #007bff; margin-bottom: 15px; display: flex; align-items: center;">
                    🚀 생성된 프롬프트
                    <button onclick="copyPrompt()" style="margin-left: auto; padding: 8px 15px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px;">📋 복사</button>
                </h3>
                <div id="promptContent" style="background: #f8f9fa; padding: 15px; border-radius: 6px; border-left: 4px solid #007bff; font-family: 'Courier New', monospace; white-space: pre-wrap; font-size: 13px; line-height: 1.4; max-height: 600px; overflow-y: auto; border: 1px solid #dee2e6;">${prompt}</div>
                <div style="margin-top: 10px; font-size: 12px; color: #6c757d;">
                    💡 이 프롬프트를 복사해서 ChatGPT, Claude, 또는 다른 AI 모델에 붙여넣어 사용하세요!
                </div>
            </div>`;
    }
    
    html += `
            <h3 style="color: #333; margin-top: 20px; margin-bottom: 10px;">📋 입력받은 데이터:</h3>
            
            <div style="background: white; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
                <h4 style="color: #007bff;">🏫 기본 정보</h4>
                <p><strong>학교급:</strong> ${requestData.school_level}</p>
                <p><strong>학년:</strong> ${requestData.grade}학년</p>
                <p><strong>총 문제 수:</strong> ${requestData.total_questions}개</p>
            </div>
            
            <div style="background: white; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
                <h4 style="color: #007bff;">🎯 선택된 영역</h4>
                <p><strong>영역:</strong> ${requestData.subjects.join(', ')}</p>
                
                ${requestData.subject_details.reading_types.length > 0 ? 
                    `<p><strong>📖 독해 유형:</strong> ${requestData.subject_details.reading_types.join(', ')}</p>` : ''}
                
                ${requestData.subject_details.grammar_categories.length > 0 ? 
                    `<p><strong>📝 문법 카테고리:</strong> ${requestData.subject_details.grammar_categories.join(', ')}</p>` : ''}
                
                ${requestData.subject_details.grammar_topics.length > 0 ? 
                    `<p><strong>📝 문법 토픽:</strong> ${requestData.subject_details.grammar_topics.join(', ')}</p>` : ''}
                
                ${requestData.subject_details.vocabulary_categories.length > 0 ? 
                    `<p><strong>📚 어휘 카테고리:</strong> ${requestData.subject_details.vocabulary_categories.join(', ')}</p>` : ''}
            </div>
            
            <div style="background: white; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
                <h4 style="color: #007bff;">⚖️ 영역별 비율</h4>
                ${requestData.subject_ratios.map(ratio => 
                    `<p><strong>${ratio.subject}:</strong> ${ratio.ratio}%</p>`
                ).join('')}
            </div>
            
            <div style="background: white; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
                <h4 style="color: #007bff;">📋 문제 형식</h4>
                <p><strong>선택된 형식:</strong> ${requestData.question_format}</p>
                ${requestData.format_ratios.map(format => 
                    `<p><strong>${format.format}:</strong> ${format.ratio}%</p>`
                ).join('')}
            </div>
            
            <div style="background: white; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
                <h4 style="color: #007bff;">🎯 난이도 분배</h4>
                ${requestData.difficulty_distribution.map(diff => 
                    `<p><strong>${diff.difficulty}:</strong> ${diff.ratio}%</p>`
                ).join('')}
            </div>`;
    
    // 추가 요구사항 표시
    if (requestData.additional_requirements) {
        html += `
            <div style="background: white; padding: 15px; border-radius: 5px;">
                <h4 style="color: #007bff;">📝 추가 요구사항</h4>
                <p style="background: #f8f9fa; padding: 10px; border-radius: 4px; border-left: 4px solid #007bff; white-space: pre-wrap;">${requestData.additional_requirements}</p>
            </div>`;
    }
    
    html += `</div>
    `;
    
    examContent.innerHTML = html;
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
                    
                    if (passage.passage_content) {
                        // article 타입 지문
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
                            <div style="font-family: 'Courier New', monospace; white-space: pre-wrap; line-height: 1.5;">${example.example_content}</div>
                        </div>`;
                    renderedExamples.add(question.question_example_id);
                }
            }
            
            // 객관식 선택지 표시
            if (question.question_choices && question.question_choices.length > 0) {
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

    if (!answerData.answer_sheet || !answerData.answer_sheet.questions) {
        html += `<p style="text-align: center; color: #6c757d;">답안지 데이터가 없습니다.</p></div>`;
        return html;
    }

    const passages = answerData.answer_sheet.passages || [];
    const examples = answerData.answer_sheet.examples || [];
    const questions = answerData.answer_sheet.questions || [];

    // 지문과 관련 문제들을 함께 표시
    const processedPassages = new Set();
    const processedExamples = new Set();
    
    questions.forEach(question => {
        // 지문이 있는 문제 처리
        if (question.passage_id && !processedPassages.has(question.passage_id)) {
            const relatedPassage = passages.find(p => p.passage_id === question.passage_id);
            if (relatedPassage) {
                processedPassages.add(question.passage_id);
                
                // 이 지문과 관련된 모든 문제 찾기
                const relatedQuestions = questions.filter(q => q.passage_id === question.passage_id);
                const questionIds = relatedQuestions.map(q => q.question_id).sort((a, b) => parseInt(a) - parseInt(b));
                
                html += `
                    <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 25px; border-left: 4px solid #17a2b8;">
                        <div style="display: flex; align-items: center; margin-bottom: 15px;">
                            <h3 style="color: #0c5460; margin: 0; margin-right: 15px;">📖 지문 ${relatedPassage.passage_id}</h3>
                            ${relatedPassage.text_type ? `<span style="background: #17a2b8; color: white; padding: 3px 8px; border-radius: 12px; font-size: 12px; font-weight: bold;">${relatedPassage.text_type}</span>` : ''}
                        </div>
                        <div style="font-weight: bold; color: #495057; margin-bottom: 10px;">[${questionIds.join('-')}] 다음을 읽고 물음에 답하시오.</div>
                        <div style="background: white; padding: 15px; border-radius: 6px; line-height: 1.6; margin-bottom: 20px; border: 1px solid #dee2e6;">
                            ${relatedPassage.original_content}
                        </div>`;
                
                // 이 지문과 관련된 모든 문제와 정답 표시
                relatedQuestions.forEach(q => {
                    html += `
                        <div style="background: white; padding: 15px; border-radius: 6px; margin-bottom: 15px; border: 1px solid #dee2e6;">
                            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                                <span style="background: #17a2b8; color: white; padding: 5px 12px; border-radius: 20px; font-weight: bold; margin-right: 15px;">문제 ${q.question_id}</span>
                                <span style="background: #28a745; color: white; padding: 5px 12px; border-radius: 4px; font-weight: bold;">정답: ${q.correct_answer}</span>
                            </div>
                            <div style="margin-bottom: 10px;">
                                <h5 style="color: #495057; margin-bottom: 8px;">📝 해설</h5>
                                <div style="background: #f8f9fa; padding: 15px; border-radius: 4px; line-height: 1.6; color: #212529;">${q.explanation}</div>
                            </div>
                            ${q.learning_point ? `
                                <div>
                                    <h5 style="color: #495057; margin-bottom: 8px;">💡 학습 포인트</h5>
                                    <div style="background: #e7f3ff; padding: 15px; border-radius: 4px; border-left: 4px solid #007bff; color: #004085;">${q.learning_point}</div>
                                </div>
                            ` : ''}
                        </div>`;
                });
                
                html += `</div>`;
            }
        }
        
        // 예문이 있는 문제 처리 (지문이 없는 경우에만)
        else if (question.example_id && !question.passage_id && !processedExamples.has(question.example_id)) {
            const relatedExample = examples.find(e => e.example_id === question.example_id);
            if (relatedExample) {
                processedExamples.add(question.example_id);
                
                html += `
                    <div style="background: #fff3cd; padding: 20px; border-radius: 8px; margin-bottom: 25px; border-left: 4px solid #ffc107;">
                        <h3 style="color: #856404; margin-bottom: 15px;">💬 예문 ${relatedExample.example_id}</h3>
                        <div style="background: white; padding: 15px; border-radius: 6px; line-height: 1.6; margin-bottom: 20px; border: 1px solid #dee2e6;">
                            ${relatedExample.original_content}
                        </div>
                        
                        <div style="background: white; padding: 15px; border-radius: 6px; margin-bottom: 15px; border: 1px solid #dee2e6;">
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
                        </div>
                    </div>`;
            }
        }
        
        // 지문도 예문도 없는 독립적인 문제 처리
        else if (!question.passage_id && !question.example_id) {
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
    
    if (!currentWorksheetData || !currentAnswerData) {
        saveResult.innerHTML = `
            <div style="color: #dc3545; font-weight: bold;">❌ 저장할 데이터가 없습니다.</div>
        `;
        saveResult.style.display = 'block';
        return;
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
        
        // API 호출
        const response = await fetch('/worksheets', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                worksheet_data: updatedWorksheetData,
                answer_data: currentAnswerData
            })
        });
        
        const result = await response.json();
        
        if (response.ok && result.status === 'success') {
            saveResult.innerHTML = `
                <div style="color: #28a745; font-weight: bold;">
                    ✅ ${result.message}<br>
                    <small style="color: #6c757d;">문제지 ID: ${result.worksheet_id}</small>
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
        const response = await fetch('/worksheets');
        const worksheets = await response.json();
        
        if (!response.ok) {
            throw new Error(worksheets.detail || '문제지 목록을 불러올 수 없습니다.');
        }
        
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

// 문제지 보기 함수
async function viewWorksheet(worksheetId) {
    try {
        const response = await fetch(`/worksheets/${worksheetId}`);
        const worksheetData = await response.json();
        
        if (!response.ok) {
            throw new Error(worksheetData.detail || '문제지를 불러올 수 없습니다.');
        }
        
        // 문제 생성 탭으로 이동하고 결과 표시
        showTab('generate-tab');
        
        // 결과 섹션에 문제지 표시
        const examContent = document.getElementById('examContent');
        examContent.innerHTML = renderExamPaper(worksheetData);
        document.getElementById('examResult').style.display = 'block';
        
        // 결과 섹션으로 스크롤
        document.getElementById('examResult').scrollIntoView({ behavior: 'smooth' });
        
    } catch (error) {
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
        const response = await fetch(`/worksheets/${worksheetId}/solve`);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || '문제지를 불러올 수 없습니다.');
        }
        
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
                            <div style="font-family: 'Courier New', monospace; white-space: pre-wrap; line-height: 1.5;">${example.example_content}</div>
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
            const choiceValue = String.fromCharCode(65 + choiceIndex); // A B C D E
            
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
                          style="width: 100%; min-height: 120px; padding: 12px; border: 2px solid #dee2e6; border-radius: 6px; font-size: 14px; resize: vertical;">
                </textarea>
            </div>`;
    }
    
    return html;
}

// 답안 저장 함수
function saveAnswer(questionId, answer) {
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
        
        console.log('답안 제출 데이터:', submissionData);
        
        // API 호출하여 답안 제출 및 채점
        const response = await fetch(`/worksheets/${currentSolvingWorksheet.worksheet_id}/submit`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(submissionData)
        });
        
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.detail || '답안 제출 중 오류가 발생했습니다.');
        }
        
        // 성공 메시지 표시
        alert(`답안이 제출되고 채점이 완료되었습니다!\n\n학생: ${result.grading_result.student_name}\n점수: ${result.grading_result.total_score}/${result.grading_result.max_score}점 (${result.grading_result.percentage}%)\n\n채점 결과는 '🎯 채점 결과' 탭에서 확인하실 수 있습니다.`);
        
        // 초기화
        currentSolvingWorksheet = null;
        studentAnswers = {};
        solveStartTime = null;
        
        // 문제지 목록 탭으로 이동
        showTab('worksheets-tab');
        
    } catch (error) {
        console.error('답안 제출 오류:', error);
        alert(`답안 제출 중 오류가 발생했습니다: ${error.message}`);
    } finally {
        const submitBtn = document.getElementById('submit-answers-btn');
        submitBtn.disabled = false;
        submitBtn.innerHTML = '📤 답안 제출하기';
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
        
        const response = await fetch('/grading-results');
        const results = await response.json();
        
        if (!response.ok) {
            throw new Error(results.detail || '채점 결과를 불러올 수 없습니다.');
        }
        
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
        
        const response = await fetch(`/grading-results/${resultId}`);
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.detail || '채점 결과를 불러올 수 없습니다.');
        }
        
        currentGradingResult = result;
        currentResultId = resultId;
        reviewedResults = {};
        
        // 상세보기 화면으로 전환
        document.getElementById('result-list').style.display = 'none';
        document.getElementById('result-detail').style.display = 'block';
        
        // 상세 내용 렌더링
        displayGradingResultDetail(result);
        
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
        const response = await fetch(`/grading-results/${currentResultId}/review`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(reviewData)
        });
        
        const result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.detail || '검수 결과 저장 중 오류가 발생했습니다.');
        }
        
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
