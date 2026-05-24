// ==========================================
// LILATOV / לילוש טובוש - Frontend
//
// Last modified by Claude: 2026-05-24 21:00 (Israel time)
// Changes in this version:
//   - 🐛 FIX: childLora is not defined ב-generate-story flow (פספסתי במהדורה הקודמת)
//   - 🔥 PRE-WARMING: שולח training_id ל-preview-options לחיפוש cache
//   - 🔥 forceRegenerate=true כשלוחצים "צור 3 חדשות" — מבטיח תמונות חדשות
//   - 🔥 שמירת training_id בתוך loraModel ב-localStorage
//   - 🔥 הודעה דינמית: "טוען את התמונות..." (cache) או "יוצר 3 תמונות..." (חדש)
//   - 🔬 Mobile fix v2: Blob hydration trick (file.slice + arrayBuffer)
//   - 🔬 Mobile fix: אזהרה במודאל ההדרכה — לא לבחור מ-Google Photos
//   - 🔬 Mobile fix: הודעת skip dialog משופרת עם פתרון ברור
//   - 🔬 Mobile fix: retry אוטומטי ב-compressImage (Google Photos lazy refs)
//   - 🔬 Mobile fix: דיאלוג Skip/Cancel אם תמונה נכשלת — לא מפיל את כל הטעינה
//   - 🔬 EXIF orientation fix — createImageBitmap עם imageOrientation='from-image'
//   - 🔬 Memory: דחיסה סדרתית במקום מקבילית, שחרור bitmap+canvas מיד
//   - 🔬 Preview: URL.createObjectURL במקום FileReader.readAsDataURL
//   - 💡 פיצ'ר G: מודאל הדרכת תמונות (מופיע פעם אחת)
//   - 🆕 בכניסה חוזרת עם מודל קיים, מציג 3 תמונות לבחירה
//   - 🆕 שמירת בחירה ב-localStorage כדי לשרוד רענון
// ==========================================

// ==========================================
// 🌐 Server Configuration
// ==========================================
const SERVER_CONFIG = {
    url: 'https://web-production-ec858.up.railway.app'
};

// ==========================================
// 🤖 AI Training Manager
// ==========================================
const AITrainingManager = {
    MODEL_KEY: 'lilush_ai_model',
    
    saveModel(modelData) {
        localStorage.setItem(this.MODEL_KEY, JSON.stringify(modelData));
        console.log('🤖 AI Model saved:', modelData.model_id);
    },
    
    loadModel() {
        const saved = localStorage.getItem(this.MODEL_KEY);
        return saved ? JSON.parse(saved) : null;
    },
    
    hasModel() {
        return !!this.loadModel();
    },
    
    deleteModel() {
        localStorage.removeItem(this.MODEL_KEY);
    }
};

// ==========================================
// 👤 Child Profile Manager
// ==========================================
const ChildProfileManager = {
    PROFILE_KEY: 'lilush_child_profile',
    
    saveProfile(profile) {
        localStorage.setItem(this.PROFILE_KEY, JSON.stringify(profile));
        console.log('👤 Profile saved:', profile.childName);
    },
    
    loadProfile() {
        const saved = localStorage.getItem(this.PROFILE_KEY);
        return saved ? JSON.parse(saved) : null;
    },
    
    hasProfile() {
        return !!this.loadProfile();
    },
    
    deleteProfile() {
        localStorage.removeItem(this.PROFILE_KEY);
        AITrainingManager.deleteModel();
    }
};

// ==========================================
// 💾 LocalStorage Manager  
// ==========================================
const StorageManager = {
    CURRENT_STORY_KEY: 'lilush_current_story',
    HISTORY_KEY: 'lilush_story_history',
    
    saveCurrentStory(story) {
        try {
            localStorage.setItem(this.CURRENT_STORY_KEY, JSON.stringify(story));
            this.updateLastSaved();
            console.log('💾 נשמר אוטומטית');
            return true;
        } catch (e) {
            console.error('❌ שגיאה בשמירה:', e);
            return false;
        }
    },
    
    loadCurrentStory() {
        try {
            const saved = localStorage.getItem(this.CURRENT_STORY_KEY);
            if (saved) {
                return JSON.parse(saved);
            }
        } catch (e) {
            console.error('❌ שגיאה בטעינה:', e);
        }
        return null;
    },
    
    saveToHistory(story) {
        try {
            let history = this.getHistory();
            const storyWithMeta = {
                ...story,
                id: Date.now(),
                savedAt: new Date().toISOString()
            };
            history.unshift(storyWithMeta);
            history = history.slice(0, 10);
            localStorage.setItem(this.HISTORY_KEY, JSON.stringify(history));
            console.log('📚 נשמר להיסטוריה');
            return true;
        } catch (e) {
            console.error('❌ שגיאה בשמירה להיסטוריה:', e);
            return false;
        }
    },
    
    getHistory() {
        try {
            const saved = localStorage.getItem(this.HISTORY_KEY);
            return saved ? JSON.parse(saved) : [];
        } catch (e) {
            console.error('❌ שגיאה בטעינת היסטוריה:', e);
            return [];
        }
    },
    
    updateLastSaved() {
        const indicator = document.getElementById('lastSavedIndicator');
        if (indicator) {
            const now = new Date().toLocaleTimeString('he-IL');
            indicator.textContent = `נשמר אוטומטית ב-${now}`;
        }
    }
};

// ==========================================
// 🎯 Main App State
// ==========================================
let currentStory = null;
const appState = {
    bookData: {
        childName: '',
        childAge: '',
        childGender: '',
        theme: '',
        style: '',
        customInput: ''
    }
};

// ==========================================
// 🎨 AI Profile Functions
// ==========================================

let uploadedPhotos = []; // Store uploaded photos globally
// 🎯 מסלול יחיד בזרימה החדשה: הילד תמיד מ-LoRA מאומן.
// המשתנה נשאר כדי שקוד ישן ימשיך לעבוד, אבל הערך קבוע.
let photoOption = 'real';

function selectPhotoOption(option) {
    // 🚫 לא בשימוש בזרימה החדשה - הזרימה כעת חד-מסלולית (LoRA בלבד).
    // הפונקציה נשארת רק כדי לא לשבור onclick ישנים ב-HTML שאולי נשארו.
    photoOption = 'real';
}

function previewPhotosInline() {
    // 🚫 לא בשימוש בזרימה החדשה - העלאת התמונות עברה ל-profileScreen.
    // הפונקציה נשארת רק כדי לא לשבור onchange ישן ב-HTML שאולי נשאר.
    return;
}

function showProfileCreation() {
    // 🤖 פישוט: בלי popups. אם יש מודל - לסיפור; אם לא - להעלאת תמונות.
    // (ה-init ב-DOMContentLoaded כבר עושה את זה, אבל הפונקציה הזו עוד נקראת
    // מכפתורי "התחל מחדש" וכו', אז כדאי שתעבוד גם בנפרד.)
    const existingModel = AITrainingManager.loadModel();
    if (existingModel) {
        console.log('Found existing model - going to story creation');
        startCreation();
    } else {
        console.log('No existing model - going to photo upload');
        // 💡 פיצ'ר G: דף הדרכה לתמונות איכותיות (מופיע פעם אחת)
        showPhotoTipsModal(() => showScreen('profileScreen'));
    }
}

/**
 * 💡 פיצ'ר G: מודאל הדרכה לבחירת תמונות אימון נקיות
 * מופיע פעם אחת לכל קוד גישה - נשמר ב-localStorage.
 */
function showPhotoTipsModal(onContinue, forceShow = false) {
    const accessCode = localStorage.getItem('lilatov_access_code') || 'default';
    const STORAGE_KEY = `lilatov_seen_photo_tips_${accessCode}_v1`;
    
    if (!forceShow && localStorage.getItem(STORAGE_KEY) === 'yes') {
        if (onContinue) onContinue();
        return;
    }
    
    const overlay = document.createElement('div');
    overlay.id = 'photoTipsOverlay';
    overlay.style.cssText = `
        position: fixed; inset: 0;
        background: rgba(0,0,0,0.7);
        display: flex; align-items: flex-start; justify-content: center;
        z-index: 10000;
        font-family: inherit;
        overflow-y: auto;
        padding: 2rem 1rem;
    `;
    
    overlay.innerHTML = `
        <div style="background: #fff; border-radius: 20px; padding: 2rem 1.5rem; max-width: 520px; width: 100%; text-align: right; box-shadow: 0 20px 60px rgba(0,0,0,0.4); margin: auto;">
            <div style="text-align: center; font-size: 3rem; margin-bottom: 0.5rem;">📸</div>
            <h2 style="margin: 0 0 0.5rem 0; color: #2A2118; font-size: 1.5rem; text-align: center;">
                תמונות אימון מעולות = ילד שמזהה את עצמו
            </h2>
            <p style="color: #5C4A35; margin-bottom: 1.5rem; font-size: 0.95rem; text-align: center; line-height: 1.5;">
                בחירת התמונות היא הכי חשובה לתוצאה.<br>
                ⏱️ 2 דקות של קריאה = ספר ש<u>באמת</u> נראה כמו הילד שלכם.
            </p>
            <div style="background: #E8F5E9; padding: 1rem 1.2rem; border-radius: 14px; margin-bottom: 1rem; border-right: 4px solid #4CAF50;">
                <div style="font-weight: 700; color: #2E7D32; margin-bottom: 0.6rem; font-size: 1rem;">✅ כן — תמונות שיעבדו מצוין:</div>
                <ul style="margin: 0; padding-right: 1.2rem; color: #2A2118; font-size: 0.92rem; line-height: 1.7;">
                    <li><b>פנים גדולות וברורות</b> — שתופסות לפחות חצי מהתמונה</li>
                    <li><b>5-10 תמונות מגוונות</b> — זוויות שונות, רקעים שונים, מצבי רוח שונים</li>
                    <li><b>תאורה טובה</b> — אור יום, ללא צללים חזקים על הפנים</li>
                    <li><b>פנים גלויות</b> — שיער מאחורי האוזניים אם אפשר</li>
                </ul>
            </div>
            <div style="background: #FFEBEE; padding: 1rem 1.2rem; border-radius: 14px; margin-bottom: 1.2rem; border-right: 4px solid #E53935;">
                <div style="font-weight: 700; color: #C62828; margin-bottom: 0.6rem; font-size: 1rem;">❌ לא — תמונות שיפגעו בתוצאה:</div>
                <ul style="margin: 0; padding-right: 1.2rem; color: #2A2118; font-size: 0.92rem; line-height: 1.7;">
                    <li><b>משקפי שמש, כובעים, מסכות</b> — כל מה שמכסה את הפנים</li>
                    <li><b>תמונות מטושטשות</b> או באיכות נמוכה</li>
                    <li><b>תמונות קבוצתיות</b> — רק הילד שלכם בפריים (אפשר לחתוך)</li>
                    <li><b>פנים קטנות מאוד</b> בתוך נוף — קרבו אם צריך</li>
                    <li><b>10 תמונות זהות</b> — גיוון חשוב יותר מכמות</li>
                </ul>
            </div>
            <div style="background: #FFF3E0; padding: 1rem 1.2rem; border-radius: 14px; margin-bottom: 1.2rem; border-right: 4px solid #FB8C00;">
                <div style="font-weight: 700; color: #E65100; margin-bottom: 0.6rem; font-size: 1rem;">📱 חשוב במיוחד למשתמשי אנדרואיד:</div>
                <p style="margin: 0; color: #2A2118; font-size: 0.92rem; line-height: 1.6;">
                    בחרו תמונות מ-<b>גלריה</b> או <b>Photos</b> במכשיר —
                    <u>לא מ-Google Photos</u> בענן.<br>
                    <span style="color: #5C4A35; font-size: 0.85rem;">
                        תמונות שעדיין בענן ולא הורדו למכשיר — לא יעלו.
                    </span>
                </p>
            </div>
            
            <div style="background: #FFF8E1; padding: 0.9rem 1.1rem; border-radius: 12px; margin-bottom: 1.5rem; font-size: 0.88rem; color: #5C4A35; line-height: 1.5;">
                💡 <b>טיפ:</b> תמונות סלפי עם הילד עובדות מצוין — הפנים גדולות, מבט לפנים, ותאורה טובה.
            </div>
            <button id="photoTipsContinue" style="
                background: #C95E48; color: white; border: none;
                padding: 1rem 2rem; border-radius: 100px; cursor: pointer;
                font-size: 1.05rem; font-weight: 700; font-family: inherit;
                width: 100%;
            ">
                הבנתי, ממשיכים להעלאת תמונות ←
            </button>
        </div>
    `;
    
    document.body.appendChild(overlay);
    document.getElementById('photoTipsContinue').onclick = () => {
        localStorage.setItem(STORAGE_KEY, 'yes');
        if (document.body.contains(overlay)) {
            document.body.removeChild(overlay);
        }
        if (onContinue) onContinue();
    };
}

