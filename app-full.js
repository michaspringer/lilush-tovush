        // ==========================================
        // 💾 LocalStorage Manager
        // ==========================================
        const StorageManager = {
            CURRENT_STORY_KEY: 'lilush_current_story',
            HISTORY_KEY: 'lilush_story_history',
            
            // שמירת הספר הנוכחי
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
            
            // טעינת הספר הנוכחי
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
            
            // שמירה להיסטוריה
            saveToHistory(story) {
                try {
                    let history = this.getHistory();
                    
                    // הוסף תאריך ו-ID
                    const storyWithMeta = {
                        ...story,
                        id: Date.now(),
                        savedAt: new Date().toISOString()
                    };
                    
                    // הוסף בתחילת המערך
                    history.unshift(storyWithMeta);
                    
                    // שמור רק 10 ספרים אחרונים
                    history = history.slice(0, 10);
                    
                    localStorage.setItem(this.HISTORY_KEY, JSON.stringify(history));
                    console.log('📚 נשמר להיסטוריה');
                    return true;
                } catch (e) {
                    console.error('❌ שגיאה בשמירה להיסטוריה:', e);
                    return false;
                }
            },
            
            // קבלת היסטוריה
            getHistory() {
                try {
                    const saved = localStorage.getItem(this.HISTORY_KEY);
                    return saved ? JSON.parse(saved) : [];
                } catch (e) {
                    return [];
                }
            },
            
            // טעינת ספר מההיסטוריה
            loadFromHistory(id) {
                const history = this.getHistory();
                return history.find(story => story.id === id);
            },
            
            // מחיקת הספר הנוכחי
            clearCurrent() {
                localStorage.removeItem(this.CURRENT_STORY_KEY);
                this.updateLastSaved();
                console.log('🗑️ נמחק');
            },
            
            // מחיקת כל ההיסטוריה
            clearHistory() {
                localStorage.removeItem(this.HISTORY_KEY);
                console.log('🗑️ היסטוריה נמחקה');
            },
            
            // עדכון תצוגת זמן שמירה אחרון
            updateLastSaved() {
                const indicator = document.getElementById('lastSavedIndicator');
                if (indicator) {
                    const saved = localStorage.getItem(this.CURRENT_STORY_KEY);
                    if (saved) {
                        const now = new Date().toLocaleTimeString('he-IL', { 
                            hour: '2-digit', 
                            minute: '2-digit' 
                        });
                        indicator.textContent = `נשמר אוטומטית ב-${now}`;
                        indicator.style.color = '#95E1D3';
                    } else {
                        indicator.textContent = 'לא נשמר';
                        indicator.style.color = '#999';
                    }
                }
            }
        };

        // Server configuration
        const SERVER_URL = 'https://web-production-ec858.up.railway.app';

        // Demo story data (in real app, this comes from API)
        const demoStory = {
            childName: 'נועה',
            pages: [
                {
                    text: 'נועה התעוררה בבוקר עם חיוך גדול. היום היא הולכת לגן החיות!',
                    illustration: 'ילדה בת 4 מחייכת במיטה, חדר צבעוני עם כרזות של חיות'
                },
                {
                    text: 'בגן החיות, נועה פגשה אריה גדול. "שלום!" אמרה היא באומץ.',
                    illustration: 'ילדה עומדת מול כלוב אריות, אריה מסתכל עליה בסקרנות'
                },
                {
                    text: 'האריה נדהם. "את לא מפחדת ממני?" שאל. נועה ענתה: "למה שאפחד?"',
                    illustration: 'האריה והילדה מדברים, האריה נראה מופתע אבל חביב'
                }
            ]
        };

        // State
        let currentStory = null;
        let editingPage = null;

        // Initialize
        window.addEventListener('load', () => {
            // נסה לטעון ספר שמור
            const savedStory = StorageManager.loadCurrentStory();
            
            if (savedStory) {
                currentStory = savedStory;
                console.log('📖 נטען ספר שמור');
                showRestoreNotification();
            } else {
                currentStory = demoStory;
                console.log('📚 נטען ספר דמו');
            }
            
            displayStory(currentStory);
            checkServerStatus();
            StorageManager.updateLastSaved();
        });

        // הצגת התראה על טעינת ספר שמור
        function showRestoreNotification() {
            const notification = document.createElement('div');
            notification.style.cssText = `
                position: fixed;
                top: 80px;
                left: 50%;
                transform: translateX(-50%);
                background: linear-gradient(135deg, #95E1D3 0%, #4ECDC4 100%);
                color: white;
                padding: 1rem 2rem;
                border-radius: 50px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.2);
                z-index: 2000;
                font-family: 'Fredoka', sans-serif;
                animation: slideDown 0.5s ease;
            `;
            notification.innerHTML = `
                📖 נטען ספר שמור של ${currentStory.childName}
                <button onclick="this.parentElement.remove()" style="
                    background: white;
                    border: none;
                    padding: 0.3rem 0.8rem;
                    margin-right: 1rem;
                    border-radius: 20px;
                    cursor: pointer;
                    font-weight: 600;
                ">✓</button>
            `;
            document.body.appendChild(notification);
            
            // הסר אחרי 5 שניות
            setTimeout(() => {
                if (notification.parentElement) {
                    notification.remove();
                }
            }, 5000);
        }

        // Display story
      function displayStory(story) {
    const container = document.getElementById('storyPages');
    container.innerHTML = '';
    
    document.getElementById('previewTitle').textContent = `🌈 הספר של ${story.childName} 🌈`;
    
    story.pages.forEach((page, index) => {
        const pageDiv = document.createElement('div');
        pageDiv.className = 'story-page';
        pageDiv.id = `page-${index}`;
        
        // יצירת HTML לתמונה
        let imageHTML = '';
        if (page.imageUrl) {
            // יש תמונה - הצג אותה!
            imageHTML = `<img src="${page.imageUrl}" class="page-image" alt="איור עמוד ${index + 1}" style="width: 100%; max-width: 500px; border-radius: 15px; margin-bottom: 1rem;">`;
        } else {
            // אין תמונה - הצג placeholder
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

        // Edit functions
        function startEdit(pageIndex) {
            // Hide all other edits
            cancelAllEdits();
            
            editingPage = pageIndex;
            document.getElementById(`text-${pageIndex}`).style.display = 'none';
            document.getElementById(`edit-${pageIndex}`).style.display = 'block';
            document.getElementById(`save-${pageIndex}`).style.display = 'inline-block';
            document.getElementById(`cancel-${pageIndex}`).style.display = 'inline-block';
            document.getElementById(`edit-${pageIndex}`).focus();
        }

        function saveEdit(pageIndex) {
            const newText = document.getElementById(`edit-${pageIndex}`).value.trim();
            if (newText) {
                currentStory.pages[pageIndex].text = newText;
                document.getElementById(`text-${pageIndex}`).textContent = newText;
                
                // 💾 שמירה אוטומטית!
                StorageManager.saveCurrentStory(currentStory);
            }
            cancelEdit(pageIndex);
        }

        function cancelEdit(pageIndex) {
            document.getElementById(`text-${pageIndex}`).style.display = 'block';
            document.getElementById(`edit-${pageIndex}`).style.display = 'none';
            document.getElementById(`save-${pageIndex}`).style.display = 'none';
            document.getElementById(`cancel-${pageIndex}`).style.display = 'none';
            document.getElementById(`edit-${pageIndex}`).value = currentStory.pages[pageIndex].text;
            editingPage = null;
        }

        function cancelAllEdits() {
            if (editingPage !== null) {
                cancelEdit(editingPage);
            }
        }

        // Suggest alternatives
        async function suggestAlternatives(pageIndex) {
            const altContainer = document.getElementById(`alternatives-${pageIndex}`);
            altContainer.style.display = 'block';
            altContainer.innerHTML = `
                <div class="loading-alternatives">
                    <div class="loading-spinner">✨</div>
                    <p>מייצר חלופות...</p>
                </div>
            `;

            try {
                const currentText = currentStory.pages[pageIndex].text;
                const alternatives = await fetchAlternatives(currentText, currentStory.childName);
                
                altContainer.innerHTML = `
                    <div class="alternatives-title">💡 בחר חלופה:</div>
                    ${alternatives.map((alt, i) => `
                        <div class="alternative-option" onclick="selectAlternative(${pageIndex}, ${i}, ${JSON.stringify(alt).replace(/"/g, '&quot;')})">
                            ${i + 1}. ${alt}
                        </div>
                    `).join('')}
                    <button class="btn-small btn-cancel" onclick="closeAlternatives(${pageIndex})" style="margin-top: 1rem;">
                        סגור
                    </button>
                `;
            } catch (error) {
                altContainer.innerHTML = `
                    <div style="color: red; text-align: center;">
                        ❌ שגיאה ביצירת חלופות: ${error.message}
                    </div>
                    <button class="btn-small btn-cancel" onclick="closeAlternatives(${pageIndex})" style="margin-top: 1rem;">
                        סגור
                    </button>
                `;
            }
        }

        async function fetchAlternatives(currentText, childName) {
            const response = await fetch(`${SERVER_URL}/api/suggest-alternative`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    currentText: currentText,
                    childName: childName
                })
            });

            if (!response.ok) {
                throw new Error('Failed to fetch alternatives');
            }

            const data = await response.json();
            return data.alternatives || [];
        }

        function selectAlternative(pageIndex, altIndex, altText) {
            currentStory.pages[pageIndex].text = altText;
            document.getElementById(`text-${pageIndex}`).textContent = altText;
            
            // 💾 שמירה אוטומטית!
            StorageManager.saveCurrentStory(currentStory);
            
            closeAlternatives(pageIndex);
        }

        function closeAlternatives(pageIndex) {
            document.getElementById(`alternatives-${pageIndex}`).style.display = 'none';
        }

        // PDF Generation
          async function downloadPDF() {
            if (!currentStory) {
                alert('אין ספר לשמירה');
                return;
            }
            
            const modal = document.getElementById('pdfModal');
            modal.classList.add('active');
            
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
                
                modal.classList.remove('active');
                
            } catch (error) {
                modal.classList.remove('active');
                alert('שגיאה ביצירת PDF: ' + error.message);
                console.error(error);
            }
        }

        // Other functions
        function approveBook() {
            // שמור להיסטוריה לפני אישור
            StorageManager.saveToHistory(currentStory);
            alert('🎉 מעולה! הספר נשמר בהיסטוריה.\nבשלב הבא נוסיף תשלום ושליחה להדפסה.');
        }

        // 💾 פונקציות ניהול אחסון
        function saveToHistory() {
            if (StorageManager.saveToHistory(currentStory)) {
                alert(`✅ הספר של ${currentStory.childName} נשמר להיסטוריה!`);
            } else {
                alert('❌ שגיאה בשמירה');
            }
        }

        function showHistory() {
            const history = StorageManager.getHistory();
            
            let modal = document.getElementById('historyModal');
            if (!modal) {
                modal = document.createElement('div');
                modal.id = 'historyModal';
                modal.className = 'history-modal';
                document.body.appendChild(modal);
            }
            
            if (history.length === 0) {
                modal.innerHTML = `
                    <div class="history-content">
                        <h2 class="history-title">📚 היסטוריית ספרים</h2>
                        <div class="history-empty">
                            <p style="font-size: 3rem; margin-bottom: 1rem;">📭</p>
                            <p style="font-size: 1.2rem;">אין ספרים שמורים בהיסטוריה</p>
                            <p style="margin-top: 1rem; color: #999;">שמרו ספרים כדי לראות אותם כאן</p>
                        </div>
                        <div class="history-actions">
                            <button class="btn btn-secondary" onclick="closeHistory()">סגור</button>
                        </div>
                    </div>
                `;
            } else {
                const historyHTML = history.map((story) => {
                    const date = new Date(story.savedAt).toLocaleString('he-IL', {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                    });
                    const pagesCount = story.pages ? story.pages.length : 0;
                    
                    return `
                        <li class="history-item" onclick="loadStoryFromHistory(${story.id})">
                            <div class="history-item-name">📖 ${story.childName}</div>
                            <div class="history-item-date">🕒 ${date}</div>
                            <div class="history-item-pages">📄 ${pagesCount} עמודים</div>
                        </li>
                    `;
                }).join('');
                
                modal.innerHTML = `
                    <div class="history-content">
                        <h2 class="history-title">📚 היסטוריית ספרים</h2>
                        <ul class="history-list">
                            ${historyHTML}
                        </ul>
                        <div class="history-actions">
                            <button class="btn btn-secondary" onclick="clearAllHistory()">
                                🗑️ מחק הכל
                            </button>
                            <button class="btn btn-primary" onclick="closeHistory()">
                                סגור
                            </button>
                        </div>
                    </div>
                `;
            }
            
            modal.classList.add('active');
            
            modal.onclick = function(e) {
                if (e.target === modal) {
                    closeHistory();
                }
            };
        }

        function closeHistory() {
            const modal = document.getElementById('historyModal');
            if (modal) {
                modal.classList.remove('active');
            }
        }

        function loadStoryFromHistory(storyId) {
            const story = StorageManager.loadFromHistory(storyId);
            
            if (!story) {
                alert('❌ לא ניתן לטעון את הספר');
                return;
            }
            
            currentStory = story;
            StorageManager.saveCurrentStory(currentStory);
            displayStory(currentStory);
            closeHistory();
            
            const notification = document.createElement('div');
            notification.style.cssText = `
                position: fixed;
                top: 80px;
                left: 50%;
                transform: translateX(-50%);
                background: linear-gradient(135deg, #95E1D3 0%, #4ECDC4 100%);
                color: white;
                padding: 1rem 2rem;
                border-radius: 50px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.2);
                z-index: 4000;
                font-family: 'Fredoka', sans-serif;
                font-size: 1.1rem;
            `;
            notification.textContent = `📖 נטען: ${story.childName}`;
            document.body.appendChild(notification);
            
            setTimeout(() => notification.remove(), 3000);
        }

        function clearCurrentStory() {
            if (confirm('🗑️ האם למחוק את הספר הנוכחי ולהתחיל מחדש?\n\n(הספר לא יימחק מההיסטוריה אם שמרת אותו)')) {
                StorageManager.clearCurrent();
                
                // טען את הדמו מחדש
                currentStory = demoStory;
                displayStory(currentStory);
                
                alert('✅ נוקה! התחל לערוך או צור ספר חדש.');
            }
        }

        function clearAllHistory() {
            if (confirm('⚠️ האם למחוק את כל ההיסטוריה?\n\nפעולה זו לא ניתנת לביטול!')) {
                StorageManager.clearHistory();
                alert('🗑️ כל ההיסטוריה נמחקה');
            }
        }

        async function checkServerStatus() {
            try {
                const response = await fetch(`${SERVER_URL}/`);
                if (response.ok) {
                    document.getElementById('statusText').textContent = 'שרת פעיל';
                    document.getElementById('statusIndicator').className = 'status-indicator status-ok';
                }
            } catch (error) {
                document.getElementById('statusText').textContent = 'שרת לא מחובר';
                document.getElementById('statusIndicator').className = 'status-indicator status-error';
            }
        }

        console.log('✅ לילוש טובוש - מוכן עם עריכה ו-PDF!');

