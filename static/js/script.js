/**
 * Employee Tracker - Frontend Logic
 * Optimized for Duy Tan University Graduation Project
 */

const loadingOverlay = document.getElementById('loading-overlay');

function showLoading() { 
    loadingOverlay.style.display = 'flex'; 
}

function hideLoading() {
    loadingOverlay.style.display = 'none';
}

// 1. Chế độ Live AI Streaming
function startStream(filename) {
    const container = document.getElementById('video-container');
    const logBody = document.getElementById('log-body');
    const title = document.getElementById('active-video-name');
    
    // UI Feedback
    logBody.innerHTML = `<tr><td colspan="3" class="text-center text-muted">Đang khởi tạo Engine AI...</td></tr>`;
    title.innerText = "LIVE STREAMING: " + filename;
    title.className = "badge bg-danger rounded-pill px-3 shadow-sm"; 
    
    showLoading();
    
    const timestamp = new Date().getTime();
    const streamUrl = `/video_feed/${filename}?t=${timestamp}`;
    
    // Sử dụng thẻ img cho multipart/x-mixed-replace stream
    container.innerHTML = `<img src="${streamUrl}" class="w-100 shadow" alt="AI Feed" id="ai-feed">`;
    
    // Tự động ẩn loading khi ảnh bắt đầu nạp luồng
    document.getElementById('ai-feed').onload = () => hideLoading();
}

function smartProcess(filename) {
    // 1. Tìm container chứa video live
    const videoContainer = document.getElementById('video-container');
    
    // 2. Nếu đang có ảnh live, xóa sạch nó để ngắt stream ngay lập tức
    if (videoContainer) {
        videoContainer.innerHTML = `
            <div class="text-center text-white-50">
                <p class="small">Đang ngắt kết nối Live AI...</p>
            </div>`;
    }

    // 3. Hiển thị màn hình chờ (loading overlay) của bạn
    if (typeof showLoading === "function") {
        showLoading();
    }

    // 4. Đợi một khoảng rất ngắn (100ms) để trình duyệt kịp ngắt socket
    // Sau đó mới chuyển hướng để xử lý offline
    setTimeout(() => {
        window.location.href = `/process_offline/${filename}`;
    }, 100);
}

// 2. Chế độ Xem lại kết quả (Offline Results)
function playResult(filename) {
    const container = document.getElementById('video-container');
    const logBody = document.getElementById('log-body');
    const title = document.getElementById('active-video-name');
    
    title.innerText = "KẾT QUẢ PHÂN TÍCH: " + filename;
    title.className = "badge bg-success rounded-pill px-3 shadow-sm";
    
    if (typeof showLoading === "function") showLoading();

    // 1. Lấy dữ liệu nhật ký cũ từ API
    fetch(`/get_video_logs/${filename}`)
        .then(res => res.json())
        .then(data => {
            let html = data.map(row => {
                // Xử lý hiển thị Timestamp (Ưu tiên định dạng 00:00:00 từ Backend)
                const timeDisplay = row.timestamp.includes(' ') ? row.timestamp.split(' ')[1] : row.timestamp;
                
                // LOGIC ĐỒNG BỘ MÀU SẮC VỚI LIVE AI
                let badgeClass = "";
                let icon = "";
                
                if (row.action.includes('Rời bàn')) {
                    badgeClass = "badge bg-danger-subtle text-danger border-0";
                } else {
                    badgeClass = "badge bg-success-subtle text-success border-0";
                }

                return `<tr>
                    <td><span class="badge bg-dark fw-normal">${timeDisplay}</span></td>
                    <td>
                        <span class="fw-bold text-dark">${row.employee_id}</span>
                        <small class="d-block text-muted">${row.full_name || 'Chưa rõ'}</small>
                    </td>
                    <td>
                        <span class="${badgeClass}">${row.action}</span>
                    </td>
                </tr>`;
            }).join('');

            logBody.innerHTML = html || '<tr><td colspan="3" class="text-center py-3 text-muted">Không có dữ liệu cho phiên này</td></tr>';
            if (typeof hideLoading === "function") hideLoading();
        })
        .catch(err => {
            console.error("Fetch error:", err);
            if (typeof hideLoading === "function") hideLoading();
        });

    // 2. Phát video kết quả
    container.innerHTML = `
        <video width="100%" height="100%" controls autoplay style="background:#000; border-radius: 8px;">
            <source src="/view_output/${filename}" type="video/mp4">
            Trình duyệt của bạn không hỗ trợ xem video.
        </video>`;
}

// 3. Cơ chế đồng bộ Dashboard tự động (Polling)
// Chỉ cập nhật khi đang ở chế độ Live AI để tiết kiệm tài nguyên
setInterval(() => {
    const activeTitle = document.getElementById('active-video-name').innerText;
    if (activeTitle.includes("KẾT QUẢ")) return;

    fetch('/')
        .then(response => response.text())
        .then(html => {
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            
            // Các vùng cần đồng bộ nội dung
            const targetIds = ['log-body', 'video-library', 'result-library', 'employee-list-container'];
            targetIds.forEach(id => {
                const newData = doc.getElementById(id);
                const oldData = document.getElementById(id);
                if (newData && oldData && newData.innerHTML !== oldData.innerHTML) {
                    oldData.innerHTML = newData.innerHTML;
                }
            });
        })
        .catch(err => console.debug("Syncing paused..."));
}, 3000);