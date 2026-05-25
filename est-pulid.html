<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🧪 PuLID POC — לילוש טובוש</title>
<style>
    /* Last modified by Claude: 2026-05-25 14:00 (Israel time) */
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
        font-family: 'Heebo', -apple-system, sans-serif;
        background: linear-gradient(135deg, #fef6e4 0%, #f9e2c4 100%);
        min-height: 100vh;
        padding: 2rem 1rem;
        color: #2A2118;
    }
    .container {
        max-width: 1100px;
        margin: 0 auto;
        background: white;
        border-radius: 24px;
        padding: 2rem;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
    }
    h1 {
        text-align: center;
        color: #C95E48;
        margin-bottom: 0.3rem;
    }
    .subtitle {
        text-align: center;
        color: #5C4A35;
        margin-bottom: 2rem;
        font-size: 0.95rem;
    }
    .section {
        background: #fef6e4;
        padding: 1.5rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
    }
    .section h2 {
        font-size: 1.1rem;
        margin-bottom: 1rem;
        color: #C95E48;
    }
    .upload-area {
        border: 3px dashed #D4A574;
        border-radius: 16px;
        padding: 2rem;
        text-align: center;
        cursor: pointer;
        transition: background 0.2s;
        background: white;
    }
    .upload-area:hover { background: #fffbf2; }
    .upload-area.has-image {
        padding: 1rem;
        border-style: solid;
        border-color: #4CAF50;
    }
    #refPreview {
        max-width: 200px;
        max-height: 200px;
        border-radius: 12px;
        margin: 0 auto;
        display: block;
    }
    .prompts-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 0.8rem;
        margin-top: 1rem;
    }
    .prompt-card {
        background: white;
        padding: 1rem;
        border-radius: 12px;
        border: 2px solid transparent;
        cursor: pointer;
        transition: all 0.2s;
        font-size: 0.9rem;
    }
    .prompt-card:hover { border-color: #D4A574; }
    .prompt-card.selected {
        border-color: #C95E48;
        background: #fff5f0;
    }
    .prompt-card .label {
        font-weight: 700;
        color: #C95E48;
        margin-bottom: 0.5rem;
    }
    .prompt-card .text {
        color: #5C4A35;
        font-size: 0.85rem;
        line-height: 1.4;
    }
    .controls {
        display: flex;
        gap: 1rem;
        align-items: center;
        flex-wrap: wrap;
        margin-top: 1rem;
    }
    .control-group {
        display: flex;
        flex-direction: column;
        gap: 0.3rem;
    }
    .control-group label {
        font-size: 0.85rem;
        color: #5C4A35;
        font-weight: 600;
    }
    .control-group select, .control-group input {
        padding: 0.5rem 0.8rem;
        border: 2px solid #D4A574;
        border-radius: 8px;
        background: white;
        font-family: inherit;
    }
    .btn {
        background: #C95E48;
        color: white;
        border: none;
        padding: 1rem 2rem;
        border-radius: 100px;
        cursor: pointer;
        font-size: 1.05rem;
        font-weight: 700;
        font-family: inherit;
        transition: all 0.2s;
        width: 100%;
        margin-top: 1rem;
    }
    .btn:hover:not(:disabled) {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(201, 94, 72, 0.3);
    }
    .btn:disabled {
        opacity: 0.5;
        cursor: not-allowed;
    }
    .results {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 1rem;
        margin-top: 1rem;
    }
    .result-card {
        background: white;
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .result-card img {
        width: 100%;
        display: block;
    }
    .result-card .info {
        padding: 0.8rem;
        font-size: 0.85rem;
        color: #5C4A35;
    }
    .loading {
        text-align: center;
        padding: 2rem;
        color: #5C4A35;
    }
    .loading .spinner {
        font-size: 2.5rem;
        animation: spin 1s linear infinite;
        display: inline-block;
    }
    @keyframes spin {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    .error {
        background: #ffebee;
        color: #c62828;
        padding: 1rem;
        border-radius: 12px;
        margin-top: 1rem;
        border-right: 4px solid #c62828;
    }
    .tip {
        background: #fff8e1;
        padding: 0.9rem 1.1rem;
        border-radius: 12px;
        margin: 1rem 0;
        font-size: 0.88rem;
        color: #5C4A35;
        line-height: 1.5;
        border-right: 4px solid #FB8C00;
    }
</style>
</head>
<body>
<div class="container">
    <h1>🧪 PuLID POC</h1>
    <p class="subtitle">בדיקה ידנית: האם PuLID-Flux שומר זהות באיורים טוב יותר מ-LoRA?</p>
    
    <div class="tip">
        💡 <b>זה POC, לא חלק מהאפליקציה.</b> מטרה: לבדוק אם PuLID יכול להחליף את ה-LoRA הקיים.
        אם זה עובד טוב — נטמיע. אם לא — נשאר עם LoRA ונשפר אחרת.
    </div>
    
    <!-- שלב 1: העלאת תמונה -->
    <div class="section">
        <h2>1️⃣ העלה תמונה ברורה של דולב</h2>
        <div class="upload-area" id="uploadArea" onclick="document.getElementById('refImage').click()">
            <div id="uploadPlaceholder">
                <div style="font-size: 3rem; margin-bottom: 0.5rem;">📸</div>
                <div style="font-weight: 600; color: #5C4A35;">לחץ להעלאת תמונה</div>
                <div style="font-size: 0.85rem; color: #999; margin-top: 0.3rem;">
                    הכי טוב: קלוז-אפ ברור של הפנים, תאורה טובה, ללא משקפיים/כובע
                </div>
            </div>
            <img id="refPreview" style="display: none;" alt="reference">
        </div>
        <input type="file" id="refImage" accept="image/*" style="display: none;">
    </div>
    
    <!-- שלב 2: פרומפט -->
    <div class="section">
        <h2>2️⃣ בחר פרומפט (סצנות מהספר הקודם)</h2>
        <div class="prompts-grid" id="promptsGrid">
            <!-- פרומפטים יוזרקו כאן -->
        </div>
        
        <div style="margin-top: 1rem;">
            <label style="font-size: 0.85rem; color: #5C4A35; font-weight: 600;">
                או הקלד פרומפט מותאם:
            </label>
            <textarea id="customPrompt" rows="2" style="
                width: 100%; margin-top: 0.3rem; padding: 0.8rem;
                border: 2px solid #D4A574; border-radius: 8px;
                font-family: inherit; resize: vertical;
            " placeholder="לדוגמה: a young boy riding an orange dragon in the clouds, children's book illustration"></textarea>
        </div>
    </div>
    
    <!-- שלב 3: פרמטרים -->
    <div class="section">
        <h2>3️⃣ פרמטרים (אופציונלי)</h2>
        <div class="controls">
            <div class="control-group">
                <label>start_step (0-4)</label>
                <select id="startStep">
                    <option value="0">0 — זהות חזקה (לסטיילים)</option>
                    <option value="1" selected>1 — זהות חזקה (default לאיורים)</option>
                    <option value="2">2 — איזון</option>
                    <option value="4">4 — ריאליסטי</option>
                </select>
            </div>
            <div class="control-group">
                <label>true_cfg</label>
                <select id="trueCfg">
                    <option value="1" selected>1 — fake CFG (default)</option>
                    <option value="1.5">1.5 — true CFG</option>
                    <option value="2">2 — true CFG חזק</option>
                </select>
            </div>
        </div>
        <div class="tip" style="margin-top: 1rem;">
            💡 <b>טיפ מ-Replicate:</b> לסגנונות איוריים — start_step=0-1.
            לריאליסטי — start_step=4. אם הזהות לא מספיק חזקה, נסה true_cfg גבוה יותר.
        </div>
    </div>
    
    <button class="btn" id="generateBtn" onclick="generate()" disabled>
        ✨ צור תמונה עם PuLID
    </button>
    
    <!-- תוצאות -->
    <div id="resultsContainer"></div>
</div>

<script>
const SERVER_URL = window.location.origin;

const PROMPTS = [
    {
        label: '🛏️ במיטה',
        text: "a young boy sitting in his bed, smiling with his arms up, colorful kid's bedroom with stars on wall, children's book illustration"
    },
    {
        label: '🐉 רוכב על דרקון',
        text: "a young boy riding on the back of a friendly orange dragon, flying through cloudy blue sky, children's book illustration"
    },
    {
        label: '⛵ ליד נמל',
        text: "a young boy standing at a colorful port with cranes and containers in the background, wearing a yellow t-shirt, children's book illustration"
    },
    {
        label: '🏔️ פסגת הר',
        text: "a young boy standing on top of a snowy mountain, looking at the view with amazement, snowy peaks in the background, children's book illustration"
    },
];

let referenceImageBase64 = null;
let selectedPrompt = null;
let allResults = []; // לשמירת היסטוריה

// אתחול grid הפרומפטים
function initPrompts() {
    const grid = document.getElementById('promptsGrid');
    PROMPTS.forEach((p, i) => {
        const card = document.createElement('div');
        card.className = 'prompt-card';
        card.innerHTML = `
            <div class="label">${p.label}</div>
            <div class="text">${p.text.substring(0, 80)}...</div>
        `;
        card.onclick = () => {
            document.querySelectorAll('.prompt-card').forEach(c => c.classList.remove('selected'));
            card.classList.add('selected');
            selectedPrompt = p.text;
            document.getElementById('customPrompt').value = '';
            updateBtn();
        };
        grid.appendChild(card);
    });
}

// העלאת תמונה
document.getElementById('refImage').addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    // קומפרסיה ל-1024px (חוסך bandwidth)
    const compressed = await compressImage(file, 1024, 0.9);
    referenceImageBase64 = compressed;
    
    document.getElementById('uploadArea').classList.add('has-image');
    document.getElementById('uploadPlaceholder').style.display = 'none';
    const preview = document.getElementById('refPreview');
    preview.src = compressed;
    preview.style.display = 'block';
    
    updateBtn();
});

document.getElementById('customPrompt').addEventListener('input', () => {
    if (document.getElementById('customPrompt').value.trim()) {
        document.querySelectorAll('.prompt-card').forEach(c => c.classList.remove('selected'));
        selectedPrompt = null;
    }
    updateBtn();
});

function updateBtn() {
    const btn = document.getElementById('generateBtn');
    const hasPrompt = selectedPrompt || document.getElementById('customPrompt').value.trim();
    btn.disabled = !(referenceImageBase64 && hasPrompt);
}

async function compressImage(file, maxWidth, quality) {
    const bitmap = await createImageBitmap(file, { imageOrientation: 'from-image' });
    let { width, height } = bitmap;
    if (width > maxWidth) {
        height = Math.round(height * maxWidth / width);
        width = maxWidth;
    }
    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    canvas.getContext('2d').drawImage(bitmap, 0, 0, width, height);
    bitmap.close();
    return canvas.toDataURL('image/jpeg', quality);
}

async function generate() {
    const promptText = selectedPrompt || document.getElementById('customPrompt').value.trim();
    if (!referenceImageBase64 || !promptText) return;
    
    const startStep = parseInt(document.getElementById('startStep').value);
    const trueCfg = parseFloat(document.getElementById('trueCfg').value);
    
    const btn = document.getElementById('generateBtn');
    btn.disabled = true;
    btn.textContent = 'יוצר... (~15-20 שניות)';
    
    const container = document.getElementById('resultsContainer');
    
    // הצגת loading
    const loadingId = 'loading-' + Date.now();
    container.insertAdjacentHTML('afterbegin', `
        <div id="${loadingId}" class="section">
            <div class="loading">
                <div class="spinner">🎨</div>
                <div style="margin-top: 0.8rem; font-weight: 600;">
                    מריץ PuLID-Flux...
                </div>
                <div style="font-size: 0.85rem; color: #999; margin-top: 0.3rem;">
                    start_step=${startStep}, true_cfg=${trueCfg}
                </div>
                <div style="font-size: 0.85rem; color: #999; margin-top: 0.3rem;">
                    "${promptText.substring(0, 60)}..."
                </div>
            </div>
        </div>
    `);
    
    try {
        const response = await fetch(`${SERVER_URL}/api/test-pulid`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                child_image: referenceImageBase64,
                prompt: promptText,
                start_step: startStep,
                true_cfg: trueCfg
            })
        });
        
        const data = await response.json();
        document.getElementById(loadingId).remove();
        
        if (!data.success) {
            container.insertAdjacentHTML('afterbegin', `
                <div class="error">
                    ❌ <b>שגיאה:</b> ${data.error || 'unknown error'}
                </div>
            `);
            return;
        }
        
        // הצגת תוצאה
        container.insertAdjacentHTML('afterbegin', `
            <div class="section">
                <h2>🎉 תוצאה</h2>
                <div class="results">
                    <div class="result-card">
                        <img src="${data.image_url}" alt="PuLID result" 
                             onclick="window.open('${data.image_url}', '_blank')"
                             style="cursor: pointer;">
                        <div class="info">
                            <div><b>זמן:</b> ${data.elapsed_seconds}s · 
                                 <b>עלות:</b> ~$${data.cost_estimate_usd}</div>
                            <div><b>start_step:</b> ${startStep} · 
                                 <b>true_cfg:</b> ${trueCfg}</div>
                            <div style="margin-top: 0.5rem; color: #888; font-size: 0.78rem;">
                                "${promptText.substring(0, 100)}..."
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `);
        
        allResults.unshift({
            url: data.image_url,
            params: data.params_used,
            elapsed: data.elapsed_seconds
        });
        
    } catch (err) {
        document.getElementById(loadingId)?.remove();
        container.insertAdjacentHTML('afterbegin', `
            <div class="error">
                ❌ <b>שגיאת רשת:</b> ${err.message}
            </div>
        `);
    } finally {
        btn.disabled = false;
        btn.textContent = '✨ צור תמונה עם PuLID';
        updateBtn();
    }
}

initPrompts();
</script>
</body>
</html>