// ========================================
// Navigation & Screen Management
// ========================================
function showScreen(screenId) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    document.getElementById(screenId).classList.add('active');
    window.scrollTo(0, 0);
}

function startCreation() {
    showScreen('creatorScreen');
}

function startOver() {
    if (confirm('האם להתחיל מחדש? השינויים הנוכחיים לא יישמרו.')) {
        appState.formStep = 1;
        showScreen('creatorScreen');
        updateFormStep();
    }
}

// ========================================
// Form Navigation
// ========================================
let appState = {
    formStep: 1,
    bookData: {
        childName: '',
        childAge: '',
        childGender: '',
        theme: '',
        style: '',
        customInput: ''
    }
};

function updateFormStep() {
    document.querySelectorAll('.form-step').forEach(s => s.classList.remove('active'));
    document.getElementById(`step${appState.formStep}`).classList.add('active');
    
    document.querySelectorAll('.progress-step').forEach((s, i) => {
        s.classList.toggle('active', i + 1 <= appState.formStep);
    });
    
    if (appState.formStep === 4) {
        updateSummary();
    }
}

function nextStep() {
    if (appState.formStep < 4) {
        appState.formStep++;
        updateFormStep();
    }
}

function prevStep() {
    if (appState.formStep > 1) {
        appState.formStep--;
        updateFormStep();
    }
}

