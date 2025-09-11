// 채점 시스템 모듈

// 채점 결과 목록 표시
async function displayGradingResults() {
    try {
        const results = await apiService.getGradingResults();
        const content = document.getElementById('result-content');
        
        if (!results || results.length === 0) {
            content.innerHTML = `
                <div style="text-align: center; padding: 40px; color: #6c757d;">
                    <h3>📋 채점 결과가 없습니다</h3>
                    <p>아직 채점된 문제지가 없습니다.</p>
                </div>
            `;
            return;
        }
        
        let html = `
            <div style="background: white; padding: 30px; border-radius: 15px; box-shadow: 0 8px 25px rgba(0,0,0,0.1);">
                <h2 style="color: #495057; margin-bottom: 30px; text-align: center;">📊 채점 결과 목록</h2>
                <div style="display: grid; gap: 20px;">`;
        
        results.forEach(result => {
            const timeMinutes = Math.floor(result.completion_time / 60);
            const timeSeconds = result.completion_time % 60;
            const percentage = Math.round((result.total_score / result.max_score) * 100);
            
            html += `
                <div style="border: 2px solid #e9ecef; border-radius: 12px; padding: 20px; background: #f8f9fa; transition: all 0.3s ease; cursor: pointer;" 
                     onmouseover="this.style.borderColor='#007bff'; this.style.boxShadow='0 4px 15px rgba(0,123,255,0.2)'" 
                     onmouseout="this.style.borderColor='#e9ecef'; this.style.boxShadow='none'"
                     onclick="viewGradingResult('${result.result_id}')">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                        <div>
                            <h3 style="margin: 0; color: #495057;">${result.student_name}</h3>
                            <p style="margin: 5px 0 0 0; color: #6c757d; font-size: 14px;">문제지: ${result.worksheet_id}</p>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 1.5rem; font-weight: bold; color: ${percentage >= 80 ? '#28a745' : percentage >= 60 ? '#ffc107' : '#dc3545'};">
                                ${result.total_score}/${result.max_score}점
                            </div>
                            <div style="color: #6c757d; font-size: 14px;">${percentage}%</div>
                        </div>
                    </div>
                    <div style="display: flex; justify-content: space-between; align-items: center; color: #6c757d; font-size: 14px;">
                        <div>
                            <span>⏱️ 소요시간: ${timeMinutes}분 ${timeSeconds}초</span>
                        </div>
                        <div>
                            <span>📅 ${new Date(result.graded_at).toLocaleDateString()}</span>
                        </div>
                    </div>
                    ${result.needs_review ? `
                        <div style="margin-top: 10px; padding: 8px 12px; background: #fff3cd; border: 1px solid #ffc107; border-radius: 6px; color: #856404; font-size: 14px;">
                            ⚠️ 검수 필요
                        </div>
                    ` : ''}
                </div>`;
        });
        
        html += `
                </div>
            </div>`;
        
        content.innerHTML = html;
        
    } catch (error) {
        console.error('채점 결과 조회 오류:', error);
        document.getElementById('result-content').innerHTML = `
            <div style="text-align: center; padding: 40px; color: #dc3545;">
                <h3>❌ 오류 발생</h3>
                <p>채점 결과를 불러오는 중 오류가 발생했습니다.</p>
                <p>${error.message}</p>
            </div>
        `;
    }
}