function showPhotoTipsAgain() {
    showPhotoTipsModal(null, true);
}

function previewTrainingPhotos() {
    const input = document.getElementById('trainingPhotos');
    const grid = document.getElementById('photoPreviewGrid');
    const btn = document.getElementById('startTrainingBtn');
    
    grid.innerHTML = '';
    
    if (!input.files || input.files.length === 0) {
        btn.disabled = true;
        return;
    }
    
    if (input.files.length < 5) {
        alert('⚠️ נא להעלות לפחות 5 תמונות לתוצאות טובות');
        btn.disabled = true;
        return;
    }
    
    if (input.files.length > 10) {
        alert('⚠️ מקסימום 10 תמונות');
        input.value = '';
        btn.disabled = true;
        return;
    }
    
    // 🔬 23/5: שימוש ב-URL.createObjectURL במקום FileReader+readAsDataURL.
    // ההפרש דרמטי: object URL הוא פוינטר (אפס RAM נוסף), data URL הוא base64 בזיכרון
    // (תמונה 5MB הופכת ל-7MB string). עם 10 תמונות מובייל זה ההבדל בין יציב לקריסה.
    Array.from(input.files).forEach((file, i) => {
        const div = document.createElement('div');
        div.style.cssText = 'position: relative; aspect-ratio: 1; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);';
        
        const img = document.createElement('img');
        const objectUrl = URL.createObjectURL(file);
        img.src = objectUrl;
        img.style.cssText = 'width: 100%; height: 100%; object-fit: cover;';
        // שחרור ה-object URL אחרי שהתמונה נטענה (חיוני לזיכרון)
        img.onload = () => URL.revokeObjectURL(objectUrl);
        
        const badge = document.createElement('div');
        badge.textContent = i + 1;
        badge.style.cssText = 'position: absolute; top: 5px; right: 5px; background: #667eea; color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.8rem; font-weight: bold;';
        
        div.appendChild(img);
        div.appendChild(badge);
        grid.appendChild(div);
    });
    
    // 🆕 לא מפעיל ישירות את הכפתור - דורש גם שם
    validateProfileStep();
}

/**
 * בודק אם יש גם שם וגם 5+ תמונות, ומפעיל את כפתור "התחל אימון" בהתאם.
 * נקרא מ-oninput של שדה השם וגם מ-previewTrainingPhotos.
 */
function validateProfileStep() {
    const btn = document.getElementById('startTrainingBtn');
    const nameInput = document.getElementById('profileChildName');
    const photosInput = document.getElementById('trainingPhotos');
    const clearBtn = document.getElementById('clearPhotosBtn');
    
    if (!btn) return;
    
    const hasName = nameInput && nameInput.value.trim().length >= 2;
    const photoCount = photosInput && photosInput.files ? photosInput.files.length : 0;
    const hasEnoughPhotos = photoCount >= 5 && photoCount <= 10;
    
    btn.disabled = !(hasName && hasEnoughPhotos);
    
    // 🆕 כפתור "מחק תמונות" מופיע רק כשיש לפחות תמונה אחת שנבחרה
    if (clearBtn) {
        clearBtn.style.display = photoCount > 0 ? 'inline-block' : 'none';
    }
}

/**
 * 🆕 מנקה את התמונות שנבחרו ואת התצוגה המקדימה.
 * מאפשר להורה להתחיל מחדש בלי לרענן את הדף.
 */
function clearTrainingPhotos() {
    if (!confirm('למחוק את כל התמונות שהעלית?')) return;
    
    const input = document.getElementById('trainingPhotos');
    const preview = document.getElementById('photoPreviewGrid');
    
    if (input) input.value = '';
    if (preview) preview.innerHTML = '';
    
    validateProfileStep();
    console.log('🗑️ Training photos cleared');
}

/**
 * דוחס תמונה בצד הלקוח לרוחב מקסימלי + איכות JPEG.
 * חיוני לפני שליחה לשרת - תמונות מטלפון (4000px, 3-5MB) יוצרות
 * ZIP של 15+ MB שעובר את מגבלת 10MB של Cloudinary.
 * 
 * 🔬 23/5: 3 תיקונים לתמונות מהמובייל:
 *   1. EXIF orientation — בלי זה, תמונות מ-iPhone באות "שכובות" ב-canvas
 *      וה-LoRA מאמן על פנים מסובבות. createImageBitmap עם imageOrientation:'from-image'
 *      מטפל ב-EXIF אוטומטית (תמיכה נרחבת מ-2019+, fallback ל-Image API במידת הצורך).
 *   2. memory — שחרור bitmap מיד אחרי השימוש (.close()) כדי להוריד עומס.
 *   3. concurrency — הקריאה מתבצעת סדרתית בצד החיצוני (ראה startTraining).
 * 
 * @param {File} file - קובץ התמונה המקורי
 * @param {number} maxWidth - רוחב מקסימלי בפיקסלים (ברירת מחדל 1024)
 * @param {number} quality - איכות JPEG 0-1 (ברירת מחדל 0.85)
 * @returns {Promise<string>} - data URL של התמונה המכווצת
 */
async function compressImage(file, maxWidth = 1024, quality = 0.85) {
    // 🔬 23/5: retry אוטומטי לקבצים מ-Google Photos באנדרואיד.
    // הקובץ עלול להגיע כ-"lazy reference" שדורש fetch מהענן בניסיון הראשון.
    // ננסה עד 2 פעמים עם השהיה ביניהן.
    const MAX_ATTEMPTS = 2;
    let lastError = null;
    
    for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {
        try {
            return await _compressImageOnce(file, maxWidth, quality);
        } catch (e) {
            lastError = e;
            console.warn(`compressImage attempt ${attempt}/${MAX_ATTEMPTS} failed:`, e.message);
            if (attempt < MAX_ATTEMPTS) {
                // השהיה קצרה לפני retry — לפעמים Google Photos צריך זמן להעלות מהענן
                await new Promise(r => setTimeout(r, 300));
            }
        }
    }
    
    throw lastError || new Error('Failed to compress image after retries');
}

async function _compressImageOnce(file, maxWidth, quality) {
    // 🔬 23/5: עוקף בעיית Google Photos באנדרואיד.
    // ה-File שמגיע לפעמים הוא רק "lazy reference" שעדיין בענן ולא קובץ מקומי.
    // פתרון: שיכפול דרך file.slice() מאלץ את אנדרואיד לקרוא את הביטים בפועל.
    // אם השיכפול נכשל — תמונה באמת לא זמינה ואין מה לעשות.
    let sourceBlob = file;
    try {
        if (file.size > 0) {
            // קריאת הביטים בכפיה — אם זה fail כאן, אז אין דרך לקרוא בכלל
            const blob = file.slice(0, file.size);
            // arrayBuffer() דחיפה אקטיבית של הנתונים לזיכרון
            const buf = await blob.arrayBuffer();
            if (buf.byteLength > 0) {
                sourceBlob = new Blob([buf], { type: file.type || 'image/jpeg' });
            }
        }
    } catch (e) {
        console.warn('Blob hydration failed (Google Photos lazy ref?):', e.message);
        // ממשיכים עם ה-File המקורי — אולי ההמשך יצליח בכל זאת
    }
    
    // ניסיון ראשון: createImageBitmap עם תיקון EXIF אוטומטי (מודרני, מהיר, פחות RAM)
    let bitmap = null;
    let img = null;
    try {
        bitmap = await createImageBitmap(sourceBlob, { imageOrientation: 'from-image' });
    } catch (e) {
        // Fallback: Image() API (ישן, ללא תיקון EXIF, אבל עובד בכל דפדפן)
        console.warn('createImageBitmap failed, falling back to Image():', e.message);
        img = await new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onerror = () => reject(new Error('Failed to read file'));
            reader.onload = (ev) => {
                const i = new Image();
                i.onerror = () => reject(new Error('Failed to load image'));
                i.onload = () => resolve(i);
                i.src = ev.target.result;
            };
            reader.readAsDataURL(sourceBlob);
        });
    }
    
    const source = bitmap || img;
    let { width, height } = source;
    
    if (width > maxWidth) {
        height = Math.round(height * maxWidth / width);
        width = maxWidth;
    }
    
    const canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(source, 0, 0, width, height);
    
    // שחרור זיכרון מיד (חשוב במובייל)
    if (bitmap) bitmap.close();
    
    const dataUrl = canvas.toDataURL('image/jpeg', quality);
    
    // עזרה ל-GC לשחרר את ה-canvas
    canvas.width = 0;
    canvas.height = 0;
    
    return dataUrl;
}