// ========================================
// Form Selections
// ========================================
function selectAge(age) {
    appState.bookData.childAge = age;
    document.querySelectorAll('.age-btn').forEach(b => b.classList.remove('selected'));
    event.target.classList.add('selected');
    validateStep1();
}

function selectGender(gender) {
    appState.bookData.childGender = gender;
    document.querySelectorAll('.gender-btn').forEach(b => b.classList.remove('selected'));
    event.target.classList.add('selected');
    validateStep1();
}

function selectTheme(theme) {
    appState.bookData.theme = theme;
    document.querySelectorAll('.theme-card').forEach(c => c.classList.remove('selected'));
    event.target.closest('.theme-card').classList.add('selected');
    document.getElementById('step2-next').disabled = false;
}

function selectStyle(style) {
    appState.bookData.style = style;
    document.querySelectorAll('.style-card').forEach(c => c.classList.remove('selected'));
    event.target.closest('.style-card').classList.add('selected');
    document.getElementById('step3-next').disabled = false;
}

function validateStep1() {
    const childName = document.getElementById('childName').value.trim();
    appState.bookData.childName = childName;
    
    const isValid = childName && appState.bookData.childAge && appState.bookData.childGender;
    document.getElementById('step1-next').disabled = !isValid;
}

document.addEventListener('DOMContentLoaded', () => {
    const nameInput = document.getElementById('childName');
    if (nameInput) {
        nameInput.addEventListener('input', validateStep1);
    }
});

