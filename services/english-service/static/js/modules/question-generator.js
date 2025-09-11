// 문제 생성 관련 모듈

// 페이지 로드 시 카테고리 데이터 가져오기
async function loadCategories() {
    try {
        const state = window.getGlobalState();
        state.categories = await apiService.loadCategories();
        window.setGlobalState(state);
        console.log('카테고리 로드됨:', state.categories);
    } catch (error) {
        console.error('카테고리 로드 실패:', error);
    }
}

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
    const state = window.getGlobalState();
    
    // 독해가 선택된 경우
    if (selectedSubjects.includes('독해') && state.categories.reading_types) {
        html += '<div style="margin-bottom: 20px;">';
        html += '<h4 style="color: #007bff; margin-bottom: 10px;">📖 독해 유형</h4>';
        html += '<div class="checkbox-group">';
        state.categories.reading_types.forEach(type => {
            const isChecked = state.selectedDetails.reading_types.includes(type.name) ? 'checked' : '';
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
    if (selectedSubjects.includes('문법') && state.categories.grammar_categories) {
        html += '<div style="margin-bottom: 20px;">';
        html += '<h4 style="color: #007bff; margin-bottom: 10px;">📝 문법 카테고리</h4>';
        state.categories.grammar_categories.forEach(cat => {
            const isCatChecked = state.selectedDetails.grammar_categories.includes(cat.name) ? 'checked' : '';
            const topicsVisible = state.selectedDetails.grammar_categories.includes(cat.name) ? 'block' : 'none';
            
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
                    const isTopicChecked = state.selectedDetails.grammar_topics.includes(topic.name) ? 'checked' : '';
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
    if (selectedSubjects.includes('어휘') && state.categories.vocabulary_categories) {
        html += '<div style="margin-bottom: 20px;">';
        html += '<h4 style="color: #007bff; margin-bottom: 10px;">📚 어휘 카테고리</h4>';
        html += '<div class="checkbox-group">';
        state.categories.vocabulary_categories.forEach(cat => {
            const isChecked = state.selectedDetails.vocabulary_categories.includes(cat.name) ? 'checked' : '';
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
    const state = window.getGlobalState();
    
    // 독해 유형 저장 (텍스트 값으로)
    state.selectedDetails.reading_types = [];
    document.querySelectorAll('input[name="reading_types"]:checked').forEach(cb => {
        state.selectedDetails.reading_types.push(cb.value);
    });
    
    // 문법 카테고리 저장 (텍스트 값으로)
    state.selectedDetails.grammar_categories = [];
    document.querySelectorAll('input[name="grammar_categories"]:checked').forEach(cb => {
        state.selectedDetails.grammar_categories.push(cb.value);
    });
    
    // 문법 토픽 저장 (텍스트 값으로)
    state.selectedDetails.grammar_topics = [];
    document.querySelectorAll('input[name^="grammar_topics_"]:checked').forEach(cb => {
        state.selectedDetails.grammar_topics.push(cb.value);
    });
    
    // 어휘 카테고리 저장 (텍스트 값으로)
    state.selectedDetails.vocabulary_categories = [];
    document.querySelectorAll('input[name="vocabulary_categories"]:checked').forEach(cb => {
        state.selectedDetails.vocabulary_categories.push(cb.value);
    });
    
    window.setGlobalState(state);
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
        worksheet_level: document.getElementById('schoolLevel').value, // worksheet_level 추가
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
        
        document.getElementById('error').innerHTML = `
            <div style="color: #dc3545; padding: 20px; border: 1px solid #dc3545; border-radius: 5px; background: #f8d7da;">
                <h3>❌ 오류 발생</h3>
                <p><strong>오류 메시지:</strong> ${error.message}</p>
                <p>문제가 지속되면 관리자에게 문의하세요.</p>
            </div>
        `;
        document.getElementById('error').style.display = 'block';
    } finally {
        // 로딩 숨기기
        document.getElementById('loading').style.display = 'none';
    }
}

// 전역 함수로 노출
window.loadCategories = loadCategories;
window.updateSubjectDetails = updateSubjectDetails;
window.saveCurrentSelections = saveCurrentSelections;
window.toggleGrammarTopics = toggleGrammarTopics;
window.updateSubjectRatios = updateSubjectRatios;
window.updateTotalRatio = updateTotalRatio;
window.syncSubjectRatio = syncSubjectRatio;
window.updateFormatCounts = updateFormatCounts;
window.updateFormatRatio = updateFormatRatio;
window.syncFormatRatio = syncFormatRatio;
window.updateDifficultyRatio = updateDifficultyRatio;
window.syncDifficultyRatio = syncDifficultyRatio;
window.collectFormData = collectFormData;
window.generateExam = generateExam;
