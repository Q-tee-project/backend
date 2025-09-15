/**
 * API 통신 유틸리티
 */

class ApiClient {
    constructor(baseUrl = '') {
        this.baseUrl = baseUrl;
    }

    async request(url, options = {}) {
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
                const errorData = await response.json().catch(() => ({ 
                    detail: `HTTP ${response.status}: ${response.statusText}` 
                }));
                console.error('API Error Details:', errorData);
                
                // 422 오류의 경우 상세한 검증 오류 표시
                if (response.status === 422 && errorData.detail && Array.isArray(errorData.detail)) {
                    const validationErrors = errorData.detail.map(err => {
                        const location = err.loc ? err.loc.join('.') : 'unknown_field';
                        const message = err.msg || 'validation error';
                        const input = err.input ? JSON.stringify(err.input).substring(0, 100) : '';
                        return `${location}: ${message} ${input ? `(input: ${input})` : ''}`;
                    }).join('; ');
                    throw new Error(`Validation Error: ${validationErrors}`);
                }
                
                throw new Error(errorData.detail || `Request failed with status ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API Request Error:', error);
            throw error;
        }
    }

    // GET 요청
    async get(url) {
        return this.request(url, { method: 'GET' });
    }

    // POST 요청
    async post(url, data) {
        return this.request(url, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    // PUT 요청
    async put(url, data) {
        return this.request(url, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    // DELETE 요청
    async delete(url) {
        return this.request(url, { method: 'DELETE' });
    }
}

// API 클라이언트 인스턴스
const api = new ApiClient();

// API 엔드포인트들
const API_ENDPOINTS = {
    // 카테고리
    categories: '/api/v1/categories',
    
    // 문제 생성
    questionGenerate: '/api/v1/question-generate',
    
    // 문제지 관리
    worksheets: '/api/v1/worksheets',
    worksheet: (id) => `/api/v1/worksheets/${id}`,
    worksheetEdit: (id) => `/api/v1/worksheets/${id}/edit`,
    worksheetSolve: (id) => `/api/v1/worksheets/${id}/solve`,
    
    // 문제지 편집
    updateQuestionText: (worksheetId, questionId) => `/api/v1/worksheets/${worksheetId}/questions/${questionId}/text`,
    updateQuestionChoice: (worksheetId, questionId) => `/api/v1/worksheets/${worksheetId}/questions/${questionId}/choice`,
    updateQuestionAnswer: (worksheetId, questionId) => `/api/v1/worksheets/${worksheetId}/questions/${questionId}/answer`,
    updatePassage: (worksheetId, passageId) => `/api/v1/worksheets/${worksheetId}/passages/${passageId}`,
    updateExample: (worksheetId, exampleId) => `/api/v1/worksheets/${worksheetId}/examples/${exampleId}`,
    
    // 채점
    submitAnswers: (worksheetId) => `/api/v1/worksheets/${worksheetId}/submit`,
    gradingResults: '/api/v1/grading-results',
    gradingResult: (id) => `/api/v1/grading-results/${id}`,
    reviewGrading: (id) => `/api/v1/grading-results/${id}/review`
};

// 편의 함수들
const ApiService = {
    // 카테고리 조회
    async getCategories() {
        return api.get(API_ENDPOINTS.categories);
    },

    // 문제 생성
    async generateQuestions(options) {
        return api.post(API_ENDPOINTS.questionGenerate, options);
    },

    // 문제지 저장
    async saveWorksheet(worksheetData) {
        // 서버가 기대하는 형식으로 데이터 변환
        const requestData = {
            worksheet_data: worksheetData
        };
        return api.post(API_ENDPOINTS.worksheets, requestData);
    },

    // 문제지 목록 조회
    async getWorksheets() {
        return api.get(API_ENDPOINTS.worksheets);
    },

    // 문제지 편집용 조회
    async getWorksheetForEdit(id) {
        return api.get(API_ENDPOINTS.worksheetEdit(id));
    },

    // 문제지 풀이용 조회
    async getWorksheetForSolve(id) {
        return api.get(API_ENDPOINTS.worksheetSolve(id));
    },

    // 문제지 삭제
    async deleteWorksheet(id) {
        return api.delete(API_ENDPOINTS.worksheet(id));
    },

    // 문제 텍스트 수정
    async updateQuestionText(worksheetId, questionId, text) {
        return api.put(API_ENDPOINTS.updateQuestionText(worksheetId, questionId), {
            question_text: text
        });
    },

    // 문제 선택지 수정
    async updateQuestionChoice(worksheetId, questionId, choiceIndex, text) {
        return api.put(API_ENDPOINTS.updateQuestionChoice(worksheetId, questionId), {
            choice_index: choiceIndex,
            choice_text: text
        });
    },

    // 문제 정답 수정
    async updateQuestionAnswer(worksheetId, questionId, answer) {
        return api.put(API_ENDPOINTS.updateQuestionAnswer(worksheetId, questionId), {
            correct_answer: answer
        });
    },

    // 지문 수정
    async updatePassage(worksheetId, passageId, content) {
        return api.put(API_ENDPOINTS.updatePassage(worksheetId, passageId), {
            passage_content: content
        });
    },

    // 예문 수정
    async updateExample(worksheetId, exampleId, content) {
        return api.put(API_ENDPOINTS.updateExample(worksheetId, exampleId), {
            example_content: content
        });
    },

    // 답안 제출 및 채점
    async submitAnswers(worksheetId, data) {
        return api.post(API_ENDPOINTS.submitAnswers(worksheetId), data);
    },

    // 채점 결과 목록 조회
    async getGradingResults() {
        return api.get(API_ENDPOINTS.gradingResults);
    },

    // 채점 결과 상세 조회
    async getGradingResult(id) {
        return api.get(API_ENDPOINTS.gradingResult(id));
    },

    // AI 채점 검수
    async reviewGrading(id, data) {
        return api.put(API_ENDPOINTS.reviewGrading(id), data);
    }
};

// 전역으로 노출
window.ApiService = ApiService;
window.api = api;