async function startTraining() {
    const input = document.getElementById('trainingPhotos');
    const files = input.files;
    
    // 🆕 קריאת שם הילד שהוקלד ב-profileScreen
    const childNameInput = document.getElementById('profileChildName');
    const childName = childNameInput ? childNameInput.value.trim() : '';
    
    if (!childName || childName.length < 2) {
        alert('נא להזין את שם הילד');
        if (childNameInput) childNameInput.focus();
        return;
    }
    
    if (!files || files.length < 5) {
        alert('נא להעלות לפחות 5 תמונות');
        return;
    }
    
    showScreen('trainingScreen');
    
    try {
        document.getElementById('trainingStatus').textContent = 'מכווץ תמונות...';
        document.getElementById('trainingProgressBar').style.width = '5%';
        
        // 🗜️ דחיסת תמונות בצד הלקוח - תמונות מטלפון יוצרות ZIP > 10MB
        // (המגבלה של Cloudinary). דוחסים ל-1024px רוחב + JPEG quality 85
        // שזה איכות מצוינת ל-LoRA training, ומקטין כל תמונה פי 10.
        // 🔬 23/5: סדרתי במקום מקבילי — Promise.all על 10 תמונות 12MP גורם
        // ל-OOM ב-iPhone ישן. סדרתי = פי 10 פחות RAM, מחיר זמן זניח (~0.3s לתמונה).
        // 🔬 23/5: אם תמונה נכשלת אחרי retry — דיאלוג skip/cancel במקום להפיל הכל.
        const photos = [];
        const skippedIndexes = [];
        for (let i = 0; i < files.length; i++) {
            try {
                const compressed = await compressImage(files[i], 1024, 0.85);
                photos.push(compressed);
                // עדכון התקדמות (5% → 25% במהלך הדחיסה)
                const pct = 5 + Math.round((i + 1) / files.length * 20);
                document.getElementById('trainingProgressBar').style.width = pct + '%';
                document.getElementById('trainingStatus').textContent =
                    `מכווץ תמונות... (${i + 1}/${files.length})`;
            } catch (err) {
                console.error(`Failed to compress photo ${i + 1} (even after retry):`, err);
                
                // שואלים את ההורה אם לדלג או לבטל
                const fileName = files[i].name || `תמונה ${i + 1}`;
                const remaining = files.length - i - 1;
                const successSoFar = photos.length;
                
                // הסבר ידידותי לפי המקור הסביר ביותר
                const skipMsg =
                    `❌ לא הצלחתי לקרוא את התמונה: "${fileName}"\n\n` +
                    `💡 הסיבה השכיחה: זו תמונה מ-Google Photos שעדיין רק בענן ולא הורדה למכשיר.\n\n` +
                    `🛠️ פתרון: סגור את הדף, פתח את "Photos" / "גלריה" של המכשיר, ובחר תמונות משם.\n\n` +
                    `📊 מצב נוכחי: ${successSoFar} תמונות תקינות, ${remaining} עוד ממתינות.\n\n` +
                    `לחץ "אישור" כדי לדלג על התמונה הזו ולהמשיך,\n` +
                    `או "ביטול" כדי לעצור ולהתחיל מחדש עם תמונות אחרות.`;
                
                if (confirm(skipMsg)) {
                    skippedIndexes.push(i + 1);
                    continue;  // ממשיך לתמונה הבאה
                } else {
                    throw new Error(`בוטל ע"י המשתמש בתמונה ${i + 1}`);
                }
            }
        }
        
        // וידוא שיש לנו מספיק תמונות לאימון
        if (photos.length < 5) {
            throw new Error(
                `נשארו רק ${photos.length} תמונות תקינות (דרושות לפחות 5).\n` +
                `אנא נסה להעלות שוב, רצוי תמונות שמורות במכשיר ולא מ-Google Photos בענן.`
            );
        }
        
        if (skippedIndexes.length > 0) {
            console.log(`⚠️ Skipped ${skippedIndexes.length} photos (${skippedIndexes.join(', ')}), proceeding with ${photos.length}`);
        }
        
        // לוג גודל כולל לאבחון
        const totalKB = photos.reduce((sum, p) => sum + Math.ceil(p.length * 0.75 / 1024), 0);
        console.log(`🗜️ Compressed ${photos.length} photos, total ~${totalKB} KB`);
        
        document.getElementById('training-upload').classList.add('active');
        document.getElementById('trainingProgressBar').style.width = '30%';
        document.getElementById('trainingStatus').textContent = 'שולח לשרת...';
        
        // 🎯 משתמשים ב-endpoint התקין של LoRA (לא ב-train-model הישן והשבור).
        // שמות הפרמטרים: child_photos + child_name (לא photos!)
        const accessCode = localStorage.getItem('lilatov_access_code') || 'unknown';
        
        // 💾 שמירת השם של הילד ב-localStorage - יישמש בטופס הסיפור
        localStorage.setItem('lilatov_child_name', childName);
        console.log('💾 Child name saved:', childName);
        
        const response = await fetch(`${SERVER_CONFIG.url}/api/start-lora-training`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                child_photos: photos,
                child_name: childName  // 🆕 השם האמיתי, לא child_<code>
            })
        });
        
        const data = await response.json();
        
        if (!response.ok || !data.success) {
            throw new Error(data.error || 'Training failed');
        }
        
        // ✅ האימון התחיל - שמירת מצב ויציאה ממסך ההמתנה.
        // הזרימה החדשה: אנחנו *לא* ממתינים בלולאה. שומרים את ה-training_id,
        // ההורה יוצא, וכשהוא חוזר - בודקים סטטוס מול השרת.
        const trainingState = {
            training_id: data.training_id,
            trigger_word: data.trigger_word,  // חשוב! נצטרך אותו בעתיד ליצירת תמונות
            access_code: accessCode,
            photo_count: photos.length,
            started_at: new Date().toISOString()
        };
        localStorage.setItem('lilatov_training_pending', JSON.stringify(trainingState));
        console.log('💾 Training state saved:', trainingState);
        
        // 📺 הצגת מסך "צא וחזור עוד 25 דקות"
        showWaitingScreen(trainingState);
        
    } catch (error) {
        console.error('Training error:', error);
        alert('❌ שגיאה באימון: ' + error.message + '\n\nאפשר לנסות שוב.');
        showScreen('profileScreen');
    }
}

// ==========================================
// ⏳ Async Training - Waiting Screen
// ==========================================

/**
 * מציג מסך המתנה ידידותי אחרי שהאימון נשלח.
 * ההורה רואה הסבר ברור על 25 הדקות, יכול לעזוב, ולחזור.
 */
function showWaitingScreen(trainingState) {
    // יצירת מסך המתנה דינמי - לא דורש HTML מראש
    let waitScreen = document.getElementById('asyncWaitScreen');
    if (!waitScreen) {
        waitScreen = document.createElement('div');
        waitScreen.id = 'asyncWaitScreen';
        waitScreen.className = 'screen';
        document.body.appendChild(waitScreen);
    }
    
    const startedAt = new Date(trainingState.started_at);
    const expectedReady = new Date(startedAt.getTime() + 25 * 60 * 1000);
    const expectedTimeStr = expectedReady.toLocaleTimeString('he-IL', {
        hour: '2-digit', minute: '2-digit'
    });
    
    waitScreen.innerHTML = `
        <div style="max-width: 560px; margin: 2rem auto; padding: 2rem 1.5rem; text-align: center; font-family: 'Heebo', sans-serif;">
            <div style="font-size: 4rem; margin-bottom: 1rem;">⏳</div>
            <h1 style="font-family: 'Fredoka', sans-serif; color: #E0552F; font-size: 2rem; margin: 0 0 0.5rem;">
                הפרופיל בתהליך יצירה!
            </h1>
            <p style="color: #5C4A35; font-size: 1.1rem; line-height: 1.6; margin: 1rem 0;">
                אנחנו יוצרים את הדמות של הילד שלכם.<br>
                זה תהליך חד-פעמי שלוקח בערך <strong>25 דקות</strong>.
            </p>
            
            <div style="background: #FFF7E8; border: 2px solid #F2A91B; border-radius: 16px; padding: 1.3rem; margin: 1.5rem 0; text-align: right;">
                <div style="font-weight: 700; color: #2A2118; margin-bottom: 0.6rem;">📍 מה לעשות עכשיו:</div>
                <ol style="margin: 0; padding-right: 1.3rem; color: #5C4A35; line-height: 1.7;">
                    <li>אפשר לסגור את הדף ולחזור בעוד 25 דקות</li>
                    <li>כשתחזרו - היכנסו שוב עם אותו קוד גישה (<strong>${trainingState.access_code}</strong>)</li>
                    <li>אם הפרופיל מוכן - תוכלו ליצור את הספר! ✨</li>
                </ol>
            </div>
            
            <div style="color: #5C4A35; font-size: 0.95rem; margin: 1.5rem 0;">
                ⏰ הפרופיל צפוי להיות מוכן בסביבות <strong>${expectedTimeStr}</strong>
            </div>
            
            <button id="checkStatusBtn" style="background: linear-gradient(135deg, #E0552F, #F2A91B); color: white; border: none; padding: 0.9rem 2rem; font-size: 1.05rem; font-weight: 700; border-radius: 50px; cursor: pointer; font-family: 'Heebo', sans-serif; box-shadow: 0 6px 18px rgba(224, 85, 47, 0.3); margin-top: 0.5rem;">
                🔄 בדקו אם מוכן עכשיו
            </button>
            
            <div id="checkStatusResult" style="margin-top: 1rem; min-height: 1.5rem; color: #5C4A35;"></div>
        </div>
    `;
    
    showScreen('asyncWaitScreen');
    
    document.getElementById('checkStatusBtn').onclick = () => checkTrainingStatus(trainingState);
}

/**
 * בדיקת סטטוס אימון מול השרת.
 * נקראת אוטומטית בעת כניסה לאפליקציה אם יש אימון ממתין,
 * וגם בלחיצה ידנית של ההורה על "בדקו אם מוכן".
 */
async function checkTrainingStatus(trainingState) {
    const resultEl = document.getElementById('checkStatusResult');
    const btnEl = document.getElementById('checkStatusBtn');
    
    if (resultEl) resultEl.textContent = '⏳ בודק...';
    if (btnEl) btnEl.disabled = true;
    
    try {
        // 🎯 קוראים ל-lora-status (התקין) ולא ל-training-status (הישן)
        const response = await fetch(`${SERVER_CONFIG.url}/api/lora-status/${trainingState.training_id}`);
        const statusData = await response.json();
        
        console.log('🔍 Training status:', statusData);
        
        if (statusData.status === 'succeeded') {
            // ✅ האימון הסתיים בהצלחה - שמור LoRA מלא (כולל URL ו-version)
            // 🐛 תיקון באג: שומרים תחת שם הילד האמיתי שההורה הקליד,
            // לא תחת קוד הגישה. אחרת findLoraForChild(childName) לא ימצא
            // את ה-LoRA, וההורה לא יקבל את 3 התמונות לבחירה.
            const savedChildName = localStorage.getItem('lilatov_child_name') || trainingState.access_code;
            const loraModel = {
                child_name: savedChildName,  // ✅ "מיכה" - לא "100"
                access_code: trainingState.access_code,  // 🔑 קוד הגישה שיצר את המודל
                trigger_word: trainingState.trigger_word,
                lora_url: statusData.lora_url,
                version: statusData.version,
                training_id: trainingState.training_id,  // 🔥 דרוש ל-pre-warm cache
                created_at: new Date().toISOString(),
                photo_count: trainingState.photo_count
            };
            // saveLoraModel קיים בקוד הישן ושומר ב-localStorage תחת המפתח הנכון
            if (typeof saveLoraModel === 'function') {
                saveLoraModel(loraModel);
            } else {
                // fallback - שמירה ידנית
                AITrainingManager.saveModel({
                    model_id: statusData.version,
                    created_at: loraModel.created_at,
                    photo_count: trainingState.photo_count,
                    lora_url: statusData.lora_url,
                    trigger_word: trainingState.trigger_word
                });
            }
            localStorage.removeItem('lilatov_training_pending');
            console.log('🎉 LoRA Model saved:', loraModel);
            
            // 🆕 שלב חדש: הצגת 3 תמונות לבחירה מיד אחרי האימון, לפני טופס הסיפור.
            // היגיון: ההורה רוצה לראות שהילד יוצא דומה לפני שהוא משקיע במילוי טופס.
            if (resultEl) resultEl.innerHTML = '✅ <strong>הפרופיל מוכן! נכין לכם 3 גרסאות לבחירה...</strong>';
            await new Promise(r => setTimeout(r, 1200));
            
            // קריאה ל-showLoraPreview עם המודל החדש
            const previewApproved = await showLoraPreview(loraModel);
            
            if (previewApproved) {
                // ✅ ההורה אישר תמונה - ממשיכים לטופס הסיפור
                startCreation();
            } else {
                // ❌ ההורה ביטל / בחר לאמן מחדש - חוזרים ל-profileScreen
                // (אם הוא בחר "אמן מחדש", showLoraPreview כבר ניקה את ה-LoRA)
                showScreen('profileScreen');
            }
            
        } else if (statusData.status === 'failed') {
            // ❌ האימון נכשל
            localStorage.removeItem('lilatov_training_pending');
            if (resultEl) resultEl.innerHTML = '❌ האימון נכשל. אנא נסו שוב.';
            if (btnEl) btnEl.disabled = false;
            await new Promise(r => setTimeout(r, 2000));
            showScreen('profileScreen');
            
        } else {
            // 🕐 עדיין רץ - חישוב זמן שעבר וזמן משוער שנותר
            const elapsedMin = Math.floor(
                (Date.now() - new Date(trainingState.started_at).getTime()) / 60000
            );
            const remainingMin = Math.max(0, 25 - elapsedMin);
            
            if (resultEl) {
                resultEl.innerHTML = remainingMin > 0
                    ? `🕐 עדיין בעבודה. עברו ${elapsedMin} דק׳, עוד כ-${remainingMin} דק׳.`
                    : '🕐 עוד מעט מוכן... נסו לרענן בעוד דקה.';
            }
            if (btnEl) btnEl.disabled = false;
        }
        
    } catch (error) {
        console.error('Status check error:', error);
        if (resultEl) resultEl.innerHTML = '⚠️ לא הצלחנו לבדוק כרגע. נסו שוב בעוד רגע.';
        if (btnEl) btnEl.disabled = false;
    }
}