function updateSummary() {
    const data = appState.bookData;
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
    
    document.getElementById('summaryContent').innerHTML = `
        <p><strong>שם:</strong> ${data.childName}</p>
        <p><strong>גיל:</strong> ${data.childAge}</p>
        <p><strong>מגדר:</strong> ${data.childGender === 'boy' ? 'בן' : 'בת'}</p>
        <p><strong>נושא:</strong> ${themeNames[data.theme]}</p>
        <p><strong>סגנון:</strong> ${styleNames[data.style]}</p>
    `;
}
// Preview photo
function previewPhoto() {
    const input = document.getElementById('childPhoto');
    const preview = document.getElementById('photoPreview');
    const img = document.getElementById('previewImg');
    
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            img.src = e.target.result;
            preview.style.display = 'block';
        };
        reader.readAsDataURL(input.files[0]);
    }
}
// ========================================
// Story Generation
// ========================================
async function generateStory() {
    appState.bookData.customInput = document.getElementById('customInput').value.trim();
    
    // Get photo if exists
    const photoInput = document.getElementById('childPhoto');
    let photoBase64 = null;
    
    if (photoInput && photoInput.files && photoInput.files[0]) {
        photoBase64 = await new Promise((resolve) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.readAsDataURL(photoInput.files[0]);
        });
    }
    
    showScreen('generatingScreen');
    
    const steps = ['progress-story', 'progress-images', 'progress-done'];
    let currentStep = 0;
    
    const progressInterval = setInterval(() => {
        if (currentStep < steps.length) {
            document.getElementById(steps[currentStep]).classList.add('active');
            currentStep++;
        }
    }, 2000);
    
    try {
        const requestData = {
            ...appState.bookData,
            childPhoto: photoBase64  // ← הוסף את זה!
        };
        
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
        
        StorageManager.saveCurrentStory(currentStory);
        displayStory(currentStory);
        showScreen('previewScreen');
        
    } catch (error) {
        clearInterval(progressInterval);
        alert('שגיאה ביצירת הסיפור: ' + error.message);
        showScreen('creatorScreen');
    }
}


