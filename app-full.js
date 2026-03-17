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
let photoOption = 'generic'; // 'generic' or 'real'

function selectPhotoOption(option) {
    photoOption = option;
    
    // Update button styles
    document.querySelectorAll('.photo-option-btn').forEach(btn => {
        btn.style.border = '3px solid #ddd';
        btn.style.background = 'white';
        btn.style.transform = 'scale(1)';
    });
    
    const selectedBtn = document.getElementById(option === 'generic' ? 'optionGeneric' : 'optionReal');
    selectedBtn.style.border = '3px solid #667eea';
    selectedBtn.style.background = 'linear-gradient(135deg, #f5f7ff 0%, #e8ecff 100%)';
    selectedBtn.style.transform = 'scale(1.02)';
    
    // Show/hide upload section
    const uploadSection = document.getElementById('photoUploadSection');
    const infoBox = document.getElementById('optionInfoBox');
    
    if (option === 'real') {
        uploadSection.style.display = 'block';
        infoBox.style.display = 'block';
        infoBox.innerHTML = `
            <div style="display: flex; align-items: start; gap: 1rem;">
                <div style="font-size: 2rem;">💡</div>
                <div>
                    <div style="font-weight: bold; color: #667eea; margin-bottom: 0.5rem;">איך זה עובד?</div>
                    <div style="font-size: 0.9rem; color: #666; line-height: 1.6;">
                        1. העלו 5-10 תמונות ברורות של הילד<br>
                        2. ה-AI ילמד את הפנים של הילד (10 דקות)<br>
                        3. הילד יופיע בכל תמונה בספר!<br>
                        <br>
                        <strong>💰 עלות:</strong> ₪349 לספר הראשון (כולל אימון AI)<br>
                        <strong>🎁 ספרים נוספים:</strong> רק ₪149 (בלי אימון מחדש!)
                    </div>
                </div>
            </div>
        `;
    } else {
        uploadSection.style.display = 'none';
        uploadedPhotos = [];
        document.getElementById('photoPreviewInline').innerHTML = '';
        infoBox.style.display = 'block';
        infoBox.innerHTML = `
            <div style="display: flex; align-items: start; gap: 1rem;">
                <div style="font-size: 2rem;">✨</div>
                <div>
                    <div style="font-weight: bold; color: #667eea; margin-bottom: 0.5rem;">ספר עם דמות יפה ועקבית</div>
                    <div style="font-size: 0.9rem; color: #666; line-height: 1.6;">
                        נשתמש ב-AI כדי ליצור דמות יפה ועקבית שתופיע בכל התמונות.<br>
                        הדמות לא תהיה הילד שלכם, אבל תהיה חמודה ועקבית!<br>
                        <br>
                        <strong>💰 עלות:</strong> ₪149 בלבד<br>
                        <strong>⚡ זמן:</strong> 2-3 דקות
                    </div>
                </div>
            </div>
        `;
    }
    
    console.log('📸 Photo option selected:', option);
}

function previewPhotosInline() {
    const input = document.getElementById('childPhotosInline');
    const preview = document.getElementById('photoPreviewInline');
    
    if (!preview) return;
    
    preview.innerHTML = '';
    uploadedPhotos = [];
    
    if (!input.files || input.files.length === 0) {
        return;
    }
    
    // For InstantID - 1 photo is enough!
    if (input.files.length > 10) {
        alert('⚠️ מקסימום 10 תמונות');
        input.value = '';
        return;
    }
    
    console.log(`📸 Processing ${input.files.length} photo(s)...`);
    
    // Convert to base64 and store
    const promises = Array.from(input.files).map(file => {
        return new Promise((resolve) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                uploadedPhotos.push(e.target.result);
                resolve(e.target.result);
            };
            reader.readAsDataURL(file);
        });
    });
    
    Promise.all(promises).then((results) => {
        // Clear and show preview container
        preview.innerHTML = '';
        preview.style.display = 'grid';
        
        results.forEach((src, i) => {
            const div = document.createElement('div');
            div.style.cssText = 'position: relative; aspect-ratio: 1; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.15); border: 3px solid #667eea;';
            
            const img = document.createElement('img');
            img.src = src;
            img.style.cssText = 'width: 100%; height: 100%; object-fit: cover;';
            
            const badge = document.createElement('div');
            badge.textContent = i + 1;
            badge.style.cssText = 'position: absolute; top: 8px; right: 8px; background: #667eea; color: white; width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.9rem; font-weight: bold; box-shadow: 0 2px 8px rgba(0,0,0,0.3);';
            
            div.appendChild(img);
            div.appendChild(badge);
            preview.appendChild(div);
        });
        
        // Add success message
        const successMsg = document.createElement('div');
        successMsg.style.cssText = 'grid-column: 1/-1; text-align: center; padding: 1rem; color: white; font-weight: bold; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; margin-top: 0.5rem; box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);';
        successMsg.innerHTML = `✅ ${uploadedPhotos.length} תמונות מוכנות!`;
        preview.appendChild(successMsg);
        
        console.log(`✅ Uploaded ${uploadedPhotos.length} photos successfully`);
        console.log(`📸 Preview displayed with ${results.length} images`);
    });
}