function skipTraining() {
    // 🚫 דילוג על אימון לא נתמך עוד.
    // הזרימה החדשה: חובה להעלות תמונות ולאמן מודל - אחרת הילד לא יופיע.
    // נשארה הפונקציה כדי לא לשבור כפתור ב-HTML, אבל היא רק מציגה הודעה.
    alert('כדי שהילד יופיע בספר, נדרש להעלות תמונות וליצור פרופיל. 📷');
    showScreen('profileScreen');
}

// ==========================================
// 🎯 Navigation & Screens
// ==========================================

function showScreen(screenId) {
    document.querySelectorAll('.screen').forEach(screen => {
        screen.classList.remove('active');
    });
    const targetScreen = document.getElementById(screenId);
    if (targetScreen) {
        targetScreen.classList.add('active');
    }
    
    // 🔝 גלילה אוטומטית לראש - בכמה דרכים כדי לתמוך בכל הדפדפנים.
    // היה לפני זה רק window.scrollTo({behavior: 'instant'}) - לא עבד בכל מקרה.
    // המעטפת ב-requestAnimationFrame מבטיחה שהמסך החדש כבר רנדר לפני הגלילה.
    requestAnimationFrame(() => {
        window.scrollTo(0, 0);
        document.documentElement.scrollTop = 0;
        document.body.scrollTop = 0;
        if (targetScreen) targetScreen.scrollTop = 0;
    });
}

function startCreation() {
    showScreen('creatorScreen');
    resetForm();
}

function resetForm() {
    // 🆕 שימוש בשם השמור מ-localStorage (הוקלד ב-profileScreen לפני האימון)
    const savedChildName = localStorage.getItem('lilatov_child_name') || '';
    
    appState.bookData = {
        childName: savedChildName,
        childAge: '',
        childGender: '',
        theme: '',
        style: '',
        customInput: ''
    };
    
    const nameInput = document.getElementById('childName');
    if (nameInput) nameInput.value = savedChildName;
    
    document.querySelectorAll('.age-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.gender-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.theme-card').forEach(card => card.classList.remove('selected'));
    document.querySelectorAll('.style-card').forEach(card => card.classList.remove('selected'));
    
    const customInput = document.getElementById('customInput');
    if (customInput) customInput.value = '';
    
    showFormStep(1);
    
    // 🆕 הפעלת validateStep1 כדי שהכפתור "המשך" יופעל אם יש כבר שם
    if (typeof validateStep1 === 'function') {
        validateStep1();
    }
}

function showFormStep(step) {
    document.querySelectorAll('.form-step').forEach(s => s.classList.remove('active'));
    const stepElement = document.getElementById(`step${step}`);
    if (stepElement) {
        stepElement.classList.add('active');
    }
    
    document.querySelectorAll('.progress-step').forEach(s => s.classList.remove('active'));
    for (let i = 1; i <= step; i++) {
        const indicator = document.getElementById(`step${i}-indicator`);
        if (indicator) {
            indicator.classList.add('active');
        }
    }
}

// ==========================================
// 📝 Form Functions
// ==========================================

function validateStep1() {
    const nameInput = document.getElementById('childName');
    const name = nameInput ? nameInput.value.trim() : '';
    const age = appState.bookData.childAge;
    const gender = appState.bookData.childGender;
    const photoOption = appState.bookData.photoOption;
    
    // Basic validation
    let isValid = name && age && gender;
    
    // If "real" option selected, require at least 1 photo
    if (photoOption === 'real' && uploadedPhotos.length === 0) {
        isValid = false;
    }
    
    const nextBtn = document.getElementById('step1-next');
    if (nextBtn) {
        nextBtn.disabled = !isValid;
        
        // Visual feedback
        if (isValid) {
            nextBtn.style.opacity = '1';
            nextBtn.style.cursor = 'pointer';
        } else {
            nextBtn.style.opacity = '0.5';
            nextBtn.style.cursor = 'not-allowed';
        }
    }
    
    if (name) appState.bookData.childName = name;
    
    console.log('📋 Validation:', {
        name: !!name,
        age: !!age,
        gender: !!gender,
        photoOption,
        photos: uploadedPhotos.length,
        isValid
    });
}

function selectAge(age) {
    document.querySelectorAll('.age-btn').forEach(btn => btn.classList.remove('active'));
    if (event && event.target) {
        event.target.classList.add('active');
    }
    appState.bookData.childAge = age;
    validateStep1();
}

function selectGender(gender) {
    document.querySelectorAll('.gender-btn').forEach(btn => btn.classList.remove('active'));
    if (event && event.target) {
        event.target.classList.add('active');
    }
    appState.bookData.childGender = gender;
    validateStep1();
}

function selectTheme(theme) {
    document.querySelectorAll('.theme-card').forEach(card => card.classList.remove('selected'));
    if (event && event.target) {
        const card = event.target.closest('.theme-card');
        if (card) card.classList.add('selected');
    }
    appState.bookData.theme = theme;
    const nextBtn = document.getElementById('step2-next');
    if (nextBtn) nextBtn.disabled = false;
}

function selectStyle(style) {
    document.querySelectorAll('.style-card').forEach(card => card.classList.remove('selected'));
    if (event && event.target) {
        const card = event.target.closest('.style-card');
        if (card) card.classList.add('selected');
    }
    appState.bookData.style = style;
    const nextBtn = document.getElementById('step3-next');
    if (nextBtn) nextBtn.disabled = false;
}

function nextStep() {
    const currentStepElement = document.querySelector('.form-step.active');
    if (!currentStepElement) return;
    
    const currentStep = currentStepElement.id.replace('step', '');
    const nextStepNum = parseInt(currentStep) + 1;
    
    if (nextStepNum === 4) {
        updateSummary();
    }
    
    showFormStep(nextStepNum);
}

function prevStep() {
    const currentStepElement = document.querySelector('.form-step.active');
    if (!currentStepElement) return;
    
    const currentStep = currentStepElement.id.replace('step', '');
    const prevStepNum = parseInt(currentStep) - 1;
    
    if (prevStepNum >= 1) {
        showFormStep(prevStepNum);
    }
}

function updateSummary() {
    const summary = document.getElementById('summaryContent');
    if (!summary) return;
    
    const themeNames = {
        'animals': 'חיות וטבע',
        'family': 'משפחה ואהבה',
        'space': 'חלל וכוכבים',
        'magic': 'קסם ופנטזיה'
    };
    
    const styleNames = {
        'funny': 'מצחיק ומשעשע',
        'educational': 'חינוכי ומלמד'
    };
    
    const aiModel = AITrainingManager.loadModel();
    const aiStatus = aiModel ? '✨ עם פרופיל AI (הילד בתמונות!)' : '🎨 איורים רגילים';
    
    summary.innerHTML = `
        <p><strong>שם:</strong> ${appState.bookData.childName}</p>
        <p><strong>גיל:</strong> ${appState.bookData.childAge}</p>
        <p><strong>מגדר:</strong> ${appState.bookData.childGender === 'boy' ? 'בן' : 'בת'}</p>
        <p><strong>נושא:</strong> ${themeNames[appState.bookData.theme] || appState.bookData.theme}</p>
        <p><strong>סגנון:</strong> ${styleNames[appState.bookData.style] || appState.bookData.style}</p>
        <p><strong>תמונות:</strong> ${aiStatus}</p>
    `;
}

// ==========================================
// 📚 Story Generation
// ==========================================

async function generateStory() {
    const customInputElement = document.getElementById('customInput');
    appState.bookData.customInput = customInputElement ? customInputElement.value.trim() : '';
    
    // הערה: בעבר היה כאן showLoraPreview - הוא הועבר מיד אחרי האימון.
    // ההורה כבר בחר את הילד שלו לפני שהוא הגיע לטופס הזה.
    
    showScreen('generatingScreen');
    
    const steps = ['progress-story', 'progress-images', 'progress-done'];
    let currentStep = 0;
    
    const progressInterval = setInterval(() => {
        if (currentStep < steps.length) {
            const stepElement = document.getElementById(steps[currentStep]);
            if (stepElement) {
                stepElement.classList.add('active');
            }
            currentStep++;
        }
    }, 2000);
    
    try {
        const aiModel = AITrainingManager.loadModel();
        
        // 🐛 FIX: הגדרת childLora — בלי זה הקריאות למטה זורקות "childLora is not defined".
        // findLoraForChild מחפש ב-lora_models[] לפי שם הילד.
        const childLora = findLoraForChild(appState.bookData.childName);
        
        console.log('📸 uploadedPhotos:', uploadedPhotos);
        console.log('📸 uploadedPhotos.length:', uploadedPhotos.length);
        
        const requestData = {
            ...appState.bookData,
            ai_model_id: null,  // Force null for now
            childPhoto: uploadedPhotos.length > 0 ? uploadedPhotos[0] : null,
            // 🎓 אם יש LoRA - שלח אותו לשרת!
            lora_url: childLora ? childLora.lora_url : null,
            trigger_word: childLora ? childLora.trigger_word : null,
            lora_version: childLora ? childLora.version : null,
            use_lora: !!childLora,
            // 🎲 ה-seed שההורה בחר בתצוגה המקדימה (עקביות לכל הספר)
            chosen_seed: appState.bookData.chosen_seed || null,
            // 💪 ה-lora_scale שההורה בחר (האיזון בין דמיון לאיור)
            chosen_lora_scale: appState.bookData.chosen_lora_scale || 1.0,
            // 🎨 הסגנון שההורה בחר (חמים-ריאליסטי/קלאסי/רך)
            chosen_style: appState.bookData.chosen_style || 'classic_illustration'
        };
        
        console.log('📤 Sending story request');
        if (appState.bookData.chosen_seed) {
            console.log(`🎲 Using chosen seed: ${appState.bookData.chosen_seed}`);
        }
        console.log('📸 With photo:', uploadedPhotos.length > 0 ? 'YES ✅' : 'NO ❌');
        console.log('🤖 With AI model:', aiModel ? 'YES ✅' : 'NO ❌');
        console.log('🎓 With LoRA:', childLora ? `YES ✅ (${childLora.trigger_word})` : 'NO ❌');
        if (childLora) {
            console.log('   Version:', childLora.version);
        }
        
        const response = await fetch(`${SERVER_CONFIG.url}/api/generate-story`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(requestData)
        });
        
        if (!response.ok) throw new Error('Failed to generate story');
        
        const data = await response.json();
        clearInterval(progressInterval);
        
        currentStory = data.story;
        currentStory.childName = appState.bookData.childName;
        currentStory.childPhotos = uploadedPhotos.length > 0 ? [...uploadedPhotos] : [];  // ← שמור תמונות!
        
        // Save profile with photos
        if (uploadedPhotos.length > 0) {
            ChildProfileManager.saveProfile({
                childName: appState.bookData.childName,
                childAge: appState.bookData.childAge,
                childGender: appState.bookData.childGender,
                photos: uploadedPhotos,
                createdAt: new Date().toISOString()
            });
        }
        
        StorageManager.saveCurrentStory(currentStory);
        displayStory(currentStory);
        showScreen('previewScreen');
        
    } catch (error) {
        clearInterval(progressInterval);
        alert('שגיאה ביצירת הסיפור: ' + error.message);
        showScreen('creatorScreen');
    }
}

