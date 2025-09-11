// 공통 유틸리티 함수 모듈

// 탭 전환 함수
function showTab(tabName) {
    // 모든 탭 숨기기
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // 모든 탭 버튼 비활성화
    document.querySelectorAll('.tab').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // 선택된 탭 표시
    const selectedTab = document.getElementById(tabName);
    if (selectedTab) {
        selectedTab.classList.add('active');
    }
    
    // 선택된 탭 버튼 활성화
    const selectedBtn = document.querySelector(`[onclick="showTab('${tabName}')"]`);
    if (selectedBtn) {
        selectedBtn.classList.add('active');
    }
    
    // 특정 탭의 초기화 함수 호출
    switch(tabName) {
        case 'worksheets-tab':
            loadWorksheets();
            break;
        case 'result-tab':
            displayGradingResults();
            break;
        case 'solve-tab':
            // 문제 풀기 탭은 별도로 처리
            break;
        case 'edit-tab':
            // 편집 탭은 별도로 처리
            break;
    }
}

// 응답 복사 함수
function copyResponse() {
    const responseContent = document.getElementById('responseContent');
    if (responseContent) {
        const text = responseContent.textContent || responseContent.innerText;
        navigator.clipboard.writeText(text).then(() => {
            alert('응답이 클립보드에 복사되었습니다.');
        }).catch(err => {
            console.error('복사 실패:', err);
            alert('복사에 실패했습니다.');
        });
    }
}

// 문제지 이름 생성 함수
function generateDefaultWorksheetName() {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    
    return `영어문제지_${year}${month}${day}_${hours}${minutes}`;
}

// 날짜 포맷팅 함수
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('ko-KR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// 시간 포맷팅 함수 (초를 분:초로 변환)
function formatTime(seconds) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
}

// 점수 색상 반환 함수
function getScoreColor(score, maxScore) {
    const percentage = (score / maxScore) * 100;
    if (percentage >= 80) return '#28a745'; // 녹색
    if (percentage >= 60) return '#ffc107'; // 노란색
    return '#dc3545'; // 빨간색
}

// 점수 아이콘 반환 함수
function getScoreIcon(score, maxScore) {
    const percentage = (score / maxScore) * 100;
    if (percentage >= 80) return '✅';
    if (percentage >= 60) return '⚠️';
    return '❌';
}

// 로딩 표시 함수
function showLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.style.display = 'block';
    }
}

// 로딩 숨기기 함수
function hideLoading(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.style.display = 'none';
    }
}

// 오류 표시 함수
function showError(elementId, message) {
    const element = document.getElementById(elementId);
    if (element) {
        element.innerHTML = `
            <div style="color: #dc3545; padding: 20px; border: 1px solid #dc3545; border-radius: 5px; background: #f8d7da;">
                <h3>❌ 오류 발생</h3>
                <p>${message}</p>
            </div>
        `;
        element.style.display = 'block';
    }
}

// 성공 메시지 표시 함수
function showSuccess(message) {
    alert(`✅ ${message}`);
}

// 확인 대화상자 함수
function confirmAction(message) {
    return confirm(message);
}

// 로컬 스토리지 저장 함수
function saveToLocalStorage(key, data) {
    try {
        localStorage.setItem(key, JSON.stringify(data));
        return true;
    } catch (error) {
        console.error('로컬 스토리지 저장 실패:', error);
        return false;
    }
}

// 로컬 스토리지 로드 함수
function loadFromLocalStorage(key) {
    try {
        const data = localStorage.getItem(key);
        return data ? JSON.parse(data) : null;
    } catch (error) {
        console.error('로컬 스토리지 로드 실패:', error);
        return null;
    }
}

// 로컬 스토리지 삭제 함수
function removeFromLocalStorage(key) {
    try {
        localStorage.removeItem(key);
        return true;
    } catch (error) {
        console.error('로컬 스토리지 삭제 실패:', error);
        return false;
    }
}

// 디바운스 함수 (연속 호출 방지)
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 스로틀 함수 (호출 빈도 제한)
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// UUID 생성 함수
function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

// 문자열 이스케이프 함수 (XSS 방지)
function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, function(m) { return map[m]; });
}

// URL 파라미터 파싱 함수
function getUrlParameter(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
}

// URL 파라미터 설정 함수
function setUrlParameter(name, value) {
    const url = new URL(window.location);
    url.searchParams.set(name, value);
    window.history.pushState({}, '', url);
}

// 페이지 새로고침 함수
function refreshPage() {
    window.location.reload();
}

// 페이지 이동 함수
function navigateTo(url) {
    window.location.href = url;
}

// 뒤로가기 함수
function goBack() {
    window.history.back();
}

// 스크롤 함수
function scrollToElement(elementId) {
    const element = document.getElementById(elementId);
    if (element) {
        element.scrollIntoView({ behavior: 'smooth' });
    }
}

// 스크롤 맨 위로 이동
function scrollToTop() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// 스크롤 맨 아래로 이동
function scrollToBottom() {
    window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' });
}

// 전역 함수로 노출
window.showTab = showTab;
window.copyResponse = copyResponse;
window.generateDefaultWorksheetName = generateDefaultWorksheetName;
window.formatDate = formatDate;
window.formatTime = formatTime;
window.getScoreColor = getScoreColor;
window.getScoreIcon = getScoreIcon;
window.showLoading = showLoading;
window.hideLoading = hideLoading;
window.showError = showError;
window.showSuccess = showSuccess;
window.confirmAction = confirmAction;
window.saveToLocalStorage = saveToLocalStorage;
window.loadFromLocalStorage = loadFromLocalStorage;
window.removeFromLocalStorage = removeFromLocalStorage;
window.debounce = debounce;
window.throttle = throttle;
window.generateUUID = generateUUID;
window.escapeHtml = escapeHtml;
window.getUrlParameter = getUrlParameter;
window.setUrlParameter = setUrlParameter;
window.refreshPage = refreshPage;
window.navigateTo = navigateTo;
window.goBack = goBack;
window.scrollToElement = scrollToElement;
window.scrollToTop = scrollToTop;
window.scrollToBottom = scrollToBottom;
