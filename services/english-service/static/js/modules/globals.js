// 전역 변수 및 공통 설정
let categories = {};

// 현재 선택 상태를 저장할 객체
let selectedDetails = {
    reading_types: [],
    grammar_categories: [],
    grammar_topics: {},
    vocabulary_categories: []
};

// 문제지 관련 전역 변수
let currentWorksheetData = null;
let currentAnswerData = null;

// 편집 관련 전역 변수
let currentEditingWorksheet = null;
let isEditMode = false;

// 문제 풀이 관련 전역 변수
let currentSolvingWorksheet = null;
let studentAnswers = {};
let solveStartTime = null;
let solveTimer = null;

// 채점 관련 전역 변수
let currentGradingResult = null;
let currentResultId = null;
let reviewedResults = {}; // 검수된 결과 저장

// 전역 변수 접근을 위한 getter/setter 함수들
window.getGlobalState = function() {
    return {
        categories,
        selectedDetails,
        currentWorksheetData,
        currentAnswerData,
        currentEditingWorksheet,
        isEditMode,
        currentSolvingWorksheet,
        studentAnswers,
        solveStartTime,
        solveTimer,
        currentGradingResult,
        currentResultId,
        reviewedResults
    };
};

window.setGlobalState = function(newState) {
    if (newState.categories !== undefined) categories = newState.categories;
    if (newState.selectedDetails !== undefined) selectedDetails = newState.selectedDetails;
    if (newState.currentWorksheetData !== undefined) currentWorksheetData = newState.currentWorksheetData;
    if (newState.currentAnswerData !== undefined) currentAnswerData = newState.currentAnswerData;
    if (newState.currentEditingWorksheet !== undefined) currentEditingWorksheet = newState.currentEditingWorksheet;
    if (newState.isEditMode !== undefined) isEditMode = newState.isEditMode;
    if (newState.currentSolvingWorksheet !== undefined) currentSolvingWorksheet = newState.currentSolvingWorksheet;
    if (newState.studentAnswers !== undefined) studentAnswers = newState.studentAnswers;
    if (newState.solveStartTime !== undefined) solveStartTime = newState.solveStartTime;
    if (newState.solveTimer !== undefined) solveTimer = newState.solveTimer;
    if (newState.currentGradingResult !== undefined) currentGradingResult = newState.currentGradingResult;
    if (newState.currentResultId !== undefined) currentResultId = newState.currentResultId;
    if (newState.reviewedResults !== undefined) reviewedResults = newState.reviewedResults;
};