// 채점 결과 상세보기
async function viewGradingResult(resultId) {
    try {
        const result = await apiService.getGradingResult(resultId);
        
        // 전역 변수에 저장
        const state = window.getGlobalState();
        state.currentGradingResult = result;
        state.currentResultId = resultId;
        window.setGlobalState(state);
        
        // 상세보기 표시
        displayGradingResultDetail(result);
        
        // 상세보기 탭으로 전환
        showTab('result-detail-tab');
        
    } catch (error) {
        console.error('채점 결과 상세보기 오류:', error);
        alert(`채점 결과를 불러오는 중 오류가 발생했습니다: ${error.message}`);
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
    
    // 문제별 결과 표시
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

// 점수 수정 함수
function editScore(questionId) {
    const state = window.getGlobalState();
    const result = state.currentGradingResult;
    const questionResult = result.question_results.find(q => q.question_id === questionId);
    
    if (!questionResult) {
        alert('문제를 찾을 수 없습니다.');
        return;
    }
    
    const currentScore = questionResult.reviewed_score !== null ? questionResult.reviewed_score : questionResult.score;
    const maxScore = questionResult.max_score;
    
    const newScore = prompt(`점수를 수정하세요 (0-${maxScore}):`, currentScore);
    
    if (newScore === null) return; // 취소
    
    const score = parseInt(newScore);
    if (isNaN(score) || score < 0 || score > maxScore) {
        alert(`0부터 ${maxScore}까지의 유효한 점수를 입력하세요.`);
        return;
    }
    
    // 검수된 결과에 저장
    if (!state.reviewedResults) {
        state.reviewedResults = {};
    }
    
    state.reviewedResults[questionId] = {
        ...state.reviewedResults[questionId],
        reviewed_score: score
    };
    
    window.setGlobalState(state);
    
    // UI 업데이트
    document.getElementById(`score-${questionId}`).textContent = score;
    
    // 점수에 따른 색상 변경
    const questionDiv = document.getElementById(`question-result-${questionId}`);
    const isCorrect = score === maxScore;
    const borderColor = isCorrect ? '#28a745' : '#dc3545';
    const bgColor = isCorrect ? '#d4edda' : '#f8d7da';
    const iconColor = isCorrect ? '✅' : '❌';
    
    questionDiv.style.borderColor = borderColor;
    questionDiv.style.backgroundColor = bgColor;
    questionDiv.querySelector('span[style*="font-size: 1.2rem"]').textContent = iconColor;
    
    // 점수 배지 색상 변경
    const scoreBadge = questionDiv.querySelector(`span[id="score-${questionId}"]`).parentElement;
    scoreBadge.style.backgroundColor = isCorrect ? '#28a745' : '#dc3545';
    
    alert(`점수가 ${score}점으로 수정되었습니다.`);
}

// 피드백 수정 함수
function editFeedback(questionId) {
    const state = window.getGlobalState();
    const result = state.currentGradingResult;
    const questionResult = result.question_results.find(q => q.question_id === questionId);
    
    if (!questionResult) {
        alert('문제를 찾을 수 없습니다.');
        return;
    }
    
    const currentFeedback = questionResult.reviewed_feedback || questionResult.ai_feedback || '';
    
    const newFeedback = prompt('피드백을 수정하세요:', currentFeedback);
    
    if (newFeedback === null) return; // 취소
    
    // 검수된 결과에 저장
    if (!state.reviewedResults) {
        state.reviewedResults = {};
    }
    
    state.reviewedResults[questionId] = {
        ...state.reviewedResults[questionId],
        reviewed_feedback: newFeedback
    };
    
    window.setGlobalState(state);
    
    // UI 업데이트
    document.getElementById(`feedback-${questionId}`).textContent = newFeedback;
    
    alert('피드백이 수정되었습니다.');
}

// 검수 완료 함수
async function completeReview() {
    const state = window.getGlobalState();
    
    if (!state.currentGradingResult || !state.currentResultId) {
        alert('검수할 결과가 없습니다.');
        return;
    }
    
    try {
        const reviewData = {
            question_results: state.reviewedResults,
            reviewed_by: "교사"
        };
        
        const result = await apiService.saveReviewedResult(state.currentResultId, reviewData);
        
        alert(`검수가 완료되었습니다!\n\n최종 점수: ${result.result.total_score}/${result.result.max_score}점 (${result.result.percentage}%)\n\n결과가 데이터베이스에 저장되었습니다.`);
        
        // 검수 완료 섹션 숨기기
        document.getElementById('review-complete-section').style.display = 'none';
        
        // 결과 다시 로드하여 최신 상태 반영
        await viewGradingResult(state.currentResultId);
        
    } catch (error) {
        console.error('검수 완료 오류:', error);
        alert(`검수 완료 중 오류가 발생했습니다: ${error.message}`);
    }
}

// 결과 목록으로 돌아가기
function showResultList() {
    showTab('result-tab');
    displayGradingResults();
}

// 전역 함수로 노출
window.displayGradingResults = displayGradingResults;
window.viewGradingResult = viewGradingResult;
window.displayGradingResultDetail = displayGradingResultDetail;
window.editScore = editScore;
window.editFeedback = editFeedback;
window.completeReview = completeReview;
window.showResultList = showResultList;