async function trainModelFromPhotos() {
    return new Promise(async (resolve, reject) => {
        try {
            const response = await fetch(`${SERVER_CONFIG.url}/api/train-model`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    photos: uploadedPhotos,
                    child_name: appState.bookData.childName || 'child_' + Date.now()
                })
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Training failed');
            }
            
            // Quick training (mock)
            const trainingId = data.training_id;
            
            // Wait a bit for mock training
            await new Promise(res => setTimeout(res, 1000));
            
            const statusResponse = await fetch(`${SERVER_CONFIG.url}/api/training-status/${trainingId}`);
            const statusData = await statusResponse.json();
            
            if (statusData.status === 'succeeded') {
                const modelData = {
                    model_id: statusData.model_id,
                    created_at: new Date().toISOString(),
                    photo_count: uploadedPhotos.length,
                    child_name: appState.bookData.childName
                };
                
                AITrainingManager.saveModel(modelData);
                console.log('🤖 Quick training completed:', modelData);
                resolve();
            } else {
                reject(new Error('Training failed'));
            }
            
        } catch (error) {
            console.error('Training error:', error);
            reject(error);
        }
    });
}

function displayStory(story) {
    const container = document.getElementById('storyPages');
    if (!container) return;
    
    container.innerHTML = '';
    
    const titleElement = document.getElementById('previewTitle');
    if (titleElement) {
        titleElement.textContent = `🌈 הספר של ${story.childName} 🌈`;
    }
    
    if (!story.pages) return;
    
    story.pages.forEach((page, index) => {
        const pageDiv = document.createElement('div');
        pageDiv.className = 'story-page';
        pageDiv.id = `page-${index}`;
        
        let imageHTML = '';
        if (page.imageUrl) {
            imageHTML = `<img src="${page.imageUrl}" class="page-image" alt="איור עמוד ${index + 1}" style="width: 100%; max-width: 500px; border-radius: 15px; margin-bottom: 1rem;">`;
        } else {
            imageHTML = `
                <div class="page-image-placeholder" style="background: linear-gradient(135deg, #e0f7fa 0%, #b2ebf2 100%); border-radius: 15px; padding: 3rem; text-align: center; color: #666; margin-bottom: 1rem;">
                    <div style="font-size: 3rem; margin-bottom: 1rem;">🎨</div>
                    <div style="font-size: 0.9rem;">${page.illustration || '[מקום לאיור]'}</div>
                </div>
            `;
        }
        
        pageDiv.innerHTML = `
            <div class="page-number">עמוד ${index + 1}</div>
            
            ${imageHTML}
            
            <div class="page-text-container">
                <div class="page-text" id="text-${index}">${page.text}</div>
                <textarea class="page-text-edit" id="edit-${index}" style="display: none;">${page.text}</textarea>
            </div>
            
            <div class="page-actions">
                <button class="btn-small btn-edit" onclick="startEdit(${index})">
                    ✏️ ערוך טקסט
                </button>
                <button class="btn-small btn-suggest" onclick="suggestAlternatives(${index})">
                    💡 הצע חלופה
                </button>
                <button class="btn-small btn-regenerate-image" onclick="showImageEditPopup(${index})" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
                    🎨 שנה תמונה
                </button>
                <button class="btn-small btn-save" id="save-${index}" style="display: none;" onclick="saveEdit(${index})">
                    ✓ שמור
                </button>
                <button class="btn-small btn-cancel" id="cancel-${index}" style="display: none;" onclick="cancelEdit(${index})">
                    ✗ ביטול
                </button>
            </div>
            
            <div id="alternatives-${index}" class="alternatives-container" style="display: none;"></div>
        `;
        container.appendChild(pageDiv);
    });
}

// ==========================================
// ✏️ Editing Functions
// ==========================================

function startEdit(pageIndex) {
    const textDiv = document.getElementById(`text-${pageIndex}`);
    const textarea = document.getElementById(`edit-${pageIndex}`);
    const saveBtn = document.getElementById(`save-${pageIndex}`);
    const cancelBtn = document.getElementById(`cancel-${pageIndex}`);
    
    if (textDiv) textDiv.style.display = 'none';
    if (textarea) {
        textarea.style.display = 'block';
        textarea.focus();
    }
    if (saveBtn) saveBtn.style.display = 'inline-block';
    if (cancelBtn) cancelBtn.style.display = 'inline-block';
}

async function saveEdit(pageIndex) {
    const textDiv = document.getElementById(`text-${pageIndex}`);
    const textarea = document.getElementById(`edit-${pageIndex}`);
    
    if (textarea && currentStory && currentStory.pages[pageIndex]) {
        const newText = textarea.value.trim();
        const oldText = currentStory.pages[pageIndex].text;
        
        if (newText && newText !== oldText) {
            currentStory.pages[pageIndex].text = newText;
            if (textDiv) textDiv.textContent = newText;
            StorageManager.saveCurrentStory(currentStory);
            
            cancelEdit(pageIndex);
            
            // 🆕 שאל אם להחליף תמונה כשהטקסט השתנה
            await askToRegenerateImage(pageIndex, oldText, newText);
            return;
        }
    }
    
    cancelEdit(pageIndex);
}

function cancelEdit(pageIndex) {
    const textDiv = document.getElementById(`text-${pageIndex}`);
    const textarea = document.getElementById(`edit-${pageIndex}`);
    const saveBtn = document.getElementById(`save-${pageIndex}`);
    const cancelBtn = document.getElementById(`cancel-${pageIndex}`);
    
    if (currentStory && currentStory.pages[pageIndex] && textarea) {
        textarea.value = currentStory.pages[pageIndex].text;
    }
    if (textDiv) textDiv.style.display = 'block';
    if (textarea) textarea.style.display = 'none';
    if (saveBtn) saveBtn.style.display = 'none';
    if (cancelBtn) cancelBtn.style.display = 'none';
}

async function suggestAlternatives(pageIndex) {
    if (!currentStory || !currentStory.pages[pageIndex]) return;
    
    const container = document.getElementById(`alternatives-${pageIndex}`);
    if (!container) return;
    
    container.innerHTML = '<div style="padding: 1rem; text-align: center;">⏳ מחפש חלופות...</div>';
    container.style.display = 'block';
    
    try {
        const response = await fetch(`${SERVER_CONFIG.url}/api/suggest-alternative`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                currentText: currentStory.pages[pageIndex].text,
                childName: currentStory.childName
            })
        });
        
        const data = await response.json();
        
        if (data.alternatives && data.alternatives.length > 0) {
            container.innerHTML = '<h4 style="margin-bottom: 0.5rem;">💡 חלופות מוצעות:</h4>';
            
            data.alternatives.forEach((alt, i) => {
                const btn = document.createElement('button');
                btn.className = 'alternative-option';
                btn.textContent = `${i + 1}. ${alt}`;
                btn.onclick = () => useAlternative(pageIndex, alt);
                container.appendChild(btn);
            });
        } else {
            container.innerHTML = '<div>לא נמצאו חלופות</div>';
        }
    } catch (error) {
        container.innerHTML = '<div style="color: red;">שגיאה בחיפוש חלופות</div>';
    }
}

async function useAlternative(pageIndex, newText) {
    if (!currentStory || !currentStory.pages[pageIndex]) return;
    
    const oldText = currentStory.pages[pageIndex].text;
    currentStory.pages[pageIndex].text = newText;
    
    const textDiv = document.getElementById(`text-${pageIndex}`);
    const textarea = document.getElementById(`edit-${pageIndex}`);
    const altContainer = document.getElementById(`alternatives-${pageIndex}`);
    
    if (textDiv) textDiv.textContent = newText;
    if (textarea) textarea.value = newText;
    if (altContainer) altContainer.style.display = 'none';
    
    StorageManager.saveCurrentStory(currentStory);
    
    // 🆕 שאל אם להחליף תמונה כשהטקסט השתנה
    await askToRegenerateImage(pageIndex, oldText, newText);
}

// ==========================================
// 🆕 שאל אם להחליף תמונה אחרי שינוי טקסט
// ==========================================
async function askToRegenerateImage(pageIndex, oldText, newText) {
    /**
     * אחרי שטקסט עמוד השתנה, מציג חלון שואל אם ליצור תמונה חדשה.
     * אם ההורה מאשר - הקוד יוצר תמונה חדשה שתואמת לטקסט החדש.
     */
    if (!currentStory || !currentStory.pages[pageIndex]) return;
    
    // בודק אם השינוי מספיק משמעותי כדי להציע (יותר מ-5 תווים שונים)
    const significantChange = Math.abs(oldText.length - newText.length) > 5 || 
                               oldText.split(' ').slice(0, 5).join(' ') !== newText.split(' ').slice(0, 5).join(' ');
    
    if (!significantChange) {
        console.log('🔍 Text change too small, not asking for new image');
        return;
    }
    
    return new Promise((resolve) => {
        // יצירת overlay מודלי
        const overlay = document.createElement('div');
        overlay.id = 'imageRegenOverlay';
        overlay.style.cssText = `
            position: fixed; inset: 0;
            background: rgba(0,0,0,0.7);
            display: flex; align-items: center; justify-content: center;
            z-index: 10000;
            font-family: inherit;
        `;
        
        overlay.innerHTML = `
            <div style="background: #fff; border-radius: 20px; padding: 2rem; max-width: 480px; width: 90%; text-align: right; box-shadow: 0 20px 60px rgba(0,0,0,0.4);">
                <div style="text-align: center; font-size: 2.5rem; margin-bottom: 0.8rem;">🎨</div>
                
                <h2 style="margin: 0 0 0.5rem 0; color: #2A2118; font-size: 1.4rem; text-align: center;">
                    הטקסט השתנה
                </h2>
                <p style="color: #5C4A35; margin-bottom: 1.5rem; font-size: 0.95rem; text-align: center;">
                    האם ליצור גם תמונה חדשה שתתאים לטקסט?
                </p>
                
                <div style="background: #FBF4E4; padding: 1rem; border-radius: 12px; margin-bottom: 1rem;">
                    <div style="font-size: 0.8rem; color: #999; margin-bottom: 0.3rem;">📝 טקסט חדש:</div>
                    <div style="color: #2A2118; font-size: 0.95rem;">${newText.substring(0, 200)}${newText.length > 200 ? '...' : ''}</div>
                </div>
                
                <div style="display: flex; gap: 0.7rem; flex-direction: column;">
                    <button id="regenYes" style="
                        background: #C95E48; color: white; border: none;
                        padding: 0.9rem 2rem; border-radius: 100px; cursor: pointer;
                        font-size: 1rem; font-weight: 700; font-family: inherit;
                    ">
                        ✅ כן, צור תמונה חדשה
                    </button>
                    <button id="regenNo" style="
                        background: transparent; color: #5C4A35;
                        border: 2px solid rgba(0,0,0,0.1);
                        padding: 0.7rem 1.5rem; border-radius: 100px; cursor: pointer;
                        font-size: 0.95rem; font-weight: 600; font-family: inherit;
                    ">
                        ❌ לא, השאר את התמונה הנוכחית
                    </button>
                </div>
                
                <p style="color: #999; font-size: 0.8rem; text-align: center; margin-top: 1rem;">
                    ⏱️ יצירת תמונה לוקחת ~10 שניות
                </p>
            </div>
        `;
        
        document.body.appendChild(overlay);
        
        function cleanup() {
            if (document.body.contains(overlay)) {
                document.body.removeChild(overlay);
            }
        }
        
        document.getElementById('regenYes').onclick = async () => {
            cleanup();
            // קריאה ל-regenerate עם הטקסט החדש
            await regenerateImageForUpdatedText(pageIndex, newText);
            resolve(true);
        };
        
        document.getElementById('regenNo').onclick = () => {
            cleanup();
            resolve(false);
        };
    });
}

