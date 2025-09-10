/**
 * 영어 서비스 API 호출 전용 모듈
 * 모든 서버 통신을 중앙집중식으로 관리
 */

class ApiService {
    constructor(baseUrl = '') {
        this.baseUrl = baseUrl;
    }

    /**
     * 기본 fetch 래퍼 - 에러 처리 및 JSON 파싱 통합
     */
    async _request(url, options = {}) {
        const config = {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        };

        try {
            const response = await fetch(this.baseUrl + url, config);
            
            if (!response.ok) {
                throw new Error(`API 호출 실패: ${response.status} ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`API 요청 오류 [${url}]:`, error);
            throw error;
        }
    }

    // =============== 카테고리 관리 ===============
    /**
     * 영역별 카테고리 데이터 로드 (독해, 문법, 어휘)
     */
    async loadCategories() {
        return await this._request('/categories');
    }

    // =============== 문제지 생성 ===============
    /**
     * 문제지 생성 옵션 전송
     */
    async generateQuestionOptions(formData) {
        return await this._request('/question-options', {
            method: 'POST',
            body: JSON.stringify(formData)
        });
    }

    /**
     * 문제지 생성 요청
     */
    async createWorksheet(worksheetData) {
        return await this._request('/worksheets', {
            method: 'POST',
            body: JSON.stringify(worksheetData)
        });
    }

    // =============== 문제지 관리 ===============
    /**
     * 저장된 문제지 목록 조회
     */
    async getWorksheets() {
        return await this._request('/worksheets');
    }

    /**
     * 특정 문제지 상세 조회
     */
    async getWorksheet(worksheetId) {
        return await this._request(`/worksheets/${worksheetId}`);
    }

    /**
     * 문제지 풀이용 데이터 조회
     */
    async getWorksheetForSolving(worksheetId) {
        return await this._request(`/worksheets/${worksheetId}/solve`);
    }

    /**
     * 편집용 문제지 조회 (정답/해설 포함)
     */
    async getWorksheetForEditing(worksheetId) {
        return await this._request(`/worksheets/${worksheetId}/edit`);
    }

    // =============== 답안 제출 및 채점 ===============
    /**
     * 답안 제출 및 자동 채점 요청
     */
    async submitAnswers(worksheetId, answerData) {
        return await this._request(`/worksheets/${worksheetId}/submit`, {
            method: 'POST',
            body: JSON.stringify(answerData)
        });
    }

    // =============== 채점 결과 관리 ===============
    /**
     * 채점 결과 목록 조회
     */
    async getGradingResults() {
        return await this._request('/grading-results');
    }

    /**
     * 특정 채점 결과 상세 조회
     */
    async getGradingResult(resultId) {
        return await this._request(`/grading-results/${resultId}`);
    }

    /**
     * 검수 완료 및 결과 저장
     */
    async saveReviewedResult(resultId, reviewData) {
        return await this._request(`/grading-results/${resultId}/review`, {
            method: 'PUT',
            body: JSON.stringify(reviewData)
        });
    }

    // =============== 문제지 편집 관리 ===============
    /**
     * 문제 수정
     */
    async updateQuestion(worksheetId, questionId, questionData) {
        return await this._request(`/worksheets/${worksheetId}/questions/${questionId}`, {
            method: 'PUT',
            body: JSON.stringify(questionData)
        });
    }

    /**
     * 문제 삭제 (정답/해설도 함께 삭제)
     */
    async deleteQuestion(worksheetId, questionId) {
        return await this._request(`/worksheets/${worksheetId}/questions/${questionId}`, {
            method: 'DELETE'
        });
    }

    /**
     * 정답/해설 수정
     */
    async updateAnswer(worksheetId, questionId, answerData) {
        return await this._request(`/worksheets/${worksheetId}/questions/${questionId}/answer`, {
            method: 'PUT',
            body: JSON.stringify(answerData)
        });
    }

    /**
     * 지문 수정
     */
    async updatePassage(worksheetId, passageId, passageData) {
        return await this._request(`/worksheets/${worksheetId}/passages/${passageId}`, {
            method: 'PUT',
            body: JSON.stringify(passageData)
        });
    }

    /**
     * 예문 수정
     */
    async updateExample(worksheetId, exampleId, exampleData) {
        return await this._request(`/worksheets/${worksheetId}/examples/${exampleId}`, {
            method: 'PUT',
            body: JSON.stringify(exampleData)
        });
    }

    /**
     * AI 문제 수정 요청
     */
    async requestAIQuestionEdit(worksheetId, questionId, editPrompt) {
        return await this._request(`/worksheets/${worksheetId}/questions/${questionId}/ai-edit`, {
            method: 'POST',
            body: JSON.stringify({ edit_prompt: editPrompt })
        });
    }

    /**
     * 지문 연계성 조회 (연관 문제들 확인)
     */
    async getPassageConnections(worksheetId, passageId) {
        return await this._request(`/worksheets/${worksheetId}/passages/${passageId}/connections`);
    }

    // =============== 유틸리티 메서드 ===============
    /**
     * 파일 업로드 (FormData 전용)
     */
    async uploadFile(url, formData) {
        const config = {
            method: 'POST',
            body: formData
            // Content-Type 헤더는 자동 설정됨 (multipart/form-data)
        };

        try {
            const response = await fetch(this.baseUrl + url, config);
            
            if (!response.ok) {
                throw new Error(`파일 업로드 실패: ${response.status} ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`파일 업로드 오류 [${url}]:`, error);
            throw error;
        }
    }

    /**
     * 헬스체크 (서버 연결 상태 확인)
     */
    async healthCheck() {
        try {
            return await this._request('/health');
        } catch (error) {
            return { status: 'error', message: error.message };
        }
    }
}

// 전역 API 서비스 인스턴스 생성
const apiService = new ApiService();

// 전역 변수로 API 서비스 제공 (브라우저 호환성)
window.apiService = apiService;
