// 메인 애플리케이션 진입점 (리팩토링된 버전)

// 페이지 로드 시 초기화
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 애플리케이션 초기화 시작');
    
    // 카테고리 로드
    loadCategories();
    
    // 이벤트 리스너 등록
    setupEventListeners();
    
    // 초기 설정
    updateSubjectRatios();
    updateFormatCounts();
    
    console.log('✅ 애플리케이션 초기화 완료');
});

// 이벤트 리스너 설정
function setupEventListeners() {
    // 영역 선택 이벤트
    document.querySelectorAll('input[name="subjects"]').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            updateSubjectDetails();
            updateSubjectRatios();
        });
    });
    
    // 문제 형식 변경 이벤트
    const questionFormatSelect = document.getElementById('questionFormat');
    if (questionFormatSelect) {
        questionFormatSelect.addEventListener('change', updateFormatCounts);
    }
    
    // 총 문제 수 변경 이벤트
    const totalQuestionsInput = document.getElementById('totalQuestions');
    if (totalQuestionsInput) {
        totalQuestionsInput.addEventListener('input', updateFormatCounts);
    }
    
    // 문제 생성 폼 제출 이벤트
    const questionForm = document.getElementById('questionForm');
    if (questionForm) {
        questionForm.addEventListener('submit', generateExam);
    }
    
    // 검수 완료 버튼 이벤트
    const completeReviewBtn = document.getElementById('complete-review-btn');
    if (completeReviewBtn) {
        completeReviewBtn.addEventListener('click', completeReview);
    }
    
    // 검수 완료 및 저장 버튼 이벤트
    const saveReviewedBtn = document.getElementById('save-reviewed-btn');
    if (saveReviewedBtn) {
        saveReviewedBtn.addEventListener('click', saveReviewedResults);
    }
}

// 검수 완료 및 저장 함수
async function saveReviewedResults() {
    const state = window.getGlobalState();
    
    if (!state.currentGradingResult || !state.currentResultId) {
        alert('저장할 결과가 없습니다.');
        return;
    }
    
    try {
        const saveBtn = document.getElementById('save-reviewed-btn');
        saveBtn.disabled = true;
        saveBtn.innerHTML = '💾 저장 중...';
        
        // 검수 데이터 준비
        const reviewData = {
            question_results: state.reviewedResults,
            reviewed_by: "교사"
        };
        
        // API 호출하여 검수 결과 저장
        const result = await apiService.saveReviewedResult(state.currentResultId, reviewData);
        
        alert(`검수가 완료되었습니다!\n\n최종 점수: ${result.result.total_score}/${result.result.max_score}점 (${result.result.percentage}%)\n\n결과가 데이터베이스에 저장되었습니다.`);
        
        // 검수 완료 섹션 숨기기
        document.getElementById('review-complete-section').style.display = 'none';
        
        // 결과 다시 로드하여 최신 상태 반영
        await viewGradingResult(state.currentResultId);
        
    } catch (error) {
        console.error('검수 결과 저장 오류:', error);
        alert(`검수 결과 저장 중 오류가 발생했습니다: ${error.message}`);
    } finally {
        const saveBtn = document.getElementById('save-reviewed-btn');
        saveBtn.disabled = false;
        saveBtn.innerHTML = '💾 검수 완료 및 저장';
    }
}

// 전역 함수로 노출
window.saveReviewedResults = saveReviewedResults;