async function regenerateImageForUpdatedText(pageIndex, newText) {
    /**
     * יוצר תמונה חדשה בהתבסס על טקסט עודכן.
     * משתמש ב-LoRA אם קיים + outfit שנבחר.
     */
    const page = currentStory.pages[pageIndex];
    
    // קבלת LoRA אם קיים
    const childLora = findLoraForChild(currentStory.childName || appState.bookData.childName);
    
    // קבלת תמונת ילד (אם אין LoRA)
    const childPhoto = (currentStory.childPhotos && currentStory.childPhotos.length > 0) 
        ? currentStory.childPhotos[0] 
        : (uploadedPhotos.length > 0 ? uploadedPhotos[0] : null);
    
    console.log('🔄 Regenerating image for updated text:');
    console.log('  📝 New text:', newText.substring(0, 80));
    console.log('  🎓 With LoRA:', childLora ? `YES ✅ (${childLora.trigger_word})` : 'NO ❌');
    console.log('  🎽 Outfit:', currentStory.outfit || 'random');
    
    // 🎯 NEW: בנה Character descriptions מ-Character Bible אם יש
    const characterDescriptions = [];
    if (currentStory.character_bible && page.characters_in_scene) {
        page.characters_in_scene.forEach(name => {
            if (currentStory.character_bible[name]) {
                characterDescriptions.push(currentStory.character_bible[name]);
            }
        });
    }
    
    showLoadingOverlay('מייצר תמונה חדשה שתתאים לטקסט... ⏳');
    
    try {
        const response = await fetch(`${SERVER_CONFIG.url}/api/regenerate-image`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                // 🎯 חשוב! שולחים את הטקסט העברי החדש כ-page_text
                // השרת יתרגם אותו ויבנה פרומפט מתאים
                page_text: newText,  // הטקסט החדש בעברית
                user_prompt: '',     // אין הוראה מיוחדת - רק התאמה לטקסט
                child_photo: childPhoto,
                lora_url: childLora ? childLora.lora_url : null,
                trigger_word: childLora ? childLora.trigger_word : null,
                lora_version: childLora ? childLora.version : null,
                outfit: currentStory.outfit || null,
                character_descriptions: characterDescriptions,
                character_bible: currentStory.character_bible || {},  // 🆕
                chosen_style: currentStory.chosen_style || appState.bookData.chosen_style || 'classic_illustration',
                chosen_seed: currentStory.chosen_seed || appState.bookData.chosen_seed || null,
                chosen_lora_scale: currentStory.chosen_lora_scale || appState.bookData.chosen_lora_scale || 1.0,
                child_gender: appState.bookData.childGender === 'girl' ? 'girl' : 'boy'
            })
        });
        
        const data = await response.json();
        
        if (data.success && data.imageUrl) {
            // עדכון התמונה
            page.imageUrl = data.imageUrl;
            
            // עדכון התצוגה
            const imgElement = document.querySelector(`#page-${pageIndex} .page-image`);
            if (imgElement) {
                imgElement.src = data.imageUrl;
            }
            
            // שמירה
            StorageManager.saveCurrentStory(currentStory);
            hideLoadingOverlay();
            showSuccessMessage('✅ תמונה חדשה נוצרה ומותאמת לטקסט!');
        } else {
            throw new Error(data.error || 'Failed to regenerate image');
        }
        
    } catch (error) {
        console.error('Image regeneration error:', error);
        hideLoadingOverlay();
        alert('❌ לא הצלחתי ליצור תמונה חדשה. נסי שוב.');
    }
}

// ==========================================
// 📄 PDF & Actions
// ==========================================

async function downloadPDF() {
    if (!currentStory) {
        alert('אין ספר לשמירה');
        return;
    }
    
    const modal = document.getElementById('pdfModal');
    if (modal) modal.classList.add('active');
    
    try {
        const response = await fetch(`${SERVER_CONFIG.url}/api/generate-pdf`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(currentStory)
        });
        
        if (!response.ok) throw new Error('Failed to generate PDF');
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `lilush_tovush_${currentStory.childName || 'story'}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        if (modal) modal.classList.remove('active');
        
    } catch (error) {
        if (modal) modal.classList.remove('active');
        alert('שגיאה ביצירת PDF: ' + error.message);
    }
}

function saveToHistory() {
    if (currentStory) {
        StorageManager.saveToHistory(currentStory);
        alert('✅ הספר נשמר להיסטוריה!');
    }
}

function showHistory() {
    const history = StorageManager.getHistory();
    if (history.length === 0) {
        alert('אין ספרים שמורים עדיין');
        return;
    }
    
    alert(`יש ${history.length} ספרים בהיסטוריה!\n\n(תכונה זו תשופר בקרוב)`);
}

function startOver() {
    if (confirm('להתחיל ספר חדש?')) {
        showScreen('landingScreen');
    }
}

// ==========================================
// 🚀 Initialization
// ==========================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 App loaded');
    
    // 🔐 בדיקת קוד גישה - אם אין, חזרה לדף הנחיתה
    const accessCode = localStorage.getItem('lilatov_access_code');
    if (!accessCode) {
        console.log('⛔ No access code - redirecting to landing');
        window.location.href = '/';
        return;
    }
    console.log('✅ Access code:', accessCode);
    
    // 🤖 בדיקה אם יש כבר מודל AI מוכן - **רק אם הוא שייך לקוד הגישה הנוכחי**!
    // localStorage הוא פר-דפדפן, אז יכול להיות שמשתמש קודם עם קוד אחר
    // השאיר מודל שאומן על ילד אחר - לא ניגע בו.
    const allModels = (() => {
        try { return JSON.parse(localStorage.getItem('lora_models') || '[]'); }
        catch { return []; }
    })();
    const matchingModel = allModels.find(m => m.access_code === accessCode);
    
    if (matchingModel) {
        console.log('🤖 AI Model found for this access code:', matchingModel.child_name);
        // 🔬 23/5: גם בכניסה חוזרת — מציגים 3 תמונות לבחירה לפני מסך הסיפור.
        // היגיון: הבחירה היא חלק מחוויית "הילד שלי", לא רק בחירת סגנון חד-פעמית.
        
        // שמירה זמנית של שם הילד ב-bookData כדי ש-findLoraForChild יעבוד מאוחר יותר
        appState.bookData.childName = matchingModel.child_name;
        
        (async () => {
            const previewApproved = await showLoraPreview(matchingModel);
            if (previewApproved) {
                showScreen('creatorScreen');
                resetForm();
                // לוודא שהשם נשאר בטופס (resetForm עשוי לנקות אותו)
                const nameInput = document.getElementById('childName');
                if (nameInput && !nameInput.value) {
                    nameInput.value = matchingModel.child_name;
                }
            } else {
                // ההורה ביטל - חזרה למסך הראשי / העלאה
                showScreen('profileScreen');
            }
        })();
    } else {
        // אין מודל לקוד הזה - בודק אם יש אימון בתהליך
        const pendingRaw = localStorage.getItem('lilatov_training_pending');
        if (pendingRaw) {
            try {
                const pending = JSON.parse(pendingRaw);
                // ודא שהאימון שייך לאותו קוד גישה
                if (pending.access_code === accessCode) {
                    console.log('⏳ Pending training found:', pending.training_id);
                    showWaitingScreen(pending);
                    // בדיקה אוטומטית מיד בכניסה
                    setTimeout(() => checkTrainingStatus(pending), 500);
                    return;
                }
            } catch (e) {
                console.warn('Bad pending training data:', e);
                localStorage.removeItem('lilatov_training_pending');
            }
        }
        // אין כלום לקוד הזה - מתחיל מהעלאת תמונות
        console.log('📷 No model/training for code', accessCode, '- starting with photo upload');
        // 💡 פיצ'ר G: דף הדרכה לתמונות איכותיות (מופיע פעם אחת)
        showPhotoTipsModal(() => showScreen('profileScreen'));
    }
    
    // Setup event listeners
    const childNameInput = document.getElementById('childName');
    if (childNameInput) {
        childNameInput.addEventListener('input', validateStep1);
    }
    
});

// ==========================================
// 🎨 Image Editing Functions
// ==========================================

function showImageEditPopup(pageIndex) {
    const page = currentStory.pages[pageIndex];
    
    // Create modal HTML
    const modalHTML = `
        <div class="modal-overlay" id="imageEditModal" onclick="closeImageEditPopup(event)">
            <div class="modal-content" onclick="event.stopPropagation()" style="max-width: 500px; background: white; padding: 2rem; border-radius: 20px; box-shadow: 0 10px 40px rgba(0,0,0,0.2);">
                <h2 style="color: #667eea; margin-bottom: 1rem; font-size: 1.5rem;">🎨 שינוי תמונה</h2>
                
                <p style="color: #666; margin-bottom: 1rem; font-size: 0.9rem;">
                    תאר במילים מה תרצה לראות בתמונה:
                </p>
                
                <textarea id="imagePromptInput" 
                    placeholder="למשל: הילד במגרש משחקים עם כדור, שמש בשמיים, עצים ברקע..." 
                    style="width: 100%; min-height: 100px; padding: 0.75rem; border: 2px solid #e0e0e0; border-radius: 10px; font-family: inherit; font-size: 0.9rem; resize: vertical; direction: rtl;"
                ></textarea>
                
                <p style="color: #999; font-size: 0.8rem; margin-top: 0.5rem; margin-bottom: 1.5rem;">
                    💡 השאר ריק כדי ליצור תמונה חדשה באופן אוטומטי
                </p>
                
                <div style="display: flex; gap: 0.75rem; justify-content: flex-end;">
                    <button onclick="closeImageEditPopup()" 
                        style="padding: 0.75rem 1.5rem; background: #f5f5f5; border: none; border-radius: 10px; cursor: pointer; font-weight: 600;">
                        ביטול
                    </button>
                    <button onclick="regenerateImage(${pageIndex})" 
                        style="padding: 0.75rem 1.5rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 10px; cursor: pointer; font-weight: 600;">
                        🎨 צור תמונה חדשה
                    </button>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Focus on textarea
    setTimeout(() => {
        const input = document.getElementById('imagePromptInput');
        if (input) input.focus();
    }, 100);
}

function closeImageEditPopup(event) {
    const modal = document.getElementById('imageEditModal');
    if (modal) {
        modal.remove();
    }
}

