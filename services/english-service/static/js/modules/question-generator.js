/**
 * 문제 생성 모듈
 */

class QuestionGenerator {
    constructor() {
        this.categories = null;
        this.currentWorksheetData = null;
        this.isEditMode = false;
        this.isWorksheetSaved = false; // DB에 저장된 상태인지 추적
        this.init();
    }

    async init() {
        // 먼저 UI 렌더링
        this.renderSubjectDistribution();
        this.setupEventListeners();
        
        // 초기 난이도 설정
        this.toggleDifficultyRatios();
        this.updateDifficultyDistribution();
        
        // 초기 형식 설정
        this.toggleFormatRatios();
        this.updateFormatDistribution();
        
        // ApiService가 로드될 때까지 대기
        await this.waitForApiService();
        await this.loadCategories();
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

    // 카테고리 데이터 로드
    async loadCategories() {
        try {
            if (typeof window.ApiService === 'undefined') {
                throw new Error('ApiService가 로드되지 않았습니다.');
            }
            this.categories = await window.ApiService.getCategories();
            console.log('카테고리 로드 완료:', this.categories);
            
            // 카테고리 로드 완료 후 세부 선택 UI 추가
            this.addCategorySelectionUI();
            
        } catch (error) {
            console.error('카테고리 로드 오류:', error);
            this.showError('카테고리 정보를 불러올 수 없습니다.');
        }
    }

    // 카테고리 세부 선택 UI 추가
    addCategorySelectionUI() {
        if (!this.categories) return;

        // 각 영역에 세부 선택 버튼과 패널 추가
        const subjects = [
            { key: 'grammar', name: '문법', categories: this.categories.grammar_categories },
            { key: 'vocabulary', name: '어휘', categories: this.categories.vocabulary_categories },
            { key: 'reading', name: '독해', categories: this.categories.reading_types }
        ];

        subjects.forEach(subject => {
            const subjectItem = document.querySelector(`[data-subject="${subject.key}"]`).closest('.subject-item');
            if (!subjectItem) return;

            // 세부 선택 버튼 추가
            const toggleBtn = document.createElement('button');
            toggleBtn.className = 'btn btn-sm btn-outline category-toggle';
            toggleBtn.textContent = '🔽 세부선택';
            toggleBtn.style.marginLeft = '10px';
            toggleBtn.onclick = () => this.toggleCategoryPanel(subject.key);
            subjectItem.querySelector('.subject-controls').appendChild(toggleBtn);

            // 세부 선택 패널 추가
            const panel = document.createElement('div');
            panel.className = 'category-panel';
            panel.id = `${subject.key}Panel`;
            panel.style.display = 'none';
            subjectItem.parentNode.appendChild(panel);
        });
    }

    // 카테고리 패널 토글
    toggleCategoryPanel(subjectKey) {
        const panel = document.getElementById(`${subjectKey}Panel`);
        const toggleBtn = document.querySelector(`[data-subject="${subjectKey}"]`)
            .closest('.subject-item').querySelector('.category-toggle');

        if (panel.style.display === 'none') {
            panel.style.display = 'block';
            toggleBtn.textContent = '🔼 접기';
            this.renderCategoryPanel(subjectKey);
        } else {
            panel.style.display = 'none';
            toggleBtn.textContent = '🔽 세부선택';
        }
    }

    // 카테고리 패널 렌더링
    renderCategoryPanel(subjectKey) {
        const panel = document.getElementById(`${subjectKey}Panel`);
        if (!panel || !this.categories) return;

        let html = '';

        switch (subjectKey) {
            case 'grammar':
                html = '<div class="category-selection"><h4>📝 문법 카테고리 선택</h4>';
                this.categories.grammar_categories.forEach(category => {
                    html += `
                        <div class="category-group">
                            <label class="category-checkbox">
                                <input type="checkbox" 
                                       data-category="grammar" 
                                       data-category-id="${category.id}"
                                       onchange="toggleSubTopics(this)">
                                <strong>${category.name}</strong>
                            </label>
                    `;
                    
                    if (category.topics && category.topics.length > 0) {
                        html += '<div class="topics-list">';
                        category.topics.forEach(topic => {
                            html += `
                                <label class="topic-checkbox">
                                    <input type="checkbox" 
                                           data-topic="grammar" 
                                           data-topic-id="${topic.id}"
                                           data-parent-category="${category.id}"
                                           onchange="updateParentCategory(this)">
                                    ${topic.name}
                                </label>
                            `;
                        });
                        html += '</div>';
                    }
                    html += '</div>';
                });
                html += '</div>';
                break;

            case 'vocabulary':
                html = '<div class="category-selection"><h4>📚 어휘 카테고리 선택</h4>';
                this.categories.vocabulary_categories.forEach(category => {
                    html += `
                        <label class="category-checkbox">
                            <input type="checkbox" 
                                   data-category="vocabulary" 
                                   data-category-id="${category.id}">
                            <strong>${category.name}</strong>
                        </label>
                    `;
                });
                html += '</div>';
                break;

            case 'reading':
                html = '<div class="category-selection"><h4>📖 독해 유형 선택</h4>';
                this.categories.reading_types.forEach(type => {
                    html += `
                        <label class="category-checkbox">
                            <input type="checkbox" 
                                   data-category="reading" 
                                   data-category-id="${type.id}">
                            <strong>${type.name}</strong>
                            <div class="category-desc">${type.description || ''}</div>
                        </label>
                    `;
                });
                html += '</div>';
                break;
        }

        panel.innerHTML = html;
    }

    // 중분류 선택시 소분류 전체 선택/해제
    toggleSubTopics(categoryCheckbox) {
        const categoryId = categoryCheckbox.dataset.categoryId;
        const isChecked = categoryCheckbox.checked;
        
        // 같은 중분류의 모든 소분류 체크박스 찾기
        const topicCheckboxes = document.querySelectorAll(`input[data-parent-category="${categoryId}"]`);
        topicCheckboxes.forEach(checkbox => {
            checkbox.checked = isChecked;
        });
    }

    // 소분류 선택시 중분류 상태 업데이트
    updateParentCategory(topicCheckbox) {
        const categoryId = topicCheckbox.dataset.parentCategory;
        const categoryCheckbox = document.querySelector(`input[data-category-id="${categoryId}"]`);
        
        if (!categoryCheckbox) return;
        
        // 같은 중분류의 모든 소분류 체크박스 찾기
        const topicCheckboxes = document.querySelectorAll(`input[data-parent-category="${categoryId}"]`);
        const checkedTopics = document.querySelectorAll(`input[data-parent-category="${categoryId}"]:checked`);
        
        // 하나라도 체크되어 있으면 중분류도 체크
        categoryCheckbox.checked = checkedTopics.length > 0;
    }

    // 이벤트 리스너 설정
    setupEventListeners() {
        // 문제 생성 버튼
        document.getElementById('generateBtn').addEventListener('click', () => {
            this.generateQuestions();
        });

        // 편집 모드 토글
        document.getElementById('editModeBtn').addEventListener('click', () => {
            this.toggleEditMode();
        });

        // 문제지 저장
        document.getElementById('saveWorksheetBtn').addEventListener('click', () => {
            this.saveWorksheet();
        });

        // 새 문제지 생성
        document.getElementById('newWorksheetBtn').addEventListener('click', () => {
            this.resetWorksheet();
        });

        // 총 문제 수 변경시 비율 재계산
        document.getElementById('totalQuestions').addEventListener('input', () => {
            this.updateSubjectDistribution();
            this.updateDifficultyDistribution();
            this.updateFormatDistribution();
        });

        // 난이도 선택 변경시 비율 패널 토글
        document.querySelectorAll('input[name="difficulty"]').forEach(radio => {
            radio.addEventListener('change', () => {
                this.toggleDifficultyRatios();
            });
        });

        // 난이도 비율 변경시 문제수 업데이트
        document.querySelectorAll('.difficulty-ratio-input').forEach(input => {
            input.addEventListener('input', () => {
                this.updateDifficultyDistribution();
            });
        });

        // 형식 선택 변경시 비율 패널 토글
        document.querySelectorAll('input[name="format"]').forEach(radio => {
            radio.addEventListener('change', () => {
                this.toggleFormatRatios();
            });
        });

        // 형식 비율 변경시 문제수 업데이트
        document.querySelectorAll('.format-ratio-input').forEach(input => {
            input.addEventListener('input', () => {
                this.updateFormatDistribution();
            });
        });
    }

    // 난이도 비율 패널 토글
    toggleDifficultyRatios() {
        const selectedDifficulty = document.querySelector('input[name="difficulty"]:checked')?.value;
        const ratiosPanel = document.getElementById('difficultyRatios');
        
        if (selectedDifficulty === '혼합') {
            ratiosPanel.style.display = 'block';
        } else {
            ratiosPanel.style.display = 'none';
        }
    }

    // 난이도별 문제 수 업데이트
    updateDifficultyDistribution() {
        const totalQuestions = parseInt(document.getElementById('totalQuestions').value) || 20;
        const inputs = document.querySelectorAll('.difficulty-ratio-input');
        let totalRatio = 0;
        
        inputs.forEach(input => {
            const ratio = parseInt(input.value) || 0;
            const questions = Math.round(totalQuestions * ratio / 100);
            const questionSpan = document.querySelector(`[data-ratio-questions="${input.dataset.difficulty}"]`);
            questionSpan.textContent = `(${questions}문제)`;
            totalRatio += ratio;
        });

        // 총 비율 업데이트
        const totalRatioSpan = document.getElementById('totalDifficultyRatio');
        totalRatioSpan.textContent = totalRatio;
        
        // 비율 검증 시각적 피드백
        inputs.forEach(input => {
            if (totalRatio !== 100) {
                input.style.borderColor = totalRatio > 100 ? '#dc3545' : '#ffc107';
            } else {
                input.style.borderColor = '#28a745';
            }
        });

        // 총 비율 색상 변경
        if (totalRatio === 100) {
            totalRatioSpan.style.color = '#28a745';
        } else {
            totalRatioSpan.style.color = totalRatio > 100 ? '#dc3545' : '#ffc107';
        }
    }

    // 형식 비율 패널 토글
    toggleFormatRatios() {
        const selectedFormat = document.querySelector('input[name="format"]:checked')?.value;
        const ratiosPanel = document.getElementById('formatRatios');
        
        if (selectedFormat === '혼합') {
            ratiosPanel.style.display = 'block';
        } else {
            ratiosPanel.style.display = 'none';
        }
    }

    // 형식별 문제 수 업데이트
    updateFormatDistribution() {
        const totalQuestions = parseInt(document.getElementById('totalQuestions').value) || 20;
        const inputs = document.querySelectorAll('.format-ratio-input');
        let totalRatio = 0;
        
        inputs.forEach(input => {
            const ratio = parseInt(input.value) || 0;
            const questions = Math.round(totalQuestions * ratio / 100);
            const questionSpan = document.querySelector(`[data-format-questions="${input.dataset.format}"]`);
            questionSpan.textContent = `(${questions}문제)`;
            totalRatio += ratio;
        });

        // 총 비율 업데이트
        const totalRatioSpan = document.getElementById('totalFormatRatio');
        totalRatioSpan.textContent = totalRatio;
        
        // 비율 검증 시각적 피드백
        inputs.forEach(input => {
            if (totalRatio !== 100) {
                input.style.borderColor = totalRatio > 100 ? '#dc3545' : '#ffc107';
            } else {
                input.style.borderColor = '#28a745';
            }
        });

        // 총 비율 색상 변경
        if (totalRatio === 100) {
            totalRatioSpan.style.color = '#28a745';
        } else {
            totalRatioSpan.style.color = totalRatio > 100 ? '#dc3545' : '#ffc107';
        }
    }

    // 영역별 비율 설정 UI 렌더링
    renderSubjectDistribution() {
        // 카테고리 로드와 무관하게 기본 영역 표시
        const container = document.getElementById('subjectDistribution');
        if (!container) {
            console.error('subjectDistribution 요소를 찾을 수 없습니다.');
            return;
        }
        const subjects = [
            { key: 'grammar', name: '문법', defaultRatio: 40 },
            { key: 'vocabulary', name: '어휘', defaultRatio: 30 },
            { key: 'reading', name: '독해', defaultRatio: 30 }
        ];

        let html = '';
        subjects.forEach(subject => {
            html += `
                <div class="subject-item">
                    <span class="subject-name">${subject.name}</span>
                    <div class="subject-controls">
                        <input type="number" 
                               class="subject-input" 
                               data-subject="${subject.key}"
                               value="${subject.defaultRatio}" 
                               min="0" max="100">
                        <span>%</span>
                        <span class="subject-questions" data-questions="${subject.key}">
                            (${Math.round(20 * subject.defaultRatio / 100)}문제)
                        </span>
                    </div>
                </div>
            `;
        });

        container.innerHTML = html;

        // 비율 변경 이벤트 리스너
        container.querySelectorAll('.subject-input').forEach(input => {
            input.addEventListener('input', () => {
                this.updateSubjectDistribution();
            });
        });
    }

    // 영역별 문제 수 업데이트
    updateSubjectDistribution() {
        const totalQuestions = parseInt(document.getElementById('totalQuestions').value) || 20;
        const inputs = document.querySelectorAll('.subject-input');
        
        inputs.forEach(input => {
            const ratio = parseInt(input.value) || 0;
            const questions = Math.round(totalQuestions * ratio / 100);
            const questionSpan = document.querySelector(`[data-questions="${input.dataset.subject}"]`);
            questionSpan.textContent = `(${questions}문제)`;
        });

        // 총 비율 검증
        const totalRatio = Array.from(inputs).reduce((sum, input) => sum + (parseInt(input.value) || 0), 0);
        if (totalRatio !== 100) {
            inputs.forEach(input => {
                input.style.borderColor = totalRatio > 100 ? '#dc3545' : '#ffc107';
            });
        } else {
            inputs.forEach(input => {
                input.style.borderColor = '#28a745';
            });
        }
    }

    // 문제 생성
    async generateQuestions() {
        const generateBtn = document.getElementById('generateBtn');
        const loadingIndicator = document.getElementById('loadingIndicator');
        
        try {
            // UI 상태 변경
            generateBtn.disabled = true;
            loadingIndicator.style.display = 'flex';

            // 입력값 수집
            const formData = this.collectFormData();
            
            // 비율 검증
            if (!this.validateRatios(formData)) {
                throw new Error('영역별 비율의 합이 100%가 되어야 합니다.');
            }

            console.log('문제 생성 요청:', formData);

            // API 호출
            const result = await window.ApiService.generateQuestions(formData);
            
            console.log('문제 생성 결과:', result);

            // 응답 구조 확인 및 데이터 추출
            let worksheetData;
            if (result.llm_response) {
                // 서버에서 llm_response에 실제 문제지 데이터가 있음
                worksheetData = result.llm_response;
            } else if (result.worksheet_data) {
                // 기존 방식 호환성 유지
                worksheetData = result.worksheet_data;
            } else {
                throw new Error('문제지 데이터를 찾을 수 없습니다.');
            }

            // 결과 저장 및 표시
            this.currentWorksheetData = worksheetData;
            this.isWorksheetSaved = false; // 새로 생성된 문제지는 아직 DB에 저장되지 않음
            this.displayGeneratedWorksheet(worksheetData);

        } catch (error) {
            console.error('문제 생성 오류:', error);
            this.showError(`문제 생성 중 오류가 발생했습니다: ${error.message}`);
        } finally {
            // UI 상태 복원
            generateBtn.disabled = false;
            loadingIndicator.style.display = 'none';
        }
    }

    // 폼 데이터 수집 (새로운 API 형식에 맞춤)
    collectFormData() {
        const totalQuestions = parseInt(document.getElementById('totalQuestions').value) || 20;
        const ratios = {};
        
        document.querySelectorAll('.subject-input').forEach(input => {
            ratios[input.dataset.subject] = parseInt(input.value) || 0;
        });

        // 선택된 카테고리 정보 수집
        const selectedCategories = this.collectSelectedCategories();
        
        // 선택된 난이도 수집
        const selectedDifficulty = document.querySelector('input[name="difficulty"]:checked')?.value || '혼합';
        const difficultyDistribution = this.collectDifficultyDistribution(selectedDifficulty);

        // 선택된 형식 수집
        const selectedFormat = document.querySelector('input[name="format"]:checked')?.value || '혼합';
        const formatRatios = this.collectFormatDistribution(selectedFormat);

        // 활성화된 과목들 (비율이 0보다 큰 과목들)
        const activeSubjects = [];
        if (ratios.grammar > 0) activeSubjects.push('문법');
        if (ratios.vocabulary > 0) activeSubjects.push('어휘');
        if (ratios.reading > 0) activeSubjects.push('독해');

        // 과목별 비율 배열
        const subjectRatios = [];
        if (ratios.grammar > 0) subjectRatios.push({ subject: '문법', ratio: ratios.grammar });
        if (ratios.vocabulary > 0) subjectRatios.push({ subject: '어휘', ratio: ratios.vocabulary });
        if (ratios.reading > 0) subjectRatios.push({ subject: '독해', ratio: ratios.reading });

        return {
            // 문제지 기본 정보
            worksheet_name: document.getElementById('worksheetTitle').value || '영어 문제지',
            school_level: document.getElementById('schoolLevel').value,
            grade: parseInt(document.getElementById('grade').value),
            total_questions: totalQuestions,
            duration: parseInt(document.getElementById('duration').value) || 45,
            
            // 과목 정보
            subjects: activeSubjects,
            subject_details: {
                reading_types: selectedCategories.reading.categories,
                grammar_categories: selectedCategories.grammar.categories,
                grammar_topics: selectedCategories.grammar.topics,
                vocabulary_categories: selectedCategories.vocabulary.categories
            },
            subject_ratios: subjectRatios,
            
            // 문제 형식
            question_format: selectedFormat === '혼합' ? "혼합형" : selectedFormat,
            format_ratios: formatRatios,
            
            // 난이도 분포
            difficulty_distribution: difficultyDistribution,
            
            // 추가 요구사항
            additional_requirements: ""
        };
    }

    // 선택된 카테고리 수집 (텍스트 값으로)
    collectSelectedCategories() {
        const result = {
            grammar: { categories: [], topics: [] },
            vocabulary: { categories: [] },
            reading: { categories: [] }
        };

        // 문법 카테고리 수집 (텍스트 값으로)
        document.querySelectorAll('input[data-category="grammar"]:checked').forEach(input => {
            const categoryId = input.dataset.categoryId;
            const category = this.categories.grammar_categories.find(cat => cat.id == categoryId);
            if (category) {
                result.grammar.categories.push(category.name);
            }
        });
        
        // 문법 토픽 수집 (텍스트 값으로)
        document.querySelectorAll('input[data-topic="grammar"]:checked').forEach(input => {
            const topicId = input.dataset.topicId;
            // 모든 카테고리의 토픽에서 찾기
            for (const category of this.categories.grammar_categories) {
                if (category.topics) {
                    const topic = category.topics.find(t => t.id == topicId);
                    if (topic) {
                        result.grammar.topics.push(topic.name);
                        break;
                    }
                }
            }
        });

        // 어휘 카테고리 수집 (텍스트 값으로)
        document.querySelectorAll('input[data-category="vocabulary"]:checked').forEach(input => {
            const categoryId = input.dataset.categoryId;
            const category = this.categories.vocabulary_categories.find(cat => cat.id == categoryId);
            if (category) {
                result.vocabulary.categories.push(category.name);
            }
        });

        // 독해 카테고리 수집 (텍스트 값으로)
        document.querySelectorAll('input[data-category="reading"]:checked').forEach(input => {
            const categoryId = input.dataset.categoryId;
            const type = this.categories.reading_types.find(rt => rt.id == categoryId);
            if (type) {
                result.reading.categories.push(type.name);
            }
        });

        return result;
    }

    // 난이도 분포 수집
    collectDifficultyDistribution(selectedDifficulty) {
        if (selectedDifficulty === '혼합') {
            // 혼합 모드: 사용자가 설정한 비율 사용
            const difficultyInputs = document.querySelectorAll('.difficulty-ratio-input');
            const distribution = [];
            
            difficultyInputs.forEach(input => {
                const difficulty = input.dataset.difficulty;
                const ratio = parseInt(input.value) || 0;
                if (ratio > 0) {
                    distribution.push({ difficulty: difficulty, ratio: ratio });
                }
            });
            
            return distribution.length > 0 ? distribution : [{ difficulty: "혼합", ratio: 100 }];
        } else {
            // 단일 난이도 모드
            return [{ difficulty: selectedDifficulty, ratio: 100 }];
        }
    }

    // 형식 분포 수집
    collectFormatDistribution(selectedFormat) {
        if (selectedFormat === '혼합') {
            // 혼합 모드: 사용자가 설정한 비율 사용
            const formatInputs = document.querySelectorAll('.format-ratio-input');
            const distribution = [];
            
            formatInputs.forEach(input => {
                const format = input.dataset.format;
                const ratio = parseInt(input.value) || 0;
                if (ratio > 0) {
                    distribution.push({ format: format, ratio: ratio });
                }
            });
            
            return distribution.length > 0 ? distribution : [{ format: "혼합형", ratio: 100 }];
        } else {
            // 단일 형식 모드
            return [{ format: selectedFormat, ratio: 100 }];
        }
    }

    // 비율 검증
    validateRatios(formData) {
        const totalRatio = formData.subject_ratios.reduce((sum, item) => sum + item.ratio, 0);
        return totalRatio === 100;
    }

    // 생성된 문제지 표시
    displayGeneratedWorksheet(worksheetData) {
        const container = document.getElementById('generatedWorksheet');
        const content = document.getElementById('worksheetContent');
        
        // WorksheetRenderer 사용하여 문제지 렌더링
        if (!this.worksheetRenderer) {
            this.worksheetRenderer = new WorksheetRenderer();
        }
        const html = this.worksheetRenderer.renderWorksheet(worksheetData, { 
            showAnswers: true, 
            editMode: true  // 생성 직후에도 편집 가능하도록 변경
        });
        content.innerHTML = html;
        
        // 편집 모드 설정
        this.isEditMode = true;
        content.classList.add('edit-mode');
        
        // 편집 이벤트 리스너 추가
        this.attachEditListeners();
        
        // 컨테이너 표시
        container.style.display = 'block';
        
        // 스크롤 이동
        container.scrollIntoView({ behavior: 'smooth' });
    }

    // 문제지 렌더링
    renderWorksheet(data) {
        let html = `
            <div class="worksheet-title editable" data-type="title">
                ${data.worksheet_name}
            </div>
            <div class="worksheet-info">
                <p><strong>학교급:</strong> ${data.worksheet_level} | 
                   <strong>학년:</strong> ${data.worksheet_grade}학년 | 
                   <strong>과목:</strong> ${data.worksheet_subject} | 
                   <strong>문제 수:</strong> ${data.total_questions}문제 | 
                   <strong>시간:</strong> ${data.worksheet_duration}분</p>
            </div>
        `;

        // 지문들을 먼저 렌더링 (중복 방지)
        const renderedPassages = new Set();
        if (data.passages && data.passages.length > 0) {
            data.passages.forEach(passage => {
                if (!renderedPassages.has(passage.passage_id)) {
                    html += this.renderPassage(passage);
                    renderedPassages.add(passage.passage_id);
                }
            });
        }

        // 예문들 렌더링
        if (data.examples && data.examples.length > 0) {
            data.examples.forEach(example => {
                html += this.renderExample(example);
            });
        }

        // 문제들 렌더링
        if (data.questions && data.questions.length > 0) {
            data.questions.forEach((question, index) => {
                html += this.renderQuestion(question, index + 1);
            });
        }

        return html;
    }

    // 지문 렌더링
    renderPassage(passage) {
        let html = `
            <div class="passage" data-passage-id="${passage.passage_id}">
                <div class="passage-title">📖 지문 ${passage.passage_id}</div>
                <div class="passage-content editable" data-type="passage" data-id="${passage.passage_id}">
        `;

        // JSON 형식에 따른 렌더링
        if (passage.passage_content && passage.passage_content.content) {
            const content = passage.passage_content.content;
            
            if (Array.isArray(content)) {
                content.forEach(item => {
                    if (item.type === 'title') {
                        html += `<h3>${item.value}</h3>`;
                    } else if (item.type === 'paragraph') {
                        html += `<p>${item.value}</p>`;
                    }
                });
            } else {
                html += `<p>${content}</p>`;
            }
        }

        html += `
                </div>
            </div>
        `;
        return html;
    }

    // 예문 렌더링
    renderExample(example) {
        return `
            <div class="example" data-example-id="${example.example_id}">
                <div class="example-title">💡 예문 ${example.example_id}</div>
                <div class="example-content editable" data-type="example" data-id="${example.example_id}">
                    ${example.example_content}
                </div>
            </div>
        `;
    }

    // 문제 렌더링
    renderQuestion(question, number) {
        let html = `
            <div class="question" data-question-id="${question.question_id}">
                <div class="question-header">
                    <span class="question-number">${number}.</span>
                    <span class="question-info">
                        ${question.question_subject} | ${question.question_difficulty} | ${question.question_type}
                    </span>
                </div>
                <div class="question-text editable" data-type="question" data-id="${question.question_id}">
                    ${question.question_text}
                </div>
        `;

        // 선택지가 있는 경우
        if (question.question_choices && question.question_choices.length > 0) {
            html += '<div class="question-choices">';
            question.question_choices.forEach((choice, index) => {
                const marker = ['①', '②', '③', '④', '⑤'][index] || `${index + 1}.`;
                html += `
                    <div class="choice">
                        <span class="choice-marker">${marker}</span>
                        <span class="choice-text editable" data-type="choice" data-question-id="${question.question_id}" data-choice-index="${index}">
                            ${choice}
                        </span>
                    </div>
                `;
            });
            html += '</div>';
        }

        // 편집 모드에서만 정답과 해설 표시
        if (this.isEditMode) {
            html += `
                <div class="question-answer">
                    <strong>정답:</strong> 
                    <span class="editable" data-type="answer" data-id="${question.question_id}">
                        ${question.correct_answer || ''}
                    </span>
                </div>
            `;
            
            if (question.explanation) {
                html += `
                    <div class="question-explanation">
                        <strong>해설:</strong> 
                        <span class="editable" data-type="explanation" data-id="${question.question_id}">
                            ${question.explanation}
                        </span>
                    </div>
                `;
            }
        }

        html += '</div>';
        return html;
    }

    // 편집 모드 토글
    toggleEditMode() {
        this.isEditMode = !this.isEditMode;
        const btn = document.getElementById('editModeBtn');
        const content = document.getElementById('worksheetContent');
        
        if (this.isEditMode) {
            btn.textContent = '📖 보기 모드';
            btn.className = 'btn btn-secondary';
            content.classList.add('edit-mode');
            this.attachEditListeners();
        } else {
            btn.textContent = '✏️ 편집 모드';
            btn.className = 'btn btn-secondary';
            content.classList.remove('edit-mode');
            this.removeEditListeners();
        }

        // 문제지 다시 렌더링 (정답/해설 표시/숨김)
        if (this.currentWorksheetData) {
            if (!this.worksheetRenderer) {
                this.worksheetRenderer = new WorksheetRenderer();
            }
            const html = this.worksheetRenderer.renderWorksheet(this.currentWorksheetData, { 
                showAnswers: showAnswers, 
                editMode: this.isEditMode 
            });
            content.innerHTML = html;
            if (this.isEditMode) {
                content.classList.add('edit-mode');
                this.attachEditListeners();
            }
        }
    }

    // 편집 이벤트 리스너 추가
    attachEditListeners() {
        const editables = document.querySelectorAll('.editable');
        editables.forEach(element => {
            element.contentEditable = true;
            element.addEventListener('blur', this.handleEdit.bind(this));
            element.addEventListener('keydown', this.handleEditKeydown.bind(this));
        });
    }

    // 편집 이벤트 리스너 제거
    removeEditListeners() {
        const editables = document.querySelectorAll('.editable');
        editables.forEach(element => {
            element.contentEditable = false;
            element.removeEventListener('blur', this.handleEdit.bind(this));
            element.removeEventListener('keydown', this.handleEditKeydown.bind(this));
        });
    }

    // 편집 처리 (메모리에서만 수정)
    async handleEdit(event) {
        const element = event.target;
        const type = element.dataset.type;
        const id = element.dataset.id;
        const newContent = element.textContent.trim();

        try {
            element.style.backgroundColor = '#fff3cd';
            
            // 메모리에서 데이터 업데이트 (DB 저장은 저장 버튼 클릭 시에만)
            switch (type) {
                case 'title':
                    this.currentWorksheetData.worksheet_name = newContent;
                    break;
                    
                case 'question':
                    this.updateQuestionInMemory(id, 'question_text', newContent);
                    break;
                    
                case 'choice':
                    const choiceIndex = parseInt(element.dataset.choiceIndex);
                    const questionId = element.dataset.questionId;
                    this.updateChoiceInMemory(questionId, choiceIndex, newContent);
                    break;
                    
                case 'answer':
                    this.updateQuestionInMemory(id, 'correct_answer', newContent);
                    break;
                    
                case 'explanation':
                    this.updateQuestionInMemory(id, 'explanation', newContent);
                    break;
                    
                case 'learning_point':
                    this.updateQuestionInMemory(id, 'learning_point', newContent);
                    break;
                    
                case 'passage':
                    // 지문은 JSON 형식 유지하면서 메모리 업데이트
                    this.updatePassageInMemory(id, element);
                    break;
                    
                case 'example':
                    this.updateExampleInMemory(id, newContent);
                    break;
            }

            // 성공 표시
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
        
        return { content: content.length > 0 ? content : [{ type: 'paragraph', value: element.textContent }] };
    }

    // 문제지 저장
    async saveWorksheet() {
        if (!this.currentWorksheetData) {
            this.showError('저장할 문제지가 없습니다.');
            return;
        }

        try {
            const saveBtn = document.getElementById('saveWorksheetBtn');
            const originalText = saveBtn.textContent;
            saveBtn.textContent = '💾 저장 중...';
            saveBtn.disabled = true;
            console.log(this.currentWorksheetData);
            const result = await window.ApiService.saveWorksheet(this.currentWorksheetData);
            console.log(result);
            this.isWorksheetSaved = true; // 저장 완료 상태로 변경
            this.showSuccess('문제지가 성공적으로 저장되었습니다.');
            
            // 저장된 ID로 업데이트
            if (result.worksheet_id) {
                this.currentWorksheetData.worksheet_id = result.worksheet_id;
            }

        } catch (error) {
            console.error('문제지 저장 오류:', error);
            this.showError(`문제지 저장에 실패했습니다: ${error.message}`);
        } finally {
            const saveBtn = document.getElementById('saveWorksheetBtn');
            saveBtn.textContent = '💾 문제지 저장';
            saveBtn.disabled = false;
        }
    }

    // 새 문제지 생성
    resetWorksheet() {
        this.currentWorksheetData = null;
        this.isEditMode = false;
        
        document.getElementById('generatedWorksheet').style.display = 'none';
        document.getElementById('worksheetContent').innerHTML = '';
        
        // 폼 초기화
        document.getElementById('worksheetTitle').value = '영어 문제지';
        document.getElementById('totalQuestions').value = '20';
        document.getElementById('duration').value = '45';
        
        this.renderSubjectDistribution();
    }

    // 성공 메시지 표시
    showSuccess(message) {
        this.showMessage(message, 'success');
    }

    // 오류 메시지 표시
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

    // 메모리에서 문제 데이터 업데이트
    updateQuestionInMemory(questionId, field, value) {
        if (this.currentWorksheetData && this.currentWorksheetData.questions) {
            const question = this.currentWorksheetData.questions.find(q => q.question_id === questionId);
            if (question) {
                question[field] = value;
            }
        }
    }

    // 메모리에서 선택지 데이터 업데이트
    updateChoiceInMemory(questionId, choiceIndex, value) {
        if (this.currentWorksheetData && this.currentWorksheetData.questions) {
            const question = this.currentWorksheetData.questions.find(q => q.question_id === questionId);
            if (question && question.question_choices && question.question_choices[choiceIndex] !== undefined) {
                question.question_choices[choiceIndex] = value;
            }
        }
    }

    // 메모리에서 지문 데이터 업데이트 (JSON 형식 유지)
    updatePassageInMemory(passageId, element) {
        if (this.currentWorksheetData && this.currentWorksheetData.passages) {
            const passage = this.currentWorksheetData.passages.find(p => p.passage_id === passageId);
            if (passage) {
                // 지문 내용을 JSON 형식으로 파싱하여 저장
                const parsedContent = this.parseEditedPassageContent(element);
                passage.passage_content = parsedContent;
            }
        }
    }

    // 메모리에서 예문 데이터 업데이트
    updateExampleInMemory(exampleId, value) {
        if (this.currentWorksheetData && this.currentWorksheetData.examples) {
            const example = this.currentWorksheetData.examples.find(e => e.example_id === exampleId);
            if (example) {
                example.example_content = value;
            }
        }
    }

    // 편집된 지문 내용을 JSON 형식으로 파싱
    parseEditedPassageContent(element) {
        // 현재 지문의 원본 구조를 유지하면서 내용만 업데이트
        const passageId = element.dataset.id;
        const passage = this.currentWorksheetData.passages?.find(p => p.passage_id === passageId);
        
        if (passage && passage.passage_content) {
            const originalContent = passage.passage_content;
            const editedText = element.textContent || element.innerText;
            
            // JSON 구조 유지하면서 텍스트 내용만 업데이트
            if (typeof originalContent === 'object' && originalContent.content) {
                const updatedContent = { ...originalContent };
                
                // 단순한 경우: 첫 번째 paragraph의 내용을 업데이트
                if (Array.isArray(updatedContent.content) && updatedContent.content.length > 0) {
                    const firstParagraph = updatedContent.content.find(item => item.type === 'paragraph');
                    if (firstParagraph) {
                        firstParagraph.value = editedText;
                    }
                }
                
                return updatedContent;
            }
        }
        
        // 기본 구조로 반환
        return {
            content: [{
                type: 'paragraph',
                value: element.textContent || element.innerText || ''
            }]
        };
    }
}

// 전역 함수들 (HTML에서 호출)
window.toggleSubTopics = function(categoryCheckbox) {
    if (window.questionGenerator) {
        window.questionGenerator.toggleSubTopics(categoryCheckbox);
    }
};

window.updateParentCategory = function(topicCheckbox) {
    if (window.questionGenerator) {
        window.questionGenerator.updateParentCategory(topicCheckbox);
    }
};

// 전역으로 노출
window.QuestionGenerator = QuestionGenerator;