function showProfileCreation() {
    const existingModel = AITrainingManager.loadModel();
    
    if (existingModel) {
        console.log('Found existing model:', existingModel);
        const createdDate = new Date(existingModel.created_at).toLocaleDateString('he-IL');
        
        if (confirm(`יש לכם כבר פרופיל AI! 🤖\n\nנוצר ב: ${createdDate}\nתמונות: ${existingModel.photo_count}\n\nרוצים ליצור ספר עם הפרופיל הקיים?`)) {
            startCreation();
        } else if (confirm('רוצים ליצור פרופיל חדש?\n\n(זה ידרוס את הפרופיל הקיים)')) {
            AITrainingManager.deleteModel();
            showScreen('profileScreen');
        }
    } else {
        console.log('No existing model found');
        showScreen('profileScreen');
    }
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
    
    Array.from(input.files).forEach((file, i) => {
        const reader = new FileReader();
        reader.onload = (e) => {
            const div = document.createElement('div');
            div.style.cssText = 'position: relative; aspect-ratio: 1; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);';
            
            const img = document.createElement('img');
            img.src = e.target.result;
            img.style.cssText = 'width: 100%; height: 100%; object-fit: cover;';
            
            const badge = document.createElement('div');
            badge.textContent = i + 1;
            badge.style.cssText = 'position: absolute; top: 5px; right: 5px; background: #667eea; color: white; width: 24px; height: 24px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.8rem; font-weight: bold;';
            
            div.appendChild(img);
            div.appendChild(badge);
            grid.appendChild(div);
        };
        reader.readAsDataURL(file);
    });
    
    btn.disabled = false;
}

async function startTraining() {
    const input = document.getElementById('trainingPhotos');
    const files = input.files;
    
    if (!files || files.length < 5) {
        alert('נא להעלות לפחות 5 תמונות');
        return;
    }
    
    showScreen('trainingScreen');
    
    try {
        document.getElementById('trainingStatus').textContent = 'מעלה תמונות...';
        document.getElementById('trainingProgressBar').style.width = '10%';
        
        const photos = await Promise.all(
            Array.from(files).map(file => {
                return new Promise((resolve) => {
                    const reader = new FileReader();
                    reader.onload = (e) => resolve(e.target.result);
                    reader.readAsDataURL(file);
                });
            })
        );
        
        document.getElementById('training-upload').classList.add('active');
        document.getElementById('trainingProgressBar').style.width = '30%';
        document.getElementById('trainingStatus').textContent = 'שולח לשרת...';
        
        const response = await fetch(`${SERVER_CONFIG.url}/api/train-model`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                photos: photos,
                child_name: 'child_' + Date.now()
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Training failed');
        }
        
        document.getElementById('training-process').classList.add('active');
        document.getElementById('trainingProgressBar').style.width = '60%';
        document.getElementById('trainingStatus').textContent = 'מאמן AI...';
        
        const trainingId = data.training_id;
        let attempts = 0;
        const maxAttempts = 60;
        
        while (attempts < maxAttempts) {
            await new Promise(resolve => setTimeout(resolve, 2000));
            attempts++;
            
            const statusResponse = await fetch(`${SERVER_CONFIG.url}/api/training-status/${trainingId}`);
            const statusData = await statusResponse.json();
            
            const progress = 60 + (attempts / maxAttempts) * 35;
            document.getElementById('trainingProgressBar').style.width = progress + '%';
            
            if (statusData.status === 'succeeded') {
                document.getElementById('training-done').classList.add('active');
                document.getElementById('trainingProgressBar').style.width = '100%';
                document.getElementById('trainingStatus').textContent = 'מוכן! 🎉';
                
                const modelData = {
                    model_id: statusData.model_id,
                    created_at: new Date().toISOString(),
                    photo_count: photos.length
                };
                
                AITrainingManager.saveModel(modelData);
                console.log('🤖 Model saved:', modelData);
                
                await new Promise(resolve => setTimeout(resolve, 1500));
                
                alert('✅ הפרופיל מוכן!\n\nעכשיו תוכלו ליצור ספרים עם הילד בתמונות! 🌟');
                
                startCreation();
                break;
                
            } else if (statusData.status === 'failed') {
                throw new Error('Training failed: ' + (statusData.error || 'Unknown error'));
            }
        }
        
        if (attempts >= maxAttempts) {
            throw new Error('Training timeout');
        }
        
    } catch (error) {
        console.error('Training error:', error);
        alert('❌ שגיאה באימון: ' + error.message + '\n\nאפשר לנסות שוב או ליצור ספר רגיל.');
        showScreen('profileScreen');
    }
}