async function regenerateImage(pageIndex) {
    const userPrompt = document.getElementById('imagePromptInput').value.trim();
    const page = currentStory.pages[pageIndex];
    
    // Get child photo from story or uploaded photos
    const childPhoto = (currentStory.childPhotos && currentStory.childPhotos.length > 0) 
        ? currentStory.childPhotos[0] 
        : (uploadedPhotos.length > 0 ? uploadedPhotos[0] : null);
    
    // 🎓 Check if there's a LoRA for this child
    const childLora = findLoraForChild(currentStory.childName || appState.bookData.childName);
    
    // 🎯 NEW: בנה Character descriptions מ-Character Bible אם יש
    const characterDescriptions = [];
    if (currentStory.character_bible && page.characters_in_scene) {
        page.characters_in_scene.forEach(name => {
            if (currentStory.character_bible[name]) {
                characterDescriptions.push(currentStory.character_bible[name]);
            }
        });
    }
    
    console.log('🎭 Regenerating image:');
    console.log('  📸 With photo:', childPhoto ? 'YES ✅' : 'NO ❌');
    console.log('  🎓 With LoRA:', childLora ? `YES ✅ (${childLora.trigger_word})` : 'NO ❌');
    console.log('  📖 Characters:', characterDescriptions.length);
    
    // Close modal
    closeImageEditPopup();
    
    // Show loading
    showLoadingOverlay(childLora ? 'מייצר תמונה חדשה עם המודל המאומן... ⏳' : 'מייצר תמונה חדשה... ⏳');
    
    try {
        const response = await fetch(`${SERVER_CONFIG.url}/api/regenerate-image`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                page_text: page.illustration,
                user_prompt: userPrompt,
                child_photo: childPhoto,
                // 🎓 LoRA parameters
                lora_url: childLora ? childLora.lora_url : null,
                trigger_word: childLora ? childLora.trigger_word : null,
                lora_version: childLora ? childLora.version : null,
                outfit: currentStory.outfit || null,
                character_descriptions: characterDescriptions,
                character_bible: currentStory.character_bible || {},  // 🆕
                chosen_style: currentStory.chosen_style || appState.bookData.chosen_style || 'classic_illustration',
                chosen_seed: currentStory.chosen_seed || appState.bookData.chosen_seed || null,
                chosen_lora_scale: currentStory.chosen_lora_scale || appState.bookData.chosen_lora_scale || 1.0,
                child_gender: appState.bookData.childGender === 'girl' ? 'girl' : 'boy'
            })
        });
        
        const data = await response.json();
        
        if (data.success && data.imageUrl) {
            // Update the image
            page.imageUrl = data.imageUrl;
            
            // Update the display
            const imgElement = document.querySelector(`#page-${pageIndex} .page-image`);
            if (imgElement) {
                imgElement.src = data.imageUrl;
            }
            
            // Save to storage
            StorageManager.saveCurrentStory(currentStory);
            
            showSuccessMessage('✅ תמונה חדשה נוצרה בהצלחה!');
        } else {
            throw new Error(data.error || 'Failed to regenerate image');
        }
        
    } catch (error) {
        console.error('Image regeneration error:', error);
        alert('שגיאה ביצירת תמונה חדשה: ' + error.message);
    } finally {
        hideLoadingOverlay();
    }
}

