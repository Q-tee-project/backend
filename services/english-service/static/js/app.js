/**
 * 메인 애플리케이션 초기화
 */

class App {
    constructor() {
        this.questionGenerator = null;
        this.worksheetEditor = null;
        this.init();
    }

    async init() {
        try {
            console.log('🚀 애플리케이션 초기화 시작');
            
            // DOM이 로드될 때까지 대기
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', () => this.initializeComponents());
            } else {
                this.initializeComponents();
            }
            
        } catch (error) {
            console.error('애플리케이션 초기화 오류:', error);
        }
    }

    async initializeComponents() {
        try {
            console.log('📦 컴포넌트 초기화 시작');
            
            // DOM 요소 존재 확인
            const requiredElements = [
                'subjectDistribution',
                'generateBtn', 
                'worksheetsList',
                'gradingResults'
            ];
            
            for (const elementId of requiredElements) {
                const element = document.getElementById(elementId);
                if (!element) {
                    throw new Error(`필수 DOM 요소를 찾을 수 없습니다: ${elementId}`);
                }
            }
            
            // 문제 생성기 초기화
            this.questionGenerator = new QuestionGenerator();
            
            // 문제지 관리자 초기화 (통합 모듈)
            this.worksheetManager = new WorksheetManager();
            
            // 전역 참조 설정 (하위 호환성)
            window.questionGenerator = this.questionGenerator;
            window.worksheetManager = this.worksheetManager;
            
            console.log('✅ 모든 컴포넌트 초기화 완료');
            
            // 추가 이벤트 리스너 설정
            this.setupGlobalEventListeners();
            
        } catch (error) {
            console.error('컴포넌트 초기화 오류:', error);
            this.showError('애플리케이션 초기화에 실패했습니다.');
        }
    }

    // 전역 이벤트 리스너 설정
    setupGlobalEventListeners() {
        // ESC 키로 모달 닫기
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                const modals = document.querySelectorAll('.modal-overlay');
                modals.forEach(modal => modal.remove());
            }
        });

        // 에러 처리
        window.addEventListener('error', (e) => {
            console.error('전역 오류:', e.error);
        });

        // 미처리 Promise 거부
        window.addEventListener('unhandledrejection', (e) => {
            console.error('미처리 Promise 거부:', e.reason);
        });

        console.log('🎯 전역 이벤트 리스너 설정 완료');
    }

    // 오류 메시지 표시
    showError(message) {
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-error';
        alertDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 8px;
            background: #dc3545;
            color: white;
            font-weight: 500;
            z-index: 1000;
            max-width: 400px;
            word-wrap: break-word;
        `;
        alertDiv.textContent = message;
        
        document.body.appendChild(alertDiv);
        
        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }
}

// 애플리케이션 시작
const app = new App();

// 전역으로 노출
window.app = app;
