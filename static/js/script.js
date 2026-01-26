function showLoading() { 
    document.getElementById('loading-overlay').style.display = 'flex'; 
}

function startStream(filename) {
    const container = document.getElementById('video-container');
    const logBody = document.getElementById('log-body');
    const title = document.getElementById('active-video-name');
    
    // Reset trạng thái
    logBody.innerHTML = `<tr><td colspan="3" class="text-center text-muted italic">Đang khởi tạo phiên mới...</td></tr>`;
    title.innerText = "LIVE: " + filename;
    title.className = "badge bg-danger rounded-pill px-3"; // Đổi màu sang đỏ cho Live
    
    showLoading();
    
    const timestamp = new Date().getTime();
    container.innerHTML = `<img src="/video_feed/${filename}?t=${timestamp}" alt="Streaming AI...">`;
    
    setTimeout(() => { 
        document.getElementById('loading-overlay').style.display = 'none'; 
    }, 1000);
}

function playResult(filename) {
    const container = document.getElementById('video-container');
    const logBody = document.getElementById('log-body');
    const title = document.getElementById('active-video-name');
    
    title.innerText = "KẾT QUẢ: " + filename;
    title.className = "badge bg-success rounded-pill px-3";
    
    showLoading();

    fetch(`/get_video_logs/${filename}`)
        .then(res => res.json())
        .then(data => {
            let html = data.map(row => {
                const timePart = row.timestamp.includes(' ') ? row.timestamp.split(' ')[1] : row.timestamp;
                return `<tr>
                    <td class="text-muted">${timePart}</td>
                    <td>
                        <span class="fw-bold text-primary">${row.employee_id}</span>
                        <small class="d-block text-muted">${row.full_name || 'Chưa rõ'}</small>
                    </td>
                    <td><span class="badge bg-light text-dark border">${row.action}</span></td>
                </tr>`;
            }).join('');
            logBody.innerHTML = html || '<tr><td colspan="3" class="text-center">Không có dữ liệu lịch sử</td></tr>';
        });

    container.innerHTML = `<video width="100%" height="100%" controls autoplay style="background:#000;">
                                <source src="/download_output/${filename}" type="video/mp4">
                           </video>`;
    
    setTimeout(() => { 
        document.getElementById('loading-overlay').style.display = 'none'; 
    }, 500);
}

// Đồng bộ Dashboard
setInterval(() => {
    const activeTitle = document.getElementById('active-video-name').innerText;
    const logBody = document.getElementById('log-body');

    if (activeTitle.includes("KẾT QUẢ")) return;

    fetch('/')
        .then(response => response.text())
        .then(html => {
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            
            // Cập nhật các vùng cần thiết
            const targetIds = ['log-body', 'video-library', 'result-library', 'employee-list-container'];
            targetIds.forEach(id => {
                const newData = doc.getElementById(id);
                if (newData) document.getElementById(id).innerHTML = newData.innerHTML;
            });
        })
        .catch(err => console.warn("Syncing..."));
}, 3000);