function showLoadingOverlay(message) {
    const overlayHTML = `
        <div id="loadingOverlay" style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); display: flex; align-items: center; justify-content: center; z-index: 10000;">
            <div style="background: white; padding: 2rem 3rem; border-radius: 20px; text-align: center;">
                <div style="font-size: 2rem; margin-bottom: 1rem;">🎨</div>
                <div style="font-size: 1.1rem; color: #333; font-weight: 600;">${message}</div>
                <div style="margin-top: 1rem; color: #666; font-size: 0.9rem;">זה ייקח כ-15 שניות...</div>
            </div>
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', overlayHTML);
}

function hideLoadingOverlay() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) overlay.remove();
}

function showSuccessMessage(message) {
    const msgHTML = `
        <div id="successMessage" style="position: fixed; top: 20px; left: 50%; transform: translateX(-50%); background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1rem 2rem; border-radius: 50px; z-index: 10001; box-shadow: 0 5px 20px rgba(0,0,0,0.2); font-weight: 600;">
            ${message}
        </div>
    `;
    document.body.insertAdjacentHTML('beforeend', msgHTML);
    
    setTimeout(() => {
        const msg = document.getElementById('successMessage');
        if (msg) {
            msg.style.transition = 'opacity 0.5s';
            msg.style.opacity = '0';
            setTimeout(() => msg.remove(), 500);
        }
    }, 3000);
}

// ==========================================
// App initialization complete
// ==========================================
console.log('✅ App initialized successfully');

// ==========================================
// 🧪 Test Face Swap Function
// ==========================================

async function testFaceSwap() {
    if (uploadedPhotos.length === 0) {
        alert('אנא העלה תמונה קודם');
        return;
    }
    
    const childName = document.getElementById('childName').value.trim() || 'הילד';
    
    // Show loading
    const preview = document.getElementById('photoPreviewInline');
    const loadingDiv = document.createElement('div');
    loadingDiv.id = 'testLoading';
    loadingDiv.style.cssText = 'grid-column: 1/-1; text-align: center; padding: 1.5rem; background: white; border-radius: 10px; margin-top: 0.5rem; box-shadow: 0 4px 12px rgba(0,0,0,0.1);';
    loadingDiv.innerHTML = `
        <div style="font-size: 2rem; margin-bottom: 0.5rem;">🎨</div>
        <div style="font-weight: bold; color: #667eea; margin-bottom: 0.5rem;">יוצר תמונת בדיקה...</div>
        <div style="font-size: 0.9rem; color: #666;">זה ייקח כ-15 שניות</div>
    `;
    preview.appendChild(loadingDiv);
    
    try {
        const response = await fetch(`${SERVER_CONFIG.url}/api/test-face-swap`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                child_photo: uploadedPhotos[0],
                child_name: childName
            })
        });
        
        const data = await response.json();
        
        if (data.success && data.imageUrl) {
            // Remove loading
            loadingDiv.remove();
            
            // Show result
            const resultDiv = document.createElement('div');
            resultDiv.style.cssText = 'grid-column: 1/-1; background: white; border-radius: 10px; padding: 1rem; margin-top: 0.5rem; box-shadow: 0 4px 12px rgba(0,0,0,0.1);';
            resultDiv.innerHTML = `
                <div style="font-weight: bold; color: #667eea; margin-bottom: 0.75rem; text-align: center;">✅ תמונת בדיקה:</div>
                <img src="${data.imageUrl}" style="width: 100%; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" />
                <div style="margin-top: 0.75rem; text-align: center; font-size: 0.9rem; color: #666;">
                    האם ${childName} מזוהה בתמונה? אם כן, אפשר להמשיך ליצור ספר!
                </div>
                <button onclick="this.parentElement.remove()" style="width: 100%; margin-top: 0.75rem; padding: 0.5rem; background: #f5f5f5; border: none; border-radius: 8px; cursor: pointer; font-weight: 600;">
                    סגור
                </button>
            `;
            preview.appendChild(resultDiv);
            
        } else {
            throw new Error(data.error || 'Failed to test face swap');
        }
        
    } catch (error) {
        console.error('Test error:', error);
        loadingDiv.remove();
        alert('שגיאה בבדיקה: ' + error.message);
    }
}

// ==========================================
// 🎓 LoRA Training Function
// ==========================================

async function startLoraTraining() {
    if (uploadedPhotos.length < 5) {
        alert('צריך לפחות 5 תמונות לאימון LoRA.\n\nהעלה עוד ' + (5 - uploadedPhotos.length) + ' תמונות.');
        return;
    }
    
    const childName = document.getElementById('childName').value.trim();
    if (!childName) {
        alert('אנא הזן שם ילד קודם');
        return;
    }
    
    const confirmed = confirm(
        `🎓 אימון LoRA מאומן\n\n` +
        `ילד: ${childName}\n` +
        `תמונות: ${uploadedPhotos.length}\n` +
        `זמן: 10 דקות\n` +
        `עלות: ₪2 (חד-פעמי)\n\n` +
        `אחרי האימון תוכל ליצור ספרים אין-סופיים עם ${childName}!\n\n` +
        `להתחיל אימון?`
    );
    
    if (!confirmed) return;
    
    // Show loading
    const preview = document.getElementById('photoPreviewInline');
    const loadingDiv = document.createElement('div');
    loadingDiv.id = 'loraLoading';
    loadingDiv.style.cssText = 'grid-column: 1/-1; text-align: center; padding: 1.5rem; background: white; border-radius: 10px; margin-top: 0.5rem; box-shadow: 0 4px 12px rgba(0,0,0,0.1);';
    loadingDiv.innerHTML = `
        <div style="font-size: 2rem; margin-bottom: 0.5rem;">🎓</div>
        <div style="font-weight: bold; color: #667eea; margin-bottom: 0.5rem;">מאמן LoRA ל-${childName}...</div>
        <div style="font-size: 0.9rem; color: #666; margin-bottom: 1rem;">זה ייקח כ-10 דקות</div>
        <div style="background: #f0f0f0; border-radius: 8px; height: 8px; overflow: hidden;">
            <div id="loraProgress" style="background: linear-gradient(90deg, #667eea, #764ba2); height: 100%; width: 0%; transition: width 0.3s;"></div>
        </div>
        <div id="loraStatus" style="margin-top: 0.5rem; font-size: 0.85rem; color: #999;">מתחיל...</div>
    `;
    preview.appendChild(loadingDiv);
    
    try {
        // Start training
        const response = await fetch(`${SERVER_CONFIG.url}/api/start-lora-training`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                child_name: childName,
                child_photos: uploadedPhotos
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Poll for status
            pollLoraStatus(data.training_id, childName, data.trigger_word);
        } else {
            throw new Error(data.error);
        }
        
    } catch (error) {
        console.error('Training error:', error);
        loadingDiv.remove();
        alert('שגיאה באימון: ' + error.message);
    }
}

async function pollLoraStatus(trainingId, childName, triggerWord) {
    const startTime = Date.now();
    const statusEl = document.getElementById('loraStatus');
    const progressEl = document.getElementById('loraProgress');
    
    const interval = setInterval(async () => {
        try {
            const response = await fetch(`${SERVER_CONFIG.url}/api/lora-status/${trainingId}`);
            const data = await response.json();
            
            const elapsed = Math.floor((Date.now() - startTime) / 1000);
            const progress = Math.min(95, (elapsed / 600) * 100);
            
            progressEl.style.width = progress + '%';
            statusEl.textContent = `${Math.floor(progress)}% • ${Math.floor(elapsed / 60)} דקות`;
            
            if (data.status === 'succeeded') {
                clearInterval(interval);
                
                progressEl.style.width = '100%';
                statusEl.textContent = '100% • אימון הושלם!';
                
                // Save LoRA
                saveLoraModel({
                    child_name: childName,
                    trigger_word: triggerWord,
                    lora_url: data.lora_url,
                    version: data.version,
                    created_at: new Date().toISOString()
                });
                
                setTimeout(() => {
                    document.getElementById('loraLoading').remove();
                    alert(`✅ אימון LoRA הושלם!\n\nעכשיו ${childName} מוכן ליצירת ספרים מושלמים!`);
                }, 2000);
                
            } else if (data.status === 'failed') {
                clearInterval(interval);
                statusEl.textContent = '❌ אימון נכשל';
                throw new Error(data.error);
            }
            
        } catch (error) {
            clearInterval(interval);
            console.error('Status check error:', error);
            document.getElementById('loraLoading').remove();
            alert('שגיאה בבדיקת סטטוס: ' + error.message);
        }
    }, 5000); // Check every 5 seconds
}

// ==========================================
// 🎓 LoRA Manager - שמירה וטעינה של LoRA models
// ==========================================
function saveLoraModel(model) {
    // שמור ברשימה של כל המודלים (לפי ילד)
    const models = JSON.parse(localStorage.getItem('lora_models') || '[]');
    
    // אם יש כבר מודל לאותו ילד - החלף אותו (לא יוצר כפילויות)
    const existingIdx = models.findIndex(m => m.child_name === model.child_name);
    if (existingIdx >= 0) {
        models[existingIdx] = model;
        console.log('🔄 Updated existing LoRA for:', model.child_name);
    } else {
        models.push(model);
        console.log('💾 New LoRA saved for:', model.child_name);
    }
    
    localStorage.setItem('lora_models', JSON.stringify(models));
    
    // שמור גם ב-AITrainingManager לתאימות עם הקוד הקיים
    AITrainingManager.saveModel({
        model_id: model.lora_url,           // ה-URL של ה-LoRA
        trigger_word: model.trigger_word,    // ה-trigger word
        lora_url: model.lora_url,            // copy
        child_name: model.child_name,
        is_lora: true,                        // דגל שזה LoRA אמיתי
        created_at: model.created_at
    });
    
    console.log('✅ LoRA model fully saved:', model);
}

function findLoraForChild(childName) {
    /**
     * מחפש LoRA מאומן עבור ילד לפי שם.
     * סינון נוסף: רק מודלים ששייכים לקוד הגישה הנוכחי.
     * (אחרת משתמש בקוד 300 יקבל את המודל של דולב שאומן עם קוד 100.)
     * מחזיר null אם אין.
     */
    if (!childName) return null;
    const currentCode = localStorage.getItem('lilatov_access_code');
    const models = JSON.parse(localStorage.getItem('lora_models') || '[]');
    const found = models.find(m =>
        m.child_name === childName &&
        // אם למודל יש access_code - חייב להתאים. אם אין (מודל ישן) - מתעלמים.
        (!m.access_code || m.access_code === currentCode)
    );
    if (found) {
        console.log(`🎯 Found LoRA for ${childName}:`, found.trigger_word);
    }
    return found || null;
}

function getAllLoraModels() {
    /** מחזיר רשימת כל המודלים המאומנים */
    return JSON.parse(localStorage.getItem('lora_models') || '[]');
}

function deleteLoraModel(childName) {
    /** מוחק מודל LoRA של ילד מסוים */
    const models = JSON.parse(localStorage.getItem('lora_models') || '[]');
    const filtered = models.filter(m => m.child_name !== childName);
    localStorage.setItem('lora_models', JSON.stringify(filtered));
    console.log(`🗑️ Deleted LoRA for: ${childName}`);
}

// ==========================================
// 🔍 LoRA Preview - Sanity Check Before Book Generation
// ==========================================
async function showLoraPreview(childLora) {
    /**
     * מציג 3 תמונות תצוגה מקדימה. ההורה בוחר אחת.
     * ה-seed של התמונה הנבחרת נשמר ל-appState.bookData.chosen_seed.
     * מחזיר Promise<boolean>: true = בחר, false = ביטול
     */
    return new Promise(async (resolve) => {
        const overlay = document.createElement('div');
        overlay.id = 'loraPreviewOverlay';
        overlay.style.cssText = `
            position: fixed; inset: 0;
            background: rgba(0,0,0,0.85);
            display: flex; align-items: center; justify-content: center;
            z-index: 10000; font-family: inherit;
            padding: 1rem; overflow-y: auto;
        `;
        
        overlay.innerHTML = `
            <div style="background: #fff; border-radius: 20px; padding: 2rem; max-width: 720px; width: 100%; text-align: center; box-shadow: 0 20px 60px rgba(0,0,0,0.4);">
                <h2 style="margin: 0 0 0.5rem 0; color: #2A2118; font-size: 1.5rem;">
                    🎨 בחרו את ${childLora.child_name}
                </h2>
                <p style="color: #5C4A35; margin-bottom: 1.5rem; font-size: 0.95rem;">
                    יצרנו 3 גרסאות. בחרו את זו שהכי דומה לילד/ה — היא תלווה את כל הספר.
                </p>
                
                <div id="previewOptionsContainer" style="
                    display: grid; grid-template-columns: repeat(3, 1fr);
                    gap: 0.8rem; margin-bottom: 1.5rem; min-height: 220px;
                ">
                    <div style="grid-column: 1 / -1; display: flex; align-items: center; justify-content: center; flex-direction: column; padding: 2rem;">
                        <div style="font-size: 2.5rem; margin-bottom: 1rem;">🎨</div>
                        <div style="color: #5C4A35; font-weight: 600;">יוצר 3 תמונות...</div>
                        <div style="color: #999; font-size: 0.85rem; margin-top: 0.5rem;">עד 3 דקות</div>
                    </div>
                </div>
                
                <div id="previewActions" style="display: none; flex-direction: column; gap: 0.7rem;">
                    <button id="previewRetry" style="
                        background: transparent; color: #5C4A35;
                        border: 2px solid rgba(0,0,0,0.1);
                        padding: 0.7rem 1.5rem; border-radius: 100px; cursor: pointer;
                        font-size: 0.95rem; font-weight: 600; font-family: inherit;
                    ">
                        🔄 צור 3 תמונות חדשות
                    </button>
                    <button id="previewRetrain" style="
                        background: transparent; color: #C95E48;
                        border: 2px solid #E0552F;
                        padding: 0.7rem 1.5rem; border-radius: 100px; cursor: pointer;
                        font-size: 0.95rem; font-weight: 600; font-family: inherit;
                    ">
                        🔁 אמן מחדש עם תמונות אחרות
                    </button>
                    <button id="previewCancel" style="
                        background: transparent; color: #999;
                        border: none; cursor: pointer;
                        font-size: 0.9rem; font-family: inherit; padding: 0.5rem;
                    ">
                        ❌ ביטול
                    </button>
                </div>
                
                <div id="previewError" style="display: none; color: #C95E48; padding: 1rem;"></div>
            </div>
        `;
        
        document.body.appendChild(overlay);
        
        function cleanup(result) {
            if (document.body.contains(overlay)) {
                document.body.removeChild(overlay);
            }
            resolve(result);
        }
        
        async function generateOptions(forceRegenerate = false) {
            document.getElementById('previewActions').style.display = 'none';
            document.getElementById('previewError').style.display = 'none';
            
            // 🔥 אם יש training_id והמשתמש לא לחץ "צור חדשות" — סביר שיש cache מ-pre-warming
            const likelyFromCache = childLora.training_id && !forceRegenerate;
            const loadingMsg = likelyFromCache ? 'טוען את התמונות...' : 'יוצר 3 תמונות...';
            const loadingTime = likelyFromCache ? 'כמה שניות' : 'עד 3 דקות';
            
            document.getElementById('previewOptionsContainer').innerHTML = `
                <div style="grid-column: 1 / -1; display: flex; align-items: center; justify-content: center; flex-direction: column; padding: 2rem;">
                    <div style="font-size: 2.5rem; margin-bottom: 1rem;">🎨</div>
                    <div style="color: #5C4A35; font-weight: 600;">${loadingMsg}</div>
                    <div style="color: #999; font-size: 0.85rem; margin-top: 0.5rem;">${loadingTime}</div>
                </div>
            `;
            
            try {
                const response = await fetch(`${SERVER_CONFIG.url}/api/preview-options`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        child_name: childLora.child_name,
                        lora_url: childLora.lora_url,
                        trigger_word: childLora.trigger_word,
                        lora_version: childLora.version,
                        training_id: childLora.training_id || null,  // 🔥 ל-pre-warm cache lookup
                        force_regenerate: forceRegenerate || false,  // 🔥 true כשלוחצים "צור 3 חדשות"
                        theme: appState.bookData.theme || 'animals',
                        child_gender: appState.bookData.childGender === 'girl' ? 'girl' : 'boy'
                    })
                });
                
                const data = await response.json();
                
                if (data.success && data.options && data.options.length > 0) {
                    const container = document.getElementById('previewOptionsContainer');
                    container.innerHTML = '';
                    
                    data.options.forEach((option, idx) => {
                        const card = document.createElement('div');
                        card.style.cssText = `
                            cursor: pointer; border-radius: 12px; overflow: hidden;
                            border: 3px solid transparent; transition: all 0.2s;
                            background: #FBF4E4;
                        `;
                        // תווית מסבירה לפי סוג הווריאציה
                        const labelText = {
                            'warm_realistic': '📷 ריאליסטי',
                            'classic_illustration': '🎨 איור קלאסי',
                            'soft_illustration': '✏️ איור רך'
                        }[option.label] || `אפשרות ${idx + 1}`;
                        
                        card.innerHTML = `
                            <img src="${option.image}" 
                                 style="width: 100%; aspect-ratio: 4/3; object-fit: cover; display: block;"
                                 alt="${labelText}">
                            <div style="padding: 0.5rem; font-size: 0.85rem; color: #5C4A35; font-weight: 600;">
                                ${labelText}
                            </div>
                        `;
                        
                        card.addEventListener('mouseenter', () => {
                            card.style.borderColor = '#C95E48';
                            card.style.transform = 'scale(1.03)';
                        });
                        card.addEventListener('mouseleave', () => {
                            card.style.borderColor = 'transparent';
                            card.style.transform = 'scale(1)';
                        });
                        
                        card.addEventListener('click', () => {
                            // 🎲 שמירת seed + lora_scale + style הנבחרים!
                            appState.bookData.chosen_seed = option.seed;
                            appState.bookData.chosen_lora_scale = option.lora_scale;
                            appState.bookData.chosen_style = option.style;
                            console.log(`✅ Parent chose: style=${option.style}, seed=${option.seed}, scale=${option.lora_scale}`);
                            // 💾 שמירה ב-localStorage כדי לשרוד רענון
                            try {
                                localStorage.setItem('lilatov_chosen_preview', JSON.stringify({
                                    seed: option.seed,
                                    lora_scale: option.lora_scale,
                                    style: option.style,
                                    chosen_at: Date.now()
                                }));
                            } catch (e) { console.warn('Could not save preview choice:', e); }
                            cleanup(true);
                        });
                        
                        container.appendChild(card);
                    });
                    
                    document.getElementById('previewActions').style.display = 'flex';
                } else {
                    throw new Error(data.error || 'יצירת התצוגות נכשלה');
                }
            } catch (err) {
                console.error('Preview options error:', err);
                document.getElementById('previewOptionsContainer').innerHTML = '';
                document.getElementById('previewError').style.display = 'block';
                document.getElementById('previewError').innerHTML = `
                    <strong>⚠️ שגיאה ביצירת התצוגות</strong><br>
                    <small>${err.message}</small>
                `;
                document.getElementById('previewActions').style.display = 'flex';
            }
        }
        
        generateOptions();
        
        overlay.addEventListener('click', (e) => {
            if (e.target.id === 'previewCancel') {
                cleanup(false);
            } else if (e.target.id === 'previewRetry') {
                // 🔥 "צור 3 חדשות" — תמיד יוצר חדשים, לא משתמש ב-cache
                generateOptions(true);
            } else if (e.target.id === 'previewRetrain') {
                // 🔁 ההורה החליט שהתמונות לא טובות ורוצה לאמן מחדש.
                // מאשרים, מוחקים את ה-LoRA הקיים, וחוזרים ל-profileScreen.
                if (!confirm('האם למחוק את הפרופיל הקיים ולהעלות תמונות חדשות?\n\nתאלצו לחכות 25 דקות נוספות לאימון מחדש.')) {
                    return;
                }
                console.log('🔁 User chose to retrain - deleting current LoRA');
                if (typeof deleteLoraModel === 'function') {
                    deleteLoraModel(childLora.child_name);
                }
                // ניקוי שם הילד הקיים, כדי שב-profileScreen ההורה ימלא חדש
                localStorage.removeItem('lilatov_child_name');
                cleanup(false);
            }
        });
    });
}
