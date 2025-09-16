/**
 * 문제지 관리 메인 모듈
 * 분리된 모듈들을 통합 관리
 */

class WorksheetManager {
    constructor() {
        this.worksheets = [];
        this.gradingResults = [];
        
        // 분리된 모듈들은 init에서 초기화
        this.worksheetEditor = null;
        this.worksheetViewer = null;
        this.gradingResultEditor = null;
        this.worksheetSolver = null;
        
        this.init();
    }

    async init() {
        // ApiService가 로드될 때까지 대기
        await this.waitForApiService();
        
        // 다른 모듈들이 로드될 때까지 대기
        await this.waitForModules();
        
        // 분리된 모듈들 초기화
        this.worksheetEditor = new WorksheetEditor();
        this.worksheetViewer = new WorksheetViewer();
        this.gradingResultEditor = new GradingResultEditor();
        this.worksheetSolver = new WorksheetSolver();
        
        // 전역 참조 설정 (하위 호환성)
        window.worksheetEditor = this.worksheetEditor;
        window.worksheetViewer = this.worksheetViewer;
        window.gradingResultEditor = this.gradingResultEditor;
        window.worksheetSolver = this.worksheetSolver;
        
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

    // 다른 모듈들 로드 대기
    async waitForModules() {
        return new Promise((resolve) => {
            const checkModules = () => {
                if (typeof WorksheetRenderer !== 'undefined' &&
                    typeof WorksheetEditor !== 'undefined' && 
                    typeof WorksheetViewer !== 'undefined' && 
                    typeof GradingResultEditor !== 'undefined' && 
                    typeof WorksheetSolver !== 'undefined') {
                    resolve();
                } else {
                    setTimeout(checkModules, 50);
                }
            };
            checkModules();
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
                const targetContent = document.getElementById(`${targetTab}-tab`);
                if (targetContent) {
                    targetContent.classList.add('active');
                }
                
                // 탭별 데이터 로드
                if (targetTab === 'worksheets') {
                    this.displayWorksheets();
                } else if (targetTab === 'results') {
                    this.displayGradingResults();
                }
            });
        });
    }

    // 문제지 목록 로드
    async loadWorksheets() {
        try {
            const response = await ApiService.getWorksheets();
            console.log('🔍 API 응답 전체:', response);
            
            // API 응답이 { value: [...], Count: n } 형태인 경우 처리
            this.worksheets = response.value || response || [];
            console.log('📋 파싱된 문제지 목록:', this.worksheets);
            
            if (this.worksheets.length > 0) {
                console.log('📄 첫 번째 문제지 상세:', this.worksheets[0]);
            }
            
            console.log('문제지 로드 완료:', this.worksheets.length, '개');
        } catch (error) {
            console.error('문제지 로드 오류:', error);
            this.worksheets = [];
        }
    }

    // 채점 결과 목록 로드
    async loadGradingResults() {
        try {
            const response = await ApiService.getGradingResults();
            // API 응답이 { value: [...], Count: n } 형태인 경우 처리
            this.gradingResults = response.value || response || [];
            console.log('채점 결과 로드 완료:', this.gradingResults.length, '개');
        } catch (error) {
            console.error('채점 결과 로드 오류:', error);
            this.gradingResults = [];
        }
    }

    // 문제지 목록 표시
    displayWorksheets() {
        const container = document.getElementById('worksheetsList');
        if (!container) return;
        
        if (!this.worksheets || this.worksheets.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <h3>📝 저장된 문제지가 없습니다</h3>
                    <p>문제 생성 탭에서 새로운 문제지를 만들어보세요.</p>
                </div>
            `;
            return;
        }

        // WorksheetRenderer를 사용하여 카드 렌더링
        const renderer = new WorksheetRenderer();
        const html = this.worksheets.map(worksheet => 
            renderer.renderWorksheetCard(worksheet)
        ).join('');
        
        container.innerHTML = html;
    }

    // 채점 결과 목록 표시
    displayGradingResults() {
        const resultsContainer = document.getElementById('gradingResults');
        if (!resultsContainer) return;

        if (this.gradingResults.length === 0) {
            resultsContainer.innerHTML = `
                <div class="empty-grading-results">
                    <h3>📝 채점 결과 없음</h3>
                    <p>아직 채점된 결과가 없습니다.<br>문제지를 풀어서 채점 결과를 생성해보세요!</p>
                </div>
            `;
            return;
        }

        let html = '<div class="grading-results-grid">';
        this.gradingResults.forEach(result => {
            const percentage = result.percentage ? result.percentage.toFixed(1) : '0.0';
            const scoreClass = percentage >= 80 ? 'excellent' : 
                              percentage >= 60 ? 'good' : 'needs-improvement';
            const completionDate = new Date(result.created_at).toLocaleDateString();
            const completionTime = Math.floor(result.completion_time / 60);
            const completionSeconds = result.completion_time % 60;
            
            html += `
                <div class="grading-result-card ${scoreClass}" data-id="${result.result_id}">
                    <h3>👤 ${result.student_name}</h3>
                    <div class="score-badge">
                        ${result.total_score}/${result.max_score}점 (${percentage}%)
                    </div>
                    <div class="result-meta">
                        <p><strong>📋 문제지:</strong> ${result.worksheet_name || '문제지'}</p>
                        <p><strong>📅 제출일:</strong> ${completionDate}</p>
                        <p><strong>⏱️ 소요시간:</strong> ${completionTime}분 ${completionSeconds}초</p>
                        ${result.needs_review ? '<p><strong>🔍 상태:</strong> <span class="needs-review">검수 필요</span></p>' : ''}
                    </div>
                    <div class="result-actions">
                        <button onclick="window.worksheetManager.viewGradingResult('${result.result_id}')" 
                                class="btn btn-primary">📊 상세보기 / 수정</button>
                    </div>
                </div>
            `;
        });
        html += '</div>';

        resultsContainer.innerHTML = html;
    }

    // 위임 메서드들 - 각 모듈로 작업을 위임
    async viewWorksheet(id) {
        await this.worksheetViewer.viewWorksheet(id);
    }

    async editWorksheet(id) {
        await this.worksheetEditor.editWorksheet(id);
    }

    async solveWorksheet(id) {
        await this.worksheetSolver.solveWorksheet(id);
    }

    async viewGradingResult(id) {
        await this.gradingResultEditor.viewGradingResult(id);
    }

    // 문제지 삭제
    async deleteWorksheet(id) {
        const confirmed = confirm('정말 이 문제지를 삭제하시겠습니까?');
        if (!confirmed) return;

        try {
            await ApiService.deleteWorksheet(id);
            await this.loadWorksheets();
            this.displayWorksheets();
            alert('문제지가 삭제되었습니다.');
        } catch (error) {
            console.error('문제지 삭제 오류:', error);
            alert('문제지 삭제 중 오류가 발생했습니다.');
        }
    }

    // 목록 새로고침
    async refreshWorksheets() {
        await this.loadWorksheets();
        this.displayWorksheets();
    }

    async refreshGradingResults() {
        await this.loadGradingResults();
        this.displayGradingResults();
    }

    // 문제지 목록으로 돌아가기
    showWorksheetsList() {
        this.worksheetViewer.showWorksheetsList();
    }

    // 채점 결과 목록으로 돌아가기
    showGradingResultsList() {
        this.gradingResultEditor.showGradingResultsList();
    }
}

// 전역으로 노출
window.WorksheetManager = WorksheetManager;

// 전역 함수들 (하위 호환성)
window.viewWorksheet = (id) => window.worksheetManager.viewWorksheet(id);
window.editWorksheet = (id) => window.worksheetManager.editWorksheet(id);
window.solveWorksheet = (id) => window.worksheetManager.solveWorksheet(id);
window.deleteWorksheet = (id) => window.worksheetManager.deleteWorksheet(id);
window.viewGradingResult = (id) => window.worksheetManager.viewGradingResult(id);

// 각 모듈의 인스턴스를 전역으로 노출 (하위 호환성을 위해 유지)
window.worksheetEditor = null;
window.worksheetViewer = null;
window.gradingResultEditor = null;
window.worksheetSolver = null;