function skipTraining() {
    if (confirm('האם אתם בטוחים שרוצים לדלג?\n\nבלי פרופיל AI, הילד לא יופיע בתמונות.')) {
        startCreation();
    }
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
}

function startCreation() {
    showScreen('creatorScreen');
    resetForm();
}

function resetForm() {
    appState.bookData = {
        childName: '',
        childAge: '',
        childGender: '',
        theme: '',
        style: '',
        customInput: ''
    };
    
    const nameInput = document.getElementById('childName');
    if (nameInput) nameInput.value = '';
    
    document.querySelectorAll('.age-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.gender-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.theme-card').forEach(card => card.classList.remove('selected'));
    document.querySelectorAll('.style-card').forEach(card => card.classList.remove('selected'));
    
    const customInput = document.getElementById('customInput');
    if (customInput) customInput.value = '';
    
    showFormStep(1);
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
    
    const isValid = name && age && gender;
    const nextBtn = document.getElementById('step1-next');
    if (nextBtn) {
        nextBtn.disabled = !isValid;
    }
    
    if (name) appState.bookData.childName = name;
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
    
    // No training needed - Fal.ai works with photos directly!
    
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
        
        console.log('📸 uploadedPhotos:', uploadedPhotos);
        console.log('📸 uploadedPhotos.length:', uploadedPhotos.length);
        
        const requestData = {
            ...appState.bookData,
            ai_model_id: null,  // Force null for now
            childPhoto: uploadedPhotos.length > 0 ? uploadedPhotos[0] : null
        };
        
        console.log('📤 Sending story request');
        console.log('📸 With photo:', uploadedPhotos.length > 0 ? 'YES ✅' : 'NO ❌');
        console.log('🤖 With AI model:', aiModel ? 'YES ✅' : 'NO ❌');
        
        console.log('📤 Sending story request');
        console.log('📸 With photo:', uploadedPhotos.length > 0 ? 'YES ✅' : 'NO ❌');
        console.log('🤖 With AI model:', aiModel ? 'YES ✅' : 'NO ❌');
        
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

function saveEdit(pageIndex) {
    const textDiv = document.getElementById(`text-${pageIndex}`);
    const textarea = document.getElementById(`edit-${pageIndex}`);
    
    if (textarea && currentStory && currentStory.pages[pageIndex]) {
        const newText = textarea.value.trim();
        if (newText) {
            currentStory.pages[pageIndex].text = newText;
            if (textDiv) textDiv.textContent = newText;
            StorageManager.saveCurrentStory(currentStory);
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

function useAlternative(pageIndex, newText) {
    if (!currentStory || !currentStory.pages[pageIndex]) return;
    
    currentStory.pages[pageIndex].text = newText;
    
    const textDiv = document.getElementById(`text-${pageIndex}`);
    const textarea = document.getElementById(`edit-${pageIndex}`);
    const altContainer = document.getElementById(`alternatives-${pageIndex}`);
    
    if (textDiv) textDiv.textContent = newText;
    if (textarea) textarea.value = newText;
    if (altContainer) altContainer.style.display = 'none';
    
    StorageManager.saveCurrentStory(currentStory);
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
    
    // Check for saved story
    const saved = StorageManager.loadCurrentStory();
    if (saved && confirm('נמצא ספר שמור. להמשיך לעבוד עליו?')) {
        currentStory = saved;
        displayStory(currentStory);
        showScreen('previewScreen');
    }
    
    // Check for AI model
    const aiModel = AITrainingManager.loadModel();
    if (aiModel) {
        console.log('🤖 AI Model loaded:', aiModel.model_id);
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
    
    console.log('🎭 Regenerating with child photo:', childPhoto ? 'YES ✅' : 'NO ❌');
    
    // Close modal
    closeImageEditPopup();
    
    // Show loading
    showLoadingOverlay('מייצר תמונה חדשה... ⏳');
    
    try {
        const response = await fetch(`${SERVER_CONFIG.url}/api/regenerate-image`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                page_text: page.illustration,
                user_prompt: userPrompt,
                child_photo: childPhoto
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
