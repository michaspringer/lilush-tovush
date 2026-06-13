#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Children's Book Generator - Full Server
Leonardo + Fal.ai Face Swap + PDF + InstantID + LoRA

Last modified by Claude: 2026-06-13 23:00 (Israel time)
Changes in this version:
  - 🔙 FULL ROLLBACK to 06-06 prompt structure:
    * הוסר human_separator (היה: "the child has only two small human ears
      and no animal features") — גרם לעיוות פרופורציות פנים
    * הוסר "human" prefix מ-"a human boy child" — חוזר ל-"a boy child"
    * appearance ללא ears כבר מההודעה הקודמת
    זה בדיוק הפרומפט הנקי של 06-06 שעבד מצוין על דולב.
    feature-bleed (אוזני פיל) אם יחזור — נטפל בדרך אחרת.
  - 🐛 FIX: handle_preview_options_pulid לא קיבל appearance — לכן 3 מ-4 הוריאציות
    יצאו עם צבע עיניים שגוי, למרות ש-Claude Vision זיהה נכון.
    הוסף appearance ל-request, נשלח לכל קריאה ל-generate_image_with_pulid.
  - 🔧 קיצור human_separator — היה עמוס מדי, אולי הציף את הפרומפט.
    עכשיו: "the child has only two small human ears and no animal features"
  - 🐛 FIX FEATURE BLEED (קודם): אוזני פיל נוספו לילד
    בתחילת הזרימה ומחזיר תיאור פיזי קצר ("with blue eyes, brown hair...").
    התיאור נכנס לכל פרומפט של PuLID בספר — מעגן צבע עיניים, שיער, וכו'
    שלפעמים נשבר בסצנות מורכבות.
    * analyze_child_appearance — קריאה ל-claude-sonnet-4 vision (~$0.003 פעם אחת)
    * handle_upload_reference — מחזיר את ה-appearance ל-frontend
    * generate_image_with_pulid — מקבל ומזריק לפרומפט
    * _add_images_with_progress — מעביר ל-PuLID בכל עמוד
  - 🆕 ASYNC BOOK GENERATION: פותר timeout של Cloudflare/Railway proxy
    * POST /api/start-book-generation — מחזיר מיד job_id, יוצר ספר ברקע
    * GET  /api/book-status/<job_id> — polling להתקדמות
    * שמירת מצב ב-/tmp/books/<job_id>.json
    * _add_images_with_progress — שכפול מ-add_images_to_story עם עדכוני התקדמות
    זה תשתית לפתרון באג #23 (broken pipe במובייל) — כעת גם דסקטופ ייהנה.
  - 🧪 STEP 2B test page: routing חדש ל-/test-pulid-book
    דף בדיקה עצמאי לזרימה המלאה: תמונה → 4 וריאציות → בחירה → ספר 8 עמודים
    מאמת ש-handle_generate_story + add_images_to_story עובדים נכון עם PuLID
    לפני שנוגעים ב-UI הראשי בשלב 2C.
    הוראות Character Bible חלות עכשיו גם על PuLID (use_identity_model).
  - 🆕 STEP 2B: handle_generate_story + add_images_to_story תומכים ב-PuLID
    * חדש: handle_generate_story מקבל reference_url מהבקשה
    * חדש: סדר עדיפות מסלולים: PuLID > LoRA > FLUX face swap > FLUX
    * outfit נבחר גם ל-PuLID (לעקביות בין עמודים)
    * Throttle 5s ב-PuLID (קל יותר מ-12s של LoRA)
    * הזרימה הישנה של LoRA נשארת פעילה לתאימות
    * ה-frontend עוד לא מעביר reference_url — יבוצע בשלב 2C
  - 🔧 STEP 2A.1: בדיקת ריאליסטי שוב (בעקבות פידבק שדולב חסר ריאליסטי)
    * הוסף warm_realistic ל-style_anchors ב-generate_image_with_pulid
    * preview-options-pulid עכשיו מחזיר 4 וריאציות במקום 3
    * המטרה: לראות אם start_step=4 לריאליסטי שומר על זיהוי טוב
  - 🆕 STEP 2A: PuLID infrastructure בשרת:
    * handle_upload_reference (POST /api/upload-reference) — מעלה תמונת
      רפרנס יחידה ל-Cloudinary, מחזיר URL ציבורי
    * handle_preview_options_pulid (POST /api/preview-options-pulid) —
      יוצר 3 וריאציות סגנון: classic_illustration, soft_illustration,
      pixar_3d (במקום warm_realistic — PuLID חלש בריאליזם)
    * generate_image_with_pulid (method חדש) — אנלוגי ל-generate_image_with_lora
      אבל לזרימה החדשה. start_step אוטומטי לפי סגנון.
    הקוד הישן של LoRA נשאר פעיל לתאימות; ה-frontend עוד לא מדבר עם
    ה-endpoints החדשים — יעודכן בשלב 2C.
  - 🧹 STEP 1 CLEANUP: הוסרו endpoints/handlers ישנים שלא בשימוש מה-frontend:
    * handle_preview_lora (היה /api/preview-lora) — תצוגה מקדימה ישנה של LoRA
    * handle_test_style_prompts (היה /api/test-style-prompts) — דף טסט פרומפטים
    * routing של /test-style ב-do_GET
    שאר קוד LoRA (training, status, generate_image_with_lora, preview-options) נשאר
    פעיל עד שלב 2 שבו יוחלף ב-PuLID.
  - 🧪 POC: /api/test-pulid + /test-pulid HTML — בדיקת PuLID-Flux לזהות
    (bytedance/flux-pulid, $0.021/תמונה, ~15s)
  - 🎯 TRIGGER REINFORCEMENT: trigger_word מופיע 3× בכל פרומפט (היה 1×)
  - 🎨 STYLE HARDENING: בלוק אנטי-ריאליסטי חוזר עבור classic/soft_illustration
  - 🎨 soft_illustration: חוזק עם "watercolor + hand-drawn + NOT photorealistic"
  - 🔥 PRE-WARM DECONFLICTION: preview-options ממתין ל-pre-warm במקום להריץ במקביל
  - 🔥 ERROR MESSAGES: זיהוי rate-limit + יתרה נמוכה והודעה ידידותית
  - 🔥 PRE-WARMING: ברגע שאימון מסתיים, השרת יוצר 3 פריוויו ברקע
  - LoRA training upgrade: steps 1000→1500, lora_rank→32, caption_dropout_rate=0.05
  - 🔬 trigger word: "_kid" → "_subj"
  - 🔬 preview options: כל 3 התמונות ב-lora_scale=1.0
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import urllib.request
import urllib.error
from io import BytesIO
import base64
import os
import re
import time
import ssl


def safe_slug(name, fallback_prefix="child"):
    """
    ממיר שם בעברית/לטינית ל-slug בטוח ל-URL ול-Replicate.
    Replicate דורש: רק אותיות לטיניות קטנות, מספרים, ומקפים.
    """
    if not name:
        return f"{fallback_prefix}-{int(time.time())}"
    
    name = name.strip().lower()
    
    # אם השם כבר באנגלית בלבד - נקה ושמור
    if re.match(r'^[a-z0-9\s_-]+$', name):
        slug = re.sub(r'[\s_]+', '-', name)
        slug = re.sub(r'-+', '-', slug).strip('-')
        return slug if slug else f"{fallback_prefix}-{int(time.time())}"
    
    # אם יש תווי עברית/אחרים - השתמש ב-prefix + timestamp
    return f"{fallback_prefix}-{int(time.time())}"

# ========================================
# API Keys
# ========================================
CLAUDE_API_KEY = os.environ.get('CLAUDE_API_KEY', 'YOUR_CLAUDE_KEY_HERE')
LEONARDO_API_KEY = os.environ.get('LEONARDO_API_KEY', '')
REPLICATE_API_TOKEN = os.environ.get('REPLICATE_API_TOKEN', '')
REPLICATE_USERNAME = os.environ.get('REPLICATE_USERNAME', '')  # Your Replicate username
FAL_KEY = os.environ.get('FAL_KEY', '')
IMAGE_MODE = os.environ.get('IMAGE_MODE', 'leonardo')

# Cloudinary for LoRA training
CLOUDINARY_URL = os.environ.get('CLOUDINARY_URL', '')
CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME', '')
CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY', '')
CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET', '')

# Parse CLOUDINARY_URL if provided
if CLOUDINARY_URL and not CLOUDINARY_CLOUD_NAME:
    # Format: cloudinary://api_key:api_secret@cloud_name
    import re
    match = re.match(r'cloudinary://([^:]+):([^@]+)@(.+)', CLOUDINARY_URL)
    if match:
        CLOUDINARY_API_KEY = match.group(1)
        CLOUDINARY_API_SECRET = match.group(2)
        CLOUDINARY_CLOUD_NAME = match.group(3)
        print(f"✅ Cloudinary configured from CLOUDINARY_URL: {CLOUDINARY_CLOUD_NAME}")

# Try to import fal_client
try:
    import fal_client
    HAS_FAL = True
except ImportError:
    HAS_FAL = False
    print("⚠️ fal_client not installed - face swap disabled")

# Try to import replicate
try:
    import replicate
    HAS_REPLICATE = True
    if REPLICATE_API_TOKEN:
        os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN
except ImportError:
    HAS_REPLICATE = False
    print("⚠️ replicate not installed - LoRA training disabled")
# ========================================

CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"

class CORSRequestHandler(SimpleHTTPRequestHandler):
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        SimpleHTTPRequestHandler.end_headers(self)
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()
    
    def do_GET(self):
        if self.path.startswith('/api/training-status/'):
            training_id = self.path.split('/')[-1]
            self.handle_training_status(training_id)
        elif self.path.startswith('/api/lora-status/'):
            training_id = self.path.split('/')[-1]
            self.handle_lora_status(training_id)
        elif self.path.startswith('/api/book-status/'):
            # 🆕 STEP 2B-async: בדיקת סטטוס יצירת ספר ברקע
            job_id = self.path.split('/')[-1]
            self.handle_book_status(job_id)
        elif self.path == '/' or self.path == '/landing.html':
            # 🏠 דף הנחיתה - מה שמבקר חדש רואה ראשון
            self.serve_file('landing.html', 'text/html')
        elif self.path == '/app' or self.path == '/app-full' or self.path == '/index-full.html':
            # 📱 האפליקציה עצמה - לכאן מגיעים אחרי קוד גישה
            self.serve_file('index-full.html', 'text/html')
        elif self.path == '/app-full.js':
            self.serve_file('app-full.js', 'application/javascript')
        elif self.path == '/styles-full.css':
            self.serve_file('styles-full.css', 'text/css')
        elif self.path == '/test-pulid' or self.path == '/test-pulid.html':
            # 🧪 POC: דף טסט PuLID (פרומפט בודד)
            self.serve_file('test-pulid.html', 'text/html')
        elif self.path == '/test-pulid-preview' or self.path == '/test-pulid-preview.html':
            # 🧪 STEP 2A: דף טסט לזרימה המלאה של PuLID (4 וריאציות סגנון)
            self.serve_file('test-pulid-preview.html', 'text/html')
        elif self.path == '/test-pulid-book' or self.path == '/test-pulid-book.html':
            # 🧪 STEP 2B: דף טסט לספר 8 עמודים מלא עם PuLID
            self.serve_file('test-pulid-book.html', 'text/html')
        else:
            # Try default handler
            try:
                SimpleHTTPRequestHandler.do_GET(self)
            except:
                self.send_error(404)
    
    def serve_file(self, filename, content_type):
        """Serve a static file"""
        try:
            with open(filename, 'rb') as f:
                content = f.read()
            
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self.send_error(404)
        except Exception as e:
            print(f"Error serving {filename}: {e}")
            self.send_error(500)
    
    def do_POST(self):
        if self.path == '/api/generate-story':
            self.handle_generate_story()
        elif self.path == '/api/suggest-alternative':
            self.handle_suggest_alternative()
        elif self.path == '/api/generate-pdf':
            self.handle_generate_pdf()
        elif self.path == '/api/train-model':
            self.handle_train_model()
        elif self.path == '/api/regenerate-image':
            self.handle_regenerate_image()
        elif self.path == '/api/test-face-swap':
            self.handle_test_face_swap()
        elif self.path == '/api/start-lora-training':
            self.handle_start_lora_training()
        elif self.path == '/api/preview-options':  # 🆕 NEW: 3 preview options
            self.handle_preview_options()
        elif self.path == '/api/test-pulid':  # 🧪 POC: PuLID identity preservation
            self.handle_test_pulid()
        elif self.path == '/api/upload-reference':  # 🆕 PuLID: upload reference image
            self.handle_upload_reference()
        elif self.path == '/api/preview-options-pulid':  # 🆕 PuLID: 3 style variations
            self.handle_preview_options_pulid()
        elif self.path == '/api/start-book-generation':  # 🆕 STEP 2B-async: ספר ברקע
            self.handle_start_book_generation()
        elif self.path.startswith('/api/training-status/'):
            training_id = self.path.split('/')[-1]
            self.handle_training_status(training_id)
        else:
            self.send_error(404)
    
    def handle_generate_story(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))
            
            child_name = request_data.get('childName', 'ילד')
            child_photo = request_data.get('childPhoto')
            ai_model_id = request_data.get('ai_model_id')
            
            # 🎓 NEW: LoRA parameters
            lora_url = request_data.get('lora_url')
            trigger_word = request_data.get('trigger_word')
            lora_version = request_data.get('lora_version')  # 🆕 NEW: trained model version
            use_lora = request_data.get('use_lora', False) and lora_url and trigger_word
            
            # 🆕 PuLID parameters (החדש — מחליף LoRA בזרימה הראשית)
            reference_url = request_data.get('reference_url')  # תמונת רפרנס מ-Cloudinary
            use_pulid = reference_url is not None and not use_lora  # PuLID לא רץ במקביל ל-LoRA
            
            # 🎲 NEW: chosen seed - ה-seed שההורה בחר בתצוגה המקדימה
            chosen_seed = request_data.get('chosen_seed')
            # 💪 NEW: chosen lora_scale - האיזון שההורה בחר (דמיון מול איור)
            chosen_lora_scale = request_data.get('chosen_lora_scale', 1.0)
            # 🎨 NEW: chosen style - הסגנון שההורה בחר (חמים-ריאליסטי/קלאסי/רך)
            chosen_style = request_data.get('chosen_style', 'classic_illustration')
            
            print(f"\n📖 Creating story for: {child_name}")
            if use_pulid:
                print(f"🆕 USING PuLID! (no training, direct identity)")
                print(f"   Reference URL: {reference_url[:80]}...")
                if chosen_seed is not None:
                    print(f"   🎲 Chosen seed: {chosen_seed} (consistent for whole book)")
                print(f"   🎨 Chosen style: {chosen_style}")
            elif use_lora:
                print(f"🎓 USING TRAINED LoRA MODEL!")
                print(f"   Trigger word: {trigger_word}")
                print(f"   LoRA URL: {lora_url[:80]}...")
                if lora_version:
                    print(f"   Version: {lora_version[:80]}...")
                if chosen_seed is not None:
                    print(f"   🎲 Chosen seed: {chosen_seed} (consistent for whole book)")
                print(f"   💪 Chosen lora_scale: {chosen_lora_scale}")
                print(f"   🎨 Chosen style: {chosen_style}")
            elif child_photo:
                print("📸 Photo uploaded - will use FLUX face swap")
            if ai_model_id:
                print(f"🤖 Using trained AI model: {ai_model_id[:20]}...")
            
            print("📝 Step 1: Generating story with Claude...")
            story_data = self.create_story_with_claude(request_data)
            
            if ai_model_id:
                story_data['ai_model_id'] = ai_model_id
            
            if IMAGE_MODE != 'none' and story_data.get('pages'):
                print(f"🎨 Step 2: Generating images ({IMAGE_MODE})...")
                # 🎓 העבר את ה-LoRA/PuLID, ה-seed, ה-scale וה-style לפונקציה
                story_data = self.add_images_to_story(
                    story_data,
                    child_photo,
                    lora_url=lora_url if use_lora else None,
                    trigger_word=trigger_word if use_lora else None,
                    lora_version=lora_version if use_lora else None,
                    reference_url=reference_url if use_pulid else None,  # 🆕 PuLID
                    chosen_seed=chosen_seed,  # 🎲 עקביות לכל הספר
                    chosen_lora_scale=chosen_lora_scale,  # 💪 האיזון שנבחר (LoRA only)
                    chosen_style=chosen_style,  # 🎨 הסגנון שנבחר
                    child_gender='girl' if request_data.get('childGender') == 'girl' else 'boy'  # 🚻
                )
            
            print("✅ Story complete!")
            self.send_json_response({
                'success': True,
                'story': story_data
            })
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()
            self.send_json_response({'error': str(e)}, status=500)
    
    def handle_preview_options(self):
        """
        🆕 יוצר 3 תמונות תצוגה מקדימה במקביל.
        כל אחת עם seed שונה + lora_scale שונה (גיוון אמיתי).
        רקע נקי - כדי שההורה יוכל לבדוק בקלות את זיהוי הילד.
        
        🔥 23/5: מחפש קודם cache מ-pre-warming. אם קיים — מחזיר מיד (~0 שניות).
        """
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            child_name = data.get('child_name', '')
            lora_url = data.get('lora_url')
            trigger_word = data.get('trigger_word')
            lora_version = data.get('lora_version')
            training_id = data.get('training_id')  # 🔥 חדש: לזיהוי cache
            
            if not lora_url or not trigger_word:
                raise Exception('LoRA not configured for this child')
            
            # 🔥 PRE-WARM CACHE CHECK: אם הורה לחץ "צור 3 חדשות" — force=true מ-frontend
            force_regenerate = data.get('force_regenerate', False)
            if training_id and not force_regenerate:
                import os as _os
                cache_path = f'/tmp/previews/{training_id}.json'
                lock_path = f'/tmp/previews/{training_id}.lock'
                
                # 🔥 שיפור 23/5: אם pre-warm רץ עכשיו — נמתין עד שיסיים במקום להריץ במקביל.
                # זה מונע 6 קריאות מקבילות (3 של pre-warm + 3 של preview-options) שגורמות ל-rate limit.
                if _os.path.exists(lock_path) and not _os.path.exists(cache_path):
                    print(f"\n🔥 PRE-WARM IN PROGRESS for {training_id} — waiting up to 120s...")
                    import time as _time
                    waited = 0
                    while _os.path.exists(lock_path) and not _os.path.exists(cache_path) and waited < 120:
                        _time.sleep(2)
                        waited += 2
                    print(f"   ⏳ Waited {waited}s for pre-warm. Cache exists: {_os.path.exists(cache_path)}")
                
                if _os.path.exists(cache_path):
                    try:
                        with open(cache_path, 'r', encoding='utf-8') as _f:
                            cached = json.load(_f)
                        print(f"\n🔥 PRE-WARM CACHE HIT for {training_id} ({child_name})")
                        print(f"   Returning {len(cached.get('options', []))} cached options instantly")
                        # מוחקים את ה-cache כדי שלחיצה הבאה ("צור 3 חדשות") תייצר מחדש
                        try:
                            _os.remove(cache_path)
                            print(f"   🗑️  Cache cleared for next request")
                        except Exception:
                            pass
                        self.send_json_response({
                            'success': True,
                            'options': cached.get('options', []),
                            'child_name': child_name,
                            'from_cache': True
                        })
                        return
                    except Exception as _e:
                        print(f"   ⚠️  Cache read failed, falling through: {_e}")
            
            child_gender = data.get('child_gender', 'boy')  # 🚻 מגדר - מונע החלקה מגדרית
            
            print(f"\n🎨 Generating 3 preview options for: {child_name}")
            print(f"   Trigger: {trigger_word}")
            
            # 🎯 רקע נקי ופשוט - בלי חיות/ילדים, כדי לבדוק זיהוי בקלות
            clean_scene = (
                "standing against a simple soft pastel background, "
                "plain clean background, happy smile, looking at viewer"
            )
            
            # 🎨 3 וריאציות - ההבדל בא מהסגנון, לא מ-lora_scale!
            # 🔬 23/5: כל ה-3 ב-scale=1.0 — הטסט מ-23/5 הוכיח שמתחת ל-1.0
            # הזיהוי נשבר ומגיע ילד גנרי. עדיף scale גבוה תמיד; הסגנון בא מ-style_anchors.
            variations = [
                {'seed': None, 'lora_scale': 1.0, 'style': 'warm_realistic',
                 'label': 'warm_realistic'},
                {'seed': None, 'lora_scale': 1.0, 'style': 'classic_illustration',
                 'label': 'classic_illustration'},
                {'seed': None, 'lora_scale': 1.0, 'style': 'soft_illustration',
                 'label': 'soft_illustration'},
            ]
            
            import random
            for v in variations:
                v['seed'] = random.randint(1, 999999)
            
            print(f"   🎨 Variations: {[(v['label'], v['lora_scale']) for v in variations]}")
            
            # 🚀 יצירת 3 התמונות במקביל (threads)
            import threading
            results = [None, None, None]
            errors = [None, None, None]  # 🔥 לזיהוי סוג השגיאה (rate limit, יתרה, וכו')
            
            def generate_one(index, variation):
                try:
                    seed = variation['seed']
                    scale = variation['lora_scale']
                    style = variation['style']
                    print(f"   🖼️  Option {index+1}/3 (style={style}, scale={scale})...")
                    img = self.generate_image_with_lora(
                        prompt=f"medium shot, {clean_scene}",
                        lora_url=lora_url,
                        trigger_word=trigger_word,
                        lora_version=lora_version,
                        style_name=style,
                        seed=seed,
                        lora_scale=scale,
                        child_gender=child_gender
                    )
                    results[index] = {
                        'image': img,
                        'seed': seed,
                        'lora_scale': scale,
                        'style': style,
                        'label': variation['label']
                    }
                except Exception as e:
                    print(f"   ⚠️ Option {index+1} failed: {e}")
                    errors[index] = str(e)
                    results[index] = None
            
            threads = []
            for i, variation in enumerate(variations):
                t = threading.Thread(target=generate_one, args=(i, variation))
                threads.append(t)
                t.start()
            
            # המתנה לסיום כל ה-threads
            for t in threads:
                t.join()
            
            # סינון תוצאות שהצליחו
            options = [r for r in results if r and r.get('image')]
            
            if not options:
                # 🔥 זיהוי הסיבה השכיחה: rate limit (status 429) או חוסר יתרה
                error_messages = [e for e in errors if e]
                joined = ' '.join(error_messages).lower()
                
                if '429' in joined or 'throttled' in joined or 'rate limit' in joined:
                    if 'less than $5' in joined or 'credit' in joined:
                        # יתרה נמוכה ב-Replicate
                        user_msg = ('🪙 יתרת השרת נמוכה. '
                                    'יצירת התמונות הופסקה זמנית. '
                                    'נסו שוב בעוד 1-2 דקות.')
                        print(f"   💸 LOW CREDIT detected — likely needs Replicate top-up")
                    else:
                        # rate limit רגיל - נוסה עוד דקה
                        user_msg = ('⏳ השרת עמוס כרגע. '
                                    'נסו שוב בעוד דקה.')
                        print(f"   ⏰ Rate limit detected — transient")
                else:
                    # שגיאה אחרת — נציג טכנית
                    user_msg = f'שגיאה ביצירת התמונות. נסו שוב.\n(פרטים בלוגים)'
                    print(f"   ❌ Non-rate-limit error: {error_messages[:1]}")
                
                raise Exception(user_msg)
            
            print(f"   ✅ {len(options)}/3 preview options ready!")
            
            self.send_json_response({
                'success': True,
                'options': options,  # [{image, seed, lora_scale, label}, ...]
                'child_name': child_name
            })
            
        except Exception as e:
            print(f"❌ Preview options error: {str(e)}")
            import traceback
            traceback.print_exc()
            self.send_json_response({
                'success': False,
                'error': str(e)
            }, status=500)
    
    def create_story_with_claude(self, data):
        """יוצר סיפור עם Claude"""
        prompt = self.build_story_prompt(data)
        
        claude_request = {
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 2000,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        headers = {
            'Content-Type': 'application/json',
            'x-api-key': CLAUDE_API_KEY,
            'anthropic-version': '2023-06-01'
        }
        
        req = urllib.request.Request(
            CLAUDE_API_URL,
            data=json.dumps(claude_request).encode('utf-8'),
            headers=headers,
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=60) as response:
            response_data = json.loads(response.read().decode('utf-8'))
            content = response_data['content'][0]['text']
            clean_content = content.replace('```json', '').replace('```', '').strip()
            story_data = json.loads(clean_content)
            return story_data
    
    def add_images_to_story(self, story_data, child_photo=None, lora_url=None, trigger_word=None, lora_version=None, reference_url=None, chosen_seed=None, chosen_lora_scale=1.0, chosen_style='classic_illustration', child_gender='boy'):
        """מוסיף תמונות לסיפור.
        
        🆕 סדר עדיפות:
          1. PuLID (אם reference_url קיים) — החדש, הזרימה הראשית
          2. LoRA (אם lora_url + trigger_word) — הישן, לתאימות
          3. FLUX + face swap (אם child_photo בלבד) — fallback
          4. FLUX רגיל (אם אין כלום) — בלי הילד
        
        chosen_seed: אם ניתן - כל עמודי הספר ישתמשו ב-seed הזה (עקביות מלאה!).
        child_gender: 'boy' או 'girl' - מונע החלקה מגדרית.
        """
        pages = story_data.get('pages', [])
        
        use_pulid = reference_url is not None
        use_lora = (not use_pulid) and lora_url and trigger_word  # PuLID גוברת על LoRA
        
        # 📖 NEW: Character Bible - מילון דמויות שClaude יצר
        characters = story_data.get('characters', [])
        char_dict = {}  # name -> english_description
        for char in characters:
            name = char.get('name', '').strip()
            desc = char.get('english_description', '').strip()
            if name and desc:
                char_dict[name] = desc
        
        if char_dict:
            print(f"  📖 Character Bible: {len(char_dict)} characters")
            for name, desc in char_dict.items():
                print(f"     - {name}: {desc[:60]}...")
        
        # 🎽 בחירת ביגוד אחיד לכל הספר (גם ל-PuLID — שומר עקביות בין עמודים)
        consistent_outfit = None
        if use_pulid or use_lora:
            import random
            outfits = [
                "wearing a yellow t-shirt and blue jeans",
                "wearing a red striped shirt and khaki shorts",
                "wearing a green hoodie and dark blue pants",
                "wearing a white t-shirt with a pattern and beige pants",
                "wearing an orange sweater and denim shorts",
                "wearing a purple shirt and gray pants",
                "wearing a blue polo shirt and brown shorts",
            ]
            consistent_outfit = random.choice(outfits)
            print(f"  🎽 Outfit chosen for entire book: {consistent_outfit}")
            story_data['outfit'] = consistent_outfit
        
        # שמירת ה-Character Bible כך שיהיה זמין לrenegerate
        story_data['character_bible'] = char_dict
        
        if use_pulid:
            print(f"  🆕 Creating {len(pages)} images with PuLID!")
            print(f"  📸 Reference: {reference_url[:80]}...")
            if chosen_seed:
                print(f"  🎲 Locked seed: {chosen_seed}")
            print(f"  🎨 Style: {chosen_style}")
        elif use_lora:
            print(f"  🎓 Creating {len(pages)} images with LoRA model!")
            print(f"  🏷️  Trigger word: {trigger_word}")
            if lora_version:
                print(f"  📌 Using trained model version directly")
        elif child_photo:
            print(f"  🎨 Creating {len(pages)} images with FLUX + face swap...")
            print(f"  👤 Child will be drawn in illustration style!")
        else:
            print(f"  🎨 Creating {len(pages)} images with FLUX (no child)...")
        
        for i, page in enumerate(pages):
            print(f"\n  🖼️  Image {i+1}/{len(pages)}...")
            
            # 🐌 Throttle - חכה בין בקשות לAPI
            # LoRA: 8-12s (rate limit חזק). PuLID: 5s (קל יותר).
            if use_pulid:
                wait_seconds = 5 if i > 0 else 3
                print(f"  ⏱️  Waiting {wait_seconds}s (PuLID rate limit protection)...")
                time.sleep(wait_seconds)
            elif use_lora:
                wait_seconds = 12 if i > 0 else 8
                print(f"  ⏱️  Waiting {wait_seconds}s (rate limit protection)...")
                time.sleep(wait_seconds)
            
            try:
                # 🎯 לוגיקה משותפת לכל הסניפים שמשתמשים בדמות הילד (PuLID/LoRA):
                # זיהוי אוטומטי של דמויות נוספות בעמוד + הזרקה מ-Character Bible
                if use_pulid or use_lora:
                    illustration = page.get('illustration', '')
                    page_text = page.get('text', '')
                    chars_in_scene = page.get('characters_in_scene', [])
                    
                    # 🛡️ FIX: זיהוי אוטומטי של דמויות בעמוד
                    detected_chars = set(chars_in_scene)
                    for char_name in char_dict.keys():
                        if char_name in page_text or char_name in illustration:
                            if char_name not in detected_chars:
                                detected_chars.add(char_name)
                                print(f"  🔍 Auto-detected character '{char_name}' in page text")
                    
                    char_descriptions = []
                    for char_name in detected_chars:
                        if char_name in char_dict:
                            char_descriptions.append(char_dict[char_name])
                    
                    if char_descriptions:
                        print(f"  📖 Using {len(char_descriptions)} character description(s) from Bible")
                
                # 🆕 PuLID: הזרימה הראשית החדשה
                if use_pulid:
                    image_url = self.generate_image_with_pulid(
                        reference_url=reference_url,
                        prompt=illustration,
                        style_name=chosen_style,
                        seed=chosen_seed,  # 🎲 אותו seed לכל הספר
                        character_descriptions=char_descriptions,
                        outfit=consistent_outfit,
                        child_gender=child_gender,
                    )
                    
                    # Fallback אם נכשל — FLUX + face swap אם יש child_photo, אחרת FLUX רגיל
                    if not image_url:
                        print(f"  ⚠️  PuLID failed, falling back to FLUX...")
                        if child_photo:
                            image_url = self.generate_image_flux_with_face(
                                illustration, child_photo
                            )
                
                elif use_lora:
                    # 🎓 מסלול LoRA עם Character Bible
                    image_url = self.generate_image_with_lora(
                        prompt=illustration,
                        lora_url=lora_url,
                        trigger_word=trigger_word,
                        lora_version=lora_version,
                        style_name=chosen_style,
                        outfit=consistent_outfit,
                        character_descriptions=char_descriptions,
                        seed=chosen_seed,
                        lora_scale=chosen_lora_scale,
                        child_gender=child_gender
                    )
                    
                    if not image_url:
                        print(f"  ⚠️  LoRA failed after retries, falling back to FLUX...")
                        image_url = self.generate_image_flux_with_face(
                            illustration, child_photo
                        )
                else:
                    # מסלול רגיל - FLUX + face swap
                    image_url = self.generate_image_flux_with_face(
                        page['illustration'],
                        child_photo
                    )
                
                page['imageUrl'] = image_url
                
            except Exception as e:
                print(f"  ⚠️  Failed: {str(e)}")
                page['imageUrl'] = None
        
        return story_data
    
    def apply_fal_face_swap(self, target_image_b64, face_image_b64):
        """Face swap with Fal.ai - simple and working"""
        try:
            if not FAL_KEY or not HAS_FAL:
                print("  ⚠️ Fal.ai not configured")
                return None
            
            print(f"  🎭 Starting Fal.ai face swap...")
            
            # Set API key
            os.environ["FAL_KEY"] = FAL_KEY
            
            # Use simple face-swap
            handler = fal_client.submit(
                "fal-ai/face-swap",
                arguments={
                    "base_image_url": target_image_b64,
                    "swap_image_url": face_image_b64
                }
            )
            
            print(f"  ⏳ Waiting for Fal.ai...")
            
            result = handler.get()
            
            if result and 'image' in result:
                output_url = result['image']['url']
                
                # Download result
                req = urllib.request.Request(
                    output_url,
                    headers={'User-Agent': 'Mozilla/5.0'}
                )
                
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                
                with urllib.request.urlopen(req, timeout=60, context=ctx) as response:
                    img_data = response.read()
                
                img_b64 = base64.b64encode(img_data).decode()
                print(f"  ✅ Fal.ai face swap succeeded!")
                return f"data:image/jpeg;base64,{img_b64}"
            
            print(f"  ⚠️ Fal.ai: No output")
            return None
            
        except Exception as e:
            print(f"  ⚠️ Fal.ai error: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def apply_instant_id(self, target_image_b64, face_image_b64):
        """Face swap with working Replicate model"""
        try:
            if not REPLICATE_API_TOKEN:
                print("  ⚠️ No Replicate token")
                return None
            
            print(f"  🎭 Starting Face Swap...")
            
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            # Ensure data URIs
            if not target_image_b64.startswith('data:'):
                target_image_b64 = f"data:image/jpeg;base64,{target_image_b64}"
            
            if not face_image_b64.startswith('data:'):
                face_image_b64 = f"data:image/jpeg;base64,{face_image_b64}"
            
            # Use simpler face swap - just swap the prediction endpoint
            swap_data = {
                "input": {
                    "target_image": target_image_b64,
                    "swap_image": face_image_b64
                }
            }
            
            headers = {
                'Authorization': f'Token {REPLICATE_API_TOKEN}',
                'Content-Type': 'application/json'
            }
            
            # Try lucataco/faceswap - more reliable
            req = urllib.request.Request(
                'https://api.replicate.com/v1/models/lucataco/faceswap/predictions',
                data=json.dumps(swap_data).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=30, context=ctx) as response:
                result = json.loads(response.read().decode('utf-8'))
                pred_id = result['id']
            
            print(f"  ⏳ Face swap processing... ({pred_id})")
            
            # Poll for result
            for attempt in range(60):
                time.sleep(2)
                
                check_req = urllib.request.Request(
                    f'https://api.replicate.com/v1/predictions/{pred_id}',
                    headers=headers
                )
                
                with urllib.request.urlopen(check_req, timeout=30, context=ctx) as check_resp:
                    check_result = json.loads(check_resp.read().decode('utf-8'))
                    
                    status = check_result['status']
                    
                    if status == 'succeeded':
                        output_url = check_result['output']
                        
                        # Download
                        img_req = urllib.request.Request(output_url, headers={'User-Agent': 'Mozilla/5.0'})
                        with urllib.request.urlopen(img_req, timeout=60, context=ctx) as img_resp:
                            img_data = img_resp.read()
                        
                        img_b64 = base64.b64encode(img_data).decode()
                        print(f"  ✅ Face swap succeeded!")
                        return f"data:image/jpeg;base64,{img_b64}"
                    
                    elif status == 'failed':
                        error = check_result.get('error', 'Unknown')
                        print(f"  ❌ Face swap failed: {error}")
                        return None
            
            print(f"  ⏱️ Face swap timeout")
            return None
            
        except Exception as e:
            print(f"  ⚠️ Face swap error: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
        """מוסיף פנים של ילד לתמונה עם InstantID"""
        try:
            if not REPLICATE_API_TOKEN:
                print("  ⚠️ No Replicate token")
                return None
            
            print(f"  🔄 Starting InstantID...")
            
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            # InstantID expects data URIs
            if not target_image_b64.startswith('data:'):
                target_image_b64 = f"data:image/jpeg;base64,{target_image_b64}"
            
            if not face_image_b64.startswith('data:'):
                face_image_b64 = f"data:image/jpeg;base64,{face_image_b64}"
            
            instant_id_data = {
                "input": {
                    "image": target_image_b64,
                    "face_image": face_image_b64,
                    "prompt": "high quality children's book illustration, colorful, friendly, detailed face",
                    "negative_prompt": "ugly, distorted, low quality, blurry, bad anatomy, scary",
                    "num_steps": 20,
                    "guidance_scale": 5.0,
                    "ip_adapter_scale": 0.8,
                    "seed": 42
                }
            }
            
            headers = {
                'Authorization': f'Token {REPLICATE_API_TOKEN}',
                'Content-Type': 'application/json'
            }
            
            # Use the correct InstantID model
            req = urllib.request.Request(
                'https://api.replicate.com/v1/models/zsxkib/instant-id/predictions',
                data=json.dumps(instant_id_data).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=30, context=ctx) as response:
                result = json.loads(response.read().decode('utf-8'))
                pred_id = result['id']
            
            print(f"  ⏳ Waiting for InstantID (prediction: {pred_id})...")
            
            # Wait for completion
            for attempt in range(60):
                time.sleep(2)
                
                check_req = urllib.request.Request(
                    f'https://api.replicate.com/v1/predictions/{pred_id}',
                    headers=headers
                )
                
                with urllib.request.urlopen(check_req, timeout=30, context=ctx) as check_resp:
                    check_result = json.loads(check_resp.read().decode('utf-8'))
                    
                    status = check_result['status']
                    
                    if status == 'succeeded':
                        output_url = check_result['output']
                        
                        # Download result
                        if isinstance(output_url, list) and len(output_url) > 0:
                            output_url = output_url[0]
                        
                        img_req = urllib.request.Request(output_url, headers={'User-Agent': 'Mozilla/5.0'})
                        with urllib.request.urlopen(img_req, timeout=60, context=ctx) as img_resp:
                            img_data = img_resp.read()
                        
                        img_b64 = base64.b64encode(img_data).decode()
                        print(f"  ✅ InstantID succeeded!")
                        return f"data:image/jpeg;base64,{img_b64}"
                    
                    elif status == 'failed':
                        error = check_result.get('error', 'Unknown error')
                        print(f"  ❌ InstantID failed: {error}")
                        return None
            
            print(f"  ⏱️ InstantID timeout")
            return None
            
        except Exception as e:
            print(f"  ⚠️ InstantID error: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def translate_to_english(self, hebrew_text):
        """תרגום תיאור תמונה מעברית לאנגלית - מודע להקשר של ספרי ילדים"""
        try:
            if not CLAUDE_API_KEY:
                return hebrew_text  # Fallback
            
            prompt = f"""You are translating a scene description for a children's book illustration from Hebrew to English.

Hebrew description: "{hebrew_text}"

CRITICAL translation rules:
1. This is a CHILDREN'S BOOK scene - translate concretely and literally
2. Watch for animal body parts - translate them EXACTLY:
   - "חדק" = "trunk" (elephant's trunk) - NEVER "snake"!
   - "זנב" = "tail"
   - "כנף" = "wing"
   - "טלף" = "hoof"
   - "קרן" = "horn"
3. If an animal is mentioned, ALWAYS name the animal explicitly in English
4. Translate every object and creature mentioned - don't drop anything
5. Be vivid and specific so an illustrator can draw it accurately

Return ONLY the English translation, no explanations."""
            
            claude_request = {
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 300,
                "messages": [{"role": "user", "content": prompt}]
            }
            
            headers = {
                'Content-Type': 'application/json',
                'x-api-key': CLAUDE_API_KEY,
                'anthropic-version': '2023-06-01'
            }
            
            req = urllib.request.Request(
                CLAUDE_API_URL,
                data=json.dumps(claude_request).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                response_data = json.loads(response.read().decode('utf-8'))
                english_text = response_data['content'][0]['text'].strip()
                print(f"  🌐 Translated: {english_text[:60]}...")
                return english_text
                
        except Exception as e:
            print(f"  ⚠️ Translation failed: {str(e)}, using original")
            return hebrew_text
    
    def analyze_child_appearance(self, image_url):
        """
        🆕 מנתח תמונת ילד עם Claude Vision כדי להוציא תיאור פיזי קצר באנגלית.
        
        מטרה: לעגן את הזהות (במיוחד צבע עיניים שעלול להישבר ב-PuLID
        על סצנות מורכבות) דרך תיאור טקסטואלי בפרומפט של כל תמונה בספר.
        
        משתמש ב-claude-sonnet-4-20250514 ל-vision quality.
        עלות: ~$0.003-0.005 לקריאה אחת בלבד בתחילת זרימה.
        
        Args:
            image_url: URL ציבורי לתמונת הילד (מ-Cloudinary)
        
        Returns:
            str: תיאור פיזי קצר באנגלית, או None אם נכשל.
            דוגמה: "with bright blue eyes, short brown hair, fair skin, rosy cheeks"
        """
        try:
            if not CLAUDE_API_KEY:
                print("  ⚠️ No CLAUDE_API_KEY — skipping appearance analysis")
                return None
            
            print(f"  👁️  Analyzing child appearance from: {image_url[:80]}...")
            
            # 📌 הנחיות:
            # 1. תיאור מינימלי - רק מה שמשפיע על זיהוי בין תמונות
            # 2. ללא ביגוד (הוא ייקבע ע"י outfit lock נפרד)
            # 3. ללא רקע / סצנה
            # 4. תוצאה כצירוף קצר שאפשר להוסיף לפרומפט באנגלית
            # ⚠️ 13/6: הוסר תיאור אוזניים מ-appearance — גרם ל-PuLID להגדיל
            # אותן לפרופורציות לא-אנושיות. ההגנה מ-feature-bleed עברה
            # ל-human_separator בלבד (בפרומפט הסצנה של PuLID).
            prompt_text = """Look at this photo of a child and write a concise physical description for use as an anchor in AI image generation.

REQUIRED format: a comma-separated list of features, starting with "with".

INCLUDE:
- Eye color (be specific: bright blue / hazel green / dark brown / etc.)
- Hair color and length (short brown / long blonde / curly black / etc.)
- Skin tone (fair / olive / medium brown / dark)
- Any distinctive facial features (rosy cheeks, dimples, freckles, etc.) — only if clearly visible

EXCLUDE:
- Clothing (do not mention what they're wearing)
- Background / scene / setting
- Emotion / expression
- Age
- Ears (do not mention ears at all)

Output EXACTLY one line in this format and nothing else:
with [eye color] eyes, [hair description], [skin tone] skin, [optional features]

Example: with bright blue eyes, short light-brown hair, fair skin, rosy cheeks"""
            
            claude_request = {
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 150,
                "messages": [{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "url",
                                "url": image_url
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt_text
                        }
                    ]
                }]
            }
            
            headers = {
                'Content-Type': 'application/json',
                'x-api-key': CLAUDE_API_KEY,
                'anthropic-version': '2023-06-01'
            }
            
            req = urllib.request.Request(
                CLAUDE_API_URL,
                data=json.dumps(claude_request).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                response_data = json.loads(response.read().decode('utf-8'))
                appearance = response_data['content'][0]['text'].strip()
                
                # ניקוי בסיסי — לפעמים Claude יוסיף הסבר. ניקח רק את השורה הראשונה.
                first_line = appearance.split('\n')[0].strip()
                # ולוודא שהיא מתחילה עם "with"
                if not first_line.lower().startswith('with'):
                    # חיפוש שורה שמתחילה ב-with
                    for line in appearance.split('\n'):
                        if line.strip().lower().startswith('with'):
                            first_line = line.strip()
                            break
                
                print(f"  ✨ Child appearance: {first_line}")
                return first_line
        
        except Exception as e:
            print(f"  ⚠️ Appearance analysis failed: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _story_to_image_description(self, hebrew_story_text, character_bible=None):
        """
        🎯 ממיר טקסט סיפור בעברית לתיאור תמונה באנגלית.
        
        זה שונה מ-translate_to_english:
        - translate_to_english: תרגום ישר של תיאור תמונה
        - _story_to_image_description: מתחקר טקסט סיפור ומחזיר תיאור ויזואלי בלבד
        
        character_bible: מילון {שם: תיאור אנגלי} - עוזר לזהות דמויות בעלות שם.
        
        דוגמה:
        טקסט: "ציפור צהובה התקרבה לדולב והגישה לו פרח אדום"
        חוזר: "yellow bird offering red flower, garden, sunny day"
        """
        try:
            if not CLAUDE_API_KEY:
                return hebrew_story_text
            
            # 🔑 בניית הקשר דמויות - אם יש Character Bible
            character_context = ""
            if character_bible:
                lines = []
                for name, desc in character_bible.items():
                    lines.append(f'- "{name}" is: {desc}')
                if lines:
                    character_context = (
                        "\n\nKNOWN CHARACTERS (use these descriptions if the name appears):\n"
                        + "\n".join(lines)
                        + "\n(If the text mentions a character name, use its full description above!)"
                    )
            
            prompt = f"""Convert this Hebrew children's story sentence into an English image description (15-25 words).

CRITICAL RULES:
1. Describe what should be VISUALLY in the image (scene, action, objects, creatures)
2. DO NOT describe the child's appearance (hair, eyes, age, clothes) - we have a special model
3. DO NOT mention the child's name
4. INCLUDE every animal, object, and creature mentioned in the text - don't drop anything!

⚠️ ANIMAL BODY PARTS - translate EXACTLY:
- "חדק" = "trunk" (elephant trunk) - NEVER translate as "snake"!
- "זנב" = "tail",  "כנף" = "wing",  "טלף" = "hoof",  "קרן" = "horn"
- When an animal is mentioned, NAME the animal explicitly (elephant, dog, bird...){character_context}

Hebrew text: "{hebrew_story_text}"

Examples of good descriptions:
- "yellow bird offering red flower, garden, sunny day"
- "large grey elephant wrapping its trunk gently around child, jungle background"
- "small brown puppy jumping near child on green grass, afternoon light"
- "reaching up toward the moon, starry night sky"

Return ONLY the English description, nothing else."""
            
            claude_request = {
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 100,
                "messages": [{"role": "user", "content": prompt}]
            }
            
            headers = {
                'Content-Type': 'application/json',
                'x-api-key': CLAUDE_API_KEY,
                'anthropic-version': '2023-06-01'
            }
            
            req = urllib.request.Request(
                CLAUDE_API_URL,
                data=json.dumps(claude_request).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=30) as response:
                response_data = json.loads(response.read().decode('utf-8'))
                description = response_data['content'][0]['text'].strip()
                print(f"  🎨 Image description: {description}")
                return description
                
        except Exception as e:
            print(f"  ⚠️ Story-to-image conversion failed: {str(e)}, falling back to translation")
            return self.translate_to_english(hebrew_story_text)
    
    def generate_image_flux_with_face(self, prompt, child_photo=None):
        """יצירת תמונה עם FLUX + InstantID - הילד מצוייר באיור!"""
        try:
            if not FAL_KEY or not HAS_FAL:
                raise Exception('Fal.ai not configured')
            
            print(f"  🎨 FLUX + InstantID...")
            
            # Translate Hebrew to English if needed
            if any(ord(c) > 127 for c in prompt):
                prompt = self.translate_to_english(prompt)
            
            # FLUX prompt - emphasize illustration style
            full_prompt = f"{prompt}, children's book illustration style, colorful, friendly, warm, high quality, professional illustration"
            
            negative_prompt = "realistic photo, photographic, multiple people, crowd, side view, back view, profile view, hidden face, blurry, low quality"
            
            print(f"  📝 Prompt: {full_prompt[:80]}...")
            
            # Set API key
            os.environ["FAL_KEY"] = FAL_KEY
            
            # Note: InstantID requires specific Replicate model access
            # For now, using FLUX + Face Swap as reliable fallback
            # TODO: Get proper InstantID model access from Replicate
            
            # Fallback: FLUX + Face Swap
            handler = fal_client.submit(
                "fal-ai/flux/dev",
                arguments={
                    "prompt": full_prompt,
                    "image_size": "landscape_4_3",
                    "num_inference_steps": 28,
                    "guidance_scale": 3.5,
                    "num_images": 1,
                    "enable_safety_checker": False,
                    "negative_prompt": negative_prompt
                }
            )
            
            print(f"  ⏳ Waiting for FLUX...")
            
            result = handler.get()
            
            if result and 'images' in result and len(result['images']) > 0:
                output_url = result['images'][0]['url']
                
                # Download
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                
                req = urllib.request.Request(
                    output_url,
                    headers={'User-Agent': 'Mozilla/5.0'}
                )
                
                with urllib.request.urlopen(req, timeout=60, context=ctx) as response:
                    img_data = response.read()
                
                img_b64 = base64.b64encode(img_data).decode()
                image_data = f"data:image/jpeg;base64,{img_b64}"
                
                print(f"  ✅ FLUX done! ({len(img_data)} bytes)")
                
                # Apply face swap if child photo provided
                if child_photo:
                    print(f"  👤 Applying face swap...")
                    face_swapped = self.apply_fal_face_swap(image_data, child_photo)
                    if face_swapped:
                        print(f"  ✅ Child's face added to image!")
                        return face_swapped
                    else:
                        print(f"  ⚠️ Face swap failed, using original FLUX image")
                
                return image_data
            
            raise Exception("No output from FLUX")
            
        except Exception as e:
            print(f"  ⚠️ Image generation error: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
            
            # Fallback: Regular FLUX without face reference
            handler = fal_client.submit(
                "fal-ai/flux/dev",
                arguments={
                    "prompt": full_prompt,
                    "image_size": "landscape_4_3",
                    "num_inference_steps": 28,
                    "guidance_scale": 3.5,
                    "num_images": 1,
                    "enable_safety_checker": False
                }
            )
            
            print(f"  ⏳ Waiting for FLUX...")
            
            result = handler.get()
            
            if result and 'images' in result and len(result['images']) > 0:
                output_url = result['images'][0]['url']
                
                # Download
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                
                req = urllib.request.Request(
                    output_url,
                    headers={'User-Agent': 'Mozilla/5.0'}
                )
                
                with urllib.request.urlopen(req, timeout=60, context=ctx) as response:
                    img_data = response.read()
                
                img_b64 = base64.b64encode(img_data).decode()
                print(f"  ✅ FLUX done! ({len(img_data)} bytes)")
                return f"data:image/jpeg;base64,{img_b64}"
            
            raise Exception("No output from FLUX")
            
        except Exception as e:
            print(f"  ⚠️ FLUX error: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def generate_image_leonardo(self, prompt, character_reference=None):
        """יוצר תמונה עם Leonardo"""
        try:
            if not LEONARDO_API_KEY:
                raise Exception('Leonardo API key missing')
            
            if character_reference:
                print(f"  🎨 Leonardo (with character reference)...")
            else:
                print(f"  🎨 Leonardo...")
            
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            # Translate Hebrew to English if needed
            if any(ord(c) > 127 for c in prompt):  # Contains non-ASCII (Hebrew)
                prompt = self.translate_to_english(prompt)
            
            # Balanced prompt - clear facial features for face swap while maintaining illustration style
            full_prompt = f"{prompt}, illustrated children's book style, character with clear visible face and distinct facial features, expressive friendly eyes, recognizable human-like face, colorful vibrant illustration, warm and inviting, professional children's book art, digital illustration"
            
            negative_prompt = "no face, hidden face, side view, back view, abstract, overly simplified, stick figure, blurry, distorted, scary, dark, photorealistic, realistic photo"
            
            gen_data = {
                "prompt": full_prompt,
                "negative_prompt": negative_prompt,
                "modelId": "6bef9f1b-29cb-40c7-b9df-32b51c1f67d3",
                "width": 1024,
                "height": 1024,
                "num_images": 1,
                "seed": 123456789,
                "num_inference_steps": 30,  # ← Balanced detail
                "guidance_scale": 7.5,  # ← Balanced adherence
                "presetStyle": "ILLUSTRATION"
            }
            
            headers = {
                'Authorization': f'Bearer {LEONARDO_API_KEY}',
                'Content-Type': 'application/json'
            }
            
            req = urllib.request.Request(
                'https://cloud.leonardo.ai/api/rest/v1/generations',
                data=json.dumps(gen_data).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=30, context=ctx) as response:
                result = json.loads(response.read().decode('utf-8'))
                gen_id = result['sdGenerationJob']['generationId']
            
            # Wait for completion
            for _ in range(60):
                time.sleep(1)
                
                check_req = urllib.request.Request(
                    f'https://cloud.leonardo.ai/api/rest/v1/generations/{gen_id}',
                    headers=headers
                )
                
                with urllib.request.urlopen(check_req, timeout=30, context=ctx) as check_resp:
                    check_result = json.loads(check_resp.read().decode('utf-8'))
                    
                    if check_result['generations_by_pk']['status'] == 'COMPLETE':
                        img_url = check_result['generations_by_pk']['generated_images'][0]['url']
                        
                        # Download
                        img_req = urllib.request.Request(img_url, headers={'User-Agent': 'Mozilla/5.0'})
                        with urllib.request.urlopen(img_req, timeout=60, context=ctx) as img_resp:
                            img_data = img_resp.read()
                        
                        img_b64 = base64.b64encode(img_data).decode()
                        print(f"  ✅ Done ({len(img_data)} bytes)")
                        
                        return f"data:image/jpeg;base64,{img_b64}"
            
            raise Exception("Timeout")
            
        except Exception as e:
            print(f"  ⚠️  Leonardo error: {str(e)}")
            return None
    
    def generate_image_pollinations(self, prompt):
        """יוצר תמונה עם Pollinations"""
        try:
            import urllib.parse
            
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            full_prompt = f"{prompt}, children's book illustration, colorful"
            encoded = urllib.parse.quote(full_prompt)
            url = f"https://image.pollinations.ai/prompt/{encoded}?width=1024&height=1024&nologo=true"
            
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            
            with urllib.request.urlopen(req, timeout=90, context=ctx) as response:
                img_data = response.read()
            
            img_b64 = base64.b64encode(img_data).decode()
            return f"data:image/jpeg;base64,{img_b64}"
            
        except Exception as e:
            print(f"  ⚠️  Pollinations error: {str(e)}")
            return None
    
    def generate_with_trained_model(self, prompt, model_id):
        """יוצר תמונה עם המודל המאומן!"""
        try:
            if not REPLICATE_API_TOKEN:
                raise Exception('Replicate API token missing')
            
            print(f"  🤖 Using trained model...")
            
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            # Enhanced prompt for children's books
            full_prompt = f"{prompt}, children's book illustration style, colorful, friendly, warm and inviting, storybook art, high quality"
            
            prediction_data = {
                "version": model_id,
                "input": {
                    "prompt": full_prompt,
                    "num_outputs": 1,
                    "aspect_ratio": "1:1",
                    "output_format": "jpg",
                    "output_quality": 90
                }
            }
            
            headers = {
                'Authorization': f'Token {REPLICATE_API_TOKEN}',
                'Content-Type': 'application/json'
            }
            
            req = urllib.request.Request(
                'https://api.replicate.com/v1/predictions',
                data=json.dumps(prediction_data).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=30, context=ctx) as response:
                result = json.loads(response.read().decode('utf-8'))
                prediction_id = result['id']
            
            # Wait for completion
            for _ in range(60):
                time.sleep(2)
                
                check_req = urllib.request.Request(
                    f'https://api.replicate.com/v1/predictions/{prediction_id}',
                    headers=headers
                )
                
                with urllib.request.urlopen(check_req, timeout=30, context=ctx) as check_resp:
                    check_result = json.loads(check_resp.read().decode('utf-8'))
                    
                    if check_result['status'] == 'succeeded':
                        output_url = check_result['output'][0] if isinstance(check_result['output'], list) else check_result['output']
                        
                        # Download image
                        img_req = urllib.request.Request(output_url, headers={'User-Agent': 'Mozilla/5.0'})
                        with urllib.request.urlopen(img_req, timeout=60, context=ctx) as img_resp:
                            img_data = img_resp.read()
                        
                        img_b64 = base64.b64encode(img_data).decode()
                        print(f"  ✅ Image with trained model received!")
                        
                        return f"data:image/jpeg;base64,{img_b64}"
                    
                    elif check_result['status'] == 'failed':
                        raise Exception(f"Prediction failed: {check_result.get('error')}")
            
            raise Exception("Timeout waiting for trained model")
            
        except Exception as e:
            print(f"  ⚠️ Trained model error: {str(e)}")
            # Fallback to regular generation
            print(f"  ⚠️ Falling back to Leonardo...")
            return self.generate_image_leonardo(prompt)
    
    def apply_face_swap(self, target_image_b64, source_face_b64):
        """החלפת פנים עם Replicate"""
        try:
            if not REPLICATE_API_TOKEN:
                return None
            
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            swap_data = {
                "version": "278a81e7ebb22db98bcba54de985d22cc1abeead2754eb1f2af717247be69b34",
                "input": {
                    "target_image": target_image_b64,
                    "swap_image": source_face_b64
                }
            }
            
            headers = {
                'Authorization': f'Token {REPLICATE_API_TOKEN}',
                'Content-Type': 'application/json'
            }
            
            req = urllib.request.Request(
                'https://api.replicate.com/v1/predictions',
                data=json.dumps(swap_data).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=30, context=ctx) as response:
                result = json.loads(response.read().decode('utf-8'))
                pred_id = result['id']
            
            # Wait for result
            for _ in range(60):
                time.sleep(1)
                
                check_req = urllib.request.Request(
                    f'https://api.replicate.com/v1/predictions/{pred_id}',
                    headers=headers
                )
                
                with urllib.request.urlopen(check_req, timeout=30, context=ctx) as check_resp:
                    check_result = json.loads(check_resp.read().decode('utf-8'))
                    
                    if check_result['status'] == 'succeeded':
                        output_url = check_result['output']
                        
                        # Download
                        img_req = urllib.request.Request(output_url, headers={'User-Agent': 'Mozilla/5.0'})
                        with urllib.request.urlopen(img_req, timeout=60, context=ctx) as img_resp:
                            img_data = img_resp.read()
                        
                        img_b64 = base64.b64encode(img_data).decode()
                        return f"data:image/jpeg;base64,{img_b64}"
                    
                    elif check_result['status'] == 'failed':
                        return None
            
            return None
            
        except Exception as e:
            print(f"  ⚠️  Face swap error: {str(e)}")
            return None
    
    def build_story_prompt(self, data):
        """בונה prompt ל-Claude"""
        theme_names = {
            'animals': 'חיות וטבע',
            'family': 'משפחה ואהבה',
            'space': 'חלל וכוכבים',
            'magic': 'קסם ופנטזיה'
        }
        
        style_names = {
            'funny': 'מצחיק',
            'educational': 'חינוכי'
        }
        
        # Full book - 8 pages for all ages (testing longer books)
        pages_by_age = {
            '0-2': '8',
            '3-5': '8',
            '6-8': '8',
            '9-12': '10'
        }
        
        pages = pages_by_age.get(data.get('childAge', '3-5'), '1')
        theme = theme_names.get(data.get('theme', ''), 'הרפתקאות')
        style = style_names.get(data.get('style', ''), 'מצחיק')
        
        # 🎯 NEW: בדיקה אם משתמשים ב-LoRA או PuLID - אם כן, נשנה את הוראות התמונות
        use_lora = bool(data.get('use_lora') and data.get('trigger_word'))
        use_pulid = bool(data.get('reference_url'))  # 🆕 PuLID flow
        use_identity_model = use_lora or use_pulid  # שניהם דורשים Character Bible
        
        prompt = f"""צור סיפור ילדים בעברית:

שם: {data.get('childName', 'ילד')}
גיל: {data.get('childAge', '3-5')}
מגדר: {'בת' if data.get('childGender') == 'girl' else 'בן'}
נושא: {theme}
סגנון: {style}
אורך: {pages} עמודים
"""
        
        if data.get('customInput'):
            prompt += f"פרטים: {data['customInput']}\n"
        
        # 🎯 שתי גרסאות שונות של הוראות תיאור התמונה - תלוי אם יש LoRA
        if use_identity_model:
            # 🎓 גרסה ל-LoRA / PuLID: Character Bible + הוראות מחמירות לדמות יחידה
            prompt += """
חשוב מאוד! הוראות לכתיבת הסיפור:

📖 שלב ראשון - Character Bible (מילון דמויות):
לפני העמודים, צור מילון של כל הדמויות (מלבד הילד הראשי).
לכל דמות נוספת (חבר, חיה, יצור) - תן תיאור באנגלית קבוע ומפורט שיופיע בכל הספר.

⚠️⚠️ התיאור חייב להיות מאוד ספציפי - זו הסיבה #1 לחוסר אחידות!
חובה שכל תיאור חיה יכלול את 5 המרכיבים האלה, בסדר הזה:
1. גזע/מין מדויק - חובה! בלי גזע הכלב ייראה שונה לגמרי בכל עמוד.
   (golden retriever / chocolate labrador / beagle / cocker spaniel)
   ❌ אסור "dog" / "puppy" כללי - חייב גזע אמיתי.
   🐘 לחיות אקזוטיות: ציין את המין המדויק -
   "an African elephant" (אפריקאי - אוזניים גדולות, חיוורות יותר) או
   "an Asian elephant" (אסיאתי - אוזניים קטנות, גוף כהה יותר) -
   אחד מהם בלבד, ולעולם לא לערבב! בחר אחד וחזור עליו בכל עמוד.
2. צבע פרווה/עור מדויק (chocolate brown / golden / grey)
3. גודל (small / medium-sized / large / huge)
4. אורך וסוג פרווה/עור (short smooth coat / long fluffy coat / thick grey skin)
   ⚠️ קריטי! אם לא תציין - החיה תקבל מראה שונה בכל עמוד.
5. מאפיינים ייחודיים קבועים (floppy ears, blue collar, white tusks)
   ⚠️ אסור להזכיר סימני קישוט (פרחים בראש, צבעים כתומים על האוזניים, ורוד)
   אלא אם הם חלק קבוע של החיה. אחרת ייווצרו סימני קישוט שונים בכל עמוד!

דוגמה טובה (כלב): "a medium-sized chocolate labrador retriever, 
short smooth chocolate-brown coat, floppy ears, dark brown eyes, 
a blue collar with a gold tag"
דוגמה טובה (פיל): "a large adult African elephant, thick grey skin,
big wide flat ears, two short white tusks, long curling trunk,
NO decorative markings on ears, plain natural grey color"
דוגמה טובה (קוף): "a small brown spider monkey, fluffy brown fur,
long curling tail, small round monkey face with dark eyes,
animal monkey appearance (NOT human face), pink animal nose"
דוגמה רעה: "a small brown dog with floppy ears" 
(אין גזע! אין סוג פרווה! - ייצא כלב אחר בכל עמוד!)
דוגמה רעה: "a friendly elephant" 
(לא ברור איזה סוג פיל - יצא שונה בכל עמוד!)

🔒 כלל ברזל: ברגע שבחרת גזע + צבע + סוג פרווה לדמות - 
הם נעולים. אסור לשנות מילה. אותו תיאור מדויק חוזר בכל עמוד.

🐒 קוף, חיה דמוית-אדם: זהירות מיוחדת! קוף הוא חיה, לא אדם.
התיאור חייב להדגיש: "animal monkey appearance, animal face, NOT human face,
fluffy fur body, not wearing clothes". אחרת המודל עלול לצייר ילד-קוף.

🚫 כללים קריטיים:
1. אל תתאר את הילד הראשי בכלל - יש לו מודל מאומן!
2. דמויות אחרות חייבות להיות בעלות תיאור באנגלית מפורט וספציפי
3. לכל סצנה - בחר אם הילד לבד או עם דמות אחת אחרת (לא יותר!)
4. חיות לא לובשות בגדים! אל תזכיר ביגוד עבור חיות.

🔑 כלל זהב - דמויות בעלות שם:
אם דמות יש לה שם (למשל "פיצי הפיל", "פליק הכלב", "סבא מיכה", "סבתא רמית") -
בכל עמוד שהיא מופיעה, ה-illustration חייב לכלול תיאור מלא שלה!

🧓 חשוב במיוחד - בני אדם בעלי שם (סבא, סבתא, אמא, אבא, חברים):
חובה להכניס אותם ל-Character Bible עם תיאור מפורט וקבוע:
- סבא: "an elderly man, short grey hair, white beard, glasses,
  warm friendly face, green shirt"
- סבתא: "an elderly woman, short white wavy hair, kind gentle face, apron"
התיאור חייב להיות זהה בכל עמוד - אחרת סבא ייראה אדם אחר בכל עמוד!

❌ טעות נפוצה (בני אדם):
   text="סבא מיכה צוחק" / illustration="grandfather laughing"  ✗
   (כללי מדי - סבא ייראה שונה בכל עמוד!)
✅ נכון:
   Character Bible: "סבא מיכה" = "an elderly man with short grey hair
   and white beard, glasses, warm smile"
   ובכל עמוד שמופיע סבא - משתמשים בתיאור המלא הזה.

❌ טעות נפוצה (חיות):
   text="פיצי חיבק את דולב" / illustration="pitzi hugging child"  ✗
✅ נכון: illustration="the elephant hugging the child with its trunk"

📌 חוק: ב-illustration תמיד תכתוב תיאור מלא (elderly man with grey beard /
   golden retriever dog), אף פעם לא רק שם פרטי (סבא מיכה / פליק).

🚨 מניעת שכפול הילד:
אם בעמוד מופיעים הילד + דמויות נוספות (סבא, חבר) - ודא ש-illustration
מתאר את הילד פעם אחת בלבד. אל תכתוב "children" ברבים. תמיד "the child"
(יחיד) + הדמויות הנוספות בנפרד.

⭐ הכלל הכי חשוב - סנכרון טקסט-תמונה:
כל יצור, חיה, אובייקט או אלמנט שמוזכר ב-text (העברית)
חייב להופיע גם ב-illustration (האנגלית)!

דוגמה:
❌ טעות: text="הפיל חיבק את דולב בחדק" / illustration="hugging in jungle"
   (אין פיל בתיאור! התמונה תצא בלי פיל!)
✅ נכון: text="הפיל חיבק את דולב בחדק" / illustration="a large grey elephant 
   wrapping its trunk around the child, jungle background"

לפני שאתה כותב illustration - עבור על ה-text ושאל:
"אילו דברים מוזכרים? פיל? עץ? כדור? כולם חייבים להיות ב-illustration!"

⚠️ זהירות עם איברי גוף של חיות - תרגם נכון לאנגלית:
- חדק של פיל = "elephant trunk" (לא snake! לא נחש!)
- זנב = "tail",  כנף = "wing",  טלף = "hoof",  קרן = "horn"
- תמיד תכתוב את שם החיה במפורש: "elephant", "dog", "lion"
דוגמה: "הפיל הרים את דולב בחדק" → "an elephant lifting the child with its trunk"
(שים לב: trunk, ולא snake!)

📝 מבנה הסיפור:
- text (עברית): טקסט מתאים לגיל
- illustration (אנגלית): description שכולל את כל האלמנטים מהטקסט (15-25 words)

⚠️ כללים לתיאור תמונה:
✓ אם רק הילד בסצנה: "alone, [scene with all objects], medium shot"
✓ אם יש דמות/חיה: "with [full description], [scene with all objects]"
✗ אל תתאר את הילד: "boy with brown hair", "wearing blue" - אסור!
✗ אל תכתוב "another child" / "second kid" - גורם לשכפול פנים!
✗ אל תשכח אף יצור/אובייקט שמוזכר בטקסט!

📏 סוג צילום - השתמש ב-"medium shot" ברוב העמודים:
- "medium shot" - הילד נראה מהמותניים ומעלה (מומלץ ברירת מחדל)
- "wide shot" - סצנה מלאה (טוב לעמודי פתיחה/סיום)
- הימנע מ-"close-up" קיצוני - זה גורם לסגנון לא עקבי בין עמודים

✅ דוגמאות טובות:
   "alone, joyful in colorful zoo with lions and giraffes, medium shot, sunny day"
   "with a large grey elephant lifting the child with its trunk, jungle, wide shot"
   "alone, holding a red balloon, reaching toward a yellow butterfly, green park, medium shot"

❌ דוגמאות רעות:
   "with another child" → גורם לכפילות פנים!
   "playing happily" → איפה הפיל/הכלב שמוזכר בטקסט?!
   "A boy wearing green" → תיאור מיותר ואסור של הילד

פורמט JSON מדויק:
{
  "characters": [
    {
      "name": "פליק",
      "english_description": "a medium-sized chocolate labrador retriever, short smooth chocolate-brown coat, floppy ears, dark brown eyes, a blue collar with a gold tag",
      "type": "dog"
    }
  ],
  "pages": [
    {
      "text": "הטקסט בעברית...",
      "illustration": "alone, playing in colorful zoo with lions, joyful, close-up shot",
      "characters_in_scene": []
    },
    {
      "text": "דולב פגש את פליק הכלב ליד עץ גדול...",
      "illustration": "with the dog flick beside a big oak tree, green garden, sunny afternoon",
      "characters_in_scene": ["פליק"]
    }
  ]
}

חשוב: אם characters ריק - הילד לבד בכל הסיפור (פשוט יותר ובטוח יותר).
זכור: כל מה שבטקסט - חייב להיות גם בתיאור התמונה!
"""
        else:
            # גרסה רגילה: תיאור מפורט (לFLUX רגיל)
            prompt += """
חשוב מאוד!
1. הטקסט (text) בעברית בלבד!
2. תיאור התמונה (illustration) גם בעברית!
3. תאר דמויות באופן עקבי בכל העמודים
4. דוגמה: "ילד בן 4 עם שיער קצר וחום לובש חולצה כחולה..."

פורמט JSON:
{
  "pages": [
    {
      "text": "הטקסט בעברית כאן...",
      "illustration": "ילד בן 4 עם שיער קצר חום עומד בגן חיות צבעוני..."
    }
  ]
}
"""
        return prompt
    
    def handle_test_pulid(self):
        """
        🧪 POC: בדיקת PuLID-Flux לשמירת זהות בלי אימון.
        
        מקבל: child_image (base64), prompt, start_step (0-4)
        מחזיר: image_url, time_taken, cost_estimate
        
        מטרה: לבדוק אם PuLID יכול להחליף את ה-LoRA הנוכחי שלנו.
        אם זה עובד טוב, נטמיע במקום LoRA training (שלוקח 25 דק' + $0.80).
        """
        try:
            if not HAS_REPLICATE:
                raise Exception('Replicate not configured')
            
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            child_image_b64 = data.get('child_image')  # base64 data URL
            prompt = data.get('prompt', '').strip()
            start_step = data.get('start_step', 0)  # 0-1 לסטיילים, 4 לריאליסטי
            true_cfg = data.get('true_cfg', 1.0)  # 1.0 = fake CFG (default). מעל = true CFG
            
            if not child_image_b64:
                raise Exception('Missing child_image (base64 data URL required)')
            if not prompt:
                raise Exception('Missing prompt')
            
            # 🖼️ שמירה זמנית של התמונה ל-disk (Replicate צריך URL ציבורי)
            print(f"\n🧪 PuLID POC starting")
            print(f"   prompt: {prompt[:80]}...")
            print(f"   start_step: {start_step}, true_cfg: {true_cfg}")
            
            # 🖼️ פיענוח ה-base64 ושמירה ל-Cloudinary
            import base64 as _b64
            import cloudinary.uploader
            
            # מסיר את ה-prefix אם קיים: "data:image/jpeg;base64,..."
            if ',' in child_image_b64:
                child_image_b64 = child_image_b64.split(',', 1)[1]
            
            img_bytes = _b64.b64decode(child_image_b64)
            print(f"   image size: {len(img_bytes)} bytes")
            
            # שמירה לדיסק זמני
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
                f.write(img_bytes)
                tmp_path = f.name
            
            try:
                # העלאה ל-Cloudinary
                print(f"   ☁️  Uploading reference image to Cloudinary...")
                upload_result = cloudinary.uploader.upload(
                    tmp_path,
                    folder="pulid_test",
                    public_id=f"pulid_ref_{int(time.time())}",
                    access_mode="public",
                    overwrite=True
                )
                ref_image_url = upload_result['secure_url']
                print(f"   ✅ Reference uploaded: {ref_image_url}")
                
                # 🚀 קריאה ל-PuLID-Flux ב-Replicate
                print(f"   🎨 Calling bytedance/flux-pulid...")
                start_time = time.time()
                
                # הפרמטרים הקריטיים — לפי schema של Replicate:
                # https://replicate.com/bytedance/flux-pulid/versions/8baa7ef2.../api
                input_params = {
                    "main_face_image": ref_image_url,
                    "prompt": prompt,
                    "num_steps": 20,           # quality vs speed
                    "start_step": start_step,  # 0-1 stylized, 4 realistic
                    "guidance_scale": 4,       # default
                    "true_cfg": true_cfg,
                    "width": 1024,
                    "height": 1024,
                    "max_sequence_length": 128,
                    "id_weight": 1,            # זהות חזק (default)
                    "output_format": "webp",
                    "output_quality": 90,
                    "num_outputs": 1,
                }
                
                output = replicate.run(
                    "bytedance/flux-pulid:8baa7ef2255075b46f4d91cd238c21d31181b3e6a864463f967960bb0112525b",
                    input=input_params
                )
                
                elapsed = time.time() - start_time
                print(f"   ✅ PuLID done in {elapsed:.1f}s")
                
                # output הוא list או iterator של URLs
                if hasattr(output, '__iter__') and not isinstance(output, str):
                    output_list = list(output)
                    result_url = output_list[0] if output_list else None
                else:
                    result_url = output
                
                if not result_url:
                    raise Exception('PuLID returned no image')
                
                # אם זה FileOutput object, נמיר ל-string
                if hasattr(result_url, 'url'):
                    result_url = result_url.url
                
                print(f"   🖼️  Result: {result_url}")
                
                self.send_json_response({
                    'success': True,
                    'image_url': str(result_url),
                    'reference_url': ref_image_url,  # לbדיקה ויזואלית
                    'elapsed_seconds': round(elapsed, 1),
                    'cost_estimate_usd': 0.021,
                    'params_used': {
                        'start_step': start_step,
                        'true_cfg': true_cfg,
                        'prompt': prompt
                    }
                })
                
            finally:
                # ניקוי הקובץ הזמני
                try:
                    import os as _os
                    if _os.path.exists(tmp_path):
                        _os.remove(tmp_path)
                except Exception:
                    pass
        
        except Exception as e:
            print(f"   ❌ PuLID test error: {str(e)}")
            import traceback
            traceback.print_exc()
            self.send_json_response({
                'success': False,
                'error': str(e)
            }, status=500)
    
    # ═══════════════════════════════════════════════════════════════════
    # 🆕 PuLID FLOW — 2A: שמירת תמונת רפרנס + יצירת 3 וריאציות סגנון
    # ═══════════════════════════════════════════════════════════════════
    
    def handle_upload_reference(self):
        """
        🆕 PuLID: מעלה תמונת רפרנס יחידה ל-Cloudinary ומחזיר URL ציבורי.
        
        הזרימה: ההורה בוחר 1-3 תמונות. בשבילה הראשית הוא בוחר את
        הטובה ביותר. רק היא נשמרת בענן ומשמשת לכל יצירת תמונה.
        
        מקבל: { child_name: str, child_image: base64_data_url }
        מחזיר: { success: bool, reference_url: str }
        """
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            child_name = data.get('child_name', 'child').strip()
            child_image_b64 = data.get('child_image')
            
            if not child_image_b64:
                raise Exception('Missing child_image (base64 data URL required)')
            
            # ניקוי שם — לשמירה ב-Cloudinary public_id
            safe_name = safe_slug(child_name)
            
            print(f"\n📤 PuLID upload-reference for: {child_name}")
            
            # פיענוח base64 ושמירה לקובץ זמני
            import base64 as _b64
            import tempfile
            import cloudinary.uploader
            
            if ',' in child_image_b64:
                child_image_b64 = child_image_b64.split(',', 1)[1]
            
            img_bytes = _b64.b64decode(child_image_b64)
            print(f"   image size: {len(img_bytes)} bytes")
            
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as f:
                f.write(img_bytes)
                tmp_path = f.name
            
            try:
                # העלאה ל-Cloudinary
                print(f"   ☁️  Uploading to Cloudinary...")
                upload_result = cloudinary.uploader.upload(
                    tmp_path,
                    folder="pulid_references",
                    public_id=f"pulid_{safe_name}_{int(time.time())}",
                    access_mode="public",
                    overwrite=True
                )
                ref_url = upload_result['secure_url']
                print(f"   ✅ Uploaded: {ref_url}")
                
                # 🆕 ניתוח מראה הילד עם Claude Vision
                # זה רץ פעם אחת בלבד פר תמונה, ויעוגן בכל פרומפט של הספר
                # (קריטי לעקביות צבע עיניים שלפעמים נשבר ב-PuLID)
                appearance = self.analyze_child_appearance(ref_url)
                
                self.send_json_response({
                    'success': True,
                    'reference_url': ref_url,
                    'child_name': child_name,
                    'appearance': appearance,  # 🆕 ההורה / ה-frontend יראו מה זוהה
                })
            finally:
                try:
                    import os as _os
                    if _os.path.exists(tmp_path):
                        _os.remove(tmp_path)
                except Exception:
                    pass
        
        except Exception as e:
            print(f"   ❌ upload-reference error: {str(e)}")
            import traceback
            traceback.print_exc()
            self.send_json_response({
                'success': False,
                'error': str(e)
            }, status=500)
    
    def handle_preview_options_pulid(self):
        """
        🆕 PuLID: יוצר 3 וריאציות סגנון של הילד.
        
        ההורה כבר בחר תמונת רפרנס (נשמרה ב-Cloudinary).
        עכשיו אנחנו יוצרים 3 וריאציות כדי שיבחר את הסגנון המועדף.
        
        מקבל: { child_name, reference_url, child_gender }
        מחזיר: { success, options: [ { style, seed, image_url, label } ] }
        """
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            child_name = data.get('child_name', '').strip()
            reference_url = data.get('reference_url', '').strip()
            child_gender = data.get('child_gender', 'boy')
            appearance = data.get('appearance')  # 🆕 מ-Claude Vision, מה-frontend
            
            if not reference_url:
                raise Exception('Missing reference_url (upload reference first)')
            
            print(f"\n🎨 PuLID preview-options for: {child_name}")
            print(f"   reference: {reference_url[:80]}...")
            print(f"   gender: {child_gender}")
            if appearance:
                print(f"   ✨ appearance: {appearance}")
            
            # סצנה נקייה — לזיהוי מהיר של ההורה
            # 🎯 הסתכלות לצדדים מעט עוזרת לאיורים להיראות פחות סטטיים מצילום
            clean_scene = (
                "standing in a simple soft pastel room, "
                "warm cheerful expression, looking towards the viewer with a smile, "
                "plain clean background"
            )
            
            # 🎨 4 וריאציות לבדיקה: 2 איורים + 3D pixar + ריאליסטי
            # 🔬 25/5: PuLID חזק ב-start_step=0 לאיורים
            # 🔬 30/5: בודקים שוב ריאליסטי כי המוצר צריך זאת
            import random
            variations = [
                {
                    'style': 'classic_illustration',
                    'label': 'classic_illustration',
                    'seed': random.randint(1, 999999),
                    'start_step': 0,
                },
                {
                    'style': 'soft_illustration',
                    'label': 'soft_illustration',
                    'seed': random.randint(1, 999999),
                    'start_step': 0,
                },
                {
                    'style': 'pixar_3d',
                    'label': 'pixar_3d',
                    'seed': random.randint(1, 999999),
                    'start_step': 2,
                },
                {
                    'style': 'warm_realistic',
                    'label': 'warm_realistic',
                    'seed': random.randint(1, 999999),
                    'start_step': 4,
                },
            ]
            
            print(f"   variations: {[(v['style'], v['start_step']) for v in variations]}")
            
            # יצירת 4 התמונות במקביל
            import threading
            results = [None, None, None, None]
            errors = [None, None, None, None]
            
            def generate_one(index, variation):
                try:
                    print(f"   🖼️  Option {index+1}/4 (style={variation['style']}, seed={variation['seed']})...")
                    img = self.generate_image_with_pulid(
                        reference_url=reference_url,
                        prompt=clean_scene,
                        style_name=variation['style'],
                        seed=variation['seed'],
                        start_step=variation['start_step'],
                        child_gender=child_gender,
                        appearance=appearance,  # 🆕 קריטי לעקביות עיניים בכל ה-4
                    )
                    if img:
                        results[index] = {
                            'image': img,
                            'seed': variation['seed'],
                            'style': variation['style'],
                            'label': variation['label'],
                            'start_step': variation['start_step'],
                        }
                        print(f"   ✅ Option {index+1} done")
                    else:
                        errors[index] = 'returned None'
                        print(f"   ❌ Option {index+1} returned None")
                except Exception as e:
                    errors[index] = str(e)
                    print(f"   ❌ Option {index+1} error: {e}")
            
            threads = []
            for i, v in enumerate(variations):
                t = threading.Thread(target=generate_one, args=(i, v))
                t.start()
                threads.append(t)
            for t in threads:
                t.join()
            
            options = [r for r in results if r and r.get('image')]
            print(f"   📊 Completed: {len(options)}/4 successful")
            
            if not options:
                # זיהוי שגיאת rate limit / יתרה
                err_blob = ' | '.join([e for e in errors if e]) or 'unknown'
                if '429' in err_blob or 'rate' in err_blob.lower():
                    raise Exception('Rate limit ב-Replicate. בדוק את היתרה (auto-reload < $5).')
                raise Exception(f'Failed to generate any preview options. Errors: {err_blob}')
            
            self.send_json_response({
                'success': True,
                'options': options,
                'child_name': child_name,
                'reference_url': reference_url,
            })
        
        except Exception as e:
            print(f"   ❌ preview-options-pulid error: {str(e)}")
            import traceback
            traceback.print_exc()
            self.send_json_response({
                'success': False,
                'error': str(e)
            }, status=500)
    
    # ═══════════════════════════════════════════════════════════════════
    # 🆕 ASYNC BOOK GENERATION — STEP 2B
    # 
    # הזרימה הסינכרונית של handle_generate_story אורכת 2-3 דקות.
    # Cloudflare / Railway proxy חותכים את החיבור אחרי ~90 שניות.
    # התוצאה: הדפדפן מקבל "upstream error" אבל השרת ממשיך לרוץ.
    # 
    # הפתרון: זרימה אסינכרונית
    #   POST /api/start-book-generation → מחזיר מיד job_id, יוצר ברקע
    #   GET  /api/book-status/<job_id>  → polling כל ~5s לבדיקת התקדמות
    # 
    # מצב ה-job נשמר ב-/tmp/books/<job_id>.json:
    #   { status, progress, total_pages, story_data?, error? }
    # ═══════════════════════════════════════════════════════════════════
    
    def handle_start_book_generation(self):
        """
        🆕 מתחיל יצירת ספר ב-thread נפרד, מחזיר מיד job_id.
        
        מקבל: אותם פרמטרים כמו /api/generate-story
        מחזיר: { success: bool, job_id: str }
        """
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))
            
            # יצירת job_id ייחודי
            import uuid
            import os as _os
            job_id = f"book_{int(time.time())}_{uuid.uuid4().hex[:8]}"
            
            # תיקיית עבודה
            books_dir = '/tmp/books'
            _os.makedirs(books_dir, exist_ok=True)
            job_path = f"{books_dir}/{job_id}.json"
            
            # שמירת מצב התחלתי
            initial_state = {
                'status': 'pending',
                'progress': 0,
                'total_pages': 0,
                'message': 'מתחיל לעבוד...',
                'created_at': time.time(),
            }
            with open(job_path, 'w', encoding='utf-8') as f:
                json.dump(initial_state, f, ensure_ascii=False)
            
            print(f"\n📚 ASYNC BOOK START: {job_id}")
            print(f"   request: child={request_data.get('childName')}, "
                  f"theme={request_data.get('theme')}, "
                  f"use_pulid={bool(request_data.get('reference_url'))}")
            
            # הפעלת thread שיעשה את כל העבודה
            import threading
            
            def background_work():
                try:
                    # עדכון: התחלנו לעבוד על הסיפור
                    self._update_book_status(job_id, {
                        'status': 'in_progress',
                        'progress': 0,
                        'total_pages': 0,
                        'message': 'כותב את הסיפור...',
                    })
                    
                    print(f"   📝 [{job_id}] Step 1: Generating story...")
                    story_data = self.create_story_with_claude(request_data)
                    
                    if not story_data or not story_data.get('pages'):
                        raise Exception('Story generation failed (no pages)')
                    
                    total = len(story_data['pages'])
                    self._update_book_status(job_id, {
                        'status': 'in_progress',
                        'progress': 0,
                        'total_pages': total,
                        'message': f'הסיפור מוכן! יוצר {total} תמונות...',
                    })
                    
                    # יצירת תמונות עם callback להתקדמות
                    print(f"   🎨 [{job_id}] Step 2: Generating {total} images...")
                    
                    # נקרא ל-add_images_to_story אבל עם עדכון התקדמות אחרי כל עמוד
                    story_data = self._add_images_with_progress(
                        story_data,
                        request_data,
                        job_id
                    )
                    
                    # שמירת תוצאה סופית
                    self._update_book_status(job_id, {
                        'status': 'complete',
                        'progress': total,
                        'total_pages': total,
                        'message': 'הספר מוכן!',
                        'story_data': story_data,
                    })
                    print(f"   ✅ [{job_id}] Book complete!")
                
                except Exception as e:
                    print(f"   ❌ [{job_id}] Background work failed: {e}")
                    import traceback
                    traceback.print_exc()
                    self._update_book_status(job_id, {
                        'status': 'error',
                        'error': str(e),
                        'message': f'שגיאה: {str(e)}',
                    })
            
            thread = threading.Thread(target=background_work, daemon=True)
            thread.start()
            
            # החזרת job_id מיד
            self.send_json_response({
                'success': True,
                'job_id': job_id,
                'message': 'יצירת הספר התחילה ברקע',
            })
        
        except Exception as e:
            print(f"   ❌ start-book-generation error: {str(e)}")
            import traceback
            traceback.print_exc()
            self.send_json_response({
                'success': False,
                'error': str(e)
            }, status=500)
    
    def handle_book_status(self, job_id):
        """
        🆕 מחזיר את הסטטוס הנוכחי של יצירת ספר.
        
        מחזיר: { success, status, progress, total_pages, message, story_data?, error? }
        """
        try:
            # ניקוי שם — סנט בסיסי
            if not job_id or '/' in job_id or '..' in job_id:
                raise Exception('Invalid job_id')
            
            job_path = f"/tmp/books/{job_id}.json"
            
            import os as _os
            if not _os.path.exists(job_path):
                self.send_json_response({
                    'success': False,
                    'error': 'Job not found (אולי השרת התאתחל מחדש)',
                }, status=404)
                return
            
            with open(job_path, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            # החזרת המצב
            response = {'success': True, **state}
            self.send_json_response(response)
        
        except Exception as e:
            print(f"   ❌ book-status error: {str(e)}")
            self.send_json_response({
                'success': False,
                'error': str(e)
            }, status=500)
    
    def _update_book_status(self, job_id, updates):
        """עוזר: עדכון אטומי של מצב job ב-tmp."""
        try:
            job_path = f"/tmp/books/{job_id}.json"
            import os as _os
            current = {}
            if _os.path.exists(job_path):
                try:
                    with open(job_path, 'r', encoding='utf-8') as f:
                        current = json.load(f)
                except Exception:
                    current = {}
            current.update(updates)
            current['updated_at'] = time.time()
            tmp_path = job_path + '.tmp'
            with open(tmp_path, 'w', encoding='utf-8') as f:
                json.dump(current, f, ensure_ascii=False)
            _os.replace(tmp_path, job_path)
        except Exception as e:
            print(f"   ⚠️  _update_book_status failed: {e}")
    
    def _add_images_with_progress(self, story_data, request_data, job_id):
        """
        🆕 עוטף את add_images_to_story עם עדכוני התקדמות.
        
        במקום לקרוא ישירות ל-add_images_to_story (שלא יודע על job_id),
        אנחנו עושים כאן את הלולאה ומעדכנים אחרי כל עמוד.
        
        זה משכפל קצת קוד מ-add_images_to_story, אבל זה מאפשר
        progress events בלי לשנות את הפונקציה המקורית.
        """
        # פרמטרים מהבקשה
        reference_url = request_data.get('reference_url')
        use_pulid = bool(reference_url)
        
        lora_url = request_data.get('lora_url')
        trigger_word = request_data.get('trigger_word')
        lora_version = request_data.get('lora_version')
        use_lora = (not use_pulid) and request_data.get('use_lora', False) and lora_url and trigger_word
        
        child_photo = request_data.get('childPhoto')
        chosen_seed = request_data.get('chosen_seed')
        chosen_lora_scale = request_data.get('chosen_lora_scale', 1.0)
        chosen_style = request_data.get('chosen_style', 'classic_illustration')
        child_gender = 'girl' if request_data.get('childGender') == 'girl' else 'boy'
        appearance = request_data.get('appearance')  # 🆕 מ-Claude Vision
        
        if appearance:
            print(f"  ✨ Using appearance anchor: {appearance}")
        
        pages = story_data.get('pages', [])
        total = len(pages)
        
        # Character Bible
        characters = story_data.get('characters', [])
        char_dict = {}
        for char in characters:
            name = char.get('name', '').strip()
            desc = char.get('english_description', '').strip()
            if name and desc:
                char_dict[name] = desc
        
        # Outfit אחיד
        consistent_outfit = None
        if use_pulid or use_lora:
            import random
            outfits = [
                "wearing a yellow t-shirt and blue jeans",
                "wearing a red striped shirt and khaki shorts",
                "wearing a green hoodie and dark blue pants",
                "wearing a white t-shirt with a pattern and beige pants",
                "wearing an orange sweater and denim shorts",
                "wearing a purple shirt and gray pants",
                "wearing a blue polo shirt and brown shorts",
            ]
            consistent_outfit = random.choice(outfits)
            print(f"  🎽 [{job_id}] Outfit: {consistent_outfit}")
            story_data['outfit'] = consistent_outfit
        
        story_data['character_bible'] = char_dict
        
        # לולאת יצירת תמונות
        for i, page in enumerate(pages):
            # עדכון התקדמות לפני יצירה
            self._update_book_status(job_id, {
                'status': 'in_progress',
                'progress': i,
                'total_pages': total,
                'message': f'יוצר תמונה {i+1} מתוך {total}...',
            })
            
            print(f"\n  🖼️  [{job_id}] Image {i+1}/{total}...")
            
            # Throttle
            if use_pulid:
                wait_seconds = 5 if i > 0 else 3
                time.sleep(wait_seconds)
            elif use_lora:
                wait_seconds = 12 if i > 0 else 8
                time.sleep(wait_seconds)
            
            try:
                # זיהוי דמויות בעמוד
                if use_pulid or use_lora:
                    illustration = page.get('illustration', '')
                    page_text = page.get('text', '')
                    chars_in_scene = page.get('characters_in_scene', [])
                    
                    detected_chars = set(chars_in_scene)
                    for char_name in char_dict.keys():
                        if char_name in page_text or char_name in illustration:
                            detected_chars.add(char_name)
                    
                    char_descriptions = [
                        char_dict[name] for name in detected_chars if name in char_dict
                    ]
                
                if use_pulid:
                    image_url = self.generate_image_with_pulid(
                        reference_url=reference_url,
                        prompt=illustration,
                        style_name=chosen_style,
                        seed=chosen_seed,
                        character_descriptions=char_descriptions,
                        outfit=consistent_outfit,
                        child_gender=child_gender,
                        appearance=appearance,  # 🆕 מ-Claude Vision
                    )
                    if not image_url and child_photo:
                        image_url = self.generate_image_flux_with_face(illustration, child_photo)
                
                elif use_lora:
                    image_url = self.generate_image_with_lora(
                        prompt=illustration,
                        lora_url=lora_url,
                        trigger_word=trigger_word,
                        lora_version=lora_version,
                        style_name=chosen_style,
                        outfit=consistent_outfit,
                        character_descriptions=char_descriptions,
                        seed=chosen_seed,
                        lora_scale=chosen_lora_scale,
                        child_gender=child_gender
                    )
                    if not image_url:
                        image_url = self.generate_image_flux_with_face(illustration, child_photo)
                else:
                    image_url = self.generate_image_flux_with_face(
                        page['illustration'], child_photo
                    )
                
                page['imageUrl'] = image_url
            
            except Exception as e:
                print(f"  ⚠️  Page {i+1} failed: {e}")
                page['imageUrl'] = None
        
        # עדכון אחרון: כולם נגמרו
        self._update_book_status(job_id, {
            'progress': total,
            'total_pages': total,
            'message': 'מסיים...',
        })
        
        return story_data
    
    def generate_image_with_pulid(
        self,
        reference_url,
        prompt,
        style_name='classic_illustration',
        seed=None,
        start_step=None,
        character_descriptions=None,
        outfit=None,
        child_gender='boy',
        appearance=None,
    ):
        """
        🆕 PuLID-Flux: יוצר תמונה יחידה עם זהות ילד מהתמונת הרפרנס.
        
        אנלוגי ל-generate_image_with_lora, אבל בלי צורך באימון.
        מבוסס על ה-POC שהוכח ב-25/5 (handle_test_pulid).
        
        Args:
            reference_url: URL ציבורי לתמונת הרפרנס (Cloudinary)
            prompt: תיאור הסצנה באנגלית
            style_name: 'classic_illustration' / 'soft_illustration' / 'pixar_3d'
            seed: לעקביות בין עמודים — אותו seed = אותה דמות
            start_step: 0 לסטיילים, 2 ל-3D, 4 לריאליסטי. None = לפי style.
            character_descriptions: רשימת תיאורי דמויות נוספות (Character Bible)
            outfit: בגדים ספציפיים (אופציונלי)
            child_gender: 'boy' / 'girl' — לפרומפט
        
        Returns:
            str: URL לתמונה שנוצרה, או None במקרה של כשל
        """
        if not HAS_REPLICATE:
            print("   ❌ Replicate not configured")
            return None
        
        # ────────────────────────────────────────────────────────────
        # 1. תרגום עברית לאנגלית (PuLID לא תומך עברית)
        # ────────────────────────────────────────────────────────────
        if any(ord(c) > 127 for c in prompt):
            prompt = self.translate_to_english(prompt)
        
        # ────────────────────────────────────────────────────────────
        # 2. הגדרת start_step אוטומטית אם לא נשלח
        # ────────────────────────────────────────────────────────────
        style_to_start_step = {
            'classic_illustration': 0,
            'soft_illustration': 0,
            'pixar_3d': 2,
            'warm_realistic': 4,  # אם בכל זאת נצטרך
        }
        if start_step is None:
            start_step = style_to_start_step.get(style_name, 0)
        
        # ────────────────────────────────────────────────────────────
        # 3. בניית פרומפט עם style anchor
        # 🎯 style anchors מעוגנים בתחילת + סוף הפרומפט
        # זה הוכח אמפירית כעובד היטב (POC 25/5)
        # ────────────────────────────────────────────────────────────
        style_anchors = {
            'classic_illustration': {
                'start': "a classic children's book illustration, ",
                'end': (
                    ", traditional storybook illustration art, "
                    "vibrant rich colors, bright cheerful palette, "
                    "clean illustration style, professional children's book art"
                ),
                'hardener': (
                    " — this is an ILLUSTRATION not a photograph, "
                    "drawn/painted art style, NOT photorealistic, NOT a real photo"
                ),
            },
            'soft_illustration': {
                'start': "a hand-drawn watercolor children's book illustration, soft painterly storybook art, ",
                'end': (
                    ", traditional watercolor painting on paper, "
                    "visible brush strokes, soft pastel washes, "
                    "delicate hand-painted illustration, "
                    "dreamy storybook art, NOT photorealistic, NOT a photograph, "
                    "artistic illustration style"
                ),
                'hardener': (
                    " — this is a WATERCOLOR ILLUSTRATION not a photograph, "
                    "painted on paper, NOT photorealistic"
                ),
            },
            'pixar_3d': {
                'start': "a 3D animated movie still in Pixar/Disney style, ",
                'end': (
                    ", 3D rendered animation, cinematic lighting, "
                    "stylized 3D character, animated movie art style, "
                    "smooth 3D textures, expressive animated face, "
                    "high quality CGI animation, NOT photorealistic, NOT a real photo"
                ),
                'hardener': (
                    " — this is a 3D ANIMATED scene, "
                    "Pixar-style render, NOT a photograph"
                ),
            },
            'warm_realistic': {
                'start': "a realistic photograph, professional portrait photography, ",
                'end': (
                    ", photorealistic, natural skin texture, realistic lighting, "
                    "shot on DSLR camera, sharp focus, lifelike, "
                    "real photograph quality, warm natural tones, "
                    "detailed facial features, authentic"
                ),
                'hardener': (
                    " — this is a REAL PHOTOGRAPH, "
                    "shot with a camera, NOT a drawing, NOT an illustration"
                ),
            },
        }
        anchor = style_anchors.get(style_name, style_anchors['classic_illustration'])
        
        # Character Bible (אם יש)
        char_part = ""
        if character_descriptions:
            char_list = ". ".join(character_descriptions)
            char_part = char_list
        
        # Outfit (אם יש)
        outfit_part = f"{outfit}" if outfit else ""
        
        # קומפוזיציה נקייה
        clean_composition = (
            "clean composition, well-framed, centered subject, "
            "full scene visible, no cropped people, no body parts at edges"
        )
        
        # 🎯 הרכבת הפרומפט הסופי:
        # [סגנון start] + [תיאור הילד מסומן] + [סצנה] + [דמויות נוספות] + [בגדים] + [סגנון end] + [hardener]
        # ה-token "id" מסמן ל-PuLID איפה הילד נמצא בסצנה
        child_token = "id"  # PuLID זיהוי הילד — דרך התמונה לא דרך הטקסט
        
        # 🆕 appearance anchor — מעוגן מיד אחרי "a boy child" כדי לחבר את
        # התכונות הפיזיות (במיוחד צבע עיניים) לזהות.
        # הגיע מ-Claude Vision שניתח את תמונת הרפרנס.
        appearance_part = f" {appearance}" if appearance else ""
        
        # 🔙 13/6: הוסר human_separator (היה: "the child has only two small human
        # ears and no animal features") וה-"human" prefix מ-"a human child".
        # שניהם גרמו לעיוות פרופורציות פנים. חזרה לפרומפט הנקי של 06-06.
        # אם feature-bleed יחזור (אוזני פיל וכו') — נטפל נקודתית.
        
        prompt_parts = [
            anchor['start'],
            f"a {child_gender} child",
            appearance_part,  # "with bright blue eyes, short brown hair, fair skin, rosy cheeks"
            ", ",
            prompt,
        ]
        if outfit_part:
            prompt_parts.append(f", wearing {outfit_part}")
        if char_part:
            prompt_parts.append(f". {char_part}")
        prompt_parts.append(f", {clean_composition}")
        prompt_parts.append(anchor['end'])
        prompt_parts.append(anchor['hardener'])
        
        full_prompt = "".join(prompt_parts)
        
        print(f"      🎨 PuLID: style={style_name}, start_step={start_step}, seed={seed}")
        if appearance:
            print(f"      ✨ appearance anchor: {appearance}")
        print(f"      📝 prompt: {full_prompt[:200]}...")
        
        # ────────────────────────────────────────────────────────────
        # 4. קריאה ל-PuLID-Flux ב-Replicate
        # ────────────────────────────────────────────────────────────
        import replicate as _replicate
        
        input_params = {
            "main_face_image": reference_url,
            "prompt": full_prompt,
            "num_steps": 20,
            "start_step": start_step,
            "guidance_scale": 4,
            "true_cfg": 1,                # 1 = fake CFG (default, מנצח לפי POC)
            "width": 1024,
            "height": 1024,
            "max_sequence_length": 128,
            "id_weight": 1,
            "output_format": "webp",
            "output_quality": 90,
            "num_outputs": 1,
        }
        if seed is not None:
            input_params["seed"] = seed
        
        try:
            start_time = time.time()
            output = _replicate.run(
                "bytedance/flux-pulid:8baa7ef2255075b46f4d91cd238c21d31181b3e6a864463f967960bb0112525b",
                input=input_params
            )
            elapsed = time.time() - start_time
            
            # output הוא list / iterator / FileOutput
            if hasattr(output, '__iter__') and not isinstance(output, str):
                output_list = list(output)
                result = output_list[0] if output_list else None
            else:
                result = output
            
            if not result:
                print(f"      ❌ PuLID returned no image")
                return None
            
            # FileOutput → URL string
            if hasattr(result, 'url'):
                result = result.url
            
            print(f"      ✅ PuLID done in {elapsed:.1f}s: {str(result)[:80]}...")
            return str(result)
        
        except Exception as e:
            err_str = str(e)
            print(f"      ❌ PuLID error: {err_str}")
            # זיהוי rate limit ל-frontend
            if '429' in err_str or 'rate' in err_str.lower():
                raise Exception(f'Rate limit: {err_str}')
            return None
    
    def handle_suggest_alternative(self):
        """מציע חלופות לטקסט"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            prompt = f"""הצע 3 חלופות:
"{data['currentText']}"

פורמט:
1. ...
2. ...
3. ...
"""
            
            claude_request = {
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 500,
                "messages": [{"role": "user", "content": prompt}]
            }
            
            headers = {
                'Content-Type': 'application/json',
                'x-api-key': CLAUDE_API_KEY,
                'anthropic-version': '2023-06-01'
            }
            
            req = urllib.request.Request(
                CLAUDE_API_URL,
                data=json.dumps(claude_request).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            with urllib.request.urlopen(req, timeout=60) as response:
                response_data = json.loads(response.read().decode('utf-8'))
                content = response_data['content'][0]['text']
                
                lines = content.strip().split('\n')
                alternatives = []
                for line in lines:
                    clean = line.strip()
                    if clean and len(clean) > 5:
                        if clean[0].isdigit() and '. ' in clean:
                            clean = clean.split('. ', 1)[1]
                        alternatives.append(clean)
                
                self.send_json_response({
                    'success': True,
                    'alternatives': alternatives[:3]
                })
                
        except Exception as e:
            self.send_json_response({'error': str(e)}, status=500)
    
    def handle_regenerate_image(self):
        """מייצר תמונה מחדש עם הנחיות מהמשתמש - תומך ב-LoRA"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            page_text = data.get('page_text', '')
            user_prompt = data.get('user_prompt', '').strip()
            child_photo = data.get('child_photo')
            
            # 🎓 LoRA parameters
            lora_url = data.get('lora_url')
            trigger_word = data.get('trigger_word')
            lora_version = data.get('lora_version')
            outfit = data.get('outfit')
            character_descriptions = data.get('character_descriptions', [])  # 🆕
            character_bible = data.get('character_bible', {})  # 🆕 מילון מלא
            use_lora = bool(lora_url and trigger_word)
            
            # 🎨 NEW: הסגנון, ה-seed וה-scale שנבחרו - לעקביות עם הספר!
            chosen_style = data.get('chosen_style', 'classic_illustration')
            chosen_seed = data.get('chosen_seed')
            chosen_lora_scale = data.get('chosen_lora_scale', 1.0)
            child_gender = 'girl' if data.get('child_gender') == 'girl' else 'boy'
            
            print(f"\n🎨 Regenerating image...")
            if use_lora:
                print(f"  🎓 Using LoRA: {trigger_word}")
                print(f"  🎨 Style: {chosen_style}, scale: {chosen_lora_scale}")
                if chosen_seed is not None:
                    print(f"  🎲 Seed: {chosen_seed}")
            if character_descriptions:
                print(f"  📖 Characters in scene: {len(character_descriptions)}")
            if user_prompt:
                print(f"  👤 User request: {user_prompt[:50]}...")
            print(f"  📖 Page text: {page_text[:80]}...")
            
            # 🎯 NEW: אם הטקסט בעברית - בקש מ-Claude להפוך אותו לתיאור תמונה
            # מעבירים גם את ה-Character Bible כדי שידע ש"פיצי" = פיל
            if any(ord(c) > 127 for c in page_text):
                print(f"  🔄 Converting Hebrew story text to image description...")
                image_description = self._story_to_image_description(page_text, character_bible)
                print(f"  📝 Image description: {image_description[:80]}...")
            else:
                image_description = page_text
            
            # Combine user prompt with image description
            if user_prompt:
                final_prompt = f"{user_prompt}, {image_description}"
            else:
                final_prompt = image_description
            
            print(f"  📝 Final prompt: {final_prompt[:100]}...")
            
            # 🎓 STRATEGY 1: Use LoRA if available (preferred!)
            if use_lora:
                image_url = self.generate_image_with_lora(
                    prompt=final_prompt,
                    lora_url=lora_url,
                    trigger_word=trigger_word,
                    lora_version=lora_version,
                    style_name=chosen_style,  # 🎨 אותו סגנון כמו הספר!
                    outfit=outfit,
                    character_descriptions=character_descriptions,  # 🆕
                    seed=chosen_seed,  # 🎲 אותו seed
                    lora_scale=chosen_lora_scale,  # 💪 אותו scale
                    child_gender=child_gender  # 🚻
                )
                
                if not image_url:
                    print(f"  ⚠️  LoRA failed, falling back to FLUX...")
                    image_url = self.generate_image_flux_with_face(final_prompt, child_photo)
            else:
                # STRATEGY 2: Fallback to FLUX + face swap
                image_url = self.generate_image_flux_with_face(final_prompt, child_photo)
            
            if not image_url:
                raise Exception("Failed to generate image")
            
            # Apply face swap only if NOT using LoRA (LoRA already includes the child)
            if not use_lora and child_photo and FAL_KEY and HAS_FAL:
                print(f"  👤 Applying Fal.ai face swap...")
                face_swapped = self.apply_fal_face_swap(image_url, child_photo)
                if face_swapped:
                    image_url = face_swapped
                    print(f"  ✅ Child added to image!")
                else:
                    print(f"  ⚠️ Face swap failed, using original image")
            
            print(f"  ✅ Image regenerated successfully!")
            
            self.send_json_response({
                'success': True,
                'imageUrl': image_url
            })
            
        except Exception as e:
            error_msg = str(e)
            print(f"  ❌ Regeneration error: {error_msg}")
            import traceback
            traceback.print_exc()
            self.send_json_response({
                'success': False,
                'error': error_msg
            }, status=500)
    
    def handle_test_face_swap(self):
        """בודק face swap עם תמונת בדיקה - מהיר!"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            child_photo = data.get('child_photo')
            child_name = data.get('child_name', 'ילד')
            
            if not child_photo:
                raise Exception('No child photo provided')
            
            print(f"\n🧪 Testing face swap for {child_name}...")
            
            # Test prompt - simple scene
            test_prompt = f"A cheerful child in a colorful playground, playing happily, sunny day"
            
            print(f"  📝 Test prompt: {test_prompt}")
            
            # Generate test image with FLUX
            image_url = self.generate_image_flux_with_face(test_prompt, child_photo)
            
            if not image_url:
                raise Exception("Failed to generate test image")
            
            print(f"  ✅ Test complete!")
            
            self.send_json_response({
                'success': True,
                'imageUrl': image_url,
                'message': 'Test image generated successfully!'
            })
            
        except Exception as e:
            error_msg = str(e)
            print(f"  ❌ Test error: {error_msg}")
            import traceback
            traceback.print_exc()
            self.send_json_response({
                'success': False,
                'error': error_msg
            }, status=500)
    
    def handle_start_lora_training(self):
        """מתחיל אימון LoRA עם Cloudinary + Replicate - גרסה מתוקנת"""
        try:
            if not HAS_REPLICATE or not REPLICATE_API_TOKEN:
                raise Exception('Replicate not configured')
            
            if not CLOUDINARY_CLOUD_NAME or not CLOUDINARY_API_KEY:
                raise Exception('Cloudinary not configured')
            
            if not REPLICATE_USERNAME:
                raise Exception('REPLICATE_USERNAME not configured in environment variables')
            
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            child_photos = data.get('child_photos', [])
            child_name_raw = data.get('child_name', '').strip()
            
            if not child_name_raw:
                raise Exception('Child name required')
            
            if len(child_photos) < 5:
                raise Exception(f'Need at least 5 photos, got {len(child_photos)}')
            
            # 🔧 FIX 1: שם בטוח ל-URL (פותר בעיית עברית בURL)
            child_slug = safe_slug(child_name_raw)
            
            print(f"\n🎓 Starting LoRA training")
            print(f"  👤 Child name (display): {child_name_raw}")
            print(f"  🔗 Child slug (API): {child_slug}")
            print(f"  📸 Photos: {len(child_photos)}")
            
            # Configure Cloudinary
            import cloudinary
            import cloudinary.uploader
            
            cloudinary.config(
                cloud_name=CLOUDINARY_CLOUD_NAME,
                api_key=CLOUDINARY_API_KEY,
                api_secret=CLOUDINARY_API_SECRET
            )
            
            # 🔧 FIX 2: trigger_word באנגלית בלבד
            # 🔬 23/5: הוסר הסיומת "_kid" — היא יצרה bias חזק לקונספט "ילד" וגרמה
            # ל-LoRA לדחוף תוצאות לכיוון איורי-ילד גם כשהפרומפט אומר אחרת.
            # סיומת ניטרלית "_subj" נותנת ל-FLUX להחליט לפי הפרומפט.
            trigger_word = f"{child_slug.replace('-', '_')}_subj"
            print(f"  🏷️  Trigger word: {trigger_word}")
            
            # Create ZIP
            import tempfile
            import zipfile
            
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, 'training_images.zip')
            
            print(f"  💾 Creating ZIP...")
            
            with zipfile.ZipFile(zip_path, 'w') as zipf:
                for i, photo_b64 in enumerate(child_photos):
                    if ',' in photo_b64:
                        photo_b64 = photo_b64.split(',')[1]
                    
                    photo_data = base64.b64decode(photo_b64)
                    
                    photo_filename = f"image_{i+1}.jpg"
                    photo_path = os.path.join(temp_dir, photo_filename)
                    
                    with open(photo_path, 'wb') as f:
                        f.write(photo_data)
                    
                    zipf.write(photo_path, photo_filename)
            
            print(f"  📦 ZIP: {os.path.getsize(zip_path)} bytes")
            
            # 🔧 FIX 4: העלאה ל-Cloudinary כקובץ ציבורי
            # type="upload" + access_mode="public" מבטיחים שReplicate יוכל להוריד
            print(f"  ☁️  Uploading to Cloudinary (public)...")
            upload_result = cloudinary.uploader.upload(
                zip_path,
                resource_type="raw",
                type="upload",
                folder="lora_training",
                public_id=f"{child_slug}_{int(time.time())}",
                access_mode="public",
                use_filename=False,
                unique_filename=False
            )
            
            zip_url = upload_result['secure_url']
            print(f"  ✅ Uploaded: {zip_url}")
            
            # 🔧 FIX 5: ודא שה-URL נגיש לפני שולח ל-Replicate
            # אם Cloudinary מחזיר 401, נכשל מהר ובהבנה
            print(f"  🔍 Verifying URL is publicly accessible...")
            try:
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                
                req = urllib.request.Request(
                    zip_url,
                    headers={'User-Agent': 'Mozilla/5.0'},
                    method='HEAD'
                )
                with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
                    if resp.status == 200:
                        print(f"  ✅ URL is publicly accessible (HTTP 200)")
                    else:
                        print(f"  ⚠️  URL returned HTTP {resp.status}")
            except urllib.error.HTTPError as he:
                if he.code == 401 or he.code == 403:
                    raise Exception(
                        f'Cloudinary URL not publicly accessible (HTTP {he.code}). '
                        f'Check Cloudinary settings: Settings → Security → '
                        f'"Restricted media types" should NOT include "raw", '
                        f'and "Resource list" delivery should be allowed.'
                    )
                else:
                    print(f"  ⚠️  HEAD check returned {he.code}, continuing anyway...")
            except Exception as verify_error:
                print(f"  ⚠️  Could not verify URL ({verify_error}), continuing anyway...")
            
            # 🔧 FIX 3: יצור את המודל ב-Replicate לפני training
            # זה הפתרון לבעיית 404 "destination does not exist"
            model_name = f"{child_slug}-lora"
            destination = f"{REPLICATE_USERNAME}/{model_name}"
            
            print(f"  📍 Destination: {destination}")
            print(f"  🏗️  Ensuring model exists at Replicate...")
            
            try:
                replicate.models.create(
                    owner=REPLICATE_USERNAME,
                    name=model_name,
                    visibility="private",
                    hardware="gpu-t4",
                    description=f"LoRA model for child book - {child_name_raw}"
                )
                print(f"  ✅ Model created: {destination}")
            except Exception as model_error:
                err_str = str(model_error).lower()
                # אם המודל כבר קיים - זה בסדר, ממשיכים
                if "already exists" in err_str or "already taken" in err_str or "422" in err_str:
                    print(f"  ℹ️  Model already exists: {destination}")
                else:
                    print(f"  ❌ Failed to create model: {model_error}")
                    raise Exception(f'Could not create Replicate model: {model_error}')
            
            # Start Replicate training
            print(f"  🎓 Starting Replicate training...")
            
            # 🎯 פרמטרים אופטימליים לפנים של ילדים:
            # - steps: 1500 (במקום 1000) - הכרחי לזיהוי פנים חזק; 1000 = under-trained
            # - lora_rank: 32 (במקום default 16) - יותר "קיבולת" ללמוד פרטים עדינים של פנים
            # - caption_dropout_rate: 0.05 - מונע overfit לרקעים/אביזרים, מתמקד בפנים
            # ⏱️  זמן אימון: ~25-30 דק' (במקום ~15); עלות: ~$0.80 (במקום ~$0.50)
            training = replicate.trainings.create(
                version="ostris/flux-dev-lora-trainer:e440909d3512c31646ee2e0c7d6f6f4923224863a6a10c494606e79fb5844497",
                input={
                    "input_images": zip_url,
                    "trigger_word": trigger_word,
                    "steps": 1500,
                    "learning_rate": 0.0004,
                    "lora_rank": 32,
                    "caption_dropout_rate": 0.05,
                    "resolution": "512,768,1024",
                    "autocaption": True
                },
                destination=destination
            )
            
            print(f"  ✅ Training started: {training.id}")
            
            # 🔥 שמירת meta לקובץ — דרוש ל-pre-warming כשהאימון מסתיים.
            # בלי זה, ב-handle_lora_status אין לנו את ה-trigger_word.
            try:
                import os as _os
                _os.makedirs('/tmp/previews', exist_ok=True)
                _meta_path = f'/tmp/previews/{training.id}.meta.json'
                with open(_meta_path, 'w', encoding='utf-8') as _f:
                    json.dump({
                        'trigger_word': trigger_word,
                        'child_name': child_name_raw,
                        'child_gender': data.get('child_gender', 'boy'),
                        'started_at': time.time()
                    }, _f, ensure_ascii=False)
                print(f"  💾 Saved training meta to {_meta_path}")
            except Exception as _e:
                print(f"  ⚠️  Could not save training meta (pre-warming disabled for this training): {_e}")
            
            self.send_json_response({
                'success': True,
                'training_id': training.id,
                'trigger_word': trigger_word,
                'destination': destination,
                'child_name': child_name_raw,
                'child_slug': child_slug,
                'estimated_time': 1500  # ~25 דק' עבור 1500 steps + rank 32
            })
            
        except Exception as e:
            error_msg = str(e)
            print(f"  ❌ Training error: {error_msg}")
            import traceback
            traceback.print_exc()
            self.send_json_response({
                'success': False,
                'error': error_msg
            }, status=500)
    
    def handle_lora_status(self, training_id):
        """בודק סטטוס אימון LoRA"""
        try:
            if not HAS_REPLICATE:
                raise Exception('Replicate not configured')
            
            print(f"  🔍 Checking LoRA training: {training_id}")
            
            training = replicate.trainings.get(training_id)
            
            response = {
                'training_id': training_id,
                'status': training.status
            }
            
            if training.status == 'succeeded':
                response['lora_url'] = training.output.get('weights')
                response['version'] = training.output.get('version')
                print(f"  ✅ Training completed!")
                
                # 🔥 PRE-WARMING: מתחיל לייצר 3 פריוויו ברקע ברגע שזיהינו succeeded.
                # ההורה כנראה לוקח לפחות עוד דקה לרענן/לפתוח את הדפדפן — מספיק לסיים.
                # פעם אחת בלבד פר training_id (ראה _prewarming_already_started).
                self._maybe_start_prewarming(
                    training_id=training_id,
                    lora_url=response['lora_url'],
                    lora_version=response['version']
                )
            elif training.status == 'failed':
                response['error'] = training.error
                print(f"  ❌ Training failed: {training.error}")
            else:
                print(f"  ⏳ Status: {training.status}")
            
            self.send_json_response(response)
            
        except Exception as e:
            print(f"  ❌ Status error: {str(e)}")
            self.send_json_response({
                'status': 'error',
                'error': str(e)
            }, status=500)
    
    def _maybe_start_prewarming(self, training_id, lora_url, lora_version):
        """🔥 מפעיל pre-warming של 3 תמונות פריוויו ברקע.
        משתמש בקובץ lock כדי לא להפעיל פעמיים. נשמור את התוצאה ב-/tmp/previews/.
        """
        import os, json, threading
        
        previews_dir = '/tmp/previews'
        os.makedirs(previews_dir, exist_ok=True)
        
        lock_path = os.path.join(previews_dir, f'{training_id}.lock')
        result_path = os.path.join(previews_dir, f'{training_id}.json')
        
        # אם התוצאה כבר קיימת — לא להתחיל שוב
        if os.path.exists(result_path):
            print(f"  🔥 Pre-warming: cached results already exist for {training_id}")
            return
        
        # אם lock כבר תפוס (יש thread רץ) — לא להתחיל שוב
        if os.path.exists(lock_path):
            print(f"  🔥 Pre-warming: already in progress for {training_id} (lock exists)")
            return
        
        # נדרשים trigger_word + child_gender — נטענים מהקובץ של start_training
        meta_path = os.path.join(previews_dir, f'{training_id}.meta.json')
        if not os.path.exists(meta_path):
            print(f"  🔥 Pre-warming SKIP: no meta file at {meta_path} (training started before this code?)")
            return
        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
        except Exception as e:
            print(f"  🔥 Pre-warming: failed to read meta: {e}")
            return
        
        trigger_word = meta.get('trigger_word')
        child_gender = meta.get('child_gender', 'boy')
        child_name = meta.get('child_name', '')
        
        if not trigger_word:
            print(f"  🔥 Pre-warming SKIP: no trigger_word in meta")
            return
        
        # יצירת lock
        try:
            with open(lock_path, 'w') as f:
                f.write(str(os.getpid()))
        except Exception as e:
            print(f"  🔥 Pre-warming: failed to create lock: {e}")
            return
        
        # רצים ברקע — לא חוסם את התגובה ל-Status
        def prewarm():
            try:
                print(f"\n🔥 PRE-WARMING starting for {training_id} ({child_name})")
                clean_scene = (
                    "standing against a simple soft pastel background, "
                    "plain clean background, happy smile, looking at viewer"
                )
                
                import random
                variations = [
                    {'seed': random.randint(1, 999999), 'lora_scale': 1.0, 'style': 'warm_realistic', 'label': 'warm_realistic'},
                    {'seed': random.randint(1, 999999), 'lora_scale': 1.0, 'style': 'classic_illustration', 'label': 'classic_illustration'},
                    {'seed': random.randint(1, 999999), 'lora_scale': 1.0, 'style': 'soft_illustration', 'label': 'soft_illustration'},
                ]
                
                results = [None, None, None]
                
                def generate_one(index, variation):
                    try:
                        img = self.generate_image_with_lora(
                            prompt=f"medium shot, {clean_scene}",
                            lora_url=lora_url,
                            trigger_word=trigger_word,
                            lora_version=lora_version,
                            style_name=variation['style'],
                            seed=variation['seed'],
                            lora_scale=variation['lora_scale'],
                            child_gender=child_gender
                        )
                        if img:
                            results[index] = {
                                'image': img,
                                'seed': variation['seed'],
                                'lora_scale': variation['lora_scale'],
                                'style': variation['style'],
                                'label': variation['label']
                            }
                    except Exception as e:
                        print(f"  🔥 Pre-warm option {index+1} failed: {e}")
                
                threads = []
                for i, v in enumerate(variations):
                    t = threading.Thread(target=generate_one, args=(i, v))
                    threads.append(t)
                    t.start()
                for t in threads:
                    t.join()
                
                options = [r for r in results if r and r.get('image')]
                if not options:
                    print(f"  🔥 Pre-warming: no successful options — aborting")
                    return
                
                # שמירה לקובץ
                with open(result_path, 'w', encoding='utf-8') as f:
                    json.dump({
                        'training_id': training_id,
                        'child_name': child_name,
                        'options': options,
                        'created_at': __import__('time').time()
                    }, f, ensure_ascii=False)
                
                print(f"  🔥 Pre-warming COMPLETE: saved {len(options)} options to {result_path}")
            
            except Exception as e:
                print(f"  🔥 Pre-warming THREAD ERROR: {e}")
                import traceback
                traceback.print_exc()
            finally:
                # שחרור lock
                try:
                    if os.path.exists(lock_path):
                        os.remove(lock_path)
                except Exception:
                    pass
        
        threading.Thread(target=prewarm, daemon=True).start()
        print(f"  🔥 Pre-warming thread spawned for {training_id}")
    
    def generate_image_with_lora(self, prompt, lora_url, trigger_word, style_name="illustration", lora_version=None, outfit=None, character_descriptions=None, seed=None, lora_scale=1.0, child_gender='boy'):
        """יוצר תמונה עם LoRA מאומן.
        
        אם lora_version קיים - משתמשים במודל המאומן ישירות (האסטרטגיה הטובה יותר!)
        אחרת - נופלים חזרה ל-ostris/flux-dev-lora (legacy)
        
        אם outfit ניתן - הילד ילבש את אותו ביגוד בכל התמונות בספר.
        אם character_descriptions ניתן - מוסיפים תיאור דמויות נלוות (כלב, חבר, וכו').
        """
        try:
            if not HAS_REPLICATE:
                raise Exception('Replicate not configured')
            
            # Style-specific prompts - מותאם ל-3 הסגנונות החדשים
            style_prompts = {
                # 3 הסגנונות החדשים - צבעים חיים ועשירים
                "warm_realistic": "high quality, detailed, warm vivid tones, rich natural colors",
                "classic_illustration": "children's book illustration style, vibrant saturated colors, bright cheerful palette, soft lighting, detailed",
                "soft_illustration": "hand-drawn watercolor illustration, soft pastel washes, painterly, dreamy, NOT photorealistic",
                # legacy
                "illustration": "children's book illustration style, vibrant colors, soft lighting, detailed",
                "watercolor": "watercolor painting, soft colors, artistic, gentle",
                "cartoon": "cartoon style, bold colors, playful, fun",
                "realistic": "realistic digital art, detailed, professional",
                "comic": "comic book style, bold lines, vibrant"
            }
            
            style_prompt = style_prompts.get(style_name, style_prompts["classic_illustration"])
            
            # Translate Hebrew to English if needed (still useful for legacy/non-LoRA mode)
            if any(ord(c) > 127 for c in prompt):
                prompt = self.translate_to_english(prompt)
            
            # 🎯 בניית פרומפט אופטימלית עבור LoRA
            outfit_part = f"{outfit}" if outfit else ""
            
            # 📖 הוספת Character Bible descriptions
            char_part = ""
            has_other_chars = False
            if character_descriptions:
                # הפרדה ברורה: כל דמות מתוארת בנפרד
                char_list = ". ".join(character_descriptions)
                char_part = char_list
                has_other_chars = True
            
            # 🧹 ניקוי שוליים - למנוע רגליים/ידיים חתוכות
            clean_composition = (
                "clean composition, well-framed, centered subjects, "
                "full scene visible, no cropped people, no body parts at edges"
            )
            
            # 🎨 עיגון סגנון - 3 וריאציות מובחנות לפי style_name
            # מ"צילום ריאליסטי" עד "איור רך"
            style_anchors = {
                # 📷 ריאליסטי - נראה כמו צילום אמיתי של הילד
                'warm_realistic': {
                    'start': "a realistic photograph, professional portrait photography, ",
                    'end': (
                        ", photorealistic, natural skin texture, realistic lighting, "
                        "shot on DSLR camera, sharp focus, lifelike, "
                        "real photograph quality, warm natural tones"
                    )
                },
                # 🎨 איור קלאסי - ספר ילדים סטנדרטי
                'classic_illustration': {
                    'start': "a classic children's book illustration, ",
                    'end': (
                        ", traditional storybook illustration art, "
                        "vibrant rich colors, bright and cheerful palette, "
                        "clean illustration style, "
                        "professional children's book art"
                    )
                },
                # ✏️ איור רך - עדין, חלומי, painterly
                # 🔬 24/5: חוזק עם "watercolor" + "hand-drawn" + "not photorealistic"
                # כדי שה-LoRA הריאליסטי לא ינצח. בלי המילים האלה — FLUX מחזיר ריאליזם.
                'soft_illustration': {
                    'start': "a hand-drawn watercolor children's book illustration, soft painterly storybook art, ",
                    'end': (
                        ", traditional watercolor painting on paper, "
                        "visible brush strokes, soft pastel washes, "
                        "delicate hand-painted illustration, "
                        "dreamy storybook art, NOT photorealistic, NOT a photograph, "
                        "artistic illustration style"
                    )
                },
            }
            # ברירת מחדל - איור קלאסי
            anchor = style_anchors.get(style_name, style_anchors['classic_illustration'])
            style_anchor_start = anchor['start']
            style_anchor_end = anchor['end']
            
            # 🎨 24/5: STYLE HARDENING — תזכורת אנטי-ריאליסטית עבור סגנונות איור
            # בפרומפטים מורכבים (סצנה עם דרקון, ים, וכו'), ה-anchor הראשי "נשכח".
            # הוספת חיזוק שמופיע 3 פעמים בפרומפט מבטיחה שהסגנון יישמר.
            if style_name in ('classic_illustration', 'soft_illustration'):
                style_hardener = (
                    " — this is an ILLUSTRATION not a photograph, "
                    "drawn/painted art style, NOT photorealistic, NOT a real photo"
                )
            else:
                style_hardener = ""
            
            # 🎯 24/5: TRIGGER REINFORCEMENT — ה-trigger מופיע 3 פעמים בפרומפט
            # במקום פעם אחת. בלי זה, בפרומפטים מורכבים FLUX לפעמים "שוכח" להפעיל את ה-LoRA
            # והתוצאה היא ילד גנרי במקום הילד האמיתי.
            trigger_strong = f"{trigger_word}, {trigger_word}"
            
            # 🎯 בניית הפרומפט - מבנה מובנה עם הפרדה ברורה בין דמויות
            # 🚻 מילת מגדר - מונעת "החלקה" של הילד למגדר אחר
            gender_word = "young girl" if child_gender == 'girl' else "young boy"
            
            if has_other_chars:
                # 🐕 יש דמות נוספת (כלב/חבר) - מבנה מפורש שמפריד ביניהן
                # חשוב: מתארים את הילד כיחידה סגורה, ואז הדמות כיחידה נפרדת
                # כדי שה-outfit לא "ידלוף" לכלב
                child_block = (
                    f"ONE human {gender_word} as main character "
                    f"({trigger_strong}), the child wearing {outfit_part}, "
                    f"detailed facial features, recognizable face"
                    if outfit_part else
                    f"ONE human {gender_word} as main character "
                    f"({trigger_strong}), detailed facial features, recognizable face"
                )
                # 🐕 חיזוק הדמות הנלווית: התיאור מוזכר פעמיים -
                # פעם כהגדרה מלאה ופעם כתזכורת בסוף - כדי שה-LoRA
                # (שמאומן בכבדות על הילד) לא "יבלע" אותה.
                # 🚨 הוראות אנטי-זליגה: ה-LoRA המאומן על הילד נוטה
                # להחיל את פני הילד גם על דמויות אחרות (חיות, קופים).
                # ההוראות החזקות למטה מונעות זאת.
                full_prompt = (
                    f"{style_anchor_start}"
                    f"a scene with exactly ONE human child and ONE non-human animal: "
                    f"FIRST: {child_block}. "
                    f"SECOND: an animal companion - {char_part}. "
                    f"CRITICAL: the animal has the head and face of {char_part} - "
                    f"NOT a human face, NOT the child's face, the animal is fully animal. "
                    f"The animal MUST look exactly like this description "
                    f"in every detail: {char_part}. "
                    f"The animal is a separate creature with its own animal head, "
                    f"the animal wears no clothes, the animal is not anthropomorphic. "
                    f"IMPORTANT: only ONE single human child in the entire image, "
                    f"the trigger word ({trigger_word}) applies ONLY to the human child, "
                    f"absolutely no second child, no duplicate child, "
                    f"no other kids, no children in the background, "
                    f"no human face on the animal. "
                    f"Scene: {prompt}, "
                    f"the human child is {trigger_word}, "  # 🎯 חיזוק שלישי של trigger
                    f"{style_prompt}, {clean_composition}"
                    f"{style_anchor_end}{style_hardener}, "
                    f"consistent animal appearance: {char_part}, "
                    f"exactly one human child only, the animal has an animal face"
                )
            else:
                # 👤 רק הילד לבד
                outfit_clause = f"the child wearing {outfit_part}, " if outfit_part else ""
                full_prompt = (
                    f"{style_anchor_start}"
                    f"solo portrait of ONE single human {gender_word}, "
                    f"exactly one child in the entire image, "
                    f"only one person, no duplicate figures, "
                    f"no second child, no twin, no other kids in the background, "
                    f"{trigger_strong}, {outfit_clause}"
                    f"detailed facial features, recognizable face, expressive eyes, "
                    f"the child is the main focus of the scene, "
                    f"{prompt}, "
                    f"the child is {trigger_word}, "  # 🎯 חיזוק שלישי של trigger
                    f"{style_prompt}, {clean_composition}"
                    f"{style_anchor_end}{style_hardener}, "
                    f"exactly one human child only, single child"
                )
            
            print(f"  🎨 Generating with LoRA...")
            print(f"  📝 Prompt: {full_prompt[:280]}...")
            
            # 🔄 Retry logic for rate limit (429) errors
            def _run_with_retry(model_target, input_params, max_retries=3):
                """מריץ replicate.run עם retry אוטומטי במקרה של rate limit"""
                last_error = None
                for attempt in range(max_retries):
                    try:
                        return replicate.run(model_target, input=input_params)
                    except Exception as e:
                        last_error = e
                        err_str = str(e).lower()
                        # אם זה rate limit - חכה ונסה שוב
                        if '429' in err_str or 'throttled' in err_str or 'rate limit' in err_str:
                            wait_time = 30 if attempt == 0 else 60
                            print(f"  ⏸️  Rate limit hit (attempt {attempt+1}/{max_retries}), waiting {wait_time}s...")
                            time.sleep(wait_time)
                            continue
                        # שגיאה אחרת - נזרק מיד
                        raise
                # אם הגענו לכאן - כל הניסיונות נכשלו
                raise last_error
            
            # 🎲 בניית input params - עם seed אם ניתן (לעקביות)
            base_input = {
                "num_outputs": 1,
                "aspect_ratio": "4:3",
                "output_format": "jpg",
                "guidance_scale": 3.5,
                "output_quality": 90,
                "num_inference_steps": 28,
                "disable_safety_checker": True
            }
            if seed is not None:
                base_input["seed"] = int(seed)
                print(f"  🎲 Using fixed seed: {seed}")
            
            # 🐕 הורדה אוטומטית של lora_scale כשיש דמות נוספת (חיה/חבר):
            # ה-LoRA נוטה "להחיל" את פני הילד גם על דמויות אחרות.
            # הורדה של 0.1 ב-scale מספיקה כדי לתת לדמות השנייה נשימה,
            # בלי לאבד את הדמיון של הילד הראשי.
            effective_lora_scale = lora_scale
            if has_other_chars and effective_lora_scale > 0.85:
                effective_lora_scale = round(effective_lora_scale - 0.1, 2)
                print(f"  🐕 Other character in scene - reducing lora_scale "
                      f"from {lora_scale} to {effective_lora_scale}")
            
            print(f"  💪 LoRA scale: {effective_lora_scale}")
            
            # 🎯 STRATEGY 1 (Preferred): Use the trained model directly
            if lora_version:
                print(f"  📌 Using trained model directly (best quality)")
                strategy1_input = dict(base_input)
                strategy1_input["prompt"] = full_prompt
                strategy1_input["lora_scale"] = effective_lora_scale
                output = _run_with_retry(lora_version, strategy1_input)
            else:
                # 🔧 STRATEGY 2 (Fallback/Legacy): Use ostris/flux-dev-lora with weights URL
                print(f"  ⚠️  No version, using legacy ostris/flux-dev-lora")
                strategy2_input = dict(base_input)
                strategy2_input["prompt"] = full_prompt
                strategy2_input["lora_url"] = lora_url
                strategy2_input["lora_scale"] = effective_lora_scale
                output = _run_with_retry("ostris/flux-dev-lora", strategy2_input)
            
            if output and len(output) > 0:
                image_url = output[0]
                
                # Download
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                
                req = urllib.request.Request(
                    image_url,
                    headers={'User-Agent': 'Mozilla/5.0'}
                )
                
                with urllib.request.urlopen(req, timeout=60, context=ctx) as response:
                    img_data = response.read()
                
                img_b64 = base64.b64encode(img_data).decode()
                print(f"  ✅ LoRA image generated! ({len(img_data)} bytes)")
                return f"data:image/jpeg;base64,{img_b64}"
            
            raise Exception("No output from LoRA generation")
            
        except Exception as e:
            print(f"  ❌ LoRA generation error: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def handle_generate_pdf(self):
        """יוצר PDF עם תמונות ועברית - גרסה משופרת"""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            from reportlab.lib.utils import simpleSplit, ImageReader
            from PIL import Image as PILImage
            
            try:
                # עברית צריכה רק bidi - לא arabic_reshaper!
                from bidi.algorithm import get_display
                has_bidi = True
            except:
                has_bidi = False
                print("  ⚠️ python-bidi not available - Hebrew will be reversed!")
            
            def clean_text_for_pdf(text):
                """מנקה תווים מיוחדים שהפונט NotoSansHebrew לא תומך בהם"""
                if not text:
                    return text
                # מילון החלפות - תווים בעייתיים → תווים רגילים שיש בכל פונט
                replacements = {
                    # ציטוטים מתולתלים → ציטוטים רגילים
                    '\u201C': '"',  # left double quotation mark
                    '\u201D': '"',  # right double quotation mark
                    '\u2018': "'",  # left single quotation mark
                    '\u2019': "'",  # right single quotation mark
                    '\u201E': '"',  # double low-9 quotation mark
                    '\u201A': "'",  # single low-9 quotation mark
                    # גרש וגרשיים עבריים → תווים רגילים
                    '\u05F3': "'",  # Hebrew geresh
                    '\u05F4': '"',  # Hebrew gershayim
                    # נקודות, מקפים מיוחדים
                    '\u2026': '...',  # ellipsis
                    '\u2013': '-',    # en dash
                    '\u2014': '-',    # em dash
                    '\u2012': '-',    # figure dash
                    '\u2015': '-',    # horizontal bar
                    '\u00A0': ' ',    # non-breaking space
                    '\u200E': '',     # left-to-right mark (invisible)
                    '\u200F': '',     # right-to-left mark (invisible)
                    '\u200B': '',     # zero-width space
                    '\u200C': '',     # zero-width non-joiner
                    '\u200D': '',     # zero-width joiner
                    '\u2028': ' ',    # line separator
                    '\u2029': ' ',    # paragraph separator
                    '\uFEFF': '',     # byte order mark
                    '\u061C': '',     # arabic letter mark
                }
                for old, new in replacements.items():
                    text = text.replace(old, new)
                
                # 🛡️ שלב הגנה אחרון - מסיר כל תו שהפונט העברי לא מכיר.
                # NotoSansHebrew תומך בעברית + לטינית בסיסית + פיסוק נפוץ,
                # אבל תווים אחרים (סמלים, אמוג'י, פיסוק נדיר) יוצאים ריבועים.
                # נשמור רק: עברית, לטינית בסיסית, ספרות, רווחים ופיסוק נפוץ.
                allowed_punct = set(' .,!?;:\'"()[]{}-/\n\t<>=+*%&@#~`^|\\$_')
                cleaned_chars = []
                for ch in text:
                    code = ord(ch)
                    is_hebrew = 0x0590 <= code <= 0x05FF
                    is_basic_latin = code < 0x0080
                    if is_hebrew or is_basic_latin or ch in allowed_punct:
                        cleaned_chars.append(ch)
                    # אחרת - מדלגים על התו (במקום להציג ריבוע)
                return ''.join(cleaned_chars)
            
            def fix_hebrew(text):
                """מסדר עברית לימין-לשמאל.
                
                ⚠️ חשוב: עברית צריכה רק bidi (סידור RTL), ולא arabic_reshaper!
                arabic_reshaper מיועד לערבית - שם האותיות משנות צורה לפי מיקום.
                עברית לא עושה את זה. הרצת reshaper על עברית מוסיפה תווים
                מיוחדים שהפונט לא תומך בהם → ריבועים בפלט!
                """
                # ניקוי תווים מיוחדים תחילה
                text = clean_text_for_pdf(text)
                
                if not has_bidi:
                    return text
                try:
                    # רק bidi - בלי reshaper! זה הפתרון לריבועים.
                    return get_display(text)
                except Exception as e:
                    print(f"  ⚠️ Hebrew bidi failed: {e}")
                    return text
            
            def load_image_for_pdf(image_url):
                """מקבל URL של תמונה (יכול להיות base64 או http) ומחזיר ImageReader"""
                if not image_url:
                    return None
                try:
                    if image_url.startswith('data:image'):
                        # base64
                        header, b64data = image_url.split(',', 1)
                        img_bytes = base64.b64decode(b64data)
                    elif image_url.startswith('http'):
                        # הורד מ-URL
                        ctx = ssl.create_default_context()
                        ctx.check_hostname = False
                        ctx.verify_mode = ssl.CERT_NONE
                        req = urllib.request.Request(image_url, headers={'User-Agent': 'Mozilla/5.0'})
                        with urllib.request.urlopen(req, timeout=30, context=ctx) as response:
                            img_bytes = response.read()
                    else:
                        return None
                    
                    img_buffer = BytesIO(img_bytes)
                    pil_img = PILImage.open(img_buffer)
                    # Convert to RGB if needed (for transparency issues)
                    if pil_img.mode in ('RGBA', 'LA', 'P'):
                        pil_img = pil_img.convert('RGB')
                    output = BytesIO()
                    pil_img.save(output, format='JPEG', quality=85)
                    output.seek(0)
                    return ImageReader(output)
                except Exception as e:
                    print(f"  ⚠️ Could not load image: {e}")
                    return None
            
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            story_data = json.loads(post_data.decode('utf-8'))
            
            child_name = story_data.get('childName', 'ילד')
            pages = story_data.get('pages', [])
            
            print(f"📄 PDF for: {child_name}")
            print(f"   Pages: {len(pages)}")
            print(f"   Hebrew support: {'✅' if has_bidi else '❌'}")
            
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)
            width, height = A4
            
            # 🇮🇱 NEW: הורדה אוטומטית של פונט עברי אמיתי מ-Google Fonts
            # זה מבטיח שעברית תיראה תקין ב-PDF, ולא ג'יבריש
            HEBREW_FONT_PATH = '/tmp/NotoSansHebrew-Regular.ttf'
            
            if not os.path.exists(HEBREW_FONT_PATH):
                try:
                    print(f"   🌐 Downloading Hebrew font from Google Fonts...")
                    font_url = "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/NotoSansHebrew/NotoSansHebrew-Regular.ttf"
                    
                    ctx = ssl.create_default_context()
                    ctx.check_hostname = False
                    ctx.verify_mode = ssl.CERT_NONE
                    
                    req = urllib.request.Request(
                        font_url,
                        headers={'User-Agent': 'Mozilla/5.0'}
                    )
                    with urllib.request.urlopen(req, timeout=30, context=ctx) as response:
                        font_data = response.read()
                    
                    with open(HEBREW_FONT_PATH, 'wb') as f:
                        f.write(font_data)
                    print(f"   ✅ Hebrew font downloaded: {len(font_data)} bytes")
                except Exception as font_err:
                    print(f"   ⚠️ Failed to download Hebrew font: {font_err}")
            
            # Register Hebrew font - first try the downloaded one, then system fonts
            hebrew_font = 'Helvetica'
            font_paths = [
                HEBREW_FONT_PATH,  # 🥇 First try our downloaded font
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
                '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
                '/usr/share/fonts/truetype/freefont/FreeSans.ttf',
                'C:\\Windows\\Fonts\\arial.ttf'
            ]
            
            for font_path in font_paths:
                try:
                    if os.path.exists(font_path):
                        pdfmetrics.registerFont(TTFont('Hebrew', font_path))
                        hebrew_font = 'Hebrew'
                        print(f"   📝 Font registered: {font_path}")
                        break
                except Exception as e:
                    print(f"   ⚠️ Font failed: {font_path} - {e}")
                    continue
            
            # ====== Cover Page ======
            c.setFillColorRGB(0.99, 0.96, 0.89)  # cream
            c.rect(0, 0, width, height, stroke=0, fill=1)
            c.setFillColorRGB(0.16, 0.13, 0.09)  # dark
            c.setFont(hebrew_font, 36)
            title = fix_hebrew(f"הספר של {child_name}")
            title_width = c.stringWidth(title, hebrew_font, 36)
            c.drawString((width - title_width) / 2, height - 200, title)
            
            c.setFont(hebrew_font, 16)
            subtitle = fix_hebrew("מבית לילוש טובוש")
            sub_width = c.stringWidth(subtitle, hebrew_font, 16)
            c.drawString((width - sub_width) / 2, height - 240, subtitle)
            c.showPage()
            
            # ====== Story Pages ======
            for i, page in enumerate(pages):
                print(f"   🖼️ Adding page {i+1}/{len(pages)}...")
                
                # Page number
                c.setFillColorRGB(0.36, 0.29, 0.21)
                c.setFont(hebrew_font, 10)
                page_num = fix_hebrew(f"עמוד {i + 1}")
                c.drawString(width - 100, 30, page_num)
                
                # ===== IMAGE =====
                image_url = page.get('imageUrl')
                if image_url:
                    img_reader = load_image_for_pdf(image_url)
                    if img_reader:
                        # Image position - top half of page
                        img_width = width - 80  # margin 40 each side
                        img_height = height * 0.55  # top 55% of page
                        img_x = 40
                        img_y = height - img_height - 60  # 60 from top
                        
                        try:
                            c.drawImage(
                                img_reader,
                                img_x, img_y,
                                width=img_width,
                                height=img_height,
                                preserveAspectRatio=True,
                                anchor='c'
                            )
                            print(f"      ✅ Image added")
                        except Exception as img_err:
                            print(f"      ⚠️ Image draw failed: {img_err}")
                
                # ===== TEXT =====
                c.setFillColorRGB(0.16, 0.13, 0.09)
                c.setFont(hebrew_font, 16)
                text = page.get('text', '')
                
                # Split and reverse for Hebrew (each line individually)
                if has_bidi and any(ord(ch) > 127 for ch in text):
                    # Hebrew: split, fix each line, then layout
                    raw_lines = simpleSplit(text, hebrew_font, 16, width - 100)
                    text_lines = [fix_hebrew(line) for line in raw_lines]
                else:
                    text_lines = simpleSplit(text, hebrew_font, 16, width - 100)
                
                # Text in bottom half
                y_position = height * 0.35  # ~35% from bottom
                for line in text_lines:
                    line_width = c.stringWidth(line, hebrew_font, 16)
                    c.drawString((width - line_width) / 2, y_position, line)
                    y_position -= 24
                
                c.showPage()
            
            c.save()
            
            pdf_data = buffer.getvalue()
            buffer.close()
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/pdf')
            
            # 🔧 FIX: תמיכה בשמות קבצים בעברית ע"פ RFC 5987
            try:
                child_name.encode('latin-1')
                self.send_header('Content-Disposition', f'attachment; filename="lilush_{child_name}.pdf"')
            except UnicodeEncodeError:
                from urllib.parse import quote
                ascii_fallback = "lilush_book.pdf"
                utf8_filename = quote(f"lilush_{child_name}.pdf", safe='')
                self.send_header(
                    'Content-Disposition',
                    f'attachment; filename="{ascii_fallback}"; filename*=UTF-8\'\'{utf8_filename}'
                )
            
            self.send_header('Content-Length', len(pdf_data))
            self.end_headers()
            self.wfile.write(pdf_data)
            
            print(f"✅ PDF done ({len(pdf_data)} bytes)")
            
        except Exception as e:
            print(f"❌ PDF error: {str(e)}")
            import traceback
            traceback.print_exc()
            self.send_json_response({'error': str(e)}, status=500)
    
    def send_json_response(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def log_message(self, format, *args):
        if self.path.startswith('/api/'):
            return
        SimpleHTTPRequestHandler.log_message(self, format, *args)
    
    # ==========================================
    # 🤖 AI Training Endpoints (NEW!)
    # ==========================================
    
    def handle_train_model(self):
        """מאמן מודל AI על בסיס תמונות הילד"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            photos = data.get('photos', [])
            child_name = data.get('child_name', 'child')
            
            print(f"\n🤖 Starting AI Training")
            print(f"📸 Photos: {len(photos)}")
            print(f"👤 Name: {child_name}")
            
            if not REPLICATE_API_TOKEN:
                raise Exception('Replicate API token not configured')
            
            if len(photos) < 5:
                raise Exception('Need at least 5 photos for training')
            
            # Start training
            training_id = self.start_replicate_training(photos, child_name)
            
            if training_id:
                print(f"✅ Training started: {training_id}")
                
                self.send_json_response({
                    'success': True,
                    'training_id': training_id,
                    'message': 'Training started successfully',
                    'estimated_time': '5-10 minutes'
                })
            else:
                raise Exception('Failed to start training')
                
        except Exception as e:
            print(f"❌ Training error: {str(e)}")
            import traceback
            traceback.print_exc()
            self.send_json_response({'error': str(e)}, status=500)
    
    def start_replicate_training(self, photos, child_name):
        """מתחיל אימון ב-Replicate - גרסה פשוטה"""
        try:
            if not REPLICATE_API_TOKEN:
                raise Exception('No Replicate token')
            
            print(f"  🚀 REAL Replicate Training starting...")
            print(f"  📸 Photos: {len(photos)}")
            
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            # Create ZIP from photos
            zip_b64 = self.create_zip_from_photos(photos)
            if not zip_b64:
                raise Exception('Failed to create ZIP')
            
            # Simplified Training - try without specific version first
            print(f"  🔍 Checking available training options...")
            
            # Try simple prediction first to test
            training_data = {
                "input": {
                    "input_images": f"data:application/zip;base64,{zip_b64}",
                    "steps": 500,
                    "trigger_word": child_name
                }
            }
            
            headers = {
                'Authorization': f'Token {REPLICATE_API_TOKEN}',
                'Content-Type': 'application/json'
            }
            
            # Try the trainings endpoint
            training_url = 'https://api.replicate.com/v1/models/ostris/flux-dev-lora-trainer/versions/4a78013f38e8c316fb9bdb7b8b7f81c0059fc7e127e60f03c90fd639b3e6408c/trainings'
            
            req = urllib.request.Request(
                'https://api.replicate.com/v1/trainings',
                data=json.dumps(training_data).encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            print(f"  📤 Sending training request to Replicate...")
            
            with urllib.request.urlopen(req, timeout=60, context=ctx) as response:
                result = json.loads(response.read().decode('utf-8'))
                training_id = result['id']
            
            print(f"  ✅ Training started: {training_id}")
            print(f"  ⏱️  This will take ~10 minutes...")
            
            return training_id
                
        except Exception as e:
            print(f"  ❌ Training error: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
    
    def create_zip_from_photos(self, photos):
        """יוצר ZIP מתמונות base64"""
        try:
            import zipfile
            from io import BytesIO
            
            zip_buffer = BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for i, photo_b64 in enumerate(photos):
                    # Remove data:image/... prefix
                    if ',' in photo_b64:
                        photo_b64 = photo_b64.split(',')[1]
                    
                    photo_data = base64.b64decode(photo_b64)
                    zip_file.writestr(f'photo_{i+1}.jpg', photo_data)
            
            zip_data = zip_buffer.getvalue()
            return base64.b64encode(zip_data).decode()
            
        except Exception as e:
            print(f"  ⚠️ ZIP creation error: {str(e)}")
            return None
    
    def handle_training_status(self, training_id):
        """בודק סטטוס של training"""
        try:
            # Mock implementation for MVP
            # In production, this would check real Replicate API
            
            if training_id.startswith('mock_training_'):
                # Simulate training completion after a short delay
                # In real implementation, this would poll Replicate
                
                # Extract model ID from training ID
                model_id = training_id.replace('mock_training_', '')
                
                # For demo purposes, mark as succeeded immediately
                response_data = {
                    'status': 'succeeded',
                    'id': training_id,
                    'model_id': model_id
                }
                
                print(f"✅ Mock training completed: {model_id}")
                
                self.send_json_response(response_data)
                return
            
            # If it's a real Replicate training ID, check it properly
            if not REPLICATE_API_TOKEN:
                raise Exception('Replicate API token not configured')
            
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            headers = {
                'Authorization': f'Token {REPLICATE_API_TOKEN}',
                'Content-Type': 'application/json'
            }
            
            req = urllib.request.Request(
                f'https://api.replicate.com/v1/trainings/{training_id}',
                headers=headers
            )
            
            with urllib.request.urlopen(req, timeout=30, context=ctx) as response:
                result = json.loads(response.read().decode('utf-8'))
                
                status = result.get('status')
                
                response_data = {
                    'status': status,
                    'id': training_id
                }
                
                if status == 'succeeded':
                    model_version = result.get('output', {}).get('version')
                    if model_version:
                        response_data['model_id'] = model_version
                        print(f"✅ Training completed: {model_version}")
                
                elif status == 'failed':
                    error = result.get('error', 'Unknown error')
                    response_data['error'] = error
                    print(f"❌ Training failed: {error}")
                
                self.send_json_response(response_data)
                
        except Exception as e:
            print(f"❌ Status check error: {str(e)}")
            self.send_json_response({'error': str(e)}, status=500)


def run_server(port=None):
    if port is None:
        port = int(os.environ.get('PORT', 8000))
    
    print("\n" + "="*60)
    print("🚀 לילוש טובוש")
    print("="*60)
    print(f"📸 Images: {IMAGE_MODE}")
    print(f"👤 Face Swap: {'ON' if FAL_KEY and HAS_FAL else 'OFF'}")
    print(f"📡 Port: {port}")
    print("="*60 + "\n")
    
    server_address = ('', port)
    httpd = HTTPServer(server_address, CORSRequestHandler)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Stopped!")


if __name__ == '__main__':
    run_server()
