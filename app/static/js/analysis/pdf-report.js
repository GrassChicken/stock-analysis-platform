/**
 * PDF 报告生成与下载模块
 * 
 * 职责:
 * - 调用后端 API 生成 PDF 报告
 * - 处理下载逻辑
 * - 显示加载状态和错误提示
 */

async function generatePDFReport() {
    const btn = document.getElementById('pdf-download-btn');
    const statusDiv = document.getElementById('pdf-status');
    
    // 禁用按钮，显示加载状态
    btn.disabled = true;
    btn.classList.add('opacity-50', 'cursor-not-allowed');
    statusDiv.classList.remove('hidden');
    statusDiv.textContent = '⏳ 正在生成 PDF 报告，请稍候...';
    statusDiv.className = 'mt-3 text-sm text-blue-600';
    
    try {
        // 调用后端 API 生成 PDF
        const res = await fetch(`/api/stock/${STOCK_CODE}/report`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!res.ok) {
            throw new Error(`HTTP error! status: ${res.status}`);
        }
        
        const data = await res.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        if (data.success && data.filepath) {
            // 下载文件
            const filename = data.filepath.split('/').pop();
            const downloadRes = await fetch(`/api/reports/${filename}`);
            
            if (!downloadRes.ok) {
                throw new Error('下载失败');
            }
            
            // 创建 blob 并触发下载
            const blob = await downloadRes.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = data.filename || `report_${STOCK_CODE}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            // 显示成功状态
            statusDiv.textContent = '✅ PDF 报告已生成并下载';
            statusDiv.className = 'mt-3 text-sm text-green-600';
        } else {
            throw new Error('API 返回数据格式错误');
        }
        
    } catch (err) {
        console.error('PDF 生成失败:', err);
        statusDiv.textContent = `❌ 生成失败: ${err.message}`;
        statusDiv.className = 'mt-3 text-sm text-red-600';
    } finally {
        // 恢复按钮状态
        btn.disabled = false;
        btn.classList.remove('opacity-50', 'cursor-not-allowed');
        
        // 5秒后隐藏状态提示
        setTimeout(() => {
            statusDiv.classList.add('hidden');
        }, 5000);
    }
}